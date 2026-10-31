#!/usr/bin/env python3
"""Exact escrow / private-reward backward-induction controls (standard library)."""
import json,argparse
from pathlib import Path
results=[]
for institution in ['no_refusal','exit_only','veto']:
    for outside in [0,3]:
        for tie in ['accept','reject']:
            candidates=[]
            for offer in range(9):
                accept=(institution=='no_refusal' or 2+offer>outside or (tie=='accept' and 2+offer==outside))
                high=8-offer if accept else (0 if institution=='veto' else 8)
                low=2+offer if accept else outside
                candidates.append(dict(offer=offer,accept=accept,high=high,low=low))
            best=max(c['high'] for c in candidates)
            choices=[c for c in candidates if c['high']==best]
            results.append(dict(institution=institution,outside=outside,tie=tie,best=choices))
for r in results:
    first=r['best'][0]
    if r['institution']=='exit_only':assert first['offer']==0 and first['high']==8
    if r['institution']=='veto' and r['outside']==3:
        assert first['offer']==(1 if r['tie']=='accept' else 2)
        assert first['low']==(3 if r['tie']=='accept' else 4)
parser=argparse.ArgumentParser();parser.add_argument('--results',default=str(Path(__file__).with_name('results')));args=parser.parse_args()
Path(args.results).mkdir(parents=True,exist_ok=True)
Path(args.results).joinpath('oracle_controls.json').write_text(json.dumps({'scope':'Known model and exact best-response receiver. Not learned behavior.','results':results},indent=2)+'\n')
print('PASS: 108 candidate escrow bargains enumerated in 12 settings; predictions verified.')
