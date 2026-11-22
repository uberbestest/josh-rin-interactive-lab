"""Durable, local accounting for one-shot API runs; no provider or OS-specific APIs.

SQLite is authoritative. JSON exports are evidence copies, never restart authority.
An unpriced reservation means a request might have reached the provider. It stays
reserved indefinitely and prevents another live run until a separate reconciliation
procedure exists. There is deliberately no reset or automatic resume operation.
"""
from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal
import json
from pathlib import Path
import sqlite3

from common import canonical, digest, money, now


SCHEMA_VERSION = 1
APPLICATION_ID = 0x4A524C42
ZERO_HASH = "0" * 64
CONTROL_EVENTS = {"run_started", "request_reserved", "response_saved",
                  "request_settled", "run_halted", "run_finished", "halt_reviewed"}
SCHEMA = {
    "runs": ("table", """CREATE TABLE runs (
        id TEXT PRIMARY KEY, mode TEXT NOT NULL CHECK(mode IN ('live','fixture')),
        protocol_id TEXT NOT NULL, plan TEXT NOT NULL, metadata TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('RUNNING','HALTED','COMPLETED')),
        summary TEXT, started_utc TEXT NOT NULL, ended_utc TEXT, halt_reason TEXT
    )"""),
    "live_protocol_once": ("index", """CREATE UNIQUE INDEX live_protocol_once
        ON runs(protocol_id) WHERE mode = 'live'"""),
    "requests": ("table", """CREATE TABLE requests (
        id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
        case_id TEXT NOT NULL, payload TEXT NOT NULL, reserve_usd TEXT NOT NULL,
        cost_usd TEXT, state TEXT NOT NULL
          CHECK(state IN ('RESERVED','RESPONSE_SAVED','SETTLED')),
        response TEXT, calculation TEXT, reserved_utc TEXT NOT NULL,
        response_utc TEXT, settled_utc TEXT
    )"""),
    "events": ("table", """CREATE TABLE events (
        run_id TEXT NOT NULL REFERENCES runs(id), sequence INTEGER NOT NULL,
        created_utc TEXT NOT NULL, kind TEXT NOT NULL, data TEXT NOT NULL,
        previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL,
        PRIMARY KEY(run_id, sequence)
    )"""),
    "events_no_update": ("trigger", """CREATE TRIGGER events_no_update
        BEFORE UPDATE ON events BEGIN
          SELECT RAISE(ABORT, 'Events are immutable'); END"""),
    "events_no_delete": ("trigger", """CREATE TRIGGER events_no_delete
        BEFORE DELETE ON events BEGIN
          SELECT RAISE(ABORT, 'Events are immutable'); END"""),
}


def _amount(value):
    return str(money(value))


def _plain(value):
    """Validate and detach JSON values, rejecting accidental credential fields."""
    def check(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise ValueError("JSON object keys must be strings")
                if key.lower().replace("-", "_") in {
                    "authorization", "proxy_authorization", "api_key",
                    "openai_api_key", "access_token", "refresh_token", "password",
                }:
                    raise ValueError("Credentials must not enter the journal")
                check(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                check(child)
    check(value)
    return json.loads(canonical(value))


def _plan(value):
    value = _plain(value)
    if not isinstance(value, dict) or not isinstance(value.get("protocol_id"), str) or not value["protocol_id"]:
        raise ValueError("Plan requires a nonempty protocol_id")
    for field in ("max_estimated_spend_usd", "max_estimated_spend_per_case_usd"):
        if field not in value:
            raise ValueError(f"Plan requires {field}")
        money(value[field])
    count = value.get("max_calls_per_case")
    if type(count) is not int or count < 1:
        raise ValueError("max_calls_per_case must be a positive integer")
    assignments = value.get("assignments")
    if not isinstance(assignments, list) or not assignments:
        raise ValueError("Plan requires assignments")
    seen = set()
    for assignment in assignments:
        if not isinstance(assignment, dict):
            raise ValueError("Assignment must be an object")
        case_id = assignment.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ValueError("Assignment case_id values must be unique nonempty strings")
        if "case" not in assignment or not isinstance(assignment.get("model"), str):
            raise ValueError("Assignment requires case and model")
        seen.add(case_id)
    return value


def _totals(requests):
    known = sum((money(r["cost_usd"]) for r in requests if r["cost_usd"] is not None), Decimal(0))
    unresolved = [r for r in requests if r["cost_usd"] is None]
    reserve = sum((money(r["reserve_usd"]) for r in unresolved), Decimal(0))
    return {
        "known_estimated_spend_usd": str(known),
        "estimated_total_cost_usd": None if unresolved else str(known),
        "unresolved_reserve_usd": str(reserve),
        "estimated_exposure_usd": str(known + reserve),
        "unresolved_requests": len(unresolved),
        "attempted_requests": len(requests),
    }


class ReserveRefused(RuntimeError):
    def __init__(self, reason, explanation):
        super().__init__(explanation)
        self.reason = reason


def _allow_reserve(run, requests, case_id, amount):
    if run["status"] != "RUNNING" or run["ended_utc"] is not None:
        raise RuntimeError("Run is not active; no more requests are permitted")
    if any(r["cost_usd"] is None for r in requests):
        raise RuntimeError("An unresolved request reserve blocks further requests")
    plan = run["plan"]
    if case_id not in {a["case_id"] for a in plan["assignments"]}:
        raise ValueError("case_id is not a frozen assignment")
    case_requests = [r for r in requests if r["case_id"] == case_id]
    if len(case_requests) >= plan["max_calls_per_case"]:
        raise ReserveRefused("CALL_LIMIT", "Case request ceiling reached")
    if money(_totals(requests)["estimated_exposure_usd"]) + amount > money(plan["max_estimated_spend_usd"]):
        raise ReserveRefused("RUN_BUDGET_EXCEEDED", "Run spending reserve would exceed the ceiling")
    if money(_totals(case_requests)["estimated_exposure_usd"]) + amount > money(plan["max_estimated_spend_per_case_usd"]):
        raise ReserveRefused("CASE_BUDGET_EXCEEDED", "Case spending reserve would exceed the ceiling")


class Journal:
    def __init__(self, path, read_only=False):
        supplied = Path(path).expanduser()
        if supplied.is_symlink():
            raise ValueError("Journal database must be a regular local path, not a symlink")
        self.path = supplied.resolve()
        self.read_only = read_only
        if not read_only:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        address = self.path.as_uri() + "?mode=ro" if read_only else str(self.path)
        self.db = sqlite3.connect(address, timeout=30, isolation_level=None, uri=read_only)
        self.db.row_factory = sqlite3.Row
        try:
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.execute("PRAGMA trusted_schema=OFF")
            # Inspect an existing database before making persistent mode changes.
            # Never turn an unrelated SQLite file into this application's journal.
            empty = (not self._schema()
                     and self.db.execute("PRAGMA user_version").fetchone()[0] == 0
                     and self.db.execute("PRAGMA application_id").fetchone()[0] == 0)
            if not empty:
                self._check_schema()
            mode = self.db.execute("PRAGMA journal_mode=WAL" if empty and not read_only else "PRAGMA journal_mode").fetchone()[0]
            self.db.execute("PRAGMA synchronous=FULL")
            if mode.lower() != "wal" or self.db.execute("PRAGMA synchronous").fetchone()[0] != 2:
                raise RuntimeError("Journal requires SQLite WAL and synchronous=FULL")
            with self._transaction(write=not read_only):
                objects = self._schema()
                version = self.db.execute("PRAGMA user_version").fetchone()[0]
                app_id = self.db.execute("PRAGMA application_id").fetchone()[0]
                if not objects and version == 0 and app_id == 0 and not read_only:
                    for _, sql in SCHEMA.values():
                        self.db.execute(sql)
                    self.db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
                    self.db.execute(f"PRAGMA application_id={APPLICATION_ID}")
                self._check_schema()
                for row in self.db.execute("SELECT id FROM runs"):
                    self._verify(self._snapshot(row["id"]))
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    @contextmanager
    def _transaction(self, write=True):
        if write and self.read_only:
            raise RuntimeError("Journal is read-only")
        self.db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def _schema(self):
        return {r["name"]: (r["type"], " ".join(r["sql"].split())) for r in self.db.execute(
            "SELECT name,type,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%'")}

    def _check_schema(self):
        expected = {name: (kind, " ".join(sql.split())) for name, (kind, sql) in SCHEMA.items()}
        if (self._schema() != expected
                or self.db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION
                or self.db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID):
            raise RuntimeError("Unknown or modified journal schema; refusing to continue")

    def _append(self, run_id, kind, data):
        previous = self.db.execute("SELECT sequence,event_hash FROM events WHERE run_id=? ORDER BY sequence DESC LIMIT 1", (run_id,)).fetchone()
        event = {"run_id": run_id, "sequence": previous[0] + 1 if previous else 1,
                 "created_utc": now(), "kind": kind, "data": _plain(data),
                 "previous_hash": previous[1] if previous else ZERO_HASH}
        event["event_hash"] = digest(event)
        self.db.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?)", (
            run_id, event["sequence"], event["created_utc"], kind, canonical(event["data"]),
            event["previous_hash"], event["event_hash"]))
        return event

    def _snapshot(self, run_id):
        row = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown run_id")
        run = dict(row)
        protocol_id = run.pop("protocol_id")
        for field in ("plan", "metadata", "summary"):
            run[field] = json.loads(run[field]) if run[field] is not None else None
        if protocol_id != run["plan"].get("protocol_id"):
            raise RuntimeError("Protocol claim does not match the frozen plan")
        requests = []
        for row in self.db.execute("SELECT * FROM requests WHERE run_id=? ORDER BY rowid", (run_id,)):
            request = dict(row)
            for field in ("payload", "response", "calculation"):
                request[field] = json.loads(request[field]) if request[field] is not None else None
            requests.append(request)
        events = []
        for row in self.db.execute("SELECT * FROM events WHERE run_id=? ORDER BY sequence", (run_id,)):
            event = dict(row)
            event["data"] = json.loads(event["data"])
            events.append(event)
        return {"run": run, "requests": requests, "events": events, "totals": _totals(requests)}

    def snapshot(self, run_id):
        with self._transaction(write=False):
            self._check_schema()
            snapshot = self._snapshot(run_id)
            self._verify(snapshot)
            return snapshot

    def _current(self, run_id):
        self._check_schema()
        snapshot = self._snapshot(run_id)
        self._verify(snapshot)
        return snapshot

    def start_run(self, run_id, mode, plan, metadata):
        if not isinstance(run_id, str) or not run_id or mode not in {"live", "fixture"}:
            raise ValueError("Run requires a nonempty id and live or fixture mode")
        plan, metadata = _plan(plan), _plain(metadata)
        with self._transaction():
            self._check_schema()
            for row in self.db.execute("SELECT id FROM runs"):
                self._verify(self._snapshot(row["id"]))
            if self.db.execute("SELECT 1 FROM runs WHERE id=?", (run_id,)).fetchone():
                raise RuntimeError("Run id is already present; no automatic resume")
            if mode == "live":
                if self.db.execute("SELECT 1 FROM runs WHERE mode='live' AND protocol_id=?", (plan["protocol_id"],)).fetchone():
                    raise RuntimeError("This live protocol has already been claimed; no relaunch")
                for previous in self.db.execute("SELECT id FROM runs WHERE mode='live' AND status IN ('RUNNING','HALTED')"):
                    if not any(e["kind"] == "halt_reviewed" for e in self._snapshot(previous["id"])["events"]):
                        raise RuntimeError("A previous live run blocks further paid execution")
            self.db.execute("INSERT INTO runs VALUES (?,?,?,?,?,'RUNNING',NULL,?,NULL,NULL)",
                            (run_id, mode, plan["protocol_id"], canonical(plan), canonical(metadata), now()))
            event = self._append(run_id, "run_started", {"mode": mode, "plan": plan, "metadata": metadata})
            self.db.execute("UPDATE runs SET started_utc=? WHERE id=?", (event["created_utc"], run_id))

    def add_event(self, run_id, kind, data):
        if not isinstance(kind, str) or not kind or kind in CONTROL_EVENTS:
            raise ValueError("Use journal methods for accounting state events")
        with self._transaction():
            snapshot = self._current(run_id)
            if snapshot["run"]["ended_utc"] is not None:
                raise RuntimeError("Run has finished")
            return self._append(run_id, kind, data)

    def reserve(self, run_id, case_id, request, amount):
        amount, request = money(amount), _plain(request)
        if not isinstance(request, dict):
            raise ValueError("Request payload must be an object")
        with self._transaction():
            snapshot = self._current(run_id)
            if snapshot["run"]["mode"] == "live" and amount <= 0:
                raise ValueError("A live request requires a positive reserve")
            _allow_reserve(snapshot["run"], snapshot["requests"], case_id, amount)
            request_id = f"{run_id}:request:{len(snapshot['requests']) + 1}"
            event = self._append(run_id, "request_reserved", {
                "id": request_id, "case_id": case_id, "payload": request, "reserve_usd": str(amount)})
            self.db.execute("INSERT INTO requests VALUES (?,?,?,?,?,NULL,'RESERVED',NULL,NULL,?,NULL,NULL)",
                            (request_id, run_id, case_id, canonical(request), str(amount), event["created_utc"]))
            return request_id

    def _request(self, request_id):
        row = self.db.execute("SELECT run_id FROM requests WHERE id=?", (request_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown request_id")
        snapshot = self._current(row[0])
        if snapshot["run"]["ended_utc"] is not None:
            raise RuntimeError("Run has finished")
        return snapshot, next(r for r in snapshot["requests"] if r["id"] == request_id)

    def save_response(self, request_id, envelope):
        envelope = _plain(envelope)
        if not isinstance(envelope, dict):
            raise ValueError("Response envelope must be an object")
        with self._transaction():
            snapshot, request = self._request(request_id)
            if request["state"] != "RESERVED":
                raise RuntimeError("Response has already been recorded")
            event = self._append(snapshot["run"]["id"], "response_saved", {"request_id": request_id, "envelope": envelope})
            self.db.execute("UPDATE requests SET response=?,response_utc=?,state='RESPONSE_SAVED' WHERE id=?",
                            (canonical(envelope), event["created_utc"], request_id))

    def settle(self, request_id, calculation):
        calculation = _plain(calculation)
        if not isinstance(calculation, dict) or "estimated_cost_usd" not in calculation:
            raise ValueError("Calculation requires estimated_cost_usd")
        cost = money(calculation["estimated_cost_usd"])
        with self._transaction():
            snapshot, request = self._request(request_id)
            if request["state"] != "RESPONSE_SAVED":
                raise RuntimeError("Capture the response before settling; settlement is single-use")
            run_id = snapshot["run"]["id"]
            event = self._append(run_id, "request_settled", {
                "request_id": request_id, "calculation": calculation, "cost_usd": str(cost)})
            self.db.execute("UPDATE requests SET cost_usd=?,calculation=?,settled_utc=?,state='SETTLED' WHERE id=?",
                            (str(cost), canonical(calculation), event["created_utc"], request_id))
            if cost > money(request["reserve_usd"]):
                self._halt(run_id, "RESERVE_EXCEEDED")

    def _halt(self, run_id, reason):
        row = self.db.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
        if row[0] == "HALTED":
            return
        if row[0] != "RUNNING":
            raise RuntimeError("Completed runs cannot be changed")
        self._append(run_id, "run_halted", {"reason": reason})
        self.db.execute("UPDATE runs SET status='HALTED',halt_reason=? WHERE id=?", (reason, run_id))

    def halt(self, run_id, reason):
        if not isinstance(reason, str) or not reason:
            raise ValueError("A halt requires a reason")
        with self._transaction():
            self._current(run_id)
            self._halt(run_id, reason)

    def finish(self, run_id, summary):
        summary = _plain(summary)
        with self._transaction():
            snapshot = self._current(run_id)
            if snapshot["run"]["ended_utc"] is not None:
                raise RuntimeError("Run has already finished")
            if snapshot["totals"]["unresolved_requests"]:
                self._halt(run_id, "Unresolved request costs require reconciliation")
            status = self.db.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()[0]
            status = "HALTED" if status == "HALTED" else "COMPLETED"
            event = self._append(run_id, "run_finished", {"summary": summary, "status": status})
            self.db.execute("UPDATE runs SET status=?,summary=?,ended_utc=? WHERE id=?",
                            (status, canonical(summary), event["created_utc"], run_id))

    def review_halt(self, run_id, expected_snapshot_hash, reviewer, note):
        """Acknowledge a finished, fully priced halt; never reset or resume it."""
        from verifier import verify_snapshot

        if not all(isinstance(value, str) and value.strip() for value in (reviewer, note)):
            raise ValueError("Review requires a reviewer and a nonempty note")
        with self._transaction():
            snapshot = self._current(run_id)
            run = snapshot["run"]
            if digest(snapshot) != expected_snapshot_hash:
                raise ValueError("Stale review: inspect the current snapshot hash")
            if (run["mode"] != "live" or run["status"] != "HALTED" or run["ended_utc"] is None
                    or run["summary"] is None or snapshot["totals"]["unresolved_requests"]):
                raise RuntimeError("Only a finished, fully accounted live halt can be reviewed")
            if any(e["kind"] == "halt_reviewed" for e in snapshot["events"]):
                raise RuntimeError("Halt has already been reviewed")
            verify_snapshot(snapshot)  # Recompute charges from the retained raw responses.
            return self._append(run_id, "halt_reviewed", {
                "reviewed_snapshot_sha256": expected_snapshot_hash,
                "reviewer": reviewer.strip(), "note": note.strip(),
                "known_estimated_spend_usd": snapshot["totals"]["known_estimated_spend_usd"]})

    @staticmethod
    def _verify(snapshot):
        """Rebuild accounting from the event chain and compare every mutable row."""
        actual = snapshot["run"]
        run, requests, previous, reviewed = None, {}, ZERO_HASH, False
        for sequence, event in enumerate(snapshot["events"], 1):
            unhashed = {k: v for k, v in event.items() if k != "event_hash"}
            if (event["run_id"] != actual["id"] or event["sequence"] != sequence
                    or event["previous_hash"] != previous or digest(unhashed) != event["event_hash"]):
                raise RuntimeError("Journal event chain verification failed")
            previous = event["event_hash"]
            kind, data, timestamp = event["kind"], event["data"], event["created_utc"]
            if sequence == 1:
                if kind != "run_started":
                    raise RuntimeError("First event must claim the run")
                run = {"id": actual["id"], "mode": data["mode"], "plan": _plan(data["plan"]),
                       "metadata": data["metadata"], "status": "RUNNING", "summary": None,
                       "started_utc": timestamp, "ended_utc": None, "halt_reason": None}
                continue
            if kind == "halt_reviewed":
                before = {"run": run, "requests": list(requests.values()),
                          "events": snapshot["events"][:sequence - 1],
                          "totals": _totals(list(requests.values()))}
                if (reviewed or run is None or run["mode"] != "live" or run["status"] != "HALTED"
                        or run["ended_utc"] is None or run["summary"] is None
                        or before["totals"]["unresolved_requests"]
                        or data.get("reviewed_snapshot_sha256") != digest(before)
                        or data.get("known_estimated_spend_usd") != before["totals"]["known_estimated_spend_usd"]
                        or any(not isinstance(data.get(k), str) or not data[k].strip() for k in ("reviewer", "note"))):
                    raise RuntimeError("Invalid fully accounted halt review")
                reviewed = True
                continue
            if run is None or run["ended_utc"] is not None or kind == "run_started":
                raise RuntimeError("Invalid run event order")
            if kind == "request_reserved":
                _allow_reserve(run, list(requests.values()), data["case_id"], money(data["reserve_usd"]))
                request_id = f"{run['id']}:request:{len(requests) + 1}"
                if data["id"] != request_id:
                    raise RuntimeError("Invalid reserved request identity")
                requests[request_id] = {"id": request_id, "run_id": run["id"], "case_id": data["case_id"],
                    "payload": data["payload"], "reserve_usd": _amount(data["reserve_usd"]), "cost_usd": None,
                    "state": "RESERVED", "response": None, "calculation": None,
                    "reserved_utc": timestamp, "response_utc": None, "settled_utc": None}
            elif kind == "response_saved":
                request = requests[data["request_id"]]
                if request["state"] != "RESERVED":
                    raise RuntimeError("Invalid response event order")
                request.update(response=data["envelope"], response_utc=timestamp, state="RESPONSE_SAVED")
            elif kind == "request_settled":
                request = requests[data["request_id"]]
                if request["state"] != "RESPONSE_SAVED" or money(data["cost_usd"]) != money(data["calculation"]["estimated_cost_usd"]):
                    raise RuntimeError("Invalid settlement event")
                request.update(cost_usd=_amount(data["cost_usd"]), calculation=data["calculation"],
                               settled_utc=timestamp, state="SETTLED")
            elif kind == "run_halted":
                if run["status"] != "RUNNING" or not data["reason"]:
                    raise RuntimeError("Invalid halt event")
                run.update(status="HALTED", halt_reason=data["reason"])
            elif kind == "run_finished":
                status = "HALTED" if run["status"] == "HALTED" else "COMPLETED"
                if data["status"] != status or (status == "COMPLETED" and _totals(list(requests.values()))["unresolved_requests"]):
                    raise RuntimeError("Invalid finished-run accounting")
                run.update(status=status, summary=data["summary"], ended_utc=timestamp)
        if run != actual or list(requests.values()) != snapshot["requests"]:
            raise RuntimeError("Journal rows do not match immutable events")
        if (any(r["cost_usd"] is not None and money(r["cost_usd"]) > money(r["reserve_usd"]) for r in requests.values())
                and run["status"] != "HALTED"):
            raise RuntimeError("A reservation overrun must halt the run")
        if snapshot["totals"] != _totals(list(requests.values())):
            raise RuntimeError("Journal totals do not match requests")

    def verify(self, run_id):
        with self._transaction(write=False):
            self._check_schema()
            snapshot = self._snapshot(run_id)
            result = verify_accounting(snapshot)
            if self.db.execute("SELECT protocol_id FROM runs WHERE id=?", (run_id,)).fetchone()[0] != snapshot["run"]["plan"]["protocol_id"]:
                raise RuntimeError("Protocol claim does not match the frozen plan")
            return result


def verify_accounting(snapshot):
    """Verify an exported snapshot without opening or modifying the live journal.

Hashes detect accidental modification; an export is not a signed provider bill
and must never be used as authority to start or resume a paid run.
"""
    try:
        Journal._verify(snapshot)
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Malformed journal accounting evidence") from exc
    return {"verified": True, "run_id": snapshot["run"]["id"],
            "events": len(snapshot["events"]), "requests": len(snapshot["requests"]),
            "totals": snapshot["totals"]}
