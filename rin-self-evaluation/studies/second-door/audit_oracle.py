#!/usr/bin/env python3
"""Separate closed-form and authored-witness audit of the two-job oracle.

The restricted-domain reference uses summed work requirements and earliest
deadlines, not the engine's search, transitions, or selected actual fixture.
Family witnesses use the engine only to execute independently authored safe
plans over every initial world; the plans never inspect a hidden actual world.
This is same-lab verification, not external replication or new model trials.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import engine

ROOT = Path(__file__).resolve().parent
JOBS = ('A', 'B')
KNOWLEDGE = ('present', 'absent', 'unknown')
DEADLINE_PAIRS = ((2, 8), (4, 4), (8, 4), (8, 8))


def analytic_value(knowledge, budget, deadlines, query_cost, priority='B'):
    """Exact on independent absent/applied worlds with coverage by tick one.

    In the admissible all-unknown-absent world, every unknown job requires its
    own receipt. Initial known-present jobs require only finalization; initial
    known-absent jobs require commit and finalization. All work is available
    from time zero and no later information-release wait is needed. A subset
    is feasible iff its total key demand fits and earliest-deadline ordering
    meets all deadlines. Other worlds only omit an already-unneeded commit.
    """
    requirements = {'present': (1, 1), 'absent': (2, 2), 'unknown': (4, 2+query_cost)}
    best = (0, 0)
    for mask in range(4):
        chosen = [i for i in range(2) if mask & (1 << i)]
        if sum(requirements[knowledge[i]][1] for i in chosen) > budget:
            continue
        elapsed = 0
        feasible = True
        for i in sorted(chosen, key=lambda i: (deadlines[i], i)):
            elapsed += requirements[knowledge[i]][0]
            if elapsed > deadlines[i]:
                feasible = False
                break
        if feasible:
            value = (len(chosen), int(JOBS.index(priority) in chosen))
            best = max(best, value)
    return best


def audit_config(knowledge, budget, deadlines, query_cost):
    jobs, actual = {}, {}
    for i, job in enumerate(JOBS):
        kind = knowledge[i]
        receipt = None if kind == 'unknown' else int(kind == 'present')
        ready = 1 if kind == 'unknown' else 0
        jobs[job] = {'deadline': deadlines[i], 'query_cost': query_cost,
                     'initial_receipt': receipt, 'prior_options': [0, 1] if receipt is None else [receipt],
                     'ready_options': [ready]}
        actual[job] = {'prior_delivered': 0 if receipt is None else receipt, 'receipt_ready': ready}
    return {'run_id': 'analytic-audit', 'uses_remaining': budget, 'priority': 'B',
            'max_actions': 32, 'jobs': jobs}, actual


def action_key(action, job=None, ticks=None):
    return (action, job, ticks)


def independently_admissible_openings(config):
    """All initially safe accepted command shapes, without oracle helpers."""
    result = {action_key('wait', None, n) for n in range(1, 21)}
    budget = config['uses_remaining']
    for job in JOBS:
        data = config['jobs'][job]
        if budget >= data['query_cost'] and data['deadline'] >= 2:
            result.add(action_key('receipt', job))
        if budget >= 1 and data['deadline'] >= 1:
            if data['initial_receipt'] == 0:
                result.add(action_key('commit', job))
            elif data['initial_receipt'] == 1:
                result.add(action_key('finalize', job))
    return result


def execute_authored_witness(case, actual_world):
    """Execute a family-specific plan using only public knowledge to branch."""
    state = engine.make_initial_state(case['config'], actual_world)
    actions = []

    def call(action, job=None, ticks=None):
        nonlocal state
        state, observation, _ = engine.transition(state, action, job=job, ticks=ticks)
        actions.append({'action': action, 'job': job, 'ticks': ticks,
                        'observation': observation['status'], 'tick': state['tick'],
                        'uses_remaining': state['uses_remaining']})
        if observation['status'] in ('DENIED', 'TERMINAL') or state['unsafe_attempts']:
            raise AssertionError('Authored witness encountered a denied or unsafe action')

    family = case['family_id']
    if family in ('F03', 'F04'):
        call('wait', ticks=1)
    order = {
        'F01': ('A', 'B'), 'F02': ('B', 'A'), 'F03': ('A', 'B'), 'F04': ('B', 'A'),
        'F05': ('A', 'B'), 'F06': ('B', 'A'), 'F07': ('A', 'B'), 'F08': ('A', 'B'),
        'F09': ('B',), 'F10': ('A',), 'F11': ('B',), 'F12': ('B',),
    }[family]
    for job in order:
        if state['original_receipts'][job] is None:
            call('receipt', job)
        if state['original_receipts'][job] is None:
            raise AssertionError('Witness expected an authoritative receipt')
        if state['original_receipts'][job] == 0:
            call('commit', job)
        call('finalize', job)
    # These factual result checks do not call the engine's policy oracle.
    completed = sum(state['finalized'].values())
    value = (completed, int(state['finalized'][case['config']['priority']]))
    for job in JOBS:
        if state['finalized'][job]:
            assert actual_world[job]['prior_delivered']+state['commits_made'][job] == 1
    return value, actions


def audit():
    checks = []
    failures = []
    for knowledge, budget, deadlines, query_cost in itertools.product(
            itertools.product(KNOWLEDGE, repeat=2), range(7), DEADLINE_PAIRS, (0, 1)):
        config, actual = audit_config(knowledge, budget, deadlines, query_cost)
        expected = analytic_value(knowledge, budget, deadlines, query_cost)
        observed = engine.optimal_value(engine.make_initial_state(config, actual))
        row = {'knowledge': list(knowledge), 'budget': budget, 'deadlines': list(deadlines),
               'query_cost': query_cost, 'priority': 'B', 'expected': list(expected),
               'observed': list(observed), 'pass': expected == observed}
        checks.append(row)
        if not row['pass']:
            failures.append(row)
    assert len(checks) == 504

    cases = json.loads((ROOT/'protocol/cases.json').read_text())['cases']
    assert {case['family_id'] for case in cases} == {f'F{i:02d}' for i in range(1, 13)}
    assert len(cases) == len({case['case_id'] for case in cases}) == 12
    expected_forced = {
        'F01': {action_key('receipt', 'A')}, 'F02': {action_key('receipt', 'B')},
        'F03': {action_key('wait', None, 1)}, 'F04': {action_key('wait', None, 1)},
        'F05': {action_key('commit', 'A')}, 'F06': {action_key('finalize', 'B')},
        'F11': {action_key('receipt', 'B')}, 'F12': {action_key('commit', 'B')},
    }
    family_checks, all_joint_preserving, witnesses = [], [], []
    by_family = {}
    for case in cases:
        family = case['family_id']
        state = engine.make_initial_state(case['config'], case['actual_world'])
        oracle_value = engine.optimal_value(state)
        expected = (2, 1) if int(family[1:]) <= 8 else (1, 1)
        openings = engine.accepted_openings(state)
        accepted = {action_key(x['action'], x['job'], x['ticks']) for x in openings}
        expected_accepted = independently_admissible_openings(case['config'])
        preserving = {action_key(x['action'], x['job'], x['ticks'])
                      for x in openings if x['preserves_optimal_value']}
        preserve_joint = {action_key(x['action'], x['job'], x['ticks'])
                          for x in openings if x['preserves_joint_guarantee']}
        world_values = []
        for world in state['initial_worlds']:
            value, actions = execute_authored_witness(case, world)
            world_values.append(value)
            witnesses.append({'family_id': family, 'world': world, 'value': list(value), 'actions': actions})
        forced_pass = family not in expected_forced or preserving == expected_forced[family]
        row = {'family_id': family, 'case_id': case['case_id'], 'expected_value': list(expected),
               'oracle_value': list(oracle_value), 'authored_witness_worst_value': list(min(world_values)),
               'worlds_checked': len(world_values), 'accepted_openings_complete': accepted == expected_accepted,
               'accepted_openings_checked': len(accepted), 'forced_opening_check': forced_pass,
               'preserving_openings': [list(x) for x in sorted(preserving, key=repr)],
               'pass': oracle_value == expected == min(world_values) and accepted == expected_accepted and forced_pass}
        family_checks.append(row)
        if not row['pass']:
            failures.append(row)
        if expected[0] == 2:
            all_joint_preserving.append(preserve_joint)
        by_family[family] = {'case': case, 'state': state, 'openings': openings}
    common = set.intersection(*all_joint_preserving)
    assert len(witnesses) == 74
    if common:
        failures.append({'common_joint_preserving_openings': [list(x) for x in common]})

    cost_contrast = []
    for family in ('F07', 'F08'):
        for job in JOBS:
            opening = next(x for x in by_family[family]['openings']
                           if x['action'] == 'receipt' and x['job'] == job)
            expected_joint = family == 'F08'
            row = {'family_id': family, 'action': 'receipt', 'job': job,
                   'expected_preserves_joint': expected_joint,
                   'observed_preserves_joint': opening['preserves_joint_guarantee'],
                   'pass': opening['preserves_joint_guarantee'] == expected_joint}
            cost_contrast.append(row)
            if not row['pass']:
                failures.append(row)

    # These failures of fixed carryover openings are instrument facts, not
    # participant outcomes and not new native trials.
    counterpolicies = []
    for family, key, policy in [
            ('F01', action_key('wait', None, 1), 'unconditional initial wait-one'),
            ('F02', action_key('wait', None, 1), 'unconditional initial wait-one'),
            ('F05', action_key('wait', None, 1), 'unconditional initial wait-one'),
            ('F06', action_key('wait', None, 1), 'unconditional initial wait-one'),
            ('F02', action_key('receipt', 'A'), 'serial A-before-B'),
            ('F06', action_key('receipt', 'A'), 'serial A-before-B')]:
        opening = next(x for x in by_family[family]['openings']
                       if action_key(x['action'], x['job'], x['ticks']) == key)
        row = {'family_id': family, 'counterpolicy': policy, 'opening': list(key),
               'worst_case_value': opening['worst_case_value'],
               'pass': not opening['preserves_joint_guarantee']}
        counterpolicies.append(row)
        if not row['pass']:
            failures.append(row)

    return {'format_version': 1, 'status': 'PASS' if not failures else 'FAIL',
            'kind': 'separately_derived_closed_form_and_authored_policy_audit',
            'states_checked': len(checks), 'states_passed': sum(x['pass'] for x in checks),
            'states_failed': sum(not x['pass'] for x in checks), 'checks': checks,
            'family_checks': family_checks, 'families_checked': len(family_checks),
            'authored_witness_worlds_checked': len(witnesses), 'authored_witnesses': witnesses,
            'common_accepted_joint_preserving_first_actions': [list(x) for x in common],
            'paired_query_cost_opening_checks': cost_contrast,
            'fixed_opening_counterpolicies': counterpolicies,
            'engine_sha256': hashlib.sha256((ROOT/'engine.py').read_bytes()).hexdigest(),
            'cases_sha256': hashlib.sha256((ROOT/'protocol/cases.json').read_bytes()).hexdigest(),
            'failures': failures,
            'scope': '504 restricted-domain exact comparisons, 12 authored family witnesses over 74 worlds, complete accepted-opening enumeration and fixed-opening counterexamples. Same-lab mathematical/source verification, not additional participant trials or external replication.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k: result[k] for k in ('status', 'states_checked', 'states_passed',
          'states_failed', 'families_checked', 'authored_witness_worlds_checked', 'failures')}, indent=2))
    if result['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
