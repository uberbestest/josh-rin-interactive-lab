#!/usr/bin/env python3
"""Recount retained evidence and optionally reproduce every assigned execution."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import tempfile
import run_study as study

ROOT = Path(__file__).resolve().parent


def normalized(value):
    if isinstance(value, list):
        return [normalized(item) for item in value]
    if isinstance(value, dict):
        omit = {'timestamp', 'previous_event_sha256', 'event_sha256', 'node_version', 'python_version'}
        return {key: normalized(item) for key, item in value.items() if key not in omit}
    return value


def verify(record_dir, reproduce=False):
    freeze=study.verify_freeze()
    engine=study.engine_module()
    checker=study.module('continuation_independent_checker', ROOT/'independent_check.py')
    summary=study.read(record_dir/'summary.json')
    rows=[]
    event_count=0
    checks=[]
    for path in sorted((record_dir/'runs').glob('*.json')):
        record=study.read(path)
        if record['diagnostics'].get('infrastructure_error'):
            checks.append({'run_id':record['run_id'], 'status':'retained_infrastructure_error'})
            rows.append(record)
            continue
        initial, events, final = record['initial_state'], record['events'], record['final_state']
        if engine.replay(initial, events) != final:
            raise AssertionError('Canonical replay mismatch: '+record['run_id'])
        independent=checker.check_episode(initial['config'], initial['actual_world'], events, final)
        checks.append({'run_id':record['run_id'], 'status':'recounted', 'independent':independent})
        event_count+=len(events)
        rows.append(record)
    aggregate=study.summarize(rows)
    sort_cells=lambda cells: sorted(cells,key=lambda c:(c['suite'],c['policy']))
    if sort_cells(aggregate['cells']) != sort_cells(summary['cells']):
        raise AssertionError('Aggregate cells differ from retained raw records')
    if aggregate['executions'] != summary['executions'] or aggregate['events'] != summary['events']:
        raise AssertionError('Retained denominator mismatch')
    legacy_events=0
    for path in sorted((record_dir/'legacy/runs').glob('*/initial_state.json')):
        directory=path.parent
        initial=study.read(path)
        events=[json.loads(line) for line in (directory/'events.jsonl').read_text().splitlines()]
        final=study.read(directory/'state.json')
        if engine.replay(initial, events)!=final:
            raise AssertionError('Legacy event replay mismatch: '+directory.name)
        checker.check_episode(initial['config'],initial['actual_world'],events,final)
        legacy_events+=len(events)
    same=True
    fresh=0
    if reproduce:
        with tempfile.TemporaryDirectory(prefix='continuation-reproduce-') as folder:
            replay_root=Path(folder)/'records'
            replay=study.execute(replay_root)
            if normalized(replay)!=normalized(summary):
                study.dump(Path(folder)/'comparison-summary.json', {'same':False})
                raise AssertionError('Reproduced summary differs from retained results')
            for path in (record_dir/'runs').glob('*.json'):
                other=replay_root/'runs'/path.name
                if normalized(study.read(path))!=normalized(study.read(other)):
                    raise AssertionError('Reproduced record differs: '+path.name)
                fresh+=1
            for path in (record_dir/'legacy/runs').rglob('*'):
                if not path.is_file():
                    continue
                rel=path.relative_to(record_dir)
                other=replay_root/rel
                if path.suffix=='.json':
                    a,b=study.read(path),study.read(other)
                elif path.suffix=='.jsonl':
                    a=[json.loads(s) for s in path.read_text().splitlines()]
                    b=[json.loads(s) for s in other.read_text().splitlines()]
                else:
                    if path.read_bytes()!=other.read_bytes():raise AssertionError('Legacy file mismatch: '+str(rel))
                    continue
                if normalized(a)!=normalized(b):
                    raise AssertionError('Reproduced legacy record differs: '+str(rel))
    return {'status':'PASS', **freeze, 'runs_replayed':len(rows)+summary['legacy_executions'],
            'events_replayed':event_count+legacy_events, 'mechanical_results_exact':True,
            'independent_recounts':len(checks)+summary['legacy_executions'],
            'fresh_scripted_executions':fresh+summary['legacy_executions'] if reproduce else 0,
            'native_participants':0, 'reproduction_requested':reproduce,
            'normalized_reproduction_exact':same if reproduce else None,
            'checks':checks,
            'scope':'Same-lab deterministic replay and separately written arithmetic; no external replication.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records',type=Path,default=ROOT/'results')
    parser.add_argument('--reproduce',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=verify(args.records,args.reproduce)
    study.dump(args.output,result)
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
