#!/usr/bin/env python3
"""Observation-only continuation planner for the published two-job contract.

This module has no service, fixture, oracle, filesystem, or network dependency.
The JSONL worker consumes a trusted public status and validates operation replies.
Its guarantee is conditional on that explicit synthetic contract, not arbitrary
remote services.  See CONTROLLER_DESIGN.md for the trust and search boundaries.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import sys
from typing import Any

VERSION = "0.1.0"
UNKNOWN, ABSENT, PRESENT, FINALIZED, DUPLICATED = range(5)


class ContractError(ValueError):
    """An input falls outside the supported public contract; no action is issued."""


def _int(value: Any, name: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ContractError(f"{name} must be an integer >= {minimum}")
    return value


def _bool(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise ContractError(f"{name} must be boolean")
    return value


def _digest(value: Any) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode()).hexdigest()


@dataclass(frozen=True)
class Model:
    names: tuple[str, str]
    deadlines: tuple[int, int]
    prices: tuple[int, int]
    priority: int
    uses: int
    tick: int
    remaining: int
    phases: tuple[int, int]
    readiness: tuple[tuple[int, ...], tuple[int, ...]]
    unbounded: tuple[bool, bool]
    sealed: bool


class ContinuationController:
    """One instance per independent task.  Only public observations are retained."""

    def __init__(self) -> None:
        self._pending_after: dict[str, int] = {}
        self._accepted_receipts: dict[str, str] = {}
        self._contract_identity: str | None = None
        self._last_status: dict[str, Any] | None = None
        self._issued: dict[str, Any] | None = None
        self._response_rejections = 0

    def _parse(self, status: dict[str, Any]) -> Model:
        if not isinstance(status, dict):
            raise ContractError("public status must be an object")
        constants = {
            "query_duration_ticks": 2,
            "commit_and_finalize_key_cost": 1,
            "commit_and_finalize_duration_ticks": 1,
        }
        for name, expected in constants.items():
            if type(status.get(name)) is not int or status[name] != expected:
                raise ContractError(f"unsupported {name}")
        if status.get("deadlines_are_inclusive") is not True:
            raise ContractError("inclusive deadlines are required")
        uses = _int(status.get("uses_remaining"), "uses_remaining")
        tick = _int(status.get("tick"), "tick")
        calls = _int(status.get("actions_taken"), "actions_taken")
        cap = _int(status.get("action_limit"), "action_limit")
        if calls > cap:
            raise ContractError("actions_taken exceeds action_limit")
        sealed = _bool(status.get("report_sealed"), "report_sealed")
        raw_jobs = status.get("jobs")
        if not isinstance(raw_jobs, dict) or len(raw_jobs) != 2:
            raise ContractError("exactly two independently uncertain jobs are supported")
        names = tuple(sorted(raw_jobs))
        if not all(isinstance(name, str) and name for name in names):
            raise ContractError("job identifiers must be nonempty strings")
        priority_name = status.get("priority_if_only_one_can_be_guaranteed")
        if priority_name not in raw_jobs:
            raise ContractError("priority must identify one of the jobs")
        deadlines, prices, phases, readiness, unbounded, contracts = [], [], [], [], [], []
        for name in names:
            job = raw_jobs[name]
            if not isinstance(job, dict):
                raise ContractError(f"{name}: job must be an object")
            if job.get("authorization") != "active" or job.get("authorization_stable") is not True:
                raise ContractError(f"{name}: stable active authorization is required")
            deadline = _int(job.get("deadline"), f"{name}.deadline")
            price = _int(job.get("query_key_cost"), f"{name}.query_key_cost")
            if price not in (0, 1):
                raise ContractError(f"{name}: only declared zero/one query prices are supported")
            receipt = job.get("original_write_receipt")
            if receipt not in ("unknown", "ABSENT", "COMMITTED"):
                raise ContractError(f"{name}: invalid original-write receipt")
            commits = _int(job.get("acknowledged_recovery_writes"), f"{name}.acknowledged_recovery_writes")
            finalized = _bool(job.get("finalized"), f"{name}.finalized")
            exact = _bool(job.get("confirmed_exactly_one_delivery"), f"{name}.confirmed_exactly_one_delivery")
            timing = job.get("receipt_timing")
            if not isinstance(timing, dict):
                raise ContractError(f"{name}: receipt timing is required")
            kind = timing.get("kind")
            if kind == "bounded":
                points = timing.get("possible_coverage_ticks")
                if not isinstance(points, list) or not points:
                    raise ContractError(f"{name}: nonempty coverage support is required")
                points = tuple(sorted(set(_int(r, f"{name}.coverage_tick") for r in points)))
                guaranteed = _int(timing.get("guaranteed_by_tick"), f"{name}.guaranteed_by_tick")
                if guaranteed != max(points):
                    raise ContractError(f"{name}: coverage bound disagrees with support")
                is_unbounded = False
            elif kind == "unbounded" and timing.get("guaranteed_by_tick") is None:
                points, is_unbounded = (), True
            else:
                raise ContractError(f"{name}: unsupported timing contract")
            if name in self._accepted_receipts and receipt != self._accepted_receipts[name]:
                raise ContractError(f"{name}: trusted status contradicts retained authoritative receipt")
            if finalized:
                if not exact:
                    raise ContractError(f"{name}: finalized without exactly-one evidence")
                phase = FINALIZED
            elif receipt == "unknown":
                if commits or exact:
                    raise ContractError(f"{name}: unresolved original write with recovery effects is unsupported")
                phase = UNKNOWN
            else:
                total = (receipt == "COMMITTED") + commits
                expected_exact = total == 1
                if exact != expected_exact:
                    raise ContractError(f"{name}: receipt and acknowledgement facts disagree")
                phase = ABSENT if total == 0 else PRESENT if total == 1 else DUPLICATED
            if phase == UNKNOWN and not is_unbounded:
                points = tuple(r for r in points if r > self._pending_after.get(name, -1))
                if not points:
                    raise ContractError(f"{name}: pending observation contradicts bounded support")
            deadlines.append(deadline)
            prices.append(price)
            phases.append(phase)
            readiness.append(points if phase == UNKNOWN else ())
            unbounded.append(is_unbounded)
            contracts.append((name, deadline, price, timing, job.get("packet"), job.get("destination")))
        if _bool(status.get("joint_complete"), "joint_complete") != all(p == FINALIZED for p in phases):
            raise ContractError("joint_complete disagrees with per-job completion")
        identity = _digest({"jobs": contracts, "priority": priority_name, "cap": cap, "constants": constants})
        if self._contract_identity is not None and identity != self._contract_identity:
            raise ContractError("task contract changed; create a new controller or reauthorize explicitly")
        self._contract_identity = identity
        if self._last_status is not None:
            previous = self._last_status
            if tick < previous["tick"] or uses > previous["uses_remaining"] or calls < previous["actions_taken"]:
                raise ContractError("trusted status counters moved backwards")
            for name in names:
                old, new = previous["jobs"][name], raw_jobs[name]
                if old["finalized"] and not new["finalized"]:
                    raise ContractError(f"{name}: finalization moved backwards")
                if new["acknowledged_recovery_writes"] < old["acknowledged_recovery_writes"]:
                    raise ContractError(f"{name}: acknowledged writes moved backwards")
                if old["original_write_receipt"] != "unknown" and new["original_write_receipt"] != old["original_write_receipt"]:
                    raise ContractError(f"{name}: immutable original receipt changed")
        self._last_status = json.loads(json.dumps(status))
        return Model(names, tuple(deadlines), tuple(prices), names.index(priority_name), uses,
                     tick, cap - calls, tuple(phases), tuple(readiness), tuple(unbounded), sealed)

    def next_action(self, public_status: dict[str, Any]) -> dict[str, Any]:
        model = self._parse(public_status)
        # A search node is an observation-equivalence class, not a selected hidden
        # world: resources, task phases and each unresolved timing support suffice.
        initial = (model.uses, model.tick, model.remaining, model.phases, model.readiness)

        def completed(phases):
            return (sum(p == FINALIZED for p in phases), int(phases[model.priority] == FINALIZED))

        def change(values, index, value):
            return tuple(value if k == index else old for k, old in enumerate(values))

        def choices(node):
            uses, tick, remaining, phases, support = node
            if not remaining or all(p == FINALIZED for p in phases):
                return
            order = sorted(range(2), key=lambda i: (model.deadlines[i], i != model.priority, model.names[i]))
            for i in order:
                phase = phases[i]
                if phase in (PRESENT, ABSENT) and uses >= 1 and tick + 1 <= model.deadlines[i]:
                    action = "finalize" if phase == PRESENT else "commit"
                    stage = FINALIZED if phase == PRESENT else PRESENT
                    next_node = (uses - 1, tick + 1, remaining - 1, change(phases, i, stage), support)
                    yield {"action": action, "job": model.names[i]}, (next_node,)
                if phase != UNKNOWN or model.unbounded[i] or uses < model.prices[i] or tick + 2 > model.deadlines[i]:
                    continue
                ready = tuple(r for r in support[i] if r <= tick + 2)
                future = tuple(r for r in support[i] if r > tick + 2)
                if not ready:
                    # A surely pending read is dominated by wait(2): same clock
                    # and action cost, no less credential remaining, no information.
                    continue
                outcomes = []
                for stage in (ABSENT, PRESENT):
                    outcomes.append((uses - model.prices[i], tick + 2, remaining - 1,
                                     change(phases, i, stage), change(support, i, ())))
                if future:
                    outcomes.append((uses - model.prices[i], tick + 2, remaining - 1,
                                     phases, change(support, i, future)))
                yield {"action": "receipt", "job": model.names[i]}, tuple(outcomes)
            # Only unresolved bounded coverage can make waiting improve information.
            # Enumerate every legal wait rather than assume a favored deadline order.
            if any(phases[i] == UNKNOWN and not model.unbounded[i] and support[i]
                   and max(support[i]) > tick + 2 for i in range(2)):
                for ticks in range(1, min(20, max(model.deadlines) - tick) + 1):
                    yield {"action": "wait", "ticks": ticks}, ((uses, tick + ticks, remaining - 1, phases, support),)

        @lru_cache(maxsize=None)
        def value(node):
            best = completed(node[3])
            if best == (2, 1) or not node[2]:
                return best
            for _, outcomes in choices(node):
                worst = min(value(outcome) for outcome in outcomes)
                if worst > best:
                    best = worst
                    if best == (2, 1):
                        break
            return best

        baseline = completed(model.phases)
        target = baseline if model.sealed else value(initial)
        selected, selected_value = {"action": "finish"}, baseline
        considered = 0
        if not model.sealed and target > baseline:
            for action, outcomes in choices(initial):
                considered += 1
                action_value = min(value(outcome) for outcome in outcomes)
                if action_value == target:
                    selected, selected_value = action, action_value
                    break
            else:
                raise RuntimeError("search value has no realizing public action")
        proof = {
            "version": "continuation-proof-v1",
            "public_status_sha256": _digest(public_status),
            "currently_finalized_value": list(baseline),
            "selected_action_worst_case_value": list(selected_value),
            "objective": "safe finalized count, then priority completion",
            "search_states": value.cache_info().currsize,
            "root_actions_examined_until_witness": considered,
            "unbounded_jobs_excluded_from_finite_guarantee": [model.names[i] for i in range(2)
                                                            if model.unbounded[i] and model.phases[i] == UNKNOWN],
            "rejected_responses_seen": self._response_rejections,
            "certificate_scope": "public-contract dynamic-programming witness; not external verification",
        }
        result = dict(selected, guaranteed_value=list(target), proof=proof)
        if selected["action"] == "finish":
            descriptions = []
            for name in model.names:
                job = public_status["jobs"][name]
                state = "finalized" if job["finalized"] else "unfinished"
                descriptions.append(f"{name}: {state}; original receipt {job['original_write_receipt']}; acknowledged recovery writes {job['acknowledged_recovery_writes']}")
            result["report"] = {
                "joint_complete": all(p == FINALIZED for p in model.phases),
                "uses_remaining": model.uses,
                "tick": model.tick,
                "summary": "; ".join(descriptions) + ". " + ("The report was already sealed." if model.sealed else
                    "No additional completion is guaranteed by the remaining public contract and resources."),
                "jobs": {name: {"finalized": public_status["jobs"][name]["finalized"],
                                  "original_write_receipt": public_status["jobs"][name]["original_write_receipt"],
                                  "confirmed_exactly_one_delivery": public_status["jobs"][name]["confirmed_exactly_one_delivery"],
                                  "acknowledged_recovery_writes": public_status["jobs"][name]["acknowledged_recovery_writes"]}
                         for name in model.names},
                "guaranteed_finalized_value": list(target),
            }
        self._issued = {k: v for k, v in selected.items() if k in ("action", "job", "ticks")}
        return result

    def observe_response(self, request: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
        """Validate the selected operation; never search unrelated nested status text.

        Rejection requests a fresh authoritative local status.  It does not issue
        finish, retry a write, or adopt the rejected header's factual claims.
        """
        def reject(reason):
            self._response_rejections += 1
            return {"accepted": False, "needs_fresh_status": True, "reason": reason}
        if not isinstance(request, dict) or not isinstance(response, dict):
            return reject("REQUEST_OR_RESPONSE_NOT_OBJECT")
        selected = {k: request[k] for k in ("action", "job", "ticks") if k in request and request[k] is not None}
        if self._issued is None or selected != self._issued:
            return reject("RESPONSE_NOT_BOUND_TO_ISSUED_REQUEST")
        action, job, status = selected["action"], selected.get("job"), response.get("status")
        if action in ("receipt", "commit", "finalize"):
            if status == "TERMINAL":
                return {"accepted": True, "needs_fresh_status": True, "reason": "TERMINAL_REQUIRES_STATUS"}
            if response.get("job") != job:
                return reject("RECEIPT_OR_ACK_JOB_MISMATCH")
            if status == "DENIED":
                if not isinstance(response.get("reason"), str):
                    return reject("DENIAL_REASON_MISSING")
                return {"accepted": True, "needs_fresh_status": True, "reason": "DENIAL_NO_DELIVERY_INFERENCE"}
        if action == "receipt":
            if response.get("transaction") != "original-write":
                return reject("RECEIPT_TRANSACTION_MISMATCH")
            if status == "PENDING":
                if response.get("coverage") != "NOT_ESTABLISHED":
                    return reject("PENDING_COVERAGE_MISMATCH")
                if self._last_status is not None:
                    end_tick = self._last_status["tick"] + 2
                    self._pending_after[job] = max(self._pending_after.get(job, -1), end_tick)
            elif status in ("ABSENT", "COMMITTED"):
                if response.get("coverage") != "AUTHORITATIVE_FINAL":
                    return reject("RECEIPT_COVERAGE_NOT_FINAL")
                old = self._accepted_receipts.get(job)
                if old is not None and old != status:
                    return reject("IMMUTABLE_RECEIPT_CHANGED")
                self._accepted_receipts[job] = status
            else:
                return reject("UNRECOGNIZED_RECEIPT_STATUS")
        elif action == "commit":
            if not (status == "APPLIED" and response.get("transaction") == "recovery-write"
                    and response.get("acknowledgement") == "AUTHORITATIVE"
                    and type(response.get("new_delivery_effects")) is int and response["new_delivery_effects"] == 1):
                return reject("FRESH_COMMIT_ACK_NOT_ESTABLISHED")
        elif action == "finalize":
            if not (status == "FINALIZED" and response.get("exactly_one_delivery") is True
                    and response.get("acknowledgement") == "AUTHORITATIVE"):
                return reject("FINALIZATION_ACK_NOT_ESTABLISHED")
        elif action == "wait":
            if status != "WAITED" or response.get("ticks") != selected["ticks"]:
                return reject("WAIT_ACK_MISMATCH")
        elif action == "finish":
            if status not in ("REPORT_RECORDED", "REPORT_ALREADY_SEALED"):
                return reject("REPORT_ACK_MISMATCH")
        else:
            return reject("UNSUPPORTED_REQUEST")
        return {"accepted": True, "needs_fresh_status": True, "reason": "SCOPED_RESPONSE_ACCEPTED"}

    record_response = observe_response


def next_action(public_status: dict[str, Any]) -> dict[str, Any]:
    """Stateless convenience; class instances additionally retain pending evidence."""
    return ContinuationController().next_action(public_status)


def main() -> None:
    controller = ContinuationController()
    for line in sys.stdin:
        try:
            item = json.loads(line)
            if item.get("op") == "decide":
                result = controller.next_action(item["status"])
            elif item.get("op") == "observe":
                result = controller.observe_response(item["request"], item["response"])
            else:
                raise ContractError("op must be decide or observe")
        except Exception as exc:
            result = {"error": type(exc).__name__, "message": str(exc), "action": None,
                      "needs_fresh_status": True}
        print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
