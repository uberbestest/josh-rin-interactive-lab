#!/usr/bin/env python3
"""Explicitly post-hoc counterexamples after the primary deadline-greedy tie.

Prepare hashes two transparent configurations before their first execution.
These six deterministic runs are never pooled with the frozen primary study.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

from independent_trace_check import check_episode

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "posthoc-diagnostics"


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True)+"\n")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod
    spec.loader.exec_module(mod); return mod


def prepare(study):
    def job(deadline, known, ready=0):
        return {"deadline": deadline, "initial_receipt": known,
                "prior_options": [0, 1], "query_cost": 1, "ready_options": [ready]}
    world = lambda a, b, ar=0: {"A": {"prior_delivered": a, "receipt_ready": ar},
                              "B": {"prior_delivered": b, "receipt_ready": 0}}
    cases = [
        {"case_id": "D01", "label": "deadline_order_spends_priority_budget",
         "config": {"jobs": {"A": job(1, 1), "B": job(2, 1)},
                    "uses_remaining": 1, "max_actions": 2, "priority": "B"},
         "worlds": [world(1, 1)],
         "reason": "Both are known present. One use allows only one finalization. Earlier-deadline A is nonpriority; B can still finish at tick 1. Count ties require choosing B."},
        {"case_id": "D02", "label": "use_waiting_interval_for_other_job",
         "config": {"jobs": {"A": job(6, None, 4), "B": job(7, 0)},
                    "uses_remaining": 5, "max_actions": 6, "priority": "A"},
         "worlds": [world(0, 0, 4), world(1, 0, 4)],
         "reason": "A's receipt cannot cover before tick 4. Commit/finalize known-absent B during ticks 1 and 2, then query A to tick 4. Waiting first wastes that interval; if A is absent, B cannot finalize by tick 7."},
    ]
    doc = {"record": "JRR-CONTINUATION-POSTHOC-DIAGNOSTIC-2026-11-19",
           "status": "EXPLORATORY_POST_HOC_NOT_HELD_OUT_NOT_PRIMARY",
           "selected_after": "Observed candidate/deadline_greedy tie in the 237-execution primary study.",
           "purpose": "Bound general equivalence of the cheap heuristic; do not retroactively claim a primary-suite superiority result.",
           "case_count": 2, "world_assignments": 3, "planned_executions": 6,
           "policies": ["candidate", "deadline_greedy"], "native_model_participants": 0,
           "cases": cases}
    dump(OUT / "cases.json", doc)
    frozen = {"frozen_at_utc": datetime.now(timezone.utc).isoformat(),
              "first_execution_occurred": False, "status": doc["status"],
              "cases_sha256": hashlib.sha256((OUT/"cases.json").read_bytes()).hexdigest(),
              "diagnostic_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "sources": {p: hashlib.sha256((study/p).read_bytes()).hexdigest()
                          for p in ("controller.py", "comparators.py", "run_study.py", "input/engine.py")}}
    dump(OUT / "freeze.json", frozen)
    print(json.dumps(frozen, indent=2, sort_keys=True))


def execute(study):
    frozen = json.loads((OUT/"freeze.json").read_text())
    if hashlib.sha256((OUT/"cases.json").read_bytes()).hexdigest() != frozen["cases_sha256"]:
        raise ValueError("Diagnostic config changed after freeze")
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != frozen["diagnostic_script_sha256"]:
        raise ValueError("Diagnostic script changed after freeze")
    for path, expected in frozen["sources"].items():
        if hashlib.sha256((study/path).read_bytes()).hexdigest() != expected:
            raise ValueError("Frozen source changed: " + path)
    runner = load_module("posthoc_frozen_runner", study/"run_study.py")
    runner.verify_freeze()
    engine = runner.engine_module()
    cases = json.loads((OUT/"cases.json").read_text())
    records, checked = [], []
    for case in cases["cases"]:
        for index, world in enumerate(case["worlds"]):
            for policy in cases["policies"]:
                run_id = f'{case["case_id"]}-W{index+1:02d}_{policy}'
                record = runner.run_episode(engine, case, world, policy, run_id, OUT,
                                            suite="exploratory_posthoc_diagnostic")
                recount = check_episode(record["initial_state"]["config"], world,
                                        record["events"], record["final_state"])
                records.append(record)
                checked.append({"run_id": run_id, "independent_recount": recount})
    result = runner.summarize(records)
    result.update(status=cases["status"], not_part_of_primary_237=True,
                  diagnostic_cases_sha256=frozen["cases_sha256"])
    dump(OUT/"summary.json", result)
    dump(OUT/"independent_check.json", {"scope": "Independent arithmetic/evidence recount; post-hoc diagnostics only.",
                                      "checked": checked})
    print(json.dumps(result["cells"], indent=2, sort_keys=True))
    for row in result["results"]:
        print(row["run_id"], row["initial_guaranteed_value"], row["safe_achieved_value"],
              "risky", row["risky_selections"], "loss", row["realized_guarantee_losses"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "run"))
    parser.add_argument("--study", type=Path, required=True)
    args = parser.parse_args()
    (prepare if args.mode == "prepare" else execute)(args.study)
