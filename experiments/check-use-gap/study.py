#!/usr/bin/env python3
"""Exact finite permission game. Standard library only; no model or network calls.

An authentic snapshot is evidence about its read tick, not a lease on the next tick.
The solver sees a SET of possible schedules. The replay sees one actual schedule.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import itertools
import json
import tempfile
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

MODES = ('snapshot', 'compare', 'atomic')
# Deterministic tie-break: maximize successes, minimize total ticks, then this order.
ACTIONS = ('raw', 'conditional', 'compare', 'main', 'inspect', 'wait', 'stop')
STUDY = 'BONDED-RSI-CHECK-USE-GAP-2026-11-16-002'
VERSION = '1.0.0'


def require(condition, message='verification failed'):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n'


@dataclass(frozen=True)
class Config:
    horizon: int
    switches: int
    main_cost: int
    initial: int
    mode: str

    def __post_init__(self):
        require(1 <= self.horizon <= 12, 'horizon must be 1..12')
        require(0 <= self.switches <= self.horizon, 'switch cap out of range')
        require(self.main_cost >= 1 and self.initial in (0, 1), 'bad route/initial value')
        require(self.mode in MODES, 'unknown interface')

    @property
    def key(self):
        return f'h{self.horizon}-k{self.switches}-m{self.main_cost}-i{self.initial}-{self.mode}'


def schedules(c):
    """All bit schedules a[0..H] with known a[0] and <=K transitions."""
    out = []
    for suffix in itertools.product((0, 1), repeat=c.horizon):
        bits = (c.initial,) + suffix
        version = [0]
        for old, new in zip(bits, bits[1:]):
            version.append(version[-1] + int(old != new))
        if version[-1] <= c.switches:
            out.append((bits, tuple(version)))
    return tuple(out)


def allowed_actions(c, t):
    if t >= c.horizon:
        return ('stop',)
    return tuple(a for a in ACTIONS if
                 (a != 'conditional' or c.mode == 'atomic') and
                 (a != 'compare' or c.mode == 'compare') and
                 (a != 'main' or t + c.main_cost <= c.horizon))


class Planner:
    """Belief-state dynamic programming; no realized future is supplied to choose().

    Each value is (number completed, sum of ticks spent) on the possible schedules.
    Raw actions are admissible only if valid on EVERY compatible next state.
    Conditional/CAS requests are explicitly permitted; they may be rejected.
    """
    def __init__(self, config, reverse=False):
        self.c = config
        self.worlds = schedules(config)
        self.reverse = reverse
        self.nodes = {}

    def state_key(self, t, belief, token):
        return (t, tuple(sorted(belief)), token)

    def branches(self, action, t, belief, token):
        """(immediate wins, immediate tick sum, [(observation, child state)]).
        None denotes an unsafe raw request; not a low-scoring admissible choice.
        """
        c, worlds, n, tick = self.c, self.worlds, len(belief), t + 1
        if action == 'stop':
            return 0, 0, []
        if action == 'main':
            return n, n * c.main_cost, []
        if action == 'raw':
            if not all(worlds[i][0][tick] for i in belief):
                return None
            return n, n, []
        if action == 'wait':
            return 0, n, [('no_notice', self.state_key(tick, belief, token))]
        if action == 'inspect':
            groups = defaultdict(list)
            for i in belief:
                bits, versions = worlds[i]
                groups[(bits[tick], versions[tick])].append(i)
            children = [(f'{bit}:{v}', self.state_key(tick, group, v))
                        for (bit, v), group in sorted(groups.items())]
            return 0, n, children
        if action in ('conditional', 'compare'):
            rejected = []
            for i in belief:
                bits, versions = worlds[i]
                permitted = bool(bits[tick])
                admitted = permitted and (action == 'conditional' or versions[tick] == token)
                if not admitted:
                    rejected.append(i)
            child = [('denied', self.state_key(tick, rejected, token))] if rejected else []
            return n - len(rejected), n, child
        raise ValueError(action)

    def solve(self, t=0, belief=None, token=0):
        if belief is None:
            belief = tuple(range(len(self.worlds)))
        key = self.state_key(t, belief, token)
        if key in self.nodes:
            return self.nodes[key]['value']
        candidates = []
        acts = allowed_actions(self.c, t)
        for action in reversed(acts) if self.reverse else acts:
            step = self.branches(action, t, key[1], token)
            if step is None:
                continue
            wins, cost, children = step
            for _, child in children:
                w, k = self.solve(*child)
                wins += w
                cost += k
            candidates.append({'action': action, 'value': (wins, cost),
                               'children': children})
        best = min(candidates, key=lambda a: (-a['value'][0], a['value'][1], ACTIONS.index(a['action'])))
        self.nodes[key] = {'value': best['value'], 'action': best['action'],
                           'alternatives': sorted(candidates, key=lambda a: ACTIONS.index(a['action']))}
        return best['value']

    def choose(self, t, belief, token):
        key = self.state_key(t, belief, token)
        self.solve(*key)
        return self.nodes[key]['action']

    def certificate(self):
        self.solve()
        keys = sorted(self.nodes)
        indices = {key: i for i, key in enumerate(keys)}
        # Compact schema: [tick, belief_bitset_hex, token, wins, cost, action_index,
        #                 [[action_index,wins,cost,[[observation,child_index],...]],...]]
        nodes = []
        for key in keys:
            node = self.nodes[key]
            mask = sum(1 << i for i in key[1])
            alternatives = [[ACTIONS.index(a['action']), *a['value'],
                             [[o, indices[k]] for o, k in a['children']]]
                            for a in node['alternatives']]
            nodes.append([key[0], format(mask, 'x'), key[2], *node['value'],
                          ACTIONS.index(node['action']), alternatives])
        return {'config': self.c.__dict__, 'root': indices[(0, tuple(range(len(self.worlds))), 0)],
                'schema': 'compact-v1', 'nodes': nodes}


def replay(planner, world_index, trace=True):
    """Separate operational simulator. Does NOT call Planner.branches()."""
    c, worlds = planner.c, planner.worlds
    actual, versions = worlds[world_index]
    possible = tuple(range(len(worlds)))
    t, token, complete, unauthorized, events = 0, 0, False, 0, []
    while True:
        require(world_index in possible, 'real world lost from belief')
        action = planner.choose(t, possible, token)
        before = t
        received = None
        admitted = None
        if action == 'stop':
            break
        if action == 'main':
            t += c.main_cost
            require(t <= c.horizon, 'main route after deadline')
            complete, admitted = True, True
        else:
            t += 1
            require(t <= c.horizon, 'action after deadline')
            if action == 'raw':
                unauthorized += int(actual[t] == 0)
                admitted = bool(actual[t])
                complete = admitted
                # Authored optimal raw decisions must be valid in all belief members.
                possible = tuple(i for i in possible if worlds[i][0][t] == actual[t])
            elif action == 'inspect':
                received = [actual[t], versions[t]]
                token = versions[t]
                possible = tuple(i for i in possible
                                 if worlds[i][0][t] == actual[t] and worlds[i][1][t] == versions[t])
            elif action == 'conditional':
                admitted = bool(actual[t])
                complete = admitted
                if not admitted:
                    possible = tuple(i for i in possible if worlds[i][0][t] == 0)
            elif action == 'compare':
                admitted = bool(actual[t] and versions[t] == token)
                complete = admitted
                if not admitted:
                    possible = tuple(i for i in possible
                                     if not (worlds[i][0][t] and worlds[i][1][t] == token))
            elif action != 'wait':
                raise ValueError(action)
        if trace:
            events.append({'from_tick': before, 'to_tick': t, 'action': action,
                           'observation': received, 'admitted': admitted,
                           'actual_permission_evaluator_only': actual[t],
                           'actual_version_evaluator_only': versions[t],
                           'compatible_schedules_after': len(possible)})
        if complete:
            break
    require(unauthorized == 0, 'synthesized policy made forbidden unconditional request')
    return {'schedule': ''.join(map(str, actual)), 'completed': complete,
            'ticks_spent': t, 'unauthorized_raw_attempts': unauthorized, 'events': events}


def enumerate_policy_values(c, t=0, belief=None, token=0):
    """Independent tiny-horizon exhaustive POLICY TREE enumeration.

    No Planner transitions/values used. Returns every distinct attainable (wins,cost)
    pair, not just the best. Cartesian products enumerate contingent child policies.
    No memoization: intended for H<=3 only. Randomization cannot improve the linear
    coverage objective subject to zero violations on every schedule.
    """
    worlds = schedules(c)
    if belief is None:
        belief = tuple(range(len(worlds)))
    n = len(belief)
    values = {(0, 0)}
    if t == c.horizon:
        return values
    if t + c.main_cost <= c.horizon:
        values.add((n, n * c.main_cost))
    tick = t + 1
    if all(worlds[i][0][tick] == 1 for i in belief):
        values.add((n, n))
    # Idle branch: same observation for every underlying schedule.
    values.update((w, k + n) for w, k in enumerate_policy_values(c, tick, belief, token))
    # Inspect branch: independently construct observation-contingent policy trees.
    partitions = {}
    for i in belief:
        obs = (worlds[i][0][tick], worlds[i][1][tick])
        partitions.setdefault(obs, []).append(i)
    totals = {(0, n)}
    for (bit, ver), ids in sorted(partitions.items()):
        choices = enumerate_policy_values(c, tick, tuple(ids), ver)
        totals = {(a + x, b + y) for a, b in totals for x, y in choices}
    values.update(totals)
    if c.mode != 'snapshot':
        accepted = [i for i in belief if worlds[i][0][tick] == 1 and
                    (c.mode == 'atomic' or worlds[i][1][tick] == token)]
        denied = tuple(i for i in belief if i not in accepted)
        if denied:
            values.update((len(accepted) + w, n + k)
                          for w, k in enumerate_policy_values(c, tick, denied, token))
        else:
            values.add((n, n))
    return values


def primary_configs(reverse=False):
    configs = [Config(h, k, m, initial, mode)
               for h in range(1, 9) for k in range(h + 1)
               for m in (2, 4, 6, 8) for initial in (0, 1) for mode in MODES]
    return reversed(configs) if reverse else configs


def oracle_count(c, worlds):
    return sum(c.main_cost <= c.horizon or any(bits[1:]) for bits, _ in worlds)


def summarize(c, planner, runs):
    value = planner.solve()
    wins, cost = sum(x['completed'] for x in runs), sum(x['ticks_spent'] for x in runs)
    require((wins, cost) == value, 'planner and replay disagree')
    return {'id': c.key, **c.__dict__, 'schedules': len(planner.worlds),
            'completions': wins, 'oracle_feasible': oracle_count(c, planner.worlds),
            'total_ticks': cost, 'first_action': planner.choose(0, tuple(range(len(planner.worlds))), 0),
            'certificate_nodes': len(planner.nodes), 'unsafe_attempts': 0}


def write_gzip(path, text):
    path.write_bytes(gzip.compress(text.encode('utf-8'), compresslevel=9, mtime=0))


def run_suite(out, reverse=False):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows, replay_count = [], 0
    # Stage bounded per-cell files, then stream canonical order. This avoids
    # holding the entire certificate corpus in memory and tests case-order invariance.
    with tempfile.TemporaryDirectory(prefix='cell-', dir=out) as tmp:
        tmp = Path(tmp)
        for c in primary_configs(reverse):
            p = Planner(c, reverse=reverse)
            p.solve()
            runs = [replay(p, i) for i in range(len(p.worlds))]
            rows.append(summarize(c, p, runs))
            replay_count += len(runs)
            (tmp / (c.key + '.cert')).write_text(canonical({'id': c.key, **p.certificate()}))
            (tmp / (c.key + '.trace')).write_text(''.join(canonical({'id': c.key, **r}) for r in runs))
        for suffix, target in (('.cert', 'certificates.jsonl.gz'), ('.trace', 'trajectories.jsonl.gz')):
            with (out / target).open('wb') as raw:
                with gzip.GzipFile(filename='', fileobj=raw, mode='wb', compresslevel=6, mtime=0) as compressed:
                    for path in sorted(tmp.glob('*' + suffix)):
                        with path.open('rb') as source:
                            shutil.copyfileobj(source, compressed)
    rows.sort(key=lambda r: r['id'])
    (out / 'frontier.json').write_text(canonical(rows))
    with (out / 'frontier.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    checks = []
    for c in primary_configs():
        if c.horizon > 3:
            continue
        values = enumerate_policy_values(c)
        optimum = min(values, key=lambda x: (-x[0], x[1]))
        expected = Planner(c).solve()
        require(optimum == expected, 'exhaustive policy enumeration disagrees: ' + c.key)
        checks.append({'id': c.key, 'distinct_score_pairs': len(values), 'optimum': optimum})
    (out / 'exhaustive_policy_check.json').write_text(canonical(checks))
    by_id = {r['id']: r for r in rows}
    # Exact monotonicity is within MATCHED underlying schedule families, not across caps.
    for r in rows:
        if r['mode'] == 'snapshot':
            other = by_id[r['id'].replace('snapshot', 'compare')]
            atomic = by_id[r['id'].replace('snapshot', 'atomic')]
            require(r['completions'] <= other['completions'] <= atomic['completions'], 'coverage order')
            require(atomic['completions'] == atomic['oracle_feasible'], 'atomic oracle gap')
    summary = {'record': STUDY, 'version': VERSION, 'status': 'FINITE_GAME_SYNTHESIS_NOT_LIVE_AGENTS',
               'parameter_cells': len(rows), 'schedule_policy_replays': replay_count,
               'certificate_nodes': sum(r['certificate_nodes'] for r in rows),
               'exhaustive_policy_tree_cells': len(checks),
               'by_interface': {mode: {'cells': sum(r['mode'] == mode for r in rows),
                    'feasible_completion_gap': sum(r['oracle_feasible'] - r['completions'] for r in rows if r['mode'] == mode),
                    'full_oracle_coverage_cells': sum(r['completions'] == r['oracle_feasible'] for r in rows if r['mode'] == mode)}
                    for mode in MODES},
               'denominator_warning': 'Designed overlapping schedule families, not independent trials or empirical prevalence.',
               'live_model_calls': 0, 'external_independent_reviews': 0, 'castle_modifications': 0}
    (out / 'summary.json').write_text(canonical(summary))
    return summary


if __name__ == '__main__':
    cli = argparse.ArgumentParser()
    cli.add_argument('--out', default='results')
    cli.add_argument('--reverse', action='store_true')
    args = cli.parse_args()
    print(json.dumps(run_suite(args.out, args.reverse), indent=2))
