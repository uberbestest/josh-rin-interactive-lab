#!/usr/bin/env python3
"""Verify the trusted canonical Round 06 reporting-checklist evidence archive.

Reuse safe extraction, the complete inventory, the externally declared freeze,
and deterministic replay. Require one fresh context in every family, selector
and report-condition cell, plus all 48 separately retained native report seals.
The OPEN condition need not contain a jobs object. Report accuracy is a scored
outcome, not a condition for publishing a complete, exactly replayed record.
Only use this with this lab's trusted evidence: replay executes archived code.
This verifier never launches participant models.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime
import json
from pathlib import Path
import tempfile

import verify_key_evidence as common

ARCHIVE_ROOT = "two-job-study"
RECORD = "JRR-CHECKLIST-2026-11-18-006"
EXPECTED_RUNS = 48
EXPECTED_FAMILIES = 12
MODELS = {"gpt-6-astra", "gpt-6.2-astra"}
CONDITIONS = {"checklist", "open"}
EXPECTED_RUN_IDS = {f"w{number:03d}" for number in range(1, EXPECTED_RUNS + 1)}
RUN_FILES = {"initial_state.json", "state.json", "events.jsonl",
             "final_report.json", "native_final_receipt.txt"}


def case_catalog(root: Path) -> dict[str, str]:
    cases = json.loads((root / "protocol/cases.json").read_text(encoding="utf-8")).get("cases")
    if not isinstance(cases, list) or len(cases) != EXPECTED_FAMILIES:
        raise ValueError("Round 06 requires the 12 authored case families")
    mapping = {}
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("Invalid case catalog row")
        case_id, family = case.get("case_id"), case.get("family_id")
        if not isinstance(case_id, str) or not case_id or case_id in mapping:
            raise ValueError("Missing or duplicate case identifier")
        if not isinstance(family, str) or not family or family in mapping.values():
            raise ValueError("The catalog must contain one case per family")
        mapping[case_id] = family
    return mapping


def check_assignments_and_seals(root: Path, result: dict) -> dict:
    assignments = json.loads((root / "protocol/assignments.json").read_text(encoding="utf-8")).get("assignments")
    if not isinstance(assignments, list) or len(assignments) != EXPECTED_RUNS:
        raise ValueError("Round 06 requires all 48 prospectively assigned runs")
    catalog = case_catalog(root)
    run_ids = set()
    cells = Counter()
    selector_conditions = Counter()
    for assignment in assignments:
        if not isinstance(assignment, dict):
            raise ValueError("Invalid assignment row")
        run_id = assignment.get("run_id")
        model = assignment.get("requested_model")
        condition = assignment.get("report_condition")
        family = assignment.get("family_id")
        case = assignment.get("case_id")
        replicate = assignment.get("replicate")
        if not isinstance(run_id, str) or run_id not in EXPECTED_RUN_IDS or run_id in run_ids:
            raise ValueError("Missing, unexpected or duplicate run identifier")
        if model not in MODELS or condition not in CONDITIONS:
            raise ValueError("Missing or invalid requested selector or report condition")
        if not isinstance(case, str) or case not in catalog or catalog[case] != family:
            raise ValueError("Assignment case/family mapping differs from the case catalog")
        if type(replicate) is not int or replicate != 1:
            raise ValueError("Round 06 has one fresh context per family/selector/condition cell")
        run_ids.add(run_id)
        cells[(family, model, condition)] += 1
        selector_conditions[(model, condition)] += 1
        directory = root / "runs" / run_id
        if not all((directory / name).is_file() for name in RUN_FILES):
            raise ValueError("Missing participant record or native seal: " + run_id)
        report_data = (directory / "final_report.json").read_bytes()
        expected = "SEALED " + run_id + " " + common.sha(report_data)
        if (directory / "native_final_receipt.txt").read_text(encoding="utf-8").strip() != expected:
            raise ValueError("Native acknowledgement does not bind the exact report: " + run_id)
    expected_cells = {(family, model, condition) for family in catalog.values()
                      for model in MODELS for condition in CONDITIONS}
    if set(cells) != expected_cells or any(count != 1 for count in cells.values()):
        raise ValueError("Matched family/selector/report-condition assignment is incomplete")
    expected_counts = Counter({(model, condition): EXPECTED_FAMILIES
                               for model in MODELS for condition in CONDITIONS})
    if selector_conditions != expected_counts:
        raise ValueError("Selector/report-condition counts differ from the frozen design")
    actual_run_ids = {path.name for path in (root / "runs").iterdir() if path.is_dir()}
    if run_ids != EXPECTED_RUN_IDS or actual_run_ids != run_ids:
        raise ValueError("Archived run directories differ from the assignment ledger")
    if result.get("runs_replayed") != EXPECTED_RUNS or result.get("preserved_scientific_record_files") != 3 * EXPECTED_RUNS:
        raise ValueError("Replay did not preserve all 48 assigned trajectories")
    observed_path = root / "results/observed.json"
    if result.get("observed_results_recomputed_exactly") is not True or not observed_path.is_file():
        raise ValueError("Observed scores were not recomputed exactly")
    if json.loads(observed_path.read_text(encoding="utf-8")).get("record") != RECORD:
        raise ValueError("Observed score identity differs from Round 06")
    return {"assignment_families_verified": len(catalog),
            "assignment_cells_verified": len(cells),
            "report_conditions_verified": sorted(CONDITIONS),
            "fresh_contexts_per_family_selector_condition": 1,
            "native_report_seals_verified": len(run_ids)}


def verify(root: Path, frozen_sha256: str, output: Path) -> dict:
    if root.name != ARCHIVE_ROOT:
        raise ValueError("Expected the canonical two-job-study archive root")
    result = common.verify(root, frozen_sha256, output)
    result.update(check_assignments_and_seals(root, result))
    result.update({"round": "round-06", "verification_kind": "reporting-checklist-v1"})
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
    with tempfile.TemporaryDirectory(prefix="rin-checklist-evidence-") as folder:
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
