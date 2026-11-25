"""Offline semantic replay. Hash consistency is not external attestation."""
from __future__ import annotations

import base64
import datetime as dt
from decimal import Decimal
import json
import math

from common import canonical, digest, money
from protocol import (CASE_FAILURES, TOOLS, Fixture, Service, initial_history, price_usage,
                      request_payload, reserve_cost, validate_plan)


def _json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    def invalid(_value):
        raise ValueError("Non-finite JSON number")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def _equal(actual, expected, explanation):
    if canonical(actual) != canonical(expected):
        raise ValueError(explanation)


def validate_output(output):
    if not isinstance(output, list):
        raise ValueError("Output must be a list")
    if any(not isinstance(item, dict) or item.get("type") not in
           {"message", "reasoning", "function_call"} for item in output):
        raise ValueError("Unsupported response output; pricing basis is unknown")
    for item in output:
        if item["type"] == "message":
            content = item.get("content", [])
            if (not isinstance(content, list) or any(not isinstance(part, dict)
                    or part.get("type") not in {"output_text", "refusal"} for part in content)):
                raise ValueError("Unsupported message content; pricing basis is unknown")


def parse_action(output, seen):
    """Return one validated tool action, recording its identity only after validation."""
    validate_output(output)
    if not output:
        raise ValueError("Completed response has no output")
    calls = [item for item in output if item["type"] == "function_call"]
    if not calls:
        return None
    if len(calls) != 1:
        raise ValueError("Exactly one function call is supported")
    call = calls[0]
    call_id = call.get("call_id")
    if (call.get("name") != "service_action" or not isinstance(call_id, str)
            or not call_id.strip() or call_id in seen or not isinstance(call.get("arguments"), str)):
        raise ValueError("Invalid tool call identity")
    try:
        args = _json(call["arguments"])
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid tool argument JSON") from exc
    if (not isinstance(args, dict) or set(args) != {"action", "job"}
            or args["action"] not in ("receipt", "commit", "finalize") or args["job"] not in ("A", "B")):
        raise ValueError("Invalid tool arguments")
    seen.add(call_id)
    return {"call_id": call_id, "action": args["action"], "job": args["job"]}


def _timing(data, allow_unknown=False):
    for field in ("started_utc", "ended_utc"):
        value = data.get(field)
        if not isinstance(value, str) or dt.datetime.fromisoformat(value).utcoffset() != dt.timedelta(0):
            raise ValueError("Missing or invalid UTC timing evidence")
    elapsed = data.get("elapsed_seconds")
    if elapsed is None and allow_unknown:
        return
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError("Invalid elapsed time evidence")


def _decode_envelope(envelope):
    _timing(envelope, allow_unknown=bool(envelope.get("error_type")))
    if envelope.get("error_type") or not envelope.get("body_complete"):
        raise ValueError("RESPONSE_UNCERTAIN")
    if type(envelope.get("http_status")) is not int or not 200 <= envelope["http_status"] < 300:
        raise ValueError("HTTP_REJECTED")
    try:
        response = _json(base64.b64decode(envelope["body_base64"], validate=True).decode("utf-8"))
    except (ValueError, UnicodeError, KeyError) as exc:
        raise ValueError("INVALID_JSON") from exc
    if not isinstance(response, dict):
        raise ValueError("INVALID_JSON")
    return response


def _sources(metadata, plan):
    for key, expected in (("plan_sha256", digest(plan)), ("prompt_sha256", digest(initial_history())),
                          ("tools_sha256", digest(TOOLS))):
        _equal(metadata.get(key), expected, "Frozen metadata hash mismatch")
    bundle = metadata.get("source_bundle")
    if not isinstance(bundle, dict) or not bundle:
        raise ValueError("Frozen source bundle is missing")
    for name, source in bundle.items():
        if not isinstance(name, str) or not name or any(part in name for part in ("/", "\\", "..")):
            raise ValueError("Invalid frozen source name")
        raw = base64.b64decode(source["body_base64"], validate=True)
        _equal(source.get("sha256"), digest(raw), "Frozen source hash mismatch")
    return len(bundle)


def _receive(state, response, mode, plan):
    state["responses"] += 1
    model = response.get("model")
    if isinstance(model, str) and model not in state["returned_models"]:
        state["returned_models"].append(model)
    if not isinstance(response.get("id"), str) or not response["id"]:
        state["issue"] = "INVALID_JSON"
    elif mode == "live" and model not in plan["accepted_returned_models"][state["assignment"]["model"]]:
        state["issue"] = "UNEXPECTED_MODEL"
    elif mode == "live" and response.get("service_tier") != "default":
        state["issue"] = "UNEXPECTED_TIER"
    else:
        try:
            validate_output(response.get("output"))
        except ValueError:
            state["issue"] = "INVALID_OUTPUT"
    state["response"] = response
    if state["issue"] is None and mode == "live":
        state["model_response_observed"] = True
        try:
            state["calculation"] = price_usage(response.get("usage"),
                plan["pricing"][state["assignment"]["model"]], plan["max_priced_input_tokens"])
        except ValueError:
            state["issue"] = "UNPRICEABLE_USAGE"


def _after_pricing(state, plan, mode):
    response = state["response"]
    if mode == "live" and response["usage"]["output_tokens"] > plan["max_output_tokens"]:
        state["issue"] = "OUTPUT_LIMIT_EXCEEDED"
        return
    if response.get("status") == "incomplete":
        state["issue"] = "INCOMPLETE_RESPONSE"
        return
    if response.get("status") != "completed":
        state["issue"] = "UNEXPECTED_RESPONSE_STATUS"
        return
    try:
        action = parse_action(response["output"], state["seen"])
    except ValueError:
        state["issue"] = "INVALID_TOOL_CALL"
        return
    state["history"].extend(response["output"])
    state["action"] = action
    if action is None:
        state["terminal"] = "COMPLETED" if state["service"].report()["safe_joint_completion"] else "STOPPED_EARLY"


def _refusal_reason(state, plan, settled):
    assignment = state["assignment"]
    try:
        amount = reserve_cost(request_payload(state["history"], assignment["model"], plan),
                              assignment["model"], plan, state["prior_usage"])
    except ValueError:
        return "INPUT_RESERVE_OUTSIDE_PRICING_BASIS"
    total = sum((cost for _, cost in settled), Decimal(0))
    case_total = sum((cost for case_id, cost in settled if case_id == assignment["case_id"]), Decimal(0))
    if total + amount > money(plan["max_estimated_spend_usd"]):
        return "RUN_BUDGET_EXCEEDED"
    if case_total + amount > money(plan["max_estimated_spend_per_case_usd"]):
        return "CASE_BUDGET_EXCEEDED"
    return None


def verify_snapshot(snapshot):
    """Replay semantics; call ledger.verify_accounting for ledger/chain integrity too."""
    run, records, events = snapshot["run"], snapshot["requests"], snapshot["events"]
    plan, mode = run["plan"], run["mode"]
    validate_plan(plan)
    if mode not in {"live", "fixture"} or (mode == "fixture" and records):
        raise ValueError("Invalid run mode or provider requests in a fixture")
    source_count = _sources(run["metadata"], plan)
    requests = {record["id"]: record for record in records}
    if len(requests) != len(records):
        raise ValueError("Repeated request identity")
    state, rows, reserved, settled = None, [], [], []
    halt_reason, tool_count = None, 0
    for event in events:
        kind, data = event["kind"], event["data"]
        if kind == "case_started":
            if state is not None or len(rows) >= len(plan["assignments"]):
                raise ValueError("Case start order mismatch")
            assignment = plan["assignments"][len(rows)]
            expected = {"case_id": assignment["case_id"], "model": assignment["model"],
                        "case": assignment["case"], "prompt_sha256": digest(initial_history()), "tools_sha256": digest(TOOLS)}
            _equal(data, expected, "Case assignment or prompt differs from the frozen plan")
            state = {"assignment": assignment, "service": Service(assignment["case"]),
                     "fixture": Fixture(assignment["case"]), "history": initial_history(), "seen": set(),
                     "calls": 0, "responses": 0, "returned_models": [], "model_response_observed": False, "issue": None,
                     "terminal": None, "action": None, "pending": None, "response": None,
                     "calculation": None, "blocked": halt_reason, "prior_usage": None}
        elif kind in {"request_reserved", "fixture_exchange"}:
            if (state is None or halt_reason is not None or state["issue"] or state["terminal"]
                    or state["action"] is not None or state["pending"] is not None):
                raise ValueError("Request issued after halt or before completing its prior action")
            assignment = state["assignment"]
            expected = request_payload(state["history"], assignment["model"], plan)
            _equal(data["case_id"], assignment["case_id"], "Request belongs to the wrong case")
            state["calls"] += 1
            if state["calls"] > plan["max_calls_per_case"]:
                raise ValueError("Request ceiling exceeded")
            if kind == "fixture_exchange":
                if mode != "fixture":
                    raise ValueError("Fixture event in a provider run")
                _equal(data["request"], expected, "Fixture request history mismatch")
                _equal(data["response"], state["fixture"].create(expected), "Scripted fixture response mismatch")
                _receive(state, data["response"], mode, plan)
                if state["issue"] is None:
                    _after_pricing(state, plan, mode)
            else:
                if mode != "live":
                    raise ValueError("Provider reservation in a fixture")
                record = requests[data["id"]]
                _equal(data["payload"], expected, "Exact provider request history mismatch")
                _equal(record["payload"], expected, "Request record differs from its event")
                amount = reserve_cost(expected, assignment["model"], plan, state["prior_usage"])
                if money(data["reserve_usd"]) != amount or money(record["reserve_usd"]) != amount:
                    raise ValueError("Request reserve does not match frozen calculation")
                reserved.append(data["id"])
                state["pending"] = data["id"]
        elif kind == "response_saved":
            if state is None or state["pending"] != data["request_id"] or state["response"] is not None:
                raise ValueError("Response order mismatch")
            _equal(data["envelope"], requests[data["request_id"]]["response"], "Response record mismatch")
            try:
                response = _decode_envelope(data["envelope"])
            except ValueError as exc:
                if str(exc) not in {"RESPONSE_UNCERTAIN", "HTTP_REJECTED", "INVALID_JSON"}:
                    raise
                state["issue"] = str(exc)
            else:
                _receive(state, response, mode, plan)
        elif kind == "request_settled":
            if state is None or state["pending"] != data["request_id"] or state["issue"] or state["calculation"] is None:
                raise ValueError("Unpriceable or missing response was settled")
            record = requests[data["request_id"]]
            _equal(data["calculation"], state["calculation"], "Recomputed price differs from settlement")
            _equal(record["calculation"], state["calculation"], "Pricing record differs from raw response usage")
            cost = money(state["calculation"]["estimated_cost_usd"])
            if money(data["cost_usd"]) != cost or money(record["cost_usd"]) != cost:
                raise ValueError("Settlement cost mismatch")
            settled.append((state["assignment"]["case_id"], cost))
            state["pending"] = None
            state["prior_usage"] = state["response"]["usage"]
            if cost > money(record["reserve_usd"]):
                state["issue"] = "RESERVE_EXCEEDED"
            else:
                _after_pricing(state, plan, mode)
        elif kind == "tool_action":
            if state is None or state["pending"] or state["issue"] or state["action"] is None:
                raise ValueError("Tool action has no valid completed, priced response")
            action = state["action"]
            result = state["service"].act(action["action"], action["job"])
            _equal(data, {"case_id": state["assignment"]["case_id"], **action, "result": result}, "Tool replay mismatch")
            state["history"].append({"type": "function_call_output", "call_id": action["call_id"], "output": canonical(result)})
            state.update(action=None, response=None, calculation=None)
            tool_count += 1
        elif kind == "run_halted":
            if halt_reason is not None:
                raise ValueError("Duplicate run halt")
            halt_reason = data["reason"]
            if state is not None and state["issue"] is None and halt_reason == "RUN_BUDGET_EXCEEDED":
                if _refusal_reason(state, plan, settled) != halt_reason:
                    raise ValueError("Reported budget refusal has no replayable basis")
                state["issue"] = halt_reason
            if state is None or state["issue"] != halt_reason or halt_reason in CASE_FAILURES:
                raise ValueError("Global halt must have a matching global safety reason")
        elif kind == "case_finished":
            if state is None or state["action"] is not None:
                raise ValueError("Missing case start or unapplied valid tool action")
            if state["blocked"] is not None:
                status, reason = "BLOCKED", state["blocked"]
            elif state["issue"] is None and data.get("reason") in {
                    "CASE_BUDGET_EXCEEDED", "INPUT_RESERVE_OUTSIDE_PRICING_BASIS"}:
                reason = _refusal_reason(state, plan, settled)
                if reason != data["reason"] or halt_reason is not None:
                    raise ValueError("Case refusal has no replayable basis")
                status = "CASE_FAILED"
            elif state["issue"]:
                reason = state["issue"]
                status = "CASE_FAILED" if reason in CASE_FAILURES else "HALTED"
                if status == "HALTED" and halt_reason is None:
                    raise ValueError("Failed case did not halt later requests")
                if status == "CASE_FAILED" and halt_reason is not None:
                    raise ValueError("Case failure incorrectly blocked later cases")
            elif state["terminal"]:
                status, reason = state["terminal"], None
            elif state["calls"] == plan["max_calls_per_case"] and state["pending"] is None:
                status, reason = "CALL_LIMIT", None
            else:
                raise ValueError("Case finished without a replayable stopping condition")
            expected = {"case_id": state["assignment"]["case_id"], "requested_model": state["assignment"]["model"],
                        "status": status, "reason": reason, "calls": state["calls"], "responses": state["responses"],
                        "returned_models": state["returned_models"], "model_response_observed": state["model_response_observed"],
                        "unsupported_claims": None,
                        "outcome": state["service"].report()}
            _equal({key: data.get(key) for key in expected}, expected, "Case result does not match response and service replay")
            _timing(data)
            rows.append(data)
            state = None
        elif kind not in {"run_started", "run_finished", "halt_reviewed"}:
            raise ValueError("Unknown replay event")
    _equal(reserved, [record["id"] for record in records], "Request denominator/order mismatch")
    if run["summary"] is not None:
        if state is not None or len(rows) != len(plan["assignments"]):
            raise ValueError("Completed summary loses assigned cases")
        totals = snapshot["totals"]
        expected = {"run_id": run["id"], "mode": mode, "protocol_id": plan["protocol_id"],
                    "assigned_contexts": len(rows), "safe_joint_completions": sum(row["outcome"]["safe_joint_completion"] for row in rows),
                    "model_contexts_observed": sum(row["model_response_observed"] for row in rows),
                    "case_failures": sum(row["status"] not in {"COMPLETED", "BLOCKED"} for row in rows),
                    "blocked_contexts": sum(row["status"] == "BLOCKED" for row in rows),
                    "successful": all(row["status"] == "COMPLETED" for row in rows),
                    "provider_cost_usd": totals["estimated_total_cost_usd"] if mode == "live" else None,
                    "cases": rows, **totals, "interpretation": "Scripted infrastructure fixture; no model evidence" if mode == "fixture"
                        else "Estimated costs; semantic claims require human review"}
        _equal(run["summary"], expected, "Summary disagrees with replayed cases/accounting")
    return {"verified_assignments": len(rows), "planned_assignments": len(plan["assignments"]),
            "verified_requests": len(records), "verified_tool_actions": tool_count,
            "verified_source_files": source_count, "complete": run["summary"] is not None, "mode": mode}
