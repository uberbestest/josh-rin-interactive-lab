#!/usr/bin/env python3
"""Verify the trusted canonical Round07 receipt-feedback evidence archive.

The 32 fresh native runs are separate from the retained retrospective helper
replays. A complete exactly replayed failure is a valid published outcome.
This wrapper never starts native model participants. Archived Python and
JavaScript are executed only for this lab's trusted reproduction record.
"""
from __future__ import annotations
import argparse
from collections import Counter
import datetime
import json
from pathlib import Path
import tempfile
import verify_key_evidence as common

ARCHIVE_ROOT = 'delivery-study'
RECORD = 'JRR-RECEIPT-SCOPE-2026-11-18-007'
MODELS = {'gpt-6-astra', 'gpt-6.2-astra'}
SCOPES = {'combined', 'target'}
ORIENTATIONS = {'original', 'reflected'}
EXPECTED_RUNS = {f'x{n:03d}' for n in range(1, 33)}
RUN_FILES = {'initial_state.json', 'state.json', 'events.jsonl',
             'presentation_events.jsonl', 'transport.json', 'final_report.json',
             'native_final_receipt.txt'}


def check_assignments_and_seals(root, result):
    assignment_document = json.loads((root / 'protocol/assignments.json').read_text())
    assignments = assignment_document.get('assignments')
    if not isinstance(assignments, list) or len(assignments) != 32:
        raise ValueError('All 32 prospectively assigned contexts are required')
    cases = json.loads((root / 'protocol/cases.json').read_text()).get('cases')
    if not isinstance(cases, list) or len(cases) != 2:
        raise ValueError('Expected one original and one reflected task setting')
    catalog = {c['case_id']: c for c in cases}
    if set(catalog) != {'C11', 'C11R'} or {c['family_id'] for c in cases} != {'F02'}:
        raise ValueError('Expected the two declared settings of the F02 family')
    run_ids, cells = set(), Counter()
    for a in assignments:
        run = a.get('run_id')
        model, scope, orientation = (a.get(k) for k in ('requested_model', 'receipt_scope', 'orientation'))
        replicate = a.get('replicate')
        if run not in EXPECTED_RUNS or run in run_ids:
            raise ValueError('Unexpected or duplicated run identifier')
        if model not in MODELS or scope not in SCOPES or orientation not in ORIENTATIONS:
            raise ValueError('Missing or invalid selector, receipt scope or orientation')
        if type(replicate) is not int or replicate not in range(1, 5):
            raise ValueError('Expected four declared repetitions per setting and cell')
        expected_case = 'C11' if orientation == 'original' else 'C11R'
        if a.get('case_id') != expected_case or a.get('family_id') != 'F02':
            raise ValueError('Case/orientation/family mapping differs from the design')
        run_ids.add(run)
        cells[(model, scope, orientation, replicate)] += 1
        directory = root / 'runs' / run
        if not all((directory / name).is_file() for name in RUN_FILES):
            raise ValueError('Missing native, presentation or seal record: ' + run)
        transport = json.loads((directory / 'transport.json').read_text())
        if transport.get('receipt_scope') != scope:
            raise ValueError('Transport and assignment scope differ: ' + run)
        expected = 'SEALED ' + run + ' ' + common.sha((directory / 'final_report.json').read_bytes())
        if (directory / 'native_final_receipt.txt').read_text().strip() != expected:
            raise ValueError('Native acknowledgment differs from the report bytes: ' + run)
    expected_cells = {(m, s, o, r) for m in MODELS for s in SCOPES for o in ORIENTATIONS for r in range(1, 5)}
    if set(cells) != expected_cells or any(n != 1 for n in cells.values()):
        raise ValueError('The complete model/scope/orientation/repetition matrix is required')
    if run_ids != EXPECTED_RUNS or {p.name for p in (root / 'runs').iterdir() if p.is_dir()} != run_ids:
        raise ValueError('Native run directories differ from the assignment ledger')
    if result.get('runs_replayed') != 32 or result.get('preserved_scientific_record_files') != 96:
        raise ValueError('Native replay did not preserve the complete 32-run record')
    if result.get('presentation_record_files_verified') != 32 or result.get('transport_records_verified') != 32:
        raise ValueError('Native presentation or transport records were not all verified')
    if result.get('observed_results_recomputed_exactly') is not True:
        raise ValueError('Native scores were not recomputed exactly')
    review = result.get('label_masked_review_verification')
    if not isinstance(review, dict) or review.get('status') != 'PASS':
        raise ValueError('The final publication requires the completed semantic-review binding')
    if any(review.get(key) != 32 for key in ('review_packet_records_verified',
            'masked_judgments_bound', 'identity_mapping_cells_verified')):
        raise ValueError('Every native report requires a sealed and bound semantic judgment')
    observed = json.loads((root / 'results/observed.json').read_text())
    if observed.get('record') != RECORD:
        raise ValueError('Observed-score identity differs from Round07')
    return {'assignment_families_verified': 1, 'assignment_settings_verified': 2,
            'assignment_cells_verified': 32, 'repetitions_per_model_scope_orientation': 4,
            'receipt_scopes_verified': sorted(SCOPES), 'native_report_seals_verified': 32}


def verify(root, frozen_sha256, output):
    if root.name != ARCHIVE_ROOT:
        raise ValueError('Expected the canonical delivery-study archive root')
    result = common.verify(root, frozen_sha256, output)
    result.update(check_assignments_and_seals(root, result))
    result.update(round='round-07', verification_kind='receipt-scope-v1')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--frozen-sha256', required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    archive = args.archive.resolve()
    if args.output is not None and args.output.resolve() == archive:
        raise ValueError('A replay receipt cannot overwrite its evidence archive')
    with tempfile.TemporaryDirectory(prefix='rin-receipt-scope-evidence-') as folder:
        temp = Path(folder)
        root = common.extract(archive, temp / 'extracted')
        result = verify(root, args.frozen_sha256, temp / 'reproduction.json')
    result.update(public_archive=archive.name, public_archive_sha256=common.sha(archive.read_bytes()),
                  public_archive_identical_to_canonical=True, fresh_extraction=True,
                  temporary_extraction_removed=True,
                  verified_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: result[key] for key in ('status', 'round', 'runs_replayed', 'events_replayed',
          'mechanical_results_exact', 'final_reports_exact', 'assignment_cells_verified',
          'native_report_seals_verified', 'presentation_record_files_verified')}, indent=2))


if __name__ == '__main__':
    main()
