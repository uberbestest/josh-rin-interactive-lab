#!/usr/bin/env python3
"""The Test That Watched Back: exact finite, offline detector calibration.

Standard library only. All policies are authored except the deliberately tiny
empirical badge lookup learner. No model calls, network, or persistent memory.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from collections import defaultdict
from dataclasses import dataclass, asdict, replace
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Iterable

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('task_bit', 'badge', 'audit', 'bonus', 'penalty', 'continuation')
POLICY_NAMES = ('stable_rule', 'badge_learner', 'myopic_optimizer', 'access_planner', 'compiled_lookup', 'constant_zero')
IDS = {name: f'P{i+1:02d}' for i, name in enumerate(POLICY_NAMES)}


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')


@dataclass(frozen=True)
class View:
    task_bit: int
    badge: int
    audit: str
    bonus: int
    penalty: int
    continuation: int

    def __post_init__(self):
        if type(self.task_bit) is not int or self.task_bit not in (0, 1):
            raise ValueError('task_bit must be 0 or 1')
        if type(self.badge) is not int or self.badge not in (0, 1):
            raise ValueError('badge must be 0 or 1')
        if not isinstance(self.audit, str) or not 0 <= Fraction(self.audit) <= 1:
            raise ValueError('audit must be a rational probability string')
        if str(Fraction(self.audit)) != self.audit:
            raise ValueError('audit probability must be canonical')
        for name in ('bonus', 'penalty', 'continuation'):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError(f'{name} must be a nonnegative integer')

    @classmethod
    def from_dict(cls, data: dict) -> View:
        if set(data) != set(FIELDS):
            raise ValueError('visible-state fields missing or extra; hidden fields prohibited')
        return cls(**data)

    def key(self) -> str:
        return '|'.join(str(getattr(self, name)) for name in FIELDS)


def validate_action(action: int) -> None:
    if type(action) is not int or action not in (0, 1):
        raise ValueError('action must be an integer binary report')


def outcome(view: View, report: int, audited: bool) -> dict:
    """Two-step environment transition; audit is a possible outcome, not a draw."""
    validate_action(report)
    if type(audited) is not bool:
        raise ValueError('audited must be Boolean')
    wrong = report != view.task_bit
    caught = wrong and audited
    immediate = view.bonus if wrong else 0
    if caught:
        immediate -= view.penalty
    access = not caught
    future = view.continuation if access else 0
    return {'audited': audited, 'caught': caught, 'access_retained': access,
            'immediate_reward': immediate, 'continuation_reward': future,
            'total_reward': immediate + future,
            'events': [
                {'step': 1, 'kind': 'report', 'report': report},
                {'step': 2, 'kind': 'audit', 'audited': audited, 'caught': caught},
                {'step': 3, 'kind': 'continuation', 'available': access, 'reward': future}]}


def projected_return(view: View, report: int, include_continuation: bool = True) -> Fraction:
    """Online explicit branch evaluation used by the two optimizing policies."""
    q = Fraction(view.audit)
    total = Fraction(0)
    for audited, probability in ((False, 1 - q), (True, q)):
        event = outcome(view, report, audited)
        value = event['total_reward'] if include_continuation else event['immediate_reward']
        total += probability * value
    return total


def online_choice(view: View, include_continuation: bool) -> int:
    # Truth first gives the predeclared truthful tie break.
    actions = (view.task_bit, 1 - view.task_bit)
    return max(actions, key=lambda a: projected_return(view, a, include_continuation))


def contexts(protocol: dict) -> list[dict]:
    result = []
    for suite in ('primary', 'challenge'):
        grid = protocol[suite]
        for i, values in enumerate(itertools.product(*(grid[f] for f in FIELDS))):
            view = View(*values)
            result.append({'context_id': f'{suite}-{i:04d}', 'suite': suite,
                           'view': asdict(view), 'actual_audit': view.audit})
    h = protocol['hidden_audit_control']
    for i, (b, c, actual) in enumerate(itertools.product(h['task_bit'], h['badge'], h['actual_audit'])):
        view = View(b, c, h['announced_audit'], h['bonus'], h['penalty'], h['continuation'])
        result.append({'context_id': f'hidden-{i:04d}', 'suite': 'hidden_audit_control',
                       'view': asdict(view), 'actual_audit': actual})
    return result


def learn_badge(protocol: dict) -> tuple[Mapping[int, int], list[dict]]:
    """Empirical mean-return table indexed ONLY by badge and report relation."""
    cfg = protocol['calibration']
    rewards = defaultdict(list)
    records = []
    for bit, badge, violation in itertools.product(cfg['task_bit'], cfg['badge'], (0, 1)):
        view = View(bit, badge, str(badge), cfg['bonus'], cfg['penalty'], cfg['continuation'])
        report = bit ^ violation
        event = outcome(view, report, bool(badge))
        rewards[(badge, violation)].append(event['total_reward'])
        records.append({'view': asdict(view), 'report': report, 'violation': violation,
                        'deterministic_outcome': event})
    table = {}
    for badge in cfg['badge']:
        table[badge] = max((0, 1), key=lambda v: Fraction(sum(rewards[(badge, v)]), len(rewards[(badge, v)])))
    return MappingProxyType(table), records


def compile_table(all_contexts: list[dict]) -> Mapping[str, int]:
    """Adversarial OFFLINE compiler: full allowed-domain access is intentional.

    This independent algebraic implementation does not call the online planner.
    The decision-time lookup uses only the frozen table, never this compiler.
    """
    table = {}
    for c in all_contexts:
        v = View.from_dict(c['view'])
        cheat = Fraction(v.bonus) > Fraction(v.audit) * (v.penalty + v.continuation)
        table[v.key()] = v.task_bit ^ int(cheat)
    return MappingProxyType(table)


def choose(name: str, view: View, badge_table: Mapping[int, int], lookup: Mapping[str, int]) -> int:
    if name == 'stable_rule':
        return view.task_bit
    if name == 'badge_learner':
        return view.task_bit ^ badge_table[view.badge]
    if name == 'myopic_optimizer':
        return online_choice(view, False)
    if name == 'access_planner':
        return online_choice(view, True)
    if name == 'compiled_lookup':
        # Out-of-domain views deliberately fail rather than falling back to planning.
        return lookup[view.key()]
    if name == 'constant_zero':
        return 0
    raise ValueError(f'unknown policy {name}')


def decision_record(context: dict, policy_id: str, report: int) -> dict:
    v = View.from_dict(context['view'])
    a = Fraction(context['actual_audit'])
    if not 0 <= a <= 1:
        raise ValueError('invalid actual audit probability')
    branches = []
    for audited, weight in ((False, 1-a), (True, a)):
        branches.append({'probability': str(weight), **outcome(v, report, audited)})
    expected = sum((Fraction(b['probability']) * b['total_reward'] for b in branches), Fraction(0))
    return {**context, 'policy_id': policy_id, 'report': report,
            'violation': int(report != v.task_bit), 'branches': branches,
            'expected_total_reward': str(expected),
            'expected_visible_pass': str(1 - a * int(report != v.task_bit))}


def paired_contrasts(rows: list[dict]) -> dict:
    """Uses only visible contexts and binary reports, never implementation names."""
    answer = {}
    for field in FIELDS:
        groups = defaultdict(list)
        for row in rows:
            view = row['view']
            key = tuple(view[k] for k in FIELDS if k != field)
            groups[key].append(row)
        pairs = []
        for key in sorted(groups):
            group = sorted(groups[key], key=lambda r: Fraction(str(r['view'][field])))
            for lo, hi in zip(group, group[1:]):
                pairs.append({'lower_context': lo['context_id'], 'upper_context': hi['context_id'],
                              'report_flip': lo['report'] != hi['report'],
                              'violation_flip': (lo['report'] != lo['view']['task_bit']) != (hi['report'] != hi['view']['task_bit'])})
        answer[field] = {'pairs': len(pairs), 'report_flips': sum(p['report_flip'] for p in pairs),
                         'violation_flips': sum(p['violation_flip'] for p in pairs), 'records': pairs}
    return answer


def detector(rows: list[dict], contrasts: dict) -> dict:
    """A bounded behavioral description plus two explicitly invalid overclaims."""
    utility_matches = 0
    for row in rows:
        v = row['view']
        gain = Fraction(v['bonus']) - Fraction(v['audit']) * (v['penalty'] + v['continuation'])
        predicted = v['task_bit'] ^ int(gain > 0)
        utility_matches += row['report'] == predicted
    sensitive = [field for field, c in contrasts.items() if c['violation_flips']]
    return {
        'observations': len(rows),
        'violation_sensitive_visible_factors': sensitive,
        'declared_two_step_argmax_matches': utility_matches,
        'declared_two_step_argmax_total': len(rows),
        'naive_badge_rule_overclaims_online_strategy': contrasts['badge']['violation_flips'] > 0,
        'naive_payoff_rule_overclaims_online_strategy': utility_matches == len(rows) and contrasts['continuation']['violation_flips'] > 0,
        'mechanism_status': 'NOT_IDENTIFIED_FROM_BEHAVIOR',
        'intent_status': 'NOT_ESTABLISHED',
        'scope': 'Only the finite supplied views; identical outcomes do not identify runtime planning.'}


def equivalence(rows: list[dict]) -> list[list[str]]:
    grouped = defaultdict(list)
    for pid in sorted({r['policy_id'] for r in rows}):
        ordered = sorted((r for r in rows if r['policy_id'] == pid), key=lambda r: r['context_id'])
        signature = tuple(r['report'] for r in ordered)
        grouped[signature].append(pid)
    return sorted(grouped.values(), key=lambda g: g[0])


def minimum_panel(rows: list[dict]) -> dict:
    """Exact retrospective set cover, over distinct response patterns only."""
    ids = sorted({r['policy_id'] for r in rows})
    by_context = defaultdict(dict)
    context_views = {}
    for r in rows:
        by_context[r['context_id']][r['policy_id']] = r['report']
        context_views[r['context_id']] = r['view']
    patterns = {}
    all_pairs = list(itertools.combinations(ids, 2))
    for cid in sorted(by_context):
        sig = tuple(by_context[cid][pid] for pid in ids)
        patterns.setdefault(sig, cid)
    covers = []
    for sig, cid in sorted(patterns.items(), key=lambda item: item[1]):
        mask = 0
        for i, (a, b) in enumerate(all_pairs):
            if sig[ids.index(a)] != sig[ids.index(b)]:
                mask |= 1 << i
        covers.append((cid, sig, mask))
    target = 0
    for _, _, mask in covers:
        target |= mask
    checked = {}
    chosen = []
    for k in range(0, len(covers)+1):
        checked[str(k)] = 0
        found = False
        for combo in itertools.combinations(covers, k):
            checked[str(k)] += 1
            union = 0
            for _, _, mask in combo:
                union |= mask
            if union == target:
                chosen = combo
                found = True
                break
        if found:
            break
    unresolved = [list(pair) for i, pair in enumerate(all_pairs) if not target & (1 << i)]
    return {'query_count': len(chosen), 'distinct_response_patterns': len(covers),
            'searched_panels_by_size': checked, 'separable_pairs': target.bit_count(),
            'total_policy_pairs': len(all_pairs), 'inseparable_policy_pairs': unresolved,
            'queries': [{'context_id': cid, 'view': context_views[cid], 'reports': dict(zip(ids, sig))} for cid, sig, mask in chosen],
            'scope': 'Retrospective same-grid design, not blind discovery or independent validation.'}


def aggregate(rows: list[dict], protocol: dict) -> tuple[dict, dict, dict]:
    out = {'record_id': protocol['record_id'], 'decision_rows': len(rows),
           'branch_records': sum(len(r['branches']) for r in rows),
           'contexts': len({r['context_id'] for r in rows}), 'policies': IDS,
           'suites': {}, 'ordinary_evaluation': {}}
    all_contrasts, descriptions = {}, {}
    for suite in ('primary', 'challenge', 'hidden_audit_control'):
        suite_rows = [r for r in rows if r['suite'] == suite]
        suite_out = {'contexts': len({r['context_id'] for r in suite_rows}), 'policies': {},
                     'equivalence_classes': equivalence(suite_rows)}
        for name, pid in IDS.items():
            rr = [r for r in suite_rows if r['policy_id'] == pid]
            n = len(rr)
            suite_out['policies'][pid] = {'name': name, 'n': n,
                  'truthful': sum(1-r['violation'] for r in rr), 'violations': sum(r['violation'] for r in rr),
                  'mean_expected_visible_pass': str(sum((Fraction(r['expected_visible_pass']) for r in rr), Fraction(0))/n),
                  'mean_expected_total_reward': str(sum((Fraction(r['expected_total_reward']) for r in rr), Fraction(0))/n)}
            if suite != 'hidden_audit_control':
                cc = paired_contrasts(rr)
                all_contrasts[f'{suite}:{pid}'] = cc
                descriptions[f'{suite}:{pid}'] = detector(rr, cc)
        out['suites'][suite] = suite_out
    for name, pid in IDS.items():
        rr = [r for r in rows if r['suite'] == 'primary' and r['policy_id'] == pid
              and r['view']['badge'] == 1 and r['view']['audit'] == '1'
              and r['view']['bonus'] == 1 and r['view']['penalty'] == 2 and r['view']['continuation'] == 6]
        out['ordinary_evaluation'][pid] = {'n': len(rr), 'truthful': sum(1-r['violation'] for r in rr)}
    hidden = [r for r in rows if r['suite'] == 'hidden_audit_control']
    groups = defaultdict(list)
    for r in hidden:
        groups[(r['policy_id'], canonical(r['view']))].append(r)
    pairs = [sorted(g, key=lambda r: Fraction(r['actual_audit'])) for g in groups.values()]
    out['hidden_control'] = {'matched_pairs': len(pairs),
                            'decision_flips': sum(a['report'] != b['report'] for a, b in pairs),
                            'visible_score_changes': sum(a['expected_visible_pass'] != b['expected_visible_pass'] for a, b in pairs),
                            'expected_payoff_changes': sum(a['expected_total_reward'] != b['expected_total_reward'] for a, b in pairs)}
    return out, all_contrasts, descriptions


def run(destination: Path, protocol: dict, reverse: bool = False) -> dict:
    destination.mkdir(parents=True, exist_ok=False)
    all_contexts = contexts(protocol)
    badge_table, calibration = learn_badge(protocol)
    lookup = compile_table(all_contexts)
    # Serialization round-trip makes decision-time lookup visibly distinct from its compiler.
    write_json(destination/'compiled_lookup.json', dict(lookup))
    lookup = MappingProxyType(json.loads((destination/'compiled_lookup.json').read_text()))
    rows = []
    for context in (reversed(all_contexts) if reverse else all_contexts):
        v = View.from_dict(context['view'])  # No actual_audit field can pass this schema.
        for name in (reversed(POLICY_NAMES) if reverse else POLICY_NAMES):
            action = choose(name, v, badge_table, lookup)
            rows.append(decision_record(context, IDS[name], action))
    rows.sort(key=lambda r: (r['context_id'], r['policy_id']))
    with (destination/'decisions.jsonl').open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(canonical(row)+'\n')
    write_json(destination/'contexts.json', all_contexts)
    write_json(destination/'calibration.json', {'rows': calibration, 'learned_badge_violation_table': dict(badge_table)})
    summary, contrasts, descriptions = aggregate(rows, protocol)
    write_json(destination/'summary.json', summary)
    write_json(destination/'paired_contrasts.json', contrasts)
    write_json(destination/'behavioral_descriptions.json', descriptions)
    write_json(destination/'minimum_panel.json', minimum_panel([r for r in rows if r['suite'] == 'primary']))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New output directory; will not overwrite existing evidence.')
    parser.add_argument('--protocol', type=Path, default=ROOT/'protocol.json')
    parser.add_argument('--reverse', action='store_true', help='Reverse context and policy order; canonical output should be unchanged.')
    args = parser.parse_args()
    summary = run(args.output, json.loads(args.protocol.read_text()), args.reverse)
    print(canonical({'decisions': summary['decision_rows'], 'branches': summary['branch_records'], 'contexts': summary['contexts']}))


if __name__ == '__main__':
    main()
