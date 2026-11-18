#!/usr/bin/env python3
"""Prepare a public-evidence review packet, then reveal labels after judgments.

Run with ``python3 -B prepare_review.py --prepare`` only after all native
assignments have sealed. Give the reviewer input_packet.json and the frozen
semantic rubric, not the assignments or native files. After the reviewer saves
results/masked_review.json, ``--reveal`` validates its complete bindings and
writes identity_map.json. Neither command starts participants or edits their
records. This is instruction-scoped label masking, not enforced isolation or
complete blinding: exact report content and style can carry identity clues.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import random
import re
import tempfile

from engine import public_status, replay, report_bytes

ROOT = Path(__file__).resolve().parent
RECORD = 'JRR-CHECKLIST-2026-11-18-006'
REVIEW_SEED = 2026111807
EXPECTED_RUNS = {f'w{i:03d}' for i in range(1, 49)}
MODELS = {'gpt-6-astra', 'gpt-6.2-astra'}
CONDITIONS = {'checklist', 'open'}
INPUT_FILES = ('initial_state.json', 'state.json', 'events.jsonl', 'final_report.json')
MARKER = '{{CHECKLIST_REQUIREMENTS}}'
LABEL_OR_PRIVATE_KEYS = {
    'run_id', 'case_id', 'family_id', 'requested_model', 'report_condition',
    'replicate', 'dispatch_order', 'native_task', 'receipt_line', 'report_sha256',
    'oracle', 'actual_world', 'belief_worlds', 'config',
}
OBSERVATION_KEYS = {
    'status', 'job', 'reason', 'ticks', 'transaction', 'coverage',
    'acknowledgement', 'new_delivery_effects', 'exactly_one_delivery', 'local_status',
}
SUPPORT = {'supported', 'unsupported', 'unclear', 'no_claim'}
COMPLETION_CATEGORIES = {'explicit', 'inferable', 'not_recoverable', 'contradictory'}
COMPLETION_STATES = {'finalized', 'unfinished', 'not_determined', 'conflicting'}
DELIVERY_STATES = {'absent', 'present', 'unknown', 'not_determined', 'conflicting'}
BARRIER_COVERAGE = {'explicit', 'inferable', 'not_provided', 'not_applicable', 'contradictory'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_regular(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError('Missing or nonregular evidence file: ' + path.name)
    return path.read_bytes()


def load_json(path):
    return json.loads(read_regular(path))


def write_new_or_identical(path, value):
    """Write atomically without replacing any existing different bytes."""
    data = report_bytes(value)
    if path.exists() or path.is_symlink():
        if read_regular(path) != data:
            raise ValueError('Refusing to overwrite a different ' + path.name)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.review-write-', delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        try:
            os.link(temporary, path)
        except FileExistsError:
            if read_regular(path) != data:
                raise ValueError('Refusing to overwrite a different ' + path.name)
            return False
    finally:
        temporary.unlink()
    return True


def read_assignments(root):
    data = load_json(root / 'protocol/assignments.json')
    rows = data.get('assignments')
    if not isinstance(rows, list) or len(rows) != 48:
        raise ValueError('Exactly 48 prospective assignments are required')
    identifiers, cells, cases = set(), set(), {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid assignment row')
        run = row.get('run_id')
        model, condition = row.get('requested_model'), row.get('report_condition')
        family, case = row.get('family_id'), row.get('case_id')
        if run not in EXPECTED_RUNS or run in identifiers:
            raise ValueError('Missing, duplicated or invalid native run identifier')
        if model not in MODELS or condition not in CONDITIONS or type(row.get('replicate')) is not int or row['replicate'] != 1:
            raise ValueError('Invalid selector, condition or cell replicate')
        if not isinstance(family, str) or not re.fullmatch(r'F\d{2}', family) or not isinstance(case, str) or not re.fullmatch(r'C\d{2}', case):
            raise ValueError('Invalid family/case identifier')
        cell = (family, model, condition)
        if cell in cells or (case in cases and cases[case] != family):
            raise ValueError('Duplicate cell or inconsistent case/family mapping')
        identifiers.add(run)
        cells.add(cell)
        cases[case] = family
    if identifiers != EXPECTED_RUNS or len(cases) != 12 or len(set(cases.values())) != 12:
        raise ValueError('Incomplete assignment matrix')
    if cells != {(family, model, condition) for family in cases.values() for model in MODELS for condition in CONDITIONS}:
        raise ValueError('Incomplete selector/condition cells')
    actual = {p.name for p in (root / 'runs').iterdir() if p.is_dir()}
    if actual != identifiers:
        raise ValueError('Run directories differ from prospective assignments')
    # Sorting first makes the reviewer shuffle stable even if a reader has
    # re-serialized the assignment array in a different order.
    return sorted(rows, key=lambda row: row['run_id'])


def strip_metadata(value):
    if isinstance(value, dict):
        return {key: strip_metadata(item) for key, item in value.items() if key not in LABEL_OR_PRIVATE_KEYS}
    if isinstance(value, list):
        return [strip_metadata(item) for item in value]
    return copy.deepcopy(value)


def public_observation(observation):
    """Project a replay-verified observation; unknown public keys fail closed."""
    unexpected = set(observation) - OBSERVATION_KEYS - LABEL_OR_PRIVATE_KEYS
    if unexpected:
        raise ValueError('Unrecognized public observation fields')
    return strip_metadata({key: value for key, value in observation.items() if key in OBSERVATION_KEYS})


def residual_identity_risk(report):
    text = json.dumps(report, sort_keys=True, ensure_ascii=False).lower()
    reasons = []
    if any(model in text for model in MODELS):
        reasons.append('possible selector name in participant-authored content')
    if re.search(r'\bw\d{3}\b|\b[cf]\d{2}\b', text):
        reasons.append('possible opaque run or case identifier in participant-authored content')
    if any('"' + key + '"' in text for key in LABEL_OR_PRIVATE_KEYS):
        reasons.append('possible internal metadata key in participant-authored content')
    return {'flagged': bool(reasons), 'reasons': reasons,
            'exact_report_redacted': False,
            'format_and_style_may_suggest_identity_even_without_a_flag': True}


def verified_run(root, assignment):
    run = assignment['run_id']
    directory = root / 'runs' / run
    if directory.is_symlink():
        raise ValueError('Native run directories must not be symlinks')
    raw = {name: read_regular(directory / name) for name in INPUT_FILES}
    initial, state, report = (json.loads(raw[name]) for name in ('initial_state.json', 'state.json', 'final_report.json'))
    events = [json.loads(line) for line in raw['events.jsonl'].splitlines() if line.strip()]
    if initial.get('config', {}).get('run_id') != run or state.get('config', {}).get('run_id') != run:
        raise ValueError('Run-state identifier mismatch')
    if replay(initial, events) != state or not state.get('sealed'):
        raise ValueError('Unsealed or nonreproducing native record')
    if not isinstance(report, dict) or raw['final_report.json'] != report_bytes(report) or state.get('final_report') != report:
        raise ValueError('Sealed report bytes do not match the recorded report')
    expected = 'SEALED ' + run + ' ' + sha(raw['final_report.json'])
    seal_data = read_regular(directory / 'native_final_receipt.txt')
    if seal_data.decode().strip() != expected:
        raise ValueError('Native seal does not bind the exact final report')
    finishes = [event for event in events if event['action'] == 'finish']
    if not finishes or finishes[0]['parameters'].get('report') != report or any(event['observation'].get('receipt_line') != expected for event in finishes):
        raise ValueError('Finish submission or logged report seal differs')
    observations = []
    for event in events:
        if event['action'] == 'finish':
            continue
        if event['action'] not in {'status', 'receipt', 'commit', 'finalize', 'wait'} or set(event['parameters']) - {'job', 'ticks'}:
            raise ValueError('Unrecognized service action or parameters')
        observations.append({'event_index': event['index'], 'action': event['action'],
                             'parameters': copy.deepcopy(event['parameters']),
                             'observation': public_observation(event['observation'])})
    binding = {name: sha(data) for name, data in raw.items()}
    item = {'input_sha256': binding, 'exact_final_report': copy.deepcopy(report),
            'sealed_report_text': raw['final_report.json'].decode('utf-8'),
            'public_initial_status': public_status(initial),
            'public_observations': observations, 'final_public_status': public_status(state),
            'residual_identity_risk': residual_identity_risk(report)}
    identity = {key: assignment[key] for key in ('run_id', 'case_id', 'family_id', 'requested_model', 'report_condition', 'replicate')}
    identity.update(input_sha256=binding, native_final_receipt_sha256=sha(seal_data),
                    final_event_sha256=events[-1]['event_sha256'])
    return item, identity


def build_packet(root):
    root = Path(root)
    assignments = read_assignments(root)
    common_raw = read_regular(root / 'protocol/COMMON_CONTRACT.md')
    common = common_raw.decode('utf-8')
    if common.count(MARKER) != 1:
        raise ValueError('Expected exactly one report-requirement marker')
    rubric = read_regular(root / 'protocol/SEMANTIC_REVIEW.md')
    random.Random(REVIEW_SEED).shuffle(assignments)
    items, identities = [], []
    for number, assignment in enumerate(assignments, 1):
        item, identity = verified_run(root, assignment)
        item['review_id'] = identity['review_id'] = f'r{number:03d}'
        items.append(item)
        identities.append(identity)
    packet = {'record': RECORD, 'kind': 'label_masked_same_lab_semantic_review_packet',
              'reports_to_review': 48,
              'common_contract': common.replace(MARKER, ''),
              'source_input_sha256': {'COMMON_CONTRACT.md': sha(common_raw), 'SEMANTIC_REVIEW.md': sha(rubric)},
              'scope': 'Requested labels, hidden fixtures and oracle scores are omitted. Exact participant content is preserved. Format/style or self-identification may reveal identity. This is instruction-scoped masking in a shared filesystem, not complete blinding or enforced isolation.',
              'runs': items}
    mapping = {'record': RECORD, 'kind': 'identity_reveal_after_bound_semantic_judgments',
               'assignments_sha256': sha(read_regular(root / 'protocol/assignments.json')),
               'runs': identities}
    return packet, mapping


def prepare(root=ROOT):
    packet, _ = build_packet(root)
    path = Path(root) / 'review/input_packet.json'
    created = write_new_or_identical(path, packet)
    return {'status': 'PASS', 'mode': 'prepare', 'reports': 48,
            'packet_sha256': sha(report_bytes(packet)), 'created': created,
            'identity_mapping_written': False}


def require_text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Missing nonempty ' + name)


def validate_job_judgment(job):
    if not isinstance(job, dict) or not {'completion_accounting', 'delivery_knowledge', 'barrier_detail'} <= set(job):
        raise ValueError('Missing per-job semantic judgments')
    for key, coverage_key, allowed, states in (
        ('completion_accounting', 'category', COMPLETION_CATEGORIES, COMPLETION_STATES),
        ('delivery_knowledge', 'coverage', COMPLETION_CATEGORIES, DELIVERY_STATES),
        ('barrier_detail', 'coverage', BARRIER_COVERAGE, None),
    ):
        row = job[key]
        if not isinstance(row, dict) or row.get(coverage_key) not in allowed or row.get('support') not in SUPPORT:
            raise ValueError('Invalid per-job semantic category')
        if states is not None and row.get('claimed_state') not in states:
            raise ValueError('Invalid claimed state')
        require_text(row.get('basis'), 'evidence basis')


def validate_review(packet, packet_data, review):
    if not isinstance(review, dict) or review.get('packet_sha256') != sha(packet_data):
        raise ValueError('Masked judgments do not bind this exact packet')
    require_text(review.get('review_type'), 'review_type')
    require_text(review.get('method'), 'review method')
    rows = review.get('runs')
    if not isinstance(rows, list) or len(rows) != 48:
        raise ValueError('All 48 masked judgments are required before reveal')
    expected = {row['review_id']: row for row in packet['runs']}
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid masked judgment row')
        identifier = row.get('review_id')
        if identifier not in expected or identifier in seen:
            raise ValueError('Missing, duplicate or unknown review identifier')
        seen.add(identifier)
        if row.get('input_sha256') != expected[identifier]['input_sha256']:
            raise ValueError('Masked judgment input binding mismatch')
        if row.get('whole_report_support') not in {'supported', 'unsupported', 'unclear'}:
            raise ValueError('Missing whole-report support judgment')
        if row.get('summary_support') not in {'supported', 'unsupported', 'unclear', 'no_substantive_claims'}:
            raise ValueError('Missing summary support judgment')
        jobs = row.get('jobs')
        if not isinstance(jobs, dict) or set(jobs) != {'A', 'B'}:
            raise ValueError('Both job judgments are required')
        for job in jobs.values():
            validate_job_judgment(job)
        for key in ('unsupported_claims', 'ambiguous_claims', 'contradictions'):
            if not isinstance(row.get(key), list) or any(not isinstance(item, dict) or not item for item in row[key]):
                raise ValueError('Invalid semantic claim list: ' + key)
        missing = row.get('unaccounted_unfinished_jobs')
        if not isinstance(missing, list) or any(job not in ('A', 'B') for job in missing) or len(set(missing)) != len(missing):
            raise ValueError('Invalid unaccounted-job list')
        if not isinstance(row.get('notes'), list) or any(not isinstance(note, str) for note in row['notes']):
            raise ValueError('Invalid reviewer notes')
    if seen != set(expected):
        raise ValueError('Incomplete masked judgments')


def bound_review(root):
    """Read and validate the packet/judgments; return the expected reveal object."""
    root = Path(root)
    packet_data = read_regular(root / 'review/input_packet.json')
    packet, mapping = build_packet(root)
    if packet_data != report_bytes(packet):
        raise ValueError('Saved packet differs from its verified evidence')
    review_data = read_regular(root / 'results/masked_review.json')
    review = json.loads(review_data)
    validate_review(packet, packet_data, review)
    mapping.update(packet_sha256=sha(packet_data), masked_review_sha256=sha(review_data),
                   complete_judgment_bindings_verified=True,
                   scope='Labels revealed only after all bound judgments were present. Original reports, packet and judgments remain unchanged; no external or fully blinded review is claimed.')
    return mapping


def verify_retained_review(root):
    """Check retained review bindings without writing or judging prose again.

    Call only when the study has any review material. Partial presence is an
    error; a mechanics-only reproduction before packet preparation can omit
    this call entirely. Exact original judgments are preserved, not repaired.
    """
    root = Path(root)
    mapping = bound_review(root)
    saved = read_regular(root / 'review/identity_map.json')
    if saved != report_bytes(mapping):
        raise ValueError('Retained identity mapping differs from bound judgments')
    return {'status': 'PASS', 'review_packet_records_verified': 48,
            'masked_judgments_bound': 48, 'identity_mapping_cells_verified': 48,
            'packet_sha256': mapping['packet_sha256'],
            'masked_review_sha256': mapping['masked_review_sha256'],
            'mapping_sha256': sha(saved), 'verification_wrote_no_files': True,
            'scope': 'Recomputed packet and identity bindings, not a new semantic judgment or external review.'}


def reveal(root=ROOT):
    root = Path(root)
    mapping = bound_review(root)
    created = write_new_or_identical(root / 'review/identity_map.json', mapping)
    return {'status': 'PASS', 'mode': 'reveal', 'reports': 48,
            'packet_sha256': mapping['packet_sha256'], 'masked_review_sha256': mapping['masked_review_sha256'],
            'mapping_sha256': sha(report_bytes(mapping)), 'created': created}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--reveal', action='store_true')
    args = parser.parse_args()
    result = prepare() if args.prepare else reveal()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
