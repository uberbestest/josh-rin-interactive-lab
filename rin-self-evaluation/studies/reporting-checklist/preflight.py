#!/usr/bin/env python3
"""Run the prospective checks before freezing or dispatching native contexts.

This preparation-stage check compares the prior study directly. The published
reproducer instead uses the bound hashes and retained case-array digest, so the
standalone evidence archive does not depend on the earlier directory.
"""
from __future__ import annotations

from collections import Counter
import contextlib
import copy
import datetime
import hashlib
import io
import json
from pathlib import Path
import unittest

import audit_oracle
from engine import make_initial_state, report_bytes
from prepare import CONDITIONS, MODELS, ROOT, design_cases, dispatch_message, planned_assignments, public_prompt

RECORD = 'JRR-CHECKLIST-2026-11-18-006'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_source_paths(root=ROOT):
    return sorted(list(root.glob('*.py')) + [path for path in (root/'protocol').iterdir()
                                          if path.is_file() and path.name not in ('frozen.json', 'preflight.json')])


def main():
    if (ROOT/'protocol/frozen.json').exists() or list((ROOT/'runs').glob('*/events.jsonl')):
        raise SystemExit('Pre-run preparation is closed after freeze or native events')
    required = ['PROTOCOL.md', 'COMMON_CONTRACT.md', 'CHECKLIST_REQUIREMENTS.md',
                'SEMANTIC_REVIEW.md', 'design_review.md', 'assignments.json', 'assignment_design.json']
    for name in required:
        assert (ROOT/'protocol'/name).is_file(), 'Missing pre-run document: ' + name
    for name in ['prepare_review.py', 'test_review_packet.py']:
        assert (ROOT/name).is_file(), 'Missing prospective review source: ' + name
    prior = ROOT.parent/'second-door-study'
    lineage = json.loads((ROOT/'protocol/lineage.json').read_text())
    assert sha(prior/'protocol/frozen.json') == lineage['source_freeze_sha256']
    old_frozen = json.loads((prior/'protocol/frozen.json').read_text())
    for name, record in lineage['copied_byte_identically'].items():
        assert sha(ROOT/name) == sha(prior/name) == record['sha256'] == old_frozen['source_hashes'][name], name
    catalog = json.loads((ROOT/'protocol/cases.json').read_text())
    old_catalog = json.loads((prior/'protocol/cases.json').read_text())
    assert catalog['cases'] == old_catalog['cases'], 'The inherited cases changed'
    assert sha(prior/'protocol/cases.json') == catalog['source_case_catalog_sha256']
    assert catalog['source_case_catalog_sha256'] == old_frozen['source_hashes']['protocol/cases.json']
    assert hashlib.sha256(report_bytes(catalog['cases'])).hexdigest() == catalog['case_array_sha256']
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT), pattern='test_*.py')
    tested = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    if not tested.wasSuccessful():
        raise AssertionError(stream.getvalue())
    with contextlib.redirect_stdout(io.StringIO()):
        audit = audit_oracle.audit()
    assert audit['status'] == 'PASS'
    assert audit == json.loads((ROOT/'protocol/oracle_audit.json').read_text())
    old_audit = json.loads((prior/'protocol/oracle_audit.json').read_text())
    assert sha(prior/'protocol/oracle_audit.json') == old_frozen['source_hashes']['protocol/oracle_audit.json']
    assert {key: value for key, value in audit.items() if key != 'cases_sha256'} == {key: value for key, value in old_audit.items() if key != 'cases_sha256'}
    assignments = json.loads((ROOT/'protocol/assignments.json').read_text())['assignments']
    plan = planned_assignments()
    assert len(assignments) == len(plan) == 48
    for actual, expected in zip(assignments, plan):
        assert all(actual[key] == value for key, value in expected.items())
    cases = {case['case_id']: case for case in catalog['cases']}
    old_assignments = json.loads((prior/'protocol/assignments.json').read_text())['assignments']
    old_first = {case: next(row['run_id'] for row in old_assignments if row['case_id'] == case) for case in cases}
    normalized_prompts = set(); normalized_dispatches = set()
    for assignment in assignments:
        run = assignment['run_id']; case = cases[assignment['case_id']]
        directory = ROOT/'runs'/run
        initial = json.loads((directory/'initial_state.json').read_text())
        config = copy.deepcopy(case['config']); config['run_id'] = run
        assert initial == make_initial_state(config, case['actual_world']), run
        assert (directory/'state.json').read_bytes() == (directory/'initial_state.json').read_bytes(), run
        inherited_name = 'runs/' + old_first[case['case_id']] + '/initial_state.json'
        assert sha(prior/inherited_name) == old_frozen['source_hashes'][inherited_name]
        inherited = json.loads((prior/inherited_name).read_text())
        inherited['config']['run_id'] = run
        assert initial == inherited, 'Initial state differs from Round05: ' + run
        prompt = (directory/'prompt.txt').read_text()
        dispatch = (directory/'dispatch_message.txt').read_text()
        assert prompt == public_prompt(run, assignment['report_condition']), run
        assert dispatch == dispatch_message(run), run
        assert hashlib.sha256(prompt.encode()).hexdigest() == assignment['prompt_sha256']
        assert hashlib.sha256(dispatch.encode()).hexdigest() == assignment['dispatch_message_sha256']
        normalized_prompts.add(prompt.replace(run, '<RUN_ID>'))
        normalized_dispatches.add(dispatch.replace(run, '<RUN_ID>'))
    assert len(normalized_prompts) == 2 and len(normalized_dispatches) == 1
    difference = json.loads((ROOT/'protocol/prompt_diff.json').read_text())
    for condition in CONDITIONS:
        assert hashlib.sha256(public_prompt('<RUN_ID>', condition).encode()).hexdigest() == difference[condition + '_prompt_sha256']
    assert not list((ROOT/'runs').glob('*/events.jsonl'))
    positions = Counter((row['requested_model'], row['report_condition'], row['within_family_position']) for row in assignments)
    assert len(positions) == 16 and set(positions.values()) == {3}
    result = {'record': RECORD, 'status': 'PASS',
              'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'contexts_planned': 48, 'families': 12, 'contexts_per_family_model_condition': 1,
              'semantic_tests': tested.testsRun, 'oracle_states': audit['states_checked'],
              'authored_policy_world_executions': audit['authored_witness_worlds_checked'],
              'oracle_status': audit['status'], 'zero_native_events': True,
              'initial_states_equal_to_round05_except_run_id': True,
              'case_array_semantically_equal_to_round05': True,
              'case_array_sha256': catalog['case_array_sha256'],
              'inherited_sources_byte_identical': sorted(lineage['copied_byte_identically']),
              'reference_audit_equal_except_catalog_metadata_hash': True,
              'condition_effect_only_public_reporting_requirement': True,
              'latest_contract_in_all_prompts': True,
              'normalized_public_prompt_variants': 2, 'normalized_dispatch_variants': 1,
              'williams_position_balance_verified': True,
              'checked_source_hashes': {path.relative_to(ROOT).as_posix(): sha(path) for path in checked_source_paths()},
              'scope': 'Pre-run same-lab instrument, manipulation, lineage and assignment checks. No participant model calls.'}
    (ROOT/'protocol/preflight.json').write_bytes(report_bytes(result))
    print(json.dumps({key: value for key, value in result.items() if key != 'checked_source_hashes'}, indent=2))


if __name__ == '__main__':
    main()
