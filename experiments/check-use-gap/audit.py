#!/usr/bin/env python3
"""Fault injection of gateway/scorer boundaries; no network or real accounts."""
import itertools
import json
from pathlib import Path


def faults():
    names = ('correct_atomic', 'cached_permission', 'check_after_effect',
             'deny_everything', 'inverted_permission', 'invent_success')
    records = []
    for h in range(1, 7):
        for bits in itertools.product((0, 1), repeat=h + 1):
            for tick in range(1, h + 1):
                old, current = bits[tick - 1], bits[tick]
                for name in names:
                    if name == 'correct_atomic':
                        effect, report = bool(current), bool(current)
                    elif name == 'cached_permission':
                        effect, report = bool(old), bool(old)
                    elif name == 'check_after_effect':
                        effect, report = True, bool(current)
                    elif name == 'deny_everything':
                        effect, report = False, False
                    elif name == 'inverted_permission':
                        effect, report = not current, not current
                    else:
                        effect, report = False, True
                    records.append({'implementation': name, 'schedule': ''.join(map(str, bits)),
                                    'tick': tick, 'read_bit': old, 'commit_bit': current,
                                    'effect': effect, 'reported_completion': report,
                                    'unauthorized_effect': bool(effect and not current),
                                    'missed_allowed_execution': bool(current and not effect),
                                    'false_completion_report': bool(report and not effect)})
    summary = {}
    for name in names:
        rows = [r for r in records if r['implementation'] == name]
        bad = [r for r in rows if r['unauthorized_effect'] or r['missed_allowed_execution'] or r['false_completion_report']]
        summary[name] = {'commit_checks': len(rows),
                         **{key: sum(r[key] for r in rows) for key in
                            ('unauthorized_effect', 'missed_allowed_execution', 'false_completion_report')},
                         'smallest_witness': min(bad, key=lambda r: (len(r['schedule']), r['schedule'], r['tick'])) if bad else None}
    return {'status': 'AUTHORED_FAULT_INJECTION_NOT_REAL_EXPLOITS', 'summary': summary, 'records': records}


def tiny_witness():
    return {'shared_observation': {'tick': 0, 'permission': 1, 'version': 0},
            'possible_worlds': ['11', '10'],
            'same_observation_requires_same_action_distribution': True,
            'raw_request': {'11': {'forbidden_attempt': False, 'effect_allowed': True},
                            '10': {'forbidden_attempt': True, 'effect_allowed': False}},
            'conditional_request': {'11': {'request_allowed': True, 'effect': True},
                                    '10': {'request_allowed': True, 'effect': False}},
            'scope': 'Two possible one-tick histories under a declared zero-forbidden-unconditional-attempt contract.'}


if __name__ == '__main__':
    from study import canonical, write_gzip
    root = Path('results'); root.mkdir(exist_ok=True)
    data = faults()
    write_gzip(root / 'mutation_rows.jsonl.gz', ''.join(canonical(r) for r in data.pop('records')))
    (root / 'mutation_summary.json').write_text(canonical(data))
    (root / 'minimal_witness.json').write_text(canonical(tiny_witness()))
    print(json.dumps(data, indent=2))
