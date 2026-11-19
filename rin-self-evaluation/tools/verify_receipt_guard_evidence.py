#!/usr/bin/env python3
"""Verify the trusted Round 08 deterministic receipt-guard evidence archive.

This wrapper executes only retained JavaScript/Python against temporary copies
of the synthetic service. It launches no model participants and requires no
invented native reports or seals. Use only this lab's trusted evidence archive.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import verify_key_evidence as common

ARCHIVE_ROOT = 'receipt-guard-study'
RECORD = 'JRR-RECEIPT-GUARDS-2026-11-18-008'
CASE_IDS = {'control_committed', 'control_absent', 'pending_absent',
            'pending_present', 'pending_no_decoy', 'wrong_job_absent',
            'wrong_job_present', 'legacy_regression'}
HELPERS = {'w041', 'w042'}
ARMS = {'recovered', 'predicate_only', 'status_guard', 'status_job_guard'}
RUN_FILES = {'initial_state.json', 'state.json', 'events.jsonl',
             'transport.json', 'analysis.json'}


def verify(root: Path, frozen_sha256: str, output: Path) -> dict:
    if root.name != ARCHIVE_ROOT:
        raise ValueError('Expected the canonical receipt-guard-study root')
    if not common.DIGEST.fullmatch(frozen_sha256):
        raise ValueError('A valid external pre-run freeze digest is required')
    inventory_before = (root / common.INVENTORY).read_bytes()
    _, actual = common.check_inventory(root)
    freeze_raw = actual[common.FREEZE].read_bytes()
    if common.sha(freeze_raw) != frozen_sha256:
        raise ValueError('Archived freeze differs from the public study identity')
    frozen = json.loads(freeze_raw)
    sources = frozen.get('source_hashes')
    required = {'input/engine.py', 'input/client.py', 'execute.py',
                'reproduce.py', 'run_helper.mjs', 'protocol/cases.json',
                'verify_witnesses.py', 'protocol/witness_checks.json',
                'tests/test_transport.mjs', 'tests/test_failure_retention.py'}
    required |= {f'helpers/{helper}_{part}.js'
                 for helper in HELPERS for part in {'setup'} | ARMS}
    if not isinstance(sources, dict) or not required <= set(sources):
        raise ValueError('Frozen instrument, cases and all helper sources are required')
    for name, entry in sources.items():
        common.relative_path(name)
        digest = entry.get('sha256') if isinstance(entry, dict) else entry
        if name not in actual or not common.DIGEST.fullmatch(str(digest)):
            raise ValueError('Invalid frozen source: ' + name)
        if common.sha(actual[name].read_bytes()) != digest:
            raise ValueError('Frozen source changed: ' + name)

    design = json.loads((root / 'protocol/cases.json').read_text())
    cases = design.get('cases')
    if design.get('record') != RECORD or not isinstance(cases, list):
        raise ValueError('Unexpected study identity or case matrix')
    if len(cases) != 8 or {c['case_id'] for c in cases} != CASE_IDS:
        raise ValueError('Expected the eight prospectively selected cases')
    if set(design.get('helper_sources', [])) != HELPERS or set(design.get('arms', [])) != ARMS:
        raise ValueError('Expected both recovered helpers and all four interventions')
    if design.get('assigned_scripted_executions') != 64 or design.get('native_participants') != 0:
        raise ValueError('Expected 64 scripted assignments and zero native participants')
    expected_ids = {f'{case}_{helper}_{arm}'
                    for case in CASE_IDS for helper in HELPERS for arm in ARMS}
    run_root = root / 'results/runs'
    if {p.name for p in run_root.iterdir() if p.is_dir()} != expected_ids:
        raise ValueError('Recorded directories do not match the complete assignment matrix')
    for run_id in expected_ids:
        if {p.name for p in (run_root / run_id).iterdir()} != RUN_FILES:
            raise ValueError('Incomplete or unexpected scripted run files: ' + run_id)
    summary = json.loads((root / 'results/summary.json').read_text())
    if summary.get('authored_service_replays') != 64 or summary.get('native_participants') != 0:
        raise ValueError('Summary does not describe the complete scripted matrix')
    if {r['run_id'] for r in summary.get('runs', [])} != expected_ids or len(summary['runs']) != 64:
        raise ValueError('Summary rows differ from scripted assignments')

    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    witness_command = [sys.executable, '-B', 'verify_witnesses.py',
                       '--check', 'protocol/witness_checks.json']
    witness_check = subprocess.run(witness_command, cwd=root, env=environment,
                                   text=True, encoding='utf-8', capture_output=True,
                                   timeout=120, check=False)
    if witness_check.returncode:
        raise ValueError('Authored witness verification failed:\n' + (witness_check.stdout + witness_check.stderr)[-3000:])
    witnesses = json.loads(witness_check.stdout.strip().splitlines()[-1])
    if witnesses != {'status': 'PASS', 'witness_world_executions': 28,
                     'initial_policy_executions': 20, 'post_pending_recovery_executions': 8,
                     'all_safe_joint_completions': True}:
        raise ValueError('Authored witness count or completion result differs')
    transport_check = subprocess.run(['node', 'tests/test_transport.mjs'], cwd=root,
                                     env=environment, text=True, encoding='utf-8',
                                     capture_output=True, timeout=60, check=False)
    if transport_check.returncode:
        raise ValueError('Transport unit checks failed:\n' + (transport_check.stdout + transport_check.stderr)[-3000:])
    transport_tests = json.loads(transport_check.stdout.strip().splitlines()[-1])
    if transport_tests != {'status': 'PASS', 'unit_tests': 10,
                           'actual_service_calls': 0, 'study_matrix_runs': 0}:
        raise ValueError('Transport unit-check count or scope differs')
    retention_check = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover',
                                      '-s', 'tests', '-p', 'test_failure_retention.py', '-v'],
                                     cwd=root, env=environment, text=True, encoding='utf-8',
                                     capture_output=True, timeout=60, check=False)
    if retention_check.returncode or 'Ran 3 tests' not in retention_check.stderr:
        raise ValueError('Failure-retention unit checks failed:\n' + (retention_check.stdout + retention_check.stderr)[-3000:])
    retention_tests = {'status': 'PASS', 'unit_tests': 3,
                       'scope': 'Isolated mocked timeout, nonzero exit and invalid JSON; no service or study matrix execution.'}
    command = [sys.executable, '-B', 'reproduce.py', '--output', str(output)]
    completed = subprocess.run(command, cwd=root, env=environment,
                               text=True, encoding='utf-8', capture_output=True,
                               timeout=600, check=False)
    if completed.returncode != 0 or not output.is_file():
        raise ValueError('Deterministic reproduction failed:\n' + (completed.stdout + completed.stderr)[-6000:])
    replay = json.loads(output.read_text())
    if replay.get('status') != 'PASS' or replay.get('retained_runs_verified') != 64:
        raise ValueError('Every retained scripted execution must verify')
    if replay.get('fresh_helper_replays') != 64 or replay.get('fresh_actions_observations_oracles_states_and_transport_match') is not True:
        raise ValueError('Every frozen helper must execute again with an exact normalized match')
    if replay.get('individual_retained_and_fresh_event_chains_verified') is not True:
        raise ValueError('Canonical event chains were not all verified')
    if replay.get('no_native_participants') is not True or replay.get('retained_files_modified') is not False:
        raise ValueError('Reproduction scope or evidence-preservation assertion differs')
    if replay.get('freeze_sha256') != frozen_sha256:
        raise ValueError('Reproduction used a different freeze')
    event_count = replay.get('retained_canonical_events_verified')
    if type(event_count) is not int or event_count != summary.get('canonical_event_count'):
        raise ValueError('Canonical event count differs from the retained summary')
    common.check_inventory(root)
    if (root / common.INVENTORY).read_bytes() != inventory_before:
        raise ValueError('The evidence inventory changed during reproduction')
    return {
        **replay, 'round': 'round-08', 'record': RECORD,
        'verification_kind': 'receipt-guards-v1',
        'canonical_frozen_sha256': frozen_sha256,
        'inventory_sha256': common.sha(inventory_before),
        'public_inventory_files': len(actual),
        'unchanged_frozen_sources_verified': len(sources),
        'frozen_scripted_assignments': 64,
        'runs_replayed': 64, 'events_replayed': event_count,
        'mechanical_results_exact': 64,
        'preserved_scientific_record_files': 192,
        'transport_records_verified': 64,
        'analysis_records_verified': 64,
        'native_participants': 0,
        'authored_witness_checks': witnesses,
        'transport_unit_checks': transport_tests,
        'failure_retention_unit_checks': retention_tests,
        'all_public_files_unchanged_during_verification': True,
        'scope': 'Same-lab deterministic execution and integrity checks of two recovered public helper texts and authored edits on eight synthetic cases, plus separately counted 28 authored schedule-world checks, 10 transport unit checks and three mocked failure-retention unit checks. The schedules do not execute the response adapter. No new model participants, native incidence estimate, model-backend attestation or external replication.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--frozen-sha256', required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    archive = args.archive.resolve()
    if args.output is not None and args.output.resolve() == archive:
        raise ValueError('A verification receipt cannot overwrite its evidence archive')
    with tempfile.TemporaryDirectory(prefix='rin-receipt-guard-evidence-') as folder:
        temporary = Path(folder)
        root = common.extract(archive, temporary / 'extracted')
        result = verify(root, args.frozen_sha256, temporary / 'reproduction.json')
    result.update(public_archive=archive.name,
                  public_archive_sha256=common.sha(archive.read_bytes()),
                  public_archive_identical_to_canonical=True,
                  fresh_extraction=True, temporary_extraction_removed=True,
                  verified_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: result[key] for key in ('status', 'round', 'runs_replayed',
          'events_replayed', 'fresh_helper_replays', 'transport_records_verified',
          'native_participants')}, indent=2))


if __name__ == '__main__':
    main()
