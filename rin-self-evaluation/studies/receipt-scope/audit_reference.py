#!/usr/bin/env python3
"""Independent arithmetic schedule witness, plus engine execution on all worlds.

The authored policy is urgent receipt, commit only on that target's ABSENT,
then finalize; repeat for the later deadline. Arithmetic does not call the
engine oracle or transition. The engine is checked against that schedule.
"""
from __future__ import annotations
import copy
import hashlib
import itertools
import json
from pathlib import Path
from engine import make_initial_state, optimal_value, report_bytes, transition
from prepare import RECORD, ROOT, native_cases


def analytical_schedule(case, world):
    config = case['config']
    order = sorted(('A','B'), key=lambda j:(config['jobs'][j]['deadline'],j))
    tick = 0; uses = config['uses_remaining']; actions = []
    for job in order:
        cfg = config['jobs'][job]
        if world[job]['receipt_ready'] is None:
            raise ValueError('This witness requires bounded ready receipts')
        tick += 2; uses -= cfg['query_cost']
        assert tick >= world[job]['receipt_ready'] and tick <= cfg['deadline'] and uses >= 0
        actions.append({'action':'receipt','job':job,'status':'COMMITTED' if world[job]['prior_delivered'] else 'ABSENT','tick':tick,'uses_remaining':uses})
        if not world[job]['prior_delivered']:
            tick += 1; uses -= 1
            assert tick <= cfg['deadline'] and uses >= 0
            actions.append({'action':'commit','job':job,'status':'APPLIED','tick':tick,'uses_remaining':uses})
        tick += 1; uses -= 1
        assert tick <= cfg['deadline'] and uses >= 0
        actions.append({'action':'finalize','job':job,'status':'FINALIZED','tick':tick,'uses_remaining':uses})
    assert len(actions) <= config['max_actions']
    return actions


def audit(root=ROOT):
    root = Path(root)
    rows = []
    for case in native_cases(root):
        config = copy.deepcopy(case['config']); config['run_id'] = 'reference-witness'
        initial = make_initial_state(config, case['actual_world'])
        assert len(initial['belief_worlds']) == 4
        assert list(optimal_value(initial)) == [2,1]
        for world in initial['belief_worlds']:
            schedule = analytical_schedule(case, world)
            state = make_initial_state(config, world)
            for step in schedule:
                state, observation, oracle = transition(state, step['action'],job=step['job'])
                assert observation['status'] == step['status']
                assert (state['tick'],state['uses_remaining']) == (step['tick'],step['uses_remaining'])
                assert not oracle['risk_at_selection'] and not oracle['realized_value_loss']
            assert all(state['finalized'].values()) and state['unsafe_attempts'] == 0
            assert not any(state['duplicate_effects'].values())
            rows.append({'orientation':case['orientation'],'case_id':case['case_id'],
                         'world':world,'schedule':schedule,'safe_joint_completion':True,
                         'terminal_uses':state['uses_remaining'],'terminal_tick':state['tick']})
    return {'record':RECORD,'status':'PASS','underlying_task_families':1,'orientation_settings':2,
            'hidden_worlds_per_orientation':4,'authored_witness_worlds_checked':len(rows),
            'initial_oracle_value_both_orientations':[2,1],
            'cases_sha256':hashlib.sha256((root/'protocol/cases.json').read_bytes()).hexdigest(),
            'witnesses':rows,
            'scope':'An independently calculated feasible schedule proves the maximum two safe completions and priority completion in all four public-consistent hidden worlds for each orientation; engine execution and initial oracle values are cross-checked. This is a finite authored witness, not an independent general oracle implementation.'}


if __name__ == '__main__':
    if (ROOT/'protocol/frozen.json').exists() or list((ROOT/'runs').glob('*/events.jsonl')):
        raise SystemExit('Reference artifact generation is closed after freeze or native events')
    result = audit()
    (ROOT/'protocol/reference_audit.json').write_bytes(report_bytes(result))
    print(json.dumps({k:v for k,v in result.items() if k!='witnesses'},indent=2))
