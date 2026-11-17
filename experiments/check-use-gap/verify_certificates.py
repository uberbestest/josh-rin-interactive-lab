#!/usr/bin/env python3
"""Standalone proof checker; does not import or execute the optimizing planner.
Reconstructs schedules from transition-time combinations (not bitstrings), then
checks every Bellman alternative and optimality value in each finite certificate.
Same-author second implementation, NOT independent external validation.
"""
import argparse
import gzip
import itertools
import json

NAMES = ('raw', 'conditional', 'compare', 'main', 'inspect', 'wait', 'stop')


def check(ok, message):
    if not ok:
        raise ValueError(message)


def check_certificate(document):
    c = document['config']
    h, cap, main, initial, mode = [c[k] for k in ('horizon', 'switches', 'main_cost', 'initial', 'mode')]
    check(mode in ('snapshot', 'compare', 'atomic'), 'interface')
    check(document['schema'] == 'compact-v1', 'schema')
    worlds = []
    for count in range(cap + 1):
        for changed_at in itertools.combinations(range(1, h + 1), count):
            bits, versions, value, version = [initial], [0], initial, 0
            for tick in range(1, h + 1):
                if tick in changed_at:
                    value = 1 - value
                    version += 1
                bits.append(value)
                versions.append(version)
            worlds.append((bits, versions))
    worlds.sort()
    n = len(worlds)
    nodes = document['nodes']
    states, state_to_index = [], {}
    for index, node in enumerate(nodes):
        tick, mask_hex, token, wins, cost, action, alternatives = node
        mask = int(mask_hex, 16)
        check(0 < mask < (1 << n), 'belief mask')
        check(0 <= tick <= h and 0 <= token <= cap, 'state range')
        belief = tuple(i for i in range(n) if mask & (1 << i))
        state = (tick, belief, token)
        check(state not in state_to_index, 'duplicate certificate state')
        check(all(worlds[i][1][tick] >= token for i in belief), 'future token')
        state_to_index[state] = index
        states.append(state)
    root = document['root']
    check(states[root] == (0, tuple(range(n)), 0), 'root belief')
    checked_alternatives = 0
    for index, node in enumerate(nodes):
        tick, belief, token = states[index]
        size = len(belief)
        wanted = []
        for ai, name in enumerate(NAMES):
            if tick == h and name != 'stop':
                continue
            if name == 'main' and tick + main > h:
                continue
            if name == 'conditional' and mode != 'atomic':
                continue
            if name == 'compare' and mode != 'compare':
                continue
            next_tick, groups, wins, cost = tick + 1, [], 0, size
            if name == 'stop':
                cost = 0
            elif name == 'main':
                wins, cost = size, size * main
            elif name == 'raw':
                if any(worlds[i][0][next_tick] == 0 for i in belief):
                    continue
                wins = size
            elif name == 'wait':
                groups = [('no_notice', belief, token)]
            elif name == 'inspect':
                groups_by_result = {}
                for i in belief:
                    obs = (worlds[i][0][next_tick], worlds[i][1][next_tick])
                    groups_by_result.setdefault(obs, []).append(i)
                groups = [(f'{a}:{v}', tuple(ids), v) for (a, v), ids in sorted(groups_by_result.items())]
            elif name in ('conditional', 'compare'):
                fail = tuple(i for i in belief if not (worlds[i][0][next_tick] == 1 and
                             (name == 'conditional' or worlds[i][1][next_tick] == token)))
                wins = size - len(fail)
                if fail:
                    groups = [('denied', fail, token)]
            children = []
            for label, subbelief, subtoken in groups:
                child_state = (next_tick, subbelief, subtoken)
                check(child_state in state_to_index, 'missing continuation state')
                child = state_to_index[child_state]
                check(states[child][0] > tick, 'non-advancing certificate edge')
                wins += nodes[child][3]
                cost += nodes[child][4]
                children.append([label, child])
            wanted.append([ai, wins, cost, children])
        check(node[6] == wanted, 'alternative values/branches mismatch at node ' + str(index))
        best = min(wanted, key=lambda a: (-a[1], a[2], a[0]))
        check(node[3:6] == [best[1], best[2], best[0]], 'not optimal at node ' + str(index))
        checked_alternatives += len(wanted)
    return {'nodes': len(nodes), 'alternatives': checked_alternatives,
            'root_value': nodes[root][3:5]}


def verify(path):
    total = {'certificates': 0, 'nodes': 0, 'alternatives': 0}
    with gzip.open(path, 'rt') as stream:
        for line in stream:
            result = check_certificate(json.loads(line))
            total['certificates'] += 1
            total['nodes'] += result['nodes']
            total['alternatives'] += result['alternatives']
    return total


if __name__ == '__main__':
    cli = argparse.ArgumentParser()
    cli.add_argument('path', nargs='?', default='results/certificates.jsonl.gz')
    print(json.dumps(verify(cli.parse_args().path), sort_keys=True))
