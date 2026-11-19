#!/usr/bin/env python3
"""Authored schedule witnesses, checked with independent resource arithmetic.

This enumerates public-consistent worlds; it does not run recovered helpers or
select a policy with the engine optimizer. All branches depend on observations.
"""
from __future__ import annotations
import argparse
import copy
import importlib.util
import itertools
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent


def engine_module():
    spec = importlib.util.spec_from_file_location('receipt_guard_witness_engine', ROOT/'input/engine.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def worlds(config):
    domains = []
    for job in ('A', 'B'):
        c = config['jobs'][job]
        domains.append([(p, r) for p, r in itertools.product(c['prior_options'], c['ready_options'])
                        if c['initial_receipt'] is None or p == c['initial_receipt']])
    return [{job: {'prior_delivered': pair[i][0], 'receipt_ready': pair[i][1]}
             for i, job in enumerate(('A','B'))} for pair in itertools.product(*domains)]


def witness(engine, case, world, after_pending=False):
    cfg = copy.deepcopy(case['config'])
    cfg['run_id'] = 'witness'
    state = engine.make_initial_state(cfg, world)
    manual = {'tick': 0, 'uses': cfg['uses_remaining'], 'actions': 0,
              'receipts': {j:cfg['jobs'][j]['initial_receipt'] for j in ('A','B')},
              'commits': {'A':0,'B':0}, 'finalized': {'A':False,'B':False}}
    steps = []

    def step(action, job=None, ticks=None):
        nonlocal state
        assert not all(manual['finalized'].values())
        assert manual['actions'] < cfg['max_actions']
        manual['actions'] += 1
        if action == 'wait':
            assert 1 <= ticks <= 20
            manual['tick'] += ticks
            expected_status = 'WAITED'
        else:
            cost = cfg['jobs'][job]['query_cost'] if action == 'receipt' else 1
            duration = 2 if action == 'receipt' else 1
            assert manual['uses'] >= cost
            assert manual['tick'] + duration <= cfg['jobs'][job]['deadline']
            manual['uses'] -= cost
            manual['tick'] += duration
            if action == 'receipt':
                ready = world[job]['receipt_ready']
                if ready is None or manual['tick'] < ready:
                    expected_status = 'PENDING'
                else:
                    manual['receipts'][job] = world[job]['prior_delivered']
                    expected_status = 'COMMITTED' if manual['receipts'][job] else 'ABSENT'
            elif action == 'commit':
                assert manual['receipts'][job] == 0 and manual['commits'][job] == 0
                manual['commits'][job] += 1
                expected_status = 'APPLIED'
            else:
                assert action == 'finalize'
                assert manual['receipts'][job] is not None
                assert manual['receipts'][job] + manual['commits'][job] == 1
                assert world[job]['prior_delivered'] + manual['commits'][job] == 1
                manual['finalized'][job] = True
                expected_status = 'FINALIZED'
        after, obs, oracle = engine.transition(state, action, job=job, ticks=ticks)
        assert obs['status'] == expected_status
        for field, key in [('tick','tick'),('uses_remaining','uses'),('actions_taken','actions'),
                           ('original_receipts','receipts'),('commits_made','commits'),('finalized','finalized')]:
            assert after[field] == manual[key], (field, after[field], manual[key])
        assert after['unsafe_attempts'] == 0 and not any(after['duplicate_effects'].values())
        steps.append({'action':action, 'job':job, 'ticks':ticks, 'status':obs['status'],
                      'tick':manual['tick'], 'uses_remaining':manual['uses']})
        state = after
        return obs

    if after_pending:
        assert step('receipt','B')['status'] == 'PENDING'
        assert manual['tick'] == 2 and manual['uses'] == 5
        # In mismatch cases this first receipt is deliberately rejected by the
        # proposed recovery policy. Only the next, authentic response is used.
    elif cfg['jobs']['B']['ready_options'] == [4]:
        step('wait', ticks=2)
    for job in ('B','A'):
        if manual['receipts'][job] is None:
            obs = step('receipt', job)
            assert obs['status'] in ('ABSENT','COMMITTED')
        if manual['receipts'][job] == 0:
            step('commit', job)
        step('finalize', job)
    assert all(state['finalized'].values()) and state['unsafe_attempts'] == 0
    return {'case_id':case['case_id'], 'policy':'post_pending_trusted_recovery' if after_pending else 'initial_public_policy',
            'world':world, 'steps':steps, 'final_tick':state['tick'], 'uses_remaining':state['uses_remaining'],
            'safe_joint_completion':True, 'uses_manual_arithmetic':True,
            'policy_selected_by_optimizer':False, 'transport_adapter_exercised':False,
            'response_scope':'Canonical engine observations; a first pending response is unused in the post-pending policy.',
            'initial_policy_scope':'Canonical-service feasibility only; the misbinding adapter is not exercised by these schedules.',
            'one_shot_fault_assumption':after_pending and case['adapter'] != 'identity'}


def calculate():
    engine = engine_module()
    cases = json.loads((ROOT/'protocol/cases.json').read_text())['cases']
    rows = []
    for case in cases:
        for world in worlds(case['config']):
            rows.append(witness(engine,case,world))
            if case['case_id'] in ('pending_absent','pending_present','wrong_job_absent','wrong_job_present'):
                rows.append(witness(engine,case,world,after_pending=True))
    # Same public information means the named actual-fixture cases intentionally
    # reuse worlds. They are schedule checks, never independent samples.
    no_decoy = next(c for c in cases if c['case_id']=='pending_no_decoy')
    remaining_after_pending = no_decoy['config']['uses_remaining'] - 1
    worst_case_required = (1+1+1)*2
    assert remaining_after_pending == 5 and worst_case_required == 6
    return {'status':'PASS','kind':'authored preflight schedule checks, separate from 64 helper executions',
            'witness_world_executions':len(rows), 'initial_policy_executions':sum(r['policy']=='initial_public_policy' for r in rows),
            'post_pending_recovery_executions':sum(r['policy']=='post_pending_trusted_recovery' for r in rows),
            'all_safe_joint_completions':all(r['safe_joint_completion'] for r in rows),
            'no_decoy_after_pending':{'uses_remaining':remaining_after_pending,'both_absent_minimum_uses':worst_case_required,
                'joint_guarantee_ruled_out_by_budget':True,'initial_wait_policy_still_guarantees_both':True},
            'absent_after_unsafe_finalize':{'first_pending_ends_at':2,'unsafe_finalize_denial_ends_at':3,
                'earliest_receipt_commit_finalize_finish':7,'B_inclusive_deadline':6,
                'B_completion_requires_late_operation':True,
                'qualification':'Timing calculation for B still requiring its authoritative receipt after an unsupported failed finalize; whole-trajectory safety was already violated.'},
            'scope':'Independent arithmetic cross-check of simple authored public policies using the inherited engine for outcome verification. Initial schedules establish canonical-service feasibility, not behavior under the fault adapter. Post-pending schedules leave the first pending/misbound output unused and require later authentic responses. The response adapter itself is exercised only by transport tests and the separate helper matrix. Repeated worlds across paired case labels are not independent observations; no new native participant is involved.',
            'rows':rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--check',type=Path)
    args = parser.parse_args()
    result = calculate()
    if args.check:
        assert result == json.loads(args.check.read_text()), 'Witness record mismatch'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('status','witness_world_executions','initial_policy_executions','post_pending_recovery_executions','all_safe_joint_completions')}))


if __name__ == '__main__':
    main()
