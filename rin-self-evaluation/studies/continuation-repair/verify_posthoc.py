#!/usr/bin/env python3
"""Reproduce the six explicitly exploratory diagnostics into a fresh directory."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import run_study as runner
from independent_check import check_episode
from verify import normalized

ROOT=Path(__file__).resolve().parent


def verify():
    directory=ROOT/'posthoc-diagnostics'
    frozen=runner.read(directory/'freeze.json')
    if runner.sha(directory/'cases.json')!=frozen['cases_sha256']:
        raise AssertionError('Diagnostic case hash mismatch')
    if runner.sha(ROOT/'posthoc_diagnostics.py')!=frozen['diagnostic_script_sha256']:
        raise AssertionError('Original diagnostic script changed')
    for name,digest in frozen['sources'].items():
        if runner.sha(ROOT/name)!=digest:raise AssertionError('Diagnostic input changed: '+name)
    original=runner.read(directory/'summary.json')
    cases=runner.read(directory/'cases.json')
    engine=runner.engine_module()
    fresh=[]
    with tempfile.TemporaryDirectory(prefix='posthoc-reproduction-') as temporary:
        output=Path(temporary)
        for case in cases['cases']:
            for index,world in enumerate(case['worlds']):
                for policy in cases['policies']:
                    run_id=f"{case['case_id']}-W{index+1:02d}_{policy}"
                    retained=runner.read(directory/'runs'/(run_id+'.json'))
                    check_episode(retained['initial_state']['config'],world,retained['events'],retained['final_state'])
                    row=runner.run_episode(engine,case,world,policy,run_id,output,suite='exploratory_posthoc_diagnostic')
                    if normalized(row)!=normalized(retained):
                        raise AssertionError('Diagnostic reproduction mismatch: '+run_id)
                    fresh.append(row)
    if runner.summarize(fresh)['cells']!=original['cells']:
        raise AssertionError('Diagnostic summary mismatch')
    return {'status':'PASS','scope':'Exploratory post-hoc diagnostics; excluded from primary237.',
            'runs_reproduced':len(fresh),'native_model_participants':0,'canonical_recounts':len(fresh),
            'cases_sha256':frozen['cases_sha256']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=verify()
    runner.dump(args.output,result)
    print(json.dumps(result,indent=2))
