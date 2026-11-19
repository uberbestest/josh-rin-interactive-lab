#!/usr/bin/env python3
"""Small structural-validation probes outside the assigned study denominator.

These probes use authored public dictionaries. They never load challenge cases,
the reference engine, or hidden worlds, and they never execute service actions.
"""
from __future__ import annotations
import argparse
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

EXPECTED = "3d6403062e9914046a487fefb4fa17bf666a51ed84eb8219394dd6d32a9317c7"


def public_status(a="unknown", b="COMMITTED"):
    jobs = {}
    for name, receipt, deadline in (("A", a, 8), ("B", b, 12)):
        exact = receipt == "COMMITTED"
        jobs[name] = {"packet": "PACKET-"+name, "destination": "ARCHIVE-"+name,
                      "authorization": "active", "authorization_stable": True,
                      "deadline": deadline, "query_key_cost": 1,
                      "original_write_receipt": receipt,
                      "receipt_timing": {"kind": "bounded", "possible_coverage_ticks": [0], "guaranteed_by_tick": 0},
                      "delivery": "unknown" if receipt == "unknown" else "present" if exact else "absent",
                      "confirmed_exactly_one_delivery": exact,
                      "acknowledged_recovery_writes": 0, "finalized": False}
    return {"uses_remaining": 6, "tick": 0, "actions_taken": 0, "action_limit": 8,
            "priority_if_only_one_can_be_guaranteed": "A", "query_duration_ticks": 2,
            "commit_and_finalize_key_cost": 1, "commit_and_finalize_duration_ticks": 1,
            "deadlines_are_inclusive": True, "jobs": jobs,
            "joint_complete": False, "report_sealed": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    source = args.candidate.read_bytes()
    if hashlib.sha256(source).hexdigest() != EXPECTED:
        raise SystemExit("Candidate differs from frozen source")
    spec = importlib.util.spec_from_file_location("frozen_candidate_audit", args.candidate)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    results, boundaries = [], []

    def selected(status, action):
        controller = module.ContinuationController()
        decision = controller.next_action(status)
        if decision["action"] != action or decision.get("job") != "A":
            raise AssertionError("Constructed probe did not select expected action")
        return controller, {k: decision[k] for k in ("action", "job", "ticks") if k in decision}

    def response_probe(name, state, action, response, expected=False):
        controller, request = selected(state, action)
        result = controller.observe_response(request, response)
        if result["accepted"] is not expected:
            raise AssertionError(name + ": unexpected validation result: " + repr(result))
        results.append({"probe": name, "passed": True, "accepted": result["accepted"], "reason": result["reason"]})

    valid_receipt = {"status": "ABSENT", "job": "A", "transaction": "original-write", "coverage": "AUTHORITATIVE_FINAL"}
    response_probe("valid target receipt control", public_status(), "receipt", valid_receipt, True)
    for label, key, value in (
        ("wrong-job receipt", "job", "B"),
        ("wrong-transaction receipt", "transaction", "recovery-write"),
        ("nonfinal receipt coverage", "coverage", "NOT_ESTABLISHED"),
        ("unrecognized receipt status", "status", "SUCCESS"),
    ):
        response = dict(valid_receipt); response[key] = value
        response_probe(label, public_status(), "receipt", response)
    pending = {"status": "PENDING", "job": "A", "transaction": "original-write", "coverage": "AUTHORITATIVE_FINAL"}
    response_probe("pending cannot assert final coverage", public_status(), "receipt", pending)
    response = dict(valid_receipt); response.pop("job")
    response_probe("missing receipt job", public_status(), "receipt", response)
    response = dict(valid_receipt); response["status"] = "PENDING"; response["coverage"] = "NOT_ESTABLISHED"
    response["other"] = {"status": "ABSENT", "job": "B"}
    response_probe("pending response not authorized by another job marker", public_status(), "receipt", response, True)

    valid_commit = {"status": "APPLIED", "job": "A", "transaction": "recovery-write",
                    "acknowledgement": "AUTHORITATIVE", "new_delivery_effects": 1}
    response_probe("valid fresh-commit control", public_status("ABSENT"), "commit", valid_commit, True)
    for label, key, value in (
        ("fresh-commit wrong job", "job", "B"),
        ("fresh-commit wrong transaction", "transaction", "original-write"),
        ("fresh-commit nonauthoritative ack", "acknowledgement", "PENDING"),
        ("fresh-commit effect bool rejected", "new_delivery_effects", True),
        ("fresh-commit multiple effects rejected", "new_delivery_effects", 2),
    ):
        response = dict(valid_commit); response[key] = value
        response_probe(label, public_status("ABSENT"), "commit", response)

    valid_finalize = {"status": "FINALIZED", "job": "A", "exactly_one_delivery": True, "acknowledgement": "AUTHORITATIVE"}
    response_probe("valid finalization control", public_status("COMMITTED"), "finalize", valid_finalize, True)
    for label, key, value in (
        ("finalization wrong job", "job", "B"),
        ("finalization missing exact evidence", "exactly_one_delivery", False),
        ("finalization integer exact flag rejected", "exactly_one_delivery", 1),
        ("finalization nonauthoritative ack", "acknowledgement", "UNVERIFIED"),
    ):
        response = dict(valid_finalize); response[key] = value
        response_probe(label, public_status("COMMITTED"), "finalize", response)

    mutations = []
    def add_status(label, mutate):
        status = public_status(); mutate(status); mutations.append((label, status))
    add_status("revoked authorization", lambda s: s["jobs"]["A"].update(authorization="revoked"))
    add_status("unstable authorization", lambda s: s["jobs"]["A"].update(authorization_stable=False))
    add_status("boolean use count", lambda s: s.update(uses_remaining=True))
    add_status("negative tick", lambda s: s.update(tick=-1))
    add_status("unsupported query duration", lambda s: s.update(query_duration_ticks=1))
    add_status("invalid priority", lambda s: s.update(priority_if_only_one_can_be_guaranteed="C"))
    add_status("unknown receipt with exact evidence", lambda s: s["jobs"]["A"].update(confirmed_exactly_one_delivery=True))
    add_status("unknown receipt with recovery write", lambda s: s["jobs"]["A"].update(acknowledged_recovery_writes=1))
    add_status("contradictory bounded timing", lambda s: s["jobs"]["A"]["receipt_timing"].update(guaranteed_by_tick=2))
    add_status("exclusive deadlines unsupported", lambda s: s.update(deadlines_are_inclusive=False))
    add_status("joint flag contradicts jobs", lambda s: s.update(joint_complete=True))
    add_status("actions exceed cap", lambda s: s.update(actions_taken=9))
    for label, state in mutations:
        try:
            module.ContinuationController().next_action(state)
        except module.ContractError as exc:
            results.append({"probe": label, "passed": True, "rejected": True, "reason": str(exc)})
        else:
            raise AssertionError("Invalid status accepted: " + label)

    for label, mutate in (
        ("changed deadline after first decision", lambda s: s["jobs"]["A"].update(deadline=9)),
        ("changed priority after first decision", lambda s: s.update(priority_if_only_one_can_be_guaranteed="B")),
        ("increased resource counter", lambda s: s.update(uses_remaining=7)),
    ):
        controller = module.ContinuationController(); state = public_status()
        controller.next_action(state); altered = deepcopy(state); mutate(altered)
        try:
            controller.next_action(altered)
        except module.ContractError as exc:
            results.append({"probe": label, "passed": True, "rejected": True, "reason": str(exc)})
        else:
            raise AssertionError("Cross-observation contradiction accepted: " + label)

    controller, request = selected(public_status(), "receipt")
    wrong_request = dict(request, job="B")
    result = controller.observe_response(wrong_request, dict(valid_receipt, job="B"))
    assert not result["accepted"]
    results.append({"probe": "reply bound to issued request", "passed": True, "accepted": False, "reason": result["reason"]})

    # Explicit boundaries are recorded, not silently relabeled as rejected inputs.
    controller, request = selected(public_status(), "receipt")
    first = controller.observe_response(request, valid_receipt)
    repeated = controller.observe_response(request, valid_receipt)
    assert first["accepted"] and repeated["accepted"]
    boundaries.append({"witness": "well-formed same-job fabricated receipt accepted structurally",
                       "result": first, "interpretation": "The parser authenticates neither source nor truthful coverage. Trusted service/status is an assumption."})
    boundaries.append({"witness": "identical reply accepted twice before another decision",
                       "result": repeated, "interpretation": "No per-request nonce or consumed-response replay defense is implemented."})

    status = public_status("ABSENT")
    status["jobs"]["A"].update(finalized=True, confirmed_exactly_one_delivery=True)
    decision = module.ContinuationController().next_action(status)
    boundaries.append({"witness": "contradictory finalized receipt facts accepted under trusted-status assumption",
                       "decision_action": decision["action"], "guaranteed_value": decision["guaranteed_value"],
                       "interpretation": "A finalized/exact flag is trusted even if ABSENT plus zero fresh writes contradicts it. This is not validation of arbitrary untrusted status."})

    status = public_status("unknown", "unknown")
    for job in status["jobs"].values():
        job["receipt_timing"] = {"kind": "bounded", "possible_coverage_ticks": [3], "guaranteed_by_tick": 3}
    controller = module.ContinuationController(); decision = controller.next_action(status)
    assert decision["action"] == "wait" and decision["ticks"] == 1
    result = controller.observe_response({"action": "wait", "ticks": 1}, {"status": "WAITED", "ticks": True})
    assert result["accepted"]
    boundaries.append({"witness": "boolean wait acknowledgement equals integer one",
                       "result": result,
                       "interpretation": "Wait ack comparison is value-based, not exact-type validation. No delivery inference is made; a fresh trusted status is still required."})

    imports = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module)
    output = {"candidate_sha256": EXPECTED, "verified_at_utc": datetime.now(timezone.utc).isoformat(),
              "source_imports": sorted(set(imports)), "structural_probes_passed": len(results),
              "boundary_witnesses": len(boundaries), "primary_study_assignments_executed": 0,
              "native_model_participants": 0, "results": results, "boundaries": boundaries,
              "scope": "Same-lab frozen-source validation probes. No hidden challenge cases, reference engine or service execution used."}
    destination = Path(__file__).resolve().parent / "candidate_validation_results.json"
    destination.write_text(json.dumps(output, indent=2, sort_keys=True)+"\n")
    print(json.dumps({k: v for k, v in output.items() if k not in ("results", "boundaries")}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
