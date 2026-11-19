#!/usr/bin/env python3
"""Validate retained evidence and rerun all frozen helpers in temporary services.

The default performs both event-chain validation and new deterministic helper
execution. It never calls a model and never overwrites retained study evidence.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import tempfile

from execute import ROOT, HELPERS, ARMS, analyze_run, cases, dump, execute, load_engine, read, require_external, verify_freeze


def normalize_transport(value):
    result = dict(value)
    result.pop('node_version',None)
    return result


def normalize_summary(value):
    result = dict(value)
    result.pop('python_version',None)
    result['runs'] = [{k:v for k,v in row.items() if k != 'node_version'} for row in value['runs']]
    return result


def normalize_events(rows):
    return [{k:v for k,v in row.items() if k not in ('timestamp','previous_event_sha256','event_sha256')} for row in rows]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--records',type=Path,default=ROOT/'results')
    parser.add_argument('--verify-only',action='store_true',help='Validate retained chains and summaries without executing fresh helper copies')
    args=parser.parse_args()
    require_external(args.output)
    freeze=verify_freeze()
    engine=load_engine()
    retained=read(args.records/'summary.json')
    recomputed=[]
    for case in cases():
        for helper in HELPERS:
            for arm in ARMS:
                run_id=f"{case['case_id']}_{helper}_{arm}"
                row=analyze_run(engine,case,helper,arm,args.records/'runs'/run_id)
                assert row==read(args.records/'runs'/run_id/'analysis.json'), run_id
                recomputed.append(row)
    assert recomputed==retained['runs'], 'Retained summary rows differ from recomputation'
    from execute import aggregate
    assert aggregate(recomputed)==retained['cells']
    rerun=None
    if not args.verify_only:
        with tempfile.TemporaryDirectory(prefix='receipt-guard-reproduction-') as temporary:
            generated=Path(temporary)
            rerun=execute(generated)
            assert normalize_summary(rerun)==normalize_summary(retained), 'Fresh deterministic outcome mismatch'
            for row in recomputed:
                name=row['run_id']
                original=args.records/'runs'/name
                fresh=generated/'runs'/name
                for file in ('initial_state.json','state.json'):
                    assert read(original/file)==read(fresh/file), (name,file)
                assert normalize_transport(read(original/'transport.json'))==normalize_transport(read(fresh/'transport.json')), (name,'transport')
                from execute import event_rows
                assert normalize_events(event_rows(original/'events.jsonl'))==normalize_events(event_rows(fresh/'events.jsonl')), (name,'events')
    result={'status':'PASS',**freeze,'retained_runs_verified':len(recomputed),
            'retained_canonical_events_verified':sum(r['canonical_event_count'] for r in recomputed),
            'fresh_helper_replays':len(recomputed) if rerun else 0,
            'fresh_actions_observations_oracles_states_and_transport_match':bool(rerun),
            'excluded_from_fresh_comparison':['wall-clock event timestamp','event chain hashes that bind timestamps','Node runtime version','Python runtime version'],
            'individual_retained_and_fresh_event_chains_verified':True,
            'no_native_participants':True,'retained_files_modified':False}
    dump(args.output,result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
