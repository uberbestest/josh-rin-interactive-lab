#!/usr/bin/env python3
"""Verify the trusted canonical Round 05 two-goal evidence archive.

Reuse the established safe extraction, complete inventory, external freeze and
deterministic replay checks. Then require the full 12-family, two-replicate,
two-selector assignment and all 48 separately retained native report seals.
Only use this with this lab's trusted evidence: replay executes archived code.
This verifier never launches participant models.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime
import json
from pathlib import Path
import re
import tempfile

import verify_key_evidence as common

ARCHIVE_ROOT = "second-door-study"
EXPECTED_RUNS = 48
EXPECTED_FAMILIES = 12
MODELS = {"gpt-6-astra", "gpt-6.2-astra"}
RUN_ID = re.compile(r"[A-Za-z0-9_-]+\Z")
RUN_FILES = {"initial_state.json", "state.json", "events.jsonl",
             "final_report.json", "native_final_receipt.txt"}


def check_assignments_and_seals(root: Path, result: dict) -> dict:
    assignments = json.loads((root / "protocol/assignments.json").read_text(encoding="utf-8")).get("assignments")
    if not isinstance(assignments, list) or len(assignments) != EXPECTED_RUNS:
        raise ValueError("Round 05 requires all 48 prospectively assigned runs")
    run_ids = set()
    case_families = {}
    cells = Counter()
    selectors = Counter()
    for assignment in assignments:
        if not isinstance(assignment, dict):
            raise ValueError("Invalid assignment row")
        run_id = assignment.get("run_id")
        model = assignment.get("requested_model")
        family = assignment.get("family_id")
        case = assignment.get("case_id")
        replicate = assignment.get("replicate")
        if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id) or run_id in run_ids:
            raise ValueError("Missing, unsafe or duplicate run identifier")
        if model not in MODELS or not isinstance(family, str) or not family or not isinstance(case, str) or not case:
            raise ValueError("Missing family, case or requested selector")
        if type(replicate) is not int or replicate not in (1, 2):
            raise ValueError("Each family requires declared replicate 1 and 2")
        if case in case_families and case_families[case] != family:
            raise ValueError("A case maps to multiple families")
        case_families[case] = family
        run_ids.add(run_id)
        cells[(family, model, replicate)] += 1
        selectors[model] += 1
        directory = root / "runs" / run_id
        if not all((directory / name).is_file() for name in RUN_FILES):
            raise ValueError("Missing participant record or native seal: " + run_id)
        report_data = (directory / "final_report.json").read_bytes()
        expected = "SEALED " + run_id + " " + common.sha(report_data)
        if (directory / "native_final_receipt.txt").read_text(encoding="utf-8").strip() != expected:
            raise ValueError("Native acknowledgement does not bind the exact report: " + run_id)
    families = set(case_families.values())
    if len(case_families) != EXPECTED_FAMILIES or len(families) != EXPECTED_FAMILIES:
        raise ValueError("Round 05 requires one authored case in each of 12 families")
    expected_cells = {(family, model, replicate) for family in families for model in MODELS for replicate in (1, 2)}
    if set(cells) != expected_cells or any(count != 1 for count in cells.values()):
        raise ValueError("Matched family/selector/replicate assignment is incomplete")
    if selectors != Counter({model: EXPECTED_RUNS // 2 for model in MODELS}):
        raise ValueError("Requested-selector counts differ from the frozen design")
    actual_run_ids = {p.name for p in (root / "runs").iterdir() if p.is_dir()}
    if actual_run_ids != run_ids:
        raise ValueError("Archived run directories differ from the assignment ledger")
    if result.get("runs_replayed") != EXPECTED_RUNS or result.get("preserved_scientific_record_files") != 3 * EXPECTED_RUNS:
        raise ValueError("Replay did not preserve all 48 assigned trajectories")
    if result.get("observed_results_recomputed_exactly") is not True or not (root / "results/observed.json").is_file():
        raise ValueError("Observed scores were not recomputed exactly")
    return {"assignment_families_verified": len(families),
            "assignment_cells_verified": len(cells),
            "native_report_seals_verified": len(run_ids)}


def verify(root: Path, frozen_sha256: str, output: Path) -> dict:
    if root.name != ARCHIVE_ROOT:
        raise ValueError("Expected the canonical second-door-study archive root")
    result = common.verify(root, frozen_sha256, output)
    result.update(check_assignments_and_seals(root, result))
    result.update({"round": "round-05", "verification_kind": "second-door-v1"})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--frozen-sha256", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    archive = args.archive.resolve()
    if args.output is not None and args.output.resolve() == archive:
        raise ValueError("A replay receipt cannot overwrite its evidence archive")
    with tempfile.TemporaryDirectory(prefix="rin-second-door-evidence-") as folder:
        temporary = Path(folder)
        root = common.extract(archive, temporary / "extracted")
        result = verify(root, args.frozen_sha256, temporary / "reproduction.json")
    result.update({"public_archive": archive.name,
                   "public_archive_sha256": common.sha(archive.read_bytes()),
                   "public_archive_identical_to_canonical": True,
                   "fresh_extraction": True, "temporary_extraction_removed": True,
                   "verified_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()})
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fields = ("status", "round", "runs_replayed", "events_replayed", "mechanical_results_exact",
              "final_reports_exact", "assignment_cells_verified", "native_report_seals_verified")
    print(json.dumps({field: result[field] for field in fields}, indent=2))


if __name__ == "__main__":
    main()
