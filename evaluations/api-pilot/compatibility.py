"""One fixed two-call compatibility instrument. Default execution is offline."""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import platform
import re
import secrets
import sqlite3
import sys
import uuid

from common import canonical, digest, money, now
from ledger import Journal, ReserveRefused, verify_accounting
from protocol import PRICE_KEYS, price_usage, reserve_cost
from runner import credentials, decode_json, envelope_response, live_database
from transport import Transport
from verifier import _timing, validate_output

HERE = Path(__file__).resolve().parent
BASELINE = "773c10571566457992534bbdb29aa69eaf6899ca"
MODEL = "gpt-6.2-astra"
BLOCKED = "INFRASTRUCTURE_BLOCKED_OR_INDETERMINATE"
NOT_DEMONSTRATED = "NOT_DEMONSTRATED"
TOOLS = [{"type": "function", "name": "lab_probe", "strict": True,
          "description": "Return a harmless local receipt with a fresh verification value.",
          "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False}}]
PROMPT = [{"role": "user", "content":
           "Invoke lab_probe once with no arguments. After receiving its receipt, return only "
           "a JSON object with exactly one property, verification_value, containing the exact "
           "value from that receipt. Do not invent a value or invoke another tool."}]
SOURCES = (".gitattributes", "common.py", "ledger.py", "protocol.py", "runner.py", "transport.py", "verifier.py",
           "compatibility.py", "COMPATIBILITY.md")


class Stop(Exception):
    def __init__(self, reason, verdict=BLOCKED):
        self.reason, self.verdict = reason, verdict


def load_plan(path):
    plan = decode_json(Path(path).read_text(encoding="utf-8"))
    validate_plan(plan)
    return plan


def validate_plan(plan):
    if not isinstance(plan, dict):
        raise ValueError("Compatibility plan must be an object")
    if (type(plan.get("schema_version")) is not int or plan["schema_version"] != 1 or plan.get("kind") != "two_call_compatibility"
            or plan.get("status") != "PROPOSED_UNRUN" or plan.get("baseline_commit") != BASELINE
            or not isinstance(plan.get("protocol_id"), str)
            or not re.fullmatch(r"[A-Za-z0-9_.-]{1,120}", plan["protocol_id"])):
        raise ValueError("Invalid compatibility proposal identity")
    if (type(plan.get("max_calls_per_case")) is not int or plan["max_calls_per_case"] != 2
            or type(plan.get("max_output_tokens")) is not int or plan["max_output_tokens"] != 4096
            or plan.get("reasoning_effort") != "medium" or type(plan.get("nonce_bytes")) is not int or plan["nonce_bytes"] != 16):
        raise ValueError("This instrument requires exactly the proposed two-call settings")
    if plan.get("assignments") != [{"case_id": "compat01", "model": MODEL, "case": {"probe": "lab_probe"}}]:
        raise ValueError("Compatibility has one fixed model and one harmless probe")
    for key in ("max_estimated_spend_usd", "max_estimated_spend_per_case_usd"):
        if not 0 < money(plan.get(key)) <= 1:
            raise ValueError("Compatibility estimates must not exceed one dollar")
    if money(plan["max_estimated_spend_per_case_usd"]) > money(plan["max_estimated_spend_usd"]):
        raise ValueError("Case allocation exceeds run ceiling")
    if type(plan.get("max_priced_input_tokens")) is not int or not 0 < plan["max_priced_input_tokens"] <= 272000:
        raise ValueError("Invalid frozen context pricing basis")
    policy = plan.get("reservation_policy", {})
    if not isinstance(policy, dict) or policy.get("version") != "provider-usage-v1":
        raise ValueError("Use the established reservation policy")
    for key in ("initial_input_tokens", "continuation_margin_tokens"):
        if type(policy.get(key)) is not int or policy[key] <= 0:
            raise ValueError("Invalid frozen token allowance")
    pricing, accepted = plan.get("pricing"), plan.get("accepted_returned_models")
    if not isinstance(pricing, dict) or not isinstance(pricing.get(MODEL), dict) or not isinstance(accepted, dict):
        raise ValueError("Missing frozen model prices/identities")
    for key in PRICE_KEYS:
        if money(pricing[MODEL].get(key)) <= 0:
            raise ValueError("Invalid frozen price")
    aliases = accepted.get(MODEL)
    if (not isinstance(aliases, list) or not aliases
            or any(not isinstance(alias, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", alias) for alias in aliases)
            or len(set(aliases)) != len(aliases)
            or not plan.get("pricing_sources")):
        raise ValueError("Missing model/pricing basis")


def source_bundle():
    return {name: {"sha256": digest(raw), "body_base64": base64.b64encode(raw).decode("ascii")}
            for name in SOURCES for raw in [(HERE / name).read_bytes()]}


def freeze_hash(plan, bundle):
    return digest({"plan": plan, "source_hashes": {name: value["sha256"] for name, value in bundle.items()}})


def payload(plan, first_response=None, receipt=None):
    history = list(PROMPT)
    if first_response is not None:
        history += first_response["output"]
        history.append({"type": "function_call_output", "call_id": receipt["call_id"],
                        "output": canonical(receipt["receipt"])})
    return {"model": MODEL, "input": history, "tools": TOOLS, "store": False,
            "service_tier": "default", "parallel_tool_calls": False,
            "include": ["reasoning.encrypted_content"],
            "prompt_cache_options": {"mode": "implicit", "ttl": "30m"},
            "max_output_tokens": plan["max_output_tokens"], "reasoning": {"effort": "medium"},
            "tool_choice": {"type": "function", "name": "lab_probe"} if first_response is None else "none"}


def checked_response(envelope, plan, mode):
    try:
        _timing(envelope, allow_unknown=bool(envelope.get("error_type")))
        response = envelope_response(envelope)
    except ValueError as exc:
        raise Stop(str(exc)) from exc
    try:
        if not isinstance(response.get("id"), str) or not response["id"]:
            raise Stop("INVALID_RESPONSE_ID")
        validate_output(response.get("output"))
        if mode == "fixture":
            if response.get("model") != "fixture-not-a-model" or response.get("usage") is not None:
                raise Stop("INVALID_FIXTURE")
            calculation = {"estimated_cost_usd": "0", "basis": "offline_fixture_not_provider_usage"}
        else:
            if response.get("model") not in plan["accepted_returned_models"][MODEL]:
                raise Stop("UNEXPECTED_MODEL")
            if response.get("service_tier") != "default":
                raise Stop("UNEXPECTED_TIER")
            calculation = price_usage(response.get("usage"), plan["pricing"][MODEL], plan["max_priced_input_tokens"])
    except (ValueError, TypeError, KeyError) as exc:
        raise Stop("UNPRICEABLE_OR_UNSUPPORTED_RESPONSE") from exc
    return response, calculation


def completed(response, plan, mode):
    if mode == "live" and response["usage"]["output_tokens"] > plan["max_output_tokens"]:
        raise Stop("OUTPUT_LIMIT_EXCEEDED")
    if response.get("status") == "incomplete":
        raise Stop("INCOMPLETE_RESPONSE", NOT_DEMONSTRATED)
    if response.get("status") != "completed":
        raise Stop("UNEXPECTED_RESPONSE_STATUS")


def probe_call(response):
    calls = [item for item in response["output"] if item["type"] == "function_call"]
    if len(calls) != 1:
        raise Stop("EXPECTED_ONE_PROBE_CALL", NOT_DEMONSTRATED)
    call = calls[0]
    try:
        valid_args = decode_json(call["arguments"]) == {}
    except (ValueError, TypeError, KeyError):
        valid_args = False
    if (call.get("name") != "lab_probe" or call.get("status", "completed") != "completed"
            or not isinstance(call.get("call_id"), str)
            or not call["call_id"].strip() or not valid_args):
        raise Stop("INVALID_PROBE_CALL", NOT_DEMONSTRATED)
    return call


def fresh_receipt(receipt, call, request_one, response_one):
    value = receipt.get("receipt", {}).get("verification_value")
    if (receipt.get("call_id") != call["call_id"] or set(receipt.get("receipt", {})) != {"verification_value"}
            or not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{32}", value) is None
            or value in canonical(request_one) or value in canonical(response_one)):
        raise Stop("INVALID_OR_NONFRESH_RECEIPT", NOT_DEMONSTRATED)
    return value


def acknowledgment(response):
    messages = [item for item in response["output"] if item["type"] == "message"]
    if (len(messages) != 1 or messages[0].get("role") != "assistant"
            or any(item["type"] == "function_call" for item in response["output"])):
        raise Stop("EXPECTED_FINAL_MESSAGE_WITHOUT_TOOLS", NOT_DEMONSTRATED)
    content = messages[0].get("content", [])
    if not content or any(part.get("type") != "output_text" or not isinstance(part.get("text"), str) for part in content):
        raise Stop("INVALID_ACKNOWLEDGMENT_FORMAT", NOT_DEMONSTRATED)
    try:
        value = decode_json("".join(part["text"] for part in content))
    except ValueError as exc:
        raise Stop("INVALID_ACKNOWLEDGMENT_FORMAT", NOT_DEMONSTRATED) from exc
    if not isinstance(value, dict) or set(value) != {"verification_value"} or not isinstance(value["verification_value"], str):
        raise Stop("INVALID_ACKNOWLEDGMENT_FORMAT", NOT_DEMONSTRATED)
    return value["verification_value"]


def refusal_reason(plan, request, prior_usage, known_cost):
    try:
        amount = reserve_cost(request, MODEL, plan, prior_usage)
    except ValueError:
        return "INPUT_RESERVE_OUTSIDE_PRICING_BASIS"
    if money(known_cost) + amount > money(plan["max_estimated_spend_usd"]):
        return "RUN_BUDGET_EXCEEDED"
    if money(known_cost) + amount > money(plan["max_estimated_spend_per_case_usd"]):
        return "CASE_BUDGET_EXCEEDED"
    return None


def inspect_exchange(snapshot):
    """Reconstruct the two stages from original bytes, not a saved PASS label."""
    verify_accounting(snapshot)
    run, records, events = snapshot["run"], snapshot["requests"], snapshot["events"]
    plan, mode = run["plan"], run["mode"]
    validate_plan(plan)
    if mode not in {"live", "fixture"} or len(records) > 2:
        raise ValueError("Invalid compatibility mode/request denominator")
    metadata = run["metadata"]
    if (metadata.get("plan_sha256") != digest(plan) or metadata.get("prompt_sha256") != digest(PROMPT)
            or metadata.get("tools_sha256") != digest(TOOLS) or metadata.get("baseline_commit") != BASELINE):
        raise ValueError("Frozen protocol metadata mismatch")
    bundle = metadata["source_bundle"]
    if set(bundle) != set(SOURCES) or metadata["freeze_sha256"] != freeze_hash(plan, bundle):
        raise ValueError("Compatibility source freeze mismatch")
    for item in bundle.values():
        if digest(base64.b64decode(item["body_base64"], validate=True)) != item["sha256"]:
            raise ValueError("Frozen source checksum mismatch")
    receipts = [e for e in events if e["kind"] == "probe_receipt"]
    first, receipt, prior, expected, observed = None, None, None, None, None
    reasoning, replayed, consumed = False, False, 0
    verdict, reason = BLOCKED, "EXCHANGE_UNFINISHED"
    try:
        for index, record in enumerate(records):
            consumed += 1
            request = payload(plan, first, receipt) if index else payload(plan)
            if record["payload"] != request or record["case_id"] != "compat01":
                raise ValueError("Exact compatibility request/history mismatch")
            if index:
                replayed = reasoning
            reserve = reserve_cost(request, MODEL, plan, prior) if mode == "live" else money(0)
            if money(record["reserve_usd"]) != reserve:
                raise ValueError("Reservation replay mismatch")
            if record["response"] is None:
                raise Stop("RESPONSE_UNRECORDED")
            if index == 0:
                try:
                    raw_output = envelope_response(record["response"]).get("output", [])
                    reasoning = isinstance(raw_output, list) and any(
                        isinstance(item, dict) and item.get("type") == "reasoning"
                        and isinstance(item.get("encrypted_content"), str) and bool(item["encrypted_content"])
                        for item in raw_output)
                except ValueError:
                    pass
            try:
                response, calculation = checked_response(record["response"], plan, mode)
            except Stop:
                if record["cost_usd"] is not None:
                    raise ValueError("An unpriceable response was settled")
                raise
            if record["cost_usd"] is None:
                raise Stop("RESPONSE_NOT_SETTLED")
            if record["calculation"] != calculation or money(record["cost_usd"]) != money(calculation["estimated_cost_usd"]):
                raise ValueError("Raw response pricing differs from settlement")
            if money(record["cost_usd"]) > reserve:
                raise Stop("RESERVE_EXCEEDED")
            completed(response, plan, mode)
            if index == 0:
                call = probe_call(response)
                first, prior = response, response.get("usage")
                if not receipts:
                    raise Stop("LOCAL_RECEIPT_UNRECORDED")
                if len(receipts) != 1:
                    raise ValueError("The local probe must execute exactly once")
                receipt = receipts[0]["data"]
                if receipt.get("request_id") != record["id"]:
                    raise ValueError("Receipt is not bound to the first request")
                expected = fresh_receipt(receipt, call, request, response)
                settled = next(e for e in events if e["kind"] == "request_settled" and e["data"]["request_id"] == record["id"])
                if receipts[0]["sequence"] <= settled["sequence"]:
                    raise ValueError("Probe executed before response settlement")
            else:
                reserved = next(e for e in events if e["kind"] == "request_reserved" and e["data"]["id"] == record["id"])
                if receipts[0]["sequence"] >= reserved["sequence"]:
                    raise ValueError("Receipt was not committed before continuation")
                observed = acknowledgment(response)
                if observed != expected:
                    raise Stop("VERIFICATION_VALUE_MISMATCH", NOT_DEMONSTRATED)
                verdict, reason = ("PASS" if mode == "live" else "FIXTURE_PASS"), "EXCHANGE_ACKNOWLEDGED"
    except Stop as stop:
        verdict, reason = stop.verdict, stop.reason
    if consumed != len(records) or (receipts and first is None):
        raise ValueError("Requests or local effects occurred after an invalid first response")
    if len(records) < 2 and first is not None and receipt is not None:
        # A pre-dispatch financial refusal must be reproducible, not an invented excuse.
        if run["halt_reason"] in {"RUN_BUDGET_EXCEEDED", "CASE_BUDGET_EXCEEDED", "INPUT_RESERVE_OUTSIDE_PRICING_BASIS"}:
            if refusal_reason(plan, payload(plan, first, receipt), prior, snapshot["totals"]["known_estimated_spend_usd"]) != run["halt_reason"]:
                raise ValueError("Financial refusal has no replayable basis")
            verdict, reason = BLOCKED, run["halt_reason"]
    elif not records and run["halt_reason"]:
        if refusal_reason(plan, payload(plan), None, 0) != run["halt_reason"]:
            raise ValueError("Initial financial refusal has no replayable basis")
        verdict, reason = BLOCKED, run["halt_reason"]
    accounting_halt = (snapshot["totals"]["unresolved_requests"] > 0
                       and run["halt_reason"] == "Unresolved request costs require reconciliation")
    if run["halt_reason"] is not None and (verdict != BLOCKED or not accounting_halt and run["halt_reason"] != reason):
        raise ValueError("Global halt disagrees with reconstructed stopping reason")
    if run["summary"] is not None and verdict == BLOCKED and run["status"] != "HALTED":
        raise ValueError("Blocked compatibility exchange was marked completed")
    return {"run_id": run["id"], "protocol_id": plan["protocol_id"], "mode": mode,
            "verdict": verdict, "reason": reason, "maximum_provider_requests": 2,
            "provider_requests_attempted": len(records) if mode == "live" else None,
            "fixture_exchanges": len(records) if mode == "fixture" else None,
            "request_slots": [{"number": n + 1, "state": "attempted" if n < len(records) else "unattempted",
                               "request_id": records[n]["id"] if n < len(records) else None} for n in range(2)],
            "local_tool_executions": len(receipts), "expected_value": expected, "observed_value": observed,
            "encrypted_reasoning_observed": reasoning, "encrypted_reasoning_in_request_2": replayed,
            "encrypted_reasoning_replay_demonstrated": reasoning and verdict == "PASS",
            "provider_cost_usd": snapshot["totals"]["estimated_total_cost_usd"] if mode == "live" else None,
            "totals": snapshot["totals"],
            "interpretation": "One tool exchange only; no model reliability, safety or full-task token claim"
                              if mode == "live" else "Scripted offline fixture; no provider usage or model evidence"}


def verify_snapshot(snapshot):
    result = inspect_exchange(snapshot)
    if snapshot["run"]["summary"] is not None and snapshot["run"]["summary"] != result:
        raise ValueError("Compatibility summary differs from reconstructed evidence")
    return result


def execute(plan, journal, mode="fixture", transport=None, nonce_factory=None, approval=None):
    validate_plan(plan)
    if mode not in {"fixture", "live"} or (mode == "live" and transport is None):
        raise ValueError("Explicit transport required for live mode")
    run_id = mode + "-compat-" + uuid.uuid4().hex
    bundle = source_bundle()
    journal.start_run(run_id, mode, plan, {"source_bundle": bundle, "freeze_sha256": freeze_hash(plan, bundle),
        "plan_sha256": digest(plan), "prompt_sha256": digest(PROMPT), "tools_sha256": digest(TOOLS),
        "python": platform.python_version(), "operating_system": platform.platform(), "sqlite_version": sqlite3.sqlite_version,
        "approval_receipt": approval, "baseline_commit": BASELINE,
        "target": {"endpoint": "https://api.openai.com/v1/responses", "organization": transport.organization,
                   "project": transport.project} if mode == "live" else None})
    first, receipt, prior = None, None, None
    try:
        for number in (1, 2):
            request = payload(plan, first, receipt) if first else payload(plan)
            try:
                amount = reserve_cost(request, MODEL, plan, prior) if mode == "live" else money(0)
                request_id = journal.reserve(run_id, "compat01", request, amount)
            except ReserveRefused as exc:
                raise Stop(exc.reason) from exc
            except ValueError as exc:
                raise Stop("INPUT_RESERVE_OUTSIDE_PRICING_BASIS") from exc
            try:
                envelope = transport.send(request) if mode == "live" else fixture_response(request, number)
            except (Exception, KeyboardInterrupt) as exc:
                envelope = {"http_status": None, "headers": {}, "body_base64": "", "body_complete": False,
                            "error_type": type(exc).__name__, "started_utc": now(), "ended_utc": now(), "elapsed_seconds": None}
            journal.save_response(request_id, envelope)
            response, calculation = checked_response(envelope, plan, mode)
            journal.settle(request_id, calculation)
            if journal.snapshot(run_id)["run"]["status"] != "RUNNING":
                raise Stop("RESERVE_EXCEEDED")
            completed(response, plan, mode)
            if number == 1:
                call = probe_call(response)
                value = nonce_factory() if nonce_factory else secrets.token_hex(plan["nonce_bytes"])
                receipt = {"request_id": request_id, "call_id": call["call_id"], "receipt": {"verification_value": value}}
                journal.add_event(run_id, "probe_receipt", receipt)
                fresh_receipt(receipt, call, request, response)
                first, prior = response, response.get("usage")
            else:
                if acknowledgment(response) != receipt["receipt"]["verification_value"]:
                    raise Stop("VERIFICATION_VALUE_MISMATCH", NOT_DEMONSTRATED)
    except Stop as stop:
        if stop.verdict == BLOCKED:
            journal.halt(run_id, stop.reason)
    result = inspect_exchange(journal.snapshot(run_id))
    journal.finish(run_id, result)
    snapshot = journal.snapshot(run_id)
    verify_snapshot(snapshot)
    return snapshot


def fixture_response(request, number):
    output = [{"type": "function_call", "name": "lab_probe", "call_id": "fixture-call", "arguments": "{}"}]
    if number == 2:
        text = request["input"][-1]["output"]
        output = [{"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": text}]}]
    body = {"id": f"fixture-{number}", "model": "fixture-not-a-model", "status": "completed", "output": output, "usage": None}
    return {"http_status": 200, "headers": {}, "body_base64": base64.b64encode(canonical(body).encode()).decode(),
            "started_utc": now(), "ended_utc": now(), "elapsed_seconds": 0, "error_type": None, "body_complete": True}


def export_snapshot(snapshot, destination):
    verify_snapshot(snapshot)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with destination.open("xb") as stream:
        stream.write((canonical({"kind": "two_call_compatibility", "snapshot_sha256": digest(snapshot),
                                 "snapshot": snapshot}) + "\n").encode("utf-8"))


def verify_export(path):
    artifact = decode_json(Path(path).read_text(encoding="utf-8"))
    if artifact.get("kind") != "two_call_compatibility" or artifact.get("snapshot_sha256") != digest(artifact["snapshot"]):
        raise ValueError("Compatibility export checksum mismatch")
    return verify_snapshot(artifact["snapshot"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "dry-run", "live"):
        sub = commands.add_parser(name)
        sub.add_argument("--plan", type=Path, default=HERE / "compatibility.json")
        if name == "dry-run":
            sub.add_argument("--output", type=Path)
        if name == "live":
            sub.add_argument("--approve-freeze", required=True, help="Exact plan+source hash printed by check; for separately authorized execution only")
    sub = commands.add_parser("verify")
    sub.add_argument("evidence", type=Path)
    for name in ("report", "export", "review-halt"):
        sub = commands.add_parser(name)
        sub.add_argument("run_id")
        if name == "export":
            sub.add_argument("destination", type=Path)
        if name == "review-halt":
            sub.add_argument("--snapshot-sha256", required=True)
            sub.add_argument("--reviewer", required=True)
            sub.add_argument("--note", required=True)
    args = parser.parse_args(["dry-run"] if argv is None and len(sys.argv) == 1 else argv)
    journal = None
    try:
        if args.command == "verify":
            print(json.dumps(verify_export(args.evidence), indent=2))
        elif args.command in {"report", "export", "review-halt"}:
            if not live_database().exists():
                raise ValueError("No live ledger exists")
            journal = Journal(live_database(), read_only=args.command != "review-halt")
            snapshot = journal.snapshot(args.run_id)
            if args.command == "export":
                export_snapshot(snapshot, args.destination)
            elif args.command == "review-halt":
                event = journal.review_halt(args.run_id, args.snapshot_sha256, args.reviewer, args.note,
                                            protocol_verifier=verify_snapshot)
                print(json.dumps({"review_receipt_sha256": event["event_hash"]}, indent=2))
            else:
                print(json.dumps({"snapshot_sha256": digest(snapshot), "result": verify_snapshot(snapshot)}, indent=2))
        else:
            plan = load_plan(args.plan)
            identity = freeze_hash(plan, source_bundle())
            if args.command == "check":
                first = reserve_cost(payload(plan), MODEL, plan)
                print(json.dumps({"status": "PROPOSED_NOT_AUTHORIZED", "plan_sha256": digest(plan),
                                  "freeze_sha256": identity, "maximum_provider_requests": 2,
                                  "first_reserve_usd": str(first), "two_base_reserves_usd": str(first * 2),
                                  "estimated_ceiling_usd": plan["max_estimated_spend_usd"], "invoice_cap": False}, indent=2))
                return 0
            output = getattr(args, "output", None) or HERE / "results" / ("compat-" + uuid.uuid4().hex)
            if args.command == "live":
                if args.approve_freeze != identity:
                    raise ValueError("Approval does not match the exact compatibility plan and source")
                key, organization, project = credentials()
                transport = Transport(key, organization, project)
                journal = Journal(live_database())
                snapshot = execute(plan, journal, "live", transport, approval={"freeze_sha256": identity})
            else:
                journal = Journal(output / "ledger.sqlite3")
                snapshot = execute(plan, journal)
            export_snapshot(snapshot, output / "evidence.json")
            result = snapshot["run"]["summary"]
            print(json.dumps({"run_id": result["run_id"], "mode": result["mode"], "verdict": result["verdict"],
                              "reason": result["reason"], "provider_cost_usd": result["provider_cost_usd"],
                              "encrypted_reasoning_replay_demonstrated": result["encrypted_reasoning_replay_demonstrated"],
                              "evidence": str(output / "evidence.json")}, indent=2))
            return 0 if result["verdict"] in {"PASS", "FIXTURE_PASS"} else 2
        return 0
    except (ValueError, RuntimeError, OSError, sqlite3.Error) as exc:
        print("Stopped: " + type(exc).__name__, file=sys.stderr)
        return 1
    finally:
        if journal is not None:
            journal.close()


if __name__ == "__main__":
    raise SystemExit(main())
