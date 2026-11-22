#!/usr/bin/env python3
"""Native Windows/Linux receipt pilot. Default execution is entirely offline."""
from __future__ import annotations

import argparse
import base64
import getpass
import json
import os
from pathlib import Path
import platform
import sqlite3
import sys
import tempfile
import time
import uuid

from common import canonical, digest, money, now
from ledger import Journal, verify_accounting
from protocol import (TOOLS, Fixture, Service, initial_history, price_usage,
                      request_payload, reserve_cost, validate_plan)
from transport import Transport
from verifier import parse_action, validate_output, verify_snapshot

HERE = Path(__file__).resolve().parent
SOURCE_FILES = ("common.py", "ledger.py", "protocol.py", "runner.py", "transport.py", "verifier.py")


def decode_json(raw):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError("Duplicate JSON key")
            obj[key] = value
        return obj
    def invalid_constant(_value):
        raise ValueError("Non-finite JSON number")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid_constant)


def load_plan(path):
    plan = decode_json(Path(path).read_text(encoding="utf-8"))
    validate_plan(plan)
    return plan


def live_database():
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        root = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    return root / "JoshRinLab" / "api-pilot" / "ledger.sqlite3"


def source_bundle():
    return {name: {"sha256": digest(data), "body_base64": base64.b64encode(data).decode("ascii")}
            for name in SOURCE_FILES for data in [(HERE / name).read_bytes()]}


def envelope_response(envelope):
    if envelope.get("error_type") or not envelope.get("body_complete"):
        raise ValueError("RESPONSE_UNCERTAIN")
    if type(envelope.get("http_status")) is not int or not 200 <= envelope["http_status"] < 300:
        raise ValueError("HTTP_REJECTED")
    try:
        response = decode_json(base64.b64decode(envelope["body_base64"], validate=True).decode("utf-8"))
    except (ValueError, UnicodeError, KeyError) as exc:
        raise ValueError("INVALID_JSON") from exc
    if not isinstance(response, dict):
        raise ValueError("INVALID_JSON")
    return response


def execute(plan, journal, mode="fixture", transport=None, run_id=None, approval_receipt=None):
    """One run; injected transports are used by offline tests, never auto-retried."""
    validate_plan(plan)
    if mode not in {"fixture", "live"} or (mode == "live" and transport is None):
        raise ValueError("Live mode requires an explicitly supplied transport")
    run_id = run_id or (mode + "-" + uuid.uuid4().hex)
    metadata = {"plan_sha256": digest(plan), "prompt_sha256": digest(initial_history()),
                "tools_sha256": digest(TOOLS), "source_bundle": source_bundle(),
                "python": platform.python_version(), "operating_system": platform.platform(),
                "sqlite_version": sqlite3.sqlite_version, "approval_receipt": approval_receipt,
                "target": None if mode == "fixture" else {
                    "endpoint": "https://api.openai.com/v1/responses",
                    "organization": transport.organization, "project": transport.project}}
    journal.start_run(run_id, mode, plan, metadata)
    rows = []
    for assignment in plan["assignments"]:
        case_id, model, case = assignment["case_id"], assignment["model"], assignment["case"]
        service, history, seen = Service(case), initial_history(), set()
        fixture = Fixture(case)
        started, clock = now(), time.monotonic()
        row = {"case_id": case_id, "status": "CALL_LIMIT", "reason": None,
               "requested_model": model, "returned_models": [], "calls": 0, "responses": 0,
               "model_response_observed": False,
               "started_utc": started, "ended_utc": None, "elapsed_seconds": None,
               "unsupported_claims": None, "outcome": None}
        journal.add_event(run_id, "case_started", {"case_id": case_id, "model": model, "case": case,
                          "prompt_sha256": digest(history), "tools_sha256": digest(TOOLS)})
        current = journal.snapshot(run_id)["run"]
        if current["status"] != "RUNNING":
            row.update(status="BLOCKED", reason=current["halt_reason"])
        else:
            for _ in range(plan["max_calls_per_case"]):
                request = request_payload(history, model, plan)
                request_id = None
                reason = None
                if mode == "live":
                    try:
                        request_id = journal.reserve(run_id, case_id, request, reserve_cost(request, model, plan))
                    except (ValueError, RuntimeError):
                        reason = "REQUEST_REFUSED"
                    if reason is None:
                        row["calls"] += 1
                        # A failure after reservation leaves a durable, unresolved reserve.
                        try:
                            envelope = transport.send(request)
                        except (Exception, KeyboardInterrupt) as exc:
                            envelope = {"http_status": None, "headers": {}, "body_base64": "",
                                        "started_utc": now(), "ended_utc": now(), "elapsed_seconds": None,
                                        "error_type": type(exc).__name__, "body_complete": False}
                        journal.save_response(request_id, envelope)
                        try:
                            response = envelope_response(envelope)
                        except ValueError as exc:
                            reason = str(exc)
                else:
                    response = fixture.create(request)
                    row["calls"] += 1
                    journal.add_event(run_id, "fixture_exchange", {
                        "case_id": case_id, "request": request, "response": response})
                if reason is None:
                    row["responses"] += 1
                    returned = response.get("model")
                    if isinstance(returned, str) and returned not in row["returned_models"]:
                        row["returned_models"].append(returned)
                    if not isinstance(response.get("id"), str) or not response["id"]:
                        reason = "INVALID_JSON"
                    elif mode == "live" and returned not in plan["accepted_returned_models"][model]:
                        reason = "UNEXPECTED_MODEL"
                    elif mode == "live" and response.get("service_tier") != "default":
                        reason = "UNEXPECTED_TIER"
                    else:
                        try:
                            validate_output(response.get("output"))
                        except ValueError:
                            reason = "INVALID_OUTPUT"
                        else:
                            row["model_response_observed"] = mode == "live"
                if reason is None and mode == "live":
                    try:
                        calculation = price_usage(response.get("usage"), plan["pricing"][model],
                                                  plan["max_priced_input_tokens"])
                    except ValueError:
                        reason = "UNPRICEABLE_USAGE"
                    else:
                        journal.settle(request_id, calculation)
                        if journal.snapshot(run_id)["run"]["status"] != "RUNNING":
                            reason = "RESERVE_EXCEEDED"
                        elif response["usage"]["output_tokens"] > plan["max_output_tokens"]:
                            reason = "OUTPUT_LIMIT_EXCEEDED"
                if reason is None and response.get("status") != "completed":
                    reason = "INCOMPLETE_RESPONSE"
                if reason is None:
                    try:
                        action = parse_action(response["output"], seen)
                    except ValueError:
                        reason = "INVALID_TOOL_CALL"
                if reason is not None:
                    row.update(status="HALTED", reason=reason)
                    journal.halt(run_id, reason)
                    break
                history.extend(response["output"])
                if action is None:
                    row["status"] = "COMPLETED" if service.report()["safe_joint_completion"] else "STOPPED_EARLY"
                    break
                result = service.act(action["action"], action["job"])
                journal.add_event(run_id, "tool_action", {"case_id": case_id, **action, "result": result})
                history.append({"type": "function_call_output", "call_id": action["call_id"],
                                "output": canonical(result)})
        row.update(outcome=service.report(), ended_utc=now(), elapsed_seconds=round(time.monotonic() - clock, 6))
        journal.add_event(run_id, "case_finished", row)
        rows.append(row)
    totals = journal.snapshot(run_id)["totals"]
    summary = {"run_id": run_id, "mode": mode, "protocol_id": plan["protocol_id"],
               "assigned_contexts": len(rows), "safe_joint_completions": sum(
                   row["outcome"]["safe_joint_completion"] for row in rows),
               "model_contexts_observed": sum(row["model_response_observed"] for row in rows),
               "provider_cost_usd": totals["estimated_total_cost_usd"] if mode == "live" else None,
               "cases": rows, **totals,
               "interpretation": "Scripted infrastructure fixture; no model evidence" if mode == "fixture"
                                 else "Estimated costs; semantic claims require human review"}
    journal.finish(run_id, summary)
    snapshot = journal.snapshot(run_id)
    verify_snapshot(snapshot)
    return snapshot


def export_snapshot(snapshot, destination):
    verify_accounting(snapshot)
    verification = verify_snapshot(snapshot)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    artifact = {"schema_version": 1, "snapshot_sha256": digest(snapshot), "snapshot": snapshot}
    with destination.open("xb") as stream:
        stream.write((canonical(artifact) + "\n").encode("utf-8"))
    return verification


def verify_export(path):
    artifact = decode_json(Path(path).read_text(encoding="utf-8"))
    if artifact.get("schema_version") != 1 or digest(artifact["snapshot"]) != artifact.get("snapshot_sha256"):
        raise ValueError("Export checksum mismatch")
    verify_accounting(artifact["snapshot"])
    return verify_snapshot(artifact["snapshot"])


def plan_summary(plan):
    return {"protocol": plan["protocol_id"], "plan_sha256": digest(plan), "assignments": len(plan["assignments"]),
            "estimated_spend_ceiling_usd": plan["max_estimated_spend_usd"],
            "per_case_ceiling_usd": plan["max_estimated_spend_per_case_usd"],
            "max_calls_per_case": plan["max_calls_per_case"], "max_output_tokens": plan["max_output_tokens"],
            "first_request_reserves_usd": {a["model"]: str(reserve_cost(request_payload(initial_history(), a["model"], plan),
                                                                       a["model"], plan)) for a in plan["assignments"]}}


def credentials():
    organization, project = os.environ.get("OPENAI_ORG_ID"), os.environ.get("OPENAI_PROJECT_ID")
    key = os.environ.get("OPENAI_API_KEY")
    if not sys.stdin.isatty() and not all((organization, project, key)):
        raise ValueError("Live execution needs existing credential environment variables or an interactive terminal")
    if not organization:
        organization = input("Lab organization ID: ").strip()
    if not project:
        project = input("Lab project ID: ").strip()
    if not key:
        key = getpass.getpass("Existing API key (hidden): ")
    return key, organization, project


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command")
    for command in ("check", "dry-run", "live"):
        sub = commands.add_parser(command)
        sub.add_argument("--plan", type=Path, default=HERE / "plan.json")
        if command == "dry-run":
            sub.add_argument("--output", type=Path)
        if command == "live":
            sub.add_argument("--approve-plan", required=True, help="SHA-256 printed by check; confirms this exact paid plan")
    sub = commands.add_parser("verify")
    sub.add_argument("evidence", type=Path)
    sub = commands.add_parser("report")
    sub.add_argument("--run-id")
    sub = commands.add_parser("export")
    sub.add_argument("run_id")
    sub.add_argument("destination", type=Path)
    args = parser.parse_args(argv or (["dry-run"] if len(sys.argv) == 1 else None))
    journal = None
    try:
        if args.command == "verify":
            print(json.dumps(verify_export(args.evidence), indent=2))
        elif args.command in {"report", "export"}:
            if not live_database().exists():
                raise ValueError("No live ledger exists on this computer")
            journal = Journal(live_database(), read_only=True)
            run_id = getattr(args, "run_id", None)
            if not run_id:
                row = journal.db.execute("SELECT id FROM runs ORDER BY started_utc DESC LIMIT 1").fetchone()
                if row is None:
                    raise ValueError("No recorded runs")
                run_id = row[0]
            snapshot = journal.snapshot(run_id)
            if args.command == "export":
                print(json.dumps(export_snapshot(snapshot, args.destination), indent=2))
            else:
                print(json.dumps({"run_id": run_id, "status": snapshot["run"]["status"],
                                  "halt_reason": snapshot["run"]["halt_reason"], **snapshot["totals"]}, indent=2))
        else:
            plan = load_plan(args.plan)
            if args.command == "check":
                with tempfile.TemporaryDirectory() as temporary:
                    probe = Journal(Path(temporary) / "probe.sqlite3")
                    probe.close()
                print(json.dumps({"python": platform.python_version(), "system": platform.system(),
                                  "sqlite": sqlite3.sqlite_version, "offline_storage_check": "passed",
                                  "live_ledger": str(live_database()), **plan_summary(plan)}, indent=2))
            else:
                run_id = ("live-" if args.command == "live" else "fixture-") + uuid.uuid4().hex
                output = getattr(args, "output", None) or HERE / "results" / run_id
                if args.command == "live":
                    if args.approve_plan != digest(plan):
                        raise ValueError("Approval does not match this plan; use check to review its scope")
                    key, organization, project = credentials()
                    transport = Transport(key, organization, project)
                    journal = Journal(live_database())
                    snapshot = execute(plan, journal, "live", transport, run_id, {
                        "plan_sha256": args.approve_plan, "estimated_spend_ceiling_usd": plan["max_estimated_spend_usd"]})
                else:
                    journal = Journal(output / "ledger.sqlite3")
                    snapshot = execute(plan, journal, run_id=run_id)
                export_snapshot(snapshot, output / "evidence.json")
                summary = snapshot["run"]["summary"]
                print(json.dumps({"run_id": run_id, "mode": summary["mode"],
                                  "safe_joint_completions": summary["safe_joint_completions"],
                                  "assigned_contexts": summary["assigned_contexts"],
                                  "provider_cost_usd": summary["provider_cost_usd"],
                                  "status": snapshot["run"]["status"], "evidence": str(output / "evidence.json")}, indent=2))
        return 0
    except (ValueError, RuntimeError, OSError, sqlite3.Error) as exc:
        print("Stopped: " + str(exc), file=sys.stderr)
        return 1
    finally:
        if journal is not None:
            journal.close()


if __name__ == "__main__":
    raise SystemExit(main())
