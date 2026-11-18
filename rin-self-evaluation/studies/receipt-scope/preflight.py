#!/usr/bin/env python3
"""Check the prospective instrument against retained Round06 evidence before freeze."""
from __future__ import annotations
from collections import Counter
import copy
import datetime
import hashlib
import io
import json
from pathlib import Path
import unittest
import audit_reference
from engine import make_initial_state,report_bytes
from prepare import ROOT,RECORD,native_cases,planned_assignments,public_prompt,dispatch_message
from presentation import validate_transport
from verification import sha,verify_forensics


def checked_source_paths(root=ROOT):
    root=Path(root)
    paths=list(root.glob('*.py'))+[p for p in (root/'protocol').iterdir()
        if p.is_file() and p.name not in ('frozen.json','preflight.json')]
    paths += [p for p in (root/'analysis').iterdir() if p.is_file() and p.suffix in ('.py','.md')] if (root/'analysis').is_dir() else []
    # Forensics are already-completed retrospective evidence, bound for integrity.
    paths += [p for p in (root/'forensics').rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and not p.name.startswith('.')]
    if any(p.is_symlink() for p in paths):raise ValueError('Frozen source cannot be symlinked')
    return sorted(paths)


def run_input_paths(root,assignments):
    return sorted(root/'runs'/a['run_id']/name for a in assignments
                  for name in ('initial_state.json','state.json','prompt.txt','dispatch_message.txt','transport.json'))


def main():
    if (ROOT/'protocol/frozen.json').exists() or any((ROOT/'runs').glob('*/events.jsonl')) or any((ROOT/'runs').glob('*/presentation_events.jsonl')):
        raise SystemExit('Pre-run preparation is closed after freeze or native events')
    for name in ('PROTOCOL.md','COMMON_CONTRACT.md','CHECKLIST_REQUIREMENTS.md','SEMANTIC_REVIEW.md',
                 'design_review.md','source_audit.md','assignments.json','assignment_design.json','reference_audit.json'):
        assert (ROOT/'protocol'/name).is_file(),'Missing pre-run document: '+name
    prior=ROOT.parent/'two-job-study';lineage=json.loads((ROOT/'protocol/lineage.json').read_text())
    assert sha(prior/'protocol/frozen.json')==lineage['source_freeze_sha256']
    frozen=json.loads((prior/'protocol/frozen.json').read_text())
    for name,binding in lineage['copied_byte_identically'].items():
        source=binding['source']
        assert sha(ROOT/name)==sha(prior/source)==binding['sha256']==frozen['source_hashes'][source],name
    assert sha(ROOT/'protocol/engine_regression_cases.json')==sha(prior/'protocol/cases.json')==lineage['source_case_catalog_sha256']
    cases={c['case_id']:c for c in native_cases()}
    old_cases=json.loads((prior/'protocol/cases.json').read_text())['cases']
    source_case=next(c for c in old_cases if c['case_id']=='C11')
    assert source_case==lineage['source_C11']
    assert {k:v for k,v in cases['C11'].items() if k!='orientation'}==source_case
    for job,other in [('A','B'),('B','A')]:
        assert cases['C11R']['config']['jobs'][job]==source_case['config']['jobs'][other]
        assert cases['C11R']['actual_world'][job]==source_case['actual_world'][other]
    assert cases['C11R']['config']['priority']=='A' and source_case['config']['priority']=='B'
    assignments=json.loads((ROOT/'protocol/assignments.json').read_text())['assignments']
    plan=planned_assignments();assert len(assignments)==len(plan)==32
    assert {p.name for p in (ROOT/'runs').iterdir() if p.is_dir()}=={a['run_id'] for a in assignments}
    for actual,expected in zip(assignments,plan):assert all(actual[k]==v for k,v in expected.items())
    old_initial=prior/'runs/w041/initial_state.json'
    assert sha(old_initial)==frozen['source_hashes']['runs/w041/initial_state.json']
    source_initial=json.loads(old_initial.read_text())
    old_prompt=prior/'runs/w041/prompt.txt'
    assert sha(old_prompt)==frozen['source_hashes']['runs/w041/prompt.txt']
    normalized_prior=old_prompt.read_text().replace('w041','<RUN_ID>').replace('two-job-study','delivery-study')
    normalized_prompts=set();normalized_dispatches=set()
    for assignment in assignments:
        run=assignment['run_id'];directory=ROOT/'runs'/run;case=cases[assignment['case_id']]
        config=copy.deepcopy(case['config']);config['run_id']=run
        initial=json.loads((directory/'initial_state.json').read_text())
        assert initial==make_initial_state(config,case['actual_world'])
        assert (directory/'state.json').read_bytes()==(directory/'initial_state.json').read_bytes()
        if assignment['orientation']=='original':
            inherited=copy.deepcopy(source_initial);inherited['config']['run_id']=run
            assert initial==inherited,'Original state differs from Round06'
        transport=json.loads((directory/'transport.json').read_text())
        assert validate_transport(transport)==assignment['receipt_scope']
        assert sha(directory/'transport.json')==assignment['transport_sha256']
        prompt=(directory/'prompt.txt').read_text();dispatch=(directory/'dispatch_message.txt').read_text()
        assert prompt==public_prompt(run) and dispatch==dispatch_message(run)
        assert sha(directory/'prompt.txt')==assignment['prompt_sha256']
        assert sha(directory/'dispatch_message.txt')==assignment['dispatch_message_sha256']
        normalized_prompts.add(prompt.replace(run,'<RUN_ID>'))
        normalized_dispatches.add(dispatch.replace(run,'<RUN_ID>'))
    assert normalized_prompts=={normalized_prior} and len(normalized_dispatches)==1
    assert hashlib.sha256(normalized_prior.encode()).hexdigest()==lineage['normalized_round06_checklist_prompt_sha256']
    positions=Counter((r['requested_model'],r['receipt_scope'],r['within_block_position']) for r in assignments)
    oriented_positions=Counter((r['orientation'],r['requested_model'],r['receipt_scope'],r['within_block_position']) for r in assignments)
    assert len(positions)==16 and set(positions.values())=={2}
    assert len(oriented_positions)==32 and set(oriented_positions.values())=={1}
    stream=io.StringIO();suite=unittest.defaultTestLoader.discover(str(ROOT),pattern='test_*.py')
    tested=unittest.TextTestRunner(stream=stream,verbosity=1).run(suite)
    if not tested.wasSuccessful():raise AssertionError(stream.getvalue())
    audit=audit_reference.audit();assert audit==json.loads((ROOT/'protocol/reference_audit.json').read_text())
    forensic=verify_forensics(ROOT)
    result={'record':RECORD,'status':'PASS','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'contexts_planned':32,'underlying_task_families':1,'orientation_settings':2,
            'fresh_repeats_per_model_scope_orientation':4,'semantic_tests':tested.testsRun,
            'authored_witness_world_executions':audit['authored_witness_worlds_checked'],
            'zero_native_events':True,'inherited_sources_byte_identical':sorted(lineage['copied_byte_identically']),
            'original_initial_states_equal_to_round06_except_run_id':True,'reflection_verified':True,
            'normalized_public_prompt_variants':1,'normalized_dispatch_variants':1,
            'normalized_prompt_equal_to_round06_checklist':True,'receipt_only_projection_verified':True,
            'williams_position_balance_verified':True,'orientation_position_balance_verified':True,
            'retrospective_forensic_verification':forensic,
            'checked_run_input_hashes':{p.relative_to(ROOT).as_posix():sha(p) for p in run_input_paths(ROOT,assignments)},
            'checked_source_hashes':{p.relative_to(ROOT).as_posix():sha(p) for p in checked_source_paths()},
            'scope':'Pre-run instrument, source lineage, prompt, projection, assignment and review-gate checks. Forensic results were already executed retrospectively and are separately bound. No fresh native participant calls.'}
    (ROOT/'protocol/preflight.json').write_bytes(report_bytes(result))
    print(json.dumps({k:v for k,v in result.items() if k not in ('checked_source_hashes','checked_run_input_hashes')},indent=2))


if __name__=='__main__':main()
