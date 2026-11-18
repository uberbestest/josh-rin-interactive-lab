#!/usr/bin/env python3
"""Replay the frozen study and compare its observed results without new models."""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import unittest
from engine import replay, report_bytes
from scoring import collect

ROOT = Path(__file__).resolve().parent


def reproduce():
    frozen = json.loads((ROOT / "protocol/frozen.json").read_text())
    for name, expected in frozen["source_hashes"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, "Frozen source changed: " + name
    suite = unittest.defaultTestLoader.discover(str(ROOT), pattern="test_*.py")
    test_stream = io.StringIO()
    test_result = unittest.TextTestRunner(stream=test_stream, verbosity=1).run(suite)
    if not test_result.wasSuccessful():
        raise AssertionError(test_stream.getvalue())
    import audit_oracle
    with contextlib.redirect_stdout(io.StringIO()):
        oracle_audit = audit_oracle.audit()
    assert oracle_audit["status"] == "PASS"
    assignments = json.loads((ROOT / "protocol/assignments.json").read_text())["assignments"]
    total_events = 0
    report_matches = 0
    state_matches = 0
    for assignment in assignments:
        directory = ROOT / "runs" / assignment["run_id"]
        initial = json.loads((directory / "initial_state.json").read_text())
        rows = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()]
        state = replay(initial, rows)
        assert state == json.loads((directory / "state.json").read_text()), assignment["run_id"]
        assert state["sealed"], "Missing final report: " + assignment["run_id"]
        state_matches += 1
        report_data = (directory / "final_report.json").read_bytes()
        assert report_data == report_bytes(state["final_report"]), "Sealed report differs"
        finish_rows = [row for row in rows if row["action"] == "finish"]
        assert finish_rows and finish_rows[0]["parameters"]["report"] == state["final_report"]
        seal = "SEALED " + assignment["run_id"] + " " + hashlib.sha256(report_data).hexdigest()
        assert (directory / "native_final_receipt.txt").read_text().strip() == seal, "Native final seal differs"
        assert finish_rows[0]["observation"]["receipt_line"] == seal, "Logged seal differs"
        report_matches += 1
        total_events += len(rows)
    observed = collect(ROOT)
    assert observed == json.loads((ROOT / "results/observed.json").read_text()), "Observed scoring differs from replay"
    return {"status": "PASS", "runs_replayed": len(assignments), "events_replayed": total_events,
            "mechanical_results_exact": state_matches, "final_reports_exact": report_matches,
            "preserved_scientific_record_files": 3 * len(assignments),
            "semantic_tests": {"status": "PASS", "tests": test_result.testsRun},
            "independent_analytic_oracle_audit": oracle_audit,
            "all_frozen_hashes_match": True, "observed_results_recomputed_exactly": True,
            "scope": "Deterministic same-lab replay, prospective scoring and separately derived oracle audit. No new model calls or external replication."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(ROOT):
        raise SystemExit("Write replay receipts outside the evidence tree")
    result = reproduce()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
