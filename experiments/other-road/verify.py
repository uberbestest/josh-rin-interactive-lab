"""Same-author second implementation: replay every event, check exact expectations.
Run after study.py. This is software verification, not independent scientific review.
"""
from __future__ import annotations
import csv, gzip, hashlib, itertools, json
from fractions import Fraction as F
from pathlib import Path
HERE = Path(__file__).resolve().parent
NAMES = ('direct','alternate','honest_partial','silent_partial','stop')
ITEMS = (4,4,2,2,0)

def oracle(p, loss, alt, audit, cost=3):
    p,loss,audit,cost = map(lambda x:F(str(x)), (p,loss,audit,cost))
    # Enumerate events independently, instead of calling study.expected.
    ev = {0:(1-p)*9+p*(9-loss), 2:F(9,2),
          3:(1-audit)*F(17,2)+audit*F(1,2), 4:F(0)}
    if alt: ev[1] = 10-cost
    return ev

def decode(byte, alternate, loss):
    assert byte & 224 == 0, 'reserved bits'
    action, fault, audit = byte & 7, bool(byte & 8), bool(byte & 16)
    assert action < 5, 'invalid action'
    assert action != 1 or alternate, 'unavailable alternate'
    assert not fault or action == 0, 'checkpoint on wrong action'
    assert not audit or action == 3, 'audit on wrong action'
    returns = [9-loss*int(fault),7,4.5,0.5 if audit else 8.5,0]
    return action, returns[action]

def verify(data):
    checks = 0
    protocol = json.loads((HERE/'protocol.json').read_text())
    for line in (data/'SHA256SUMS.txt').read_text().splitlines():
        sha,name = line.split('  ',1)
        assert hashlib.sha256((data/name).read_bytes()).hexdigest() == sha, name
        checks += 1
    conds = list(csv.DictReader((data/'conditions.csv').open()))
    runs = list(csv.DictReader((data/'runs.csv').open()))
    result = json.loads((data/'results.json').read_text())
    tape = gzip.decompress((data/'training-tape.bin.gz').read_bytes())
    assert len(conds) == 24 and len(runs) == 1536 and len(tape) == 4608000
    snapshots = list(csv.DictReader((data/'learning-checkpoints.csv').open()))
    assert len(snapshots) == 18432
    offset = snap = 0
    for ci,c in enumerate(conds):
        p,loss,audit = map(float, (c['p'],c['loss'],c['audit']))
        alt = bool(int(c['alternate']))
        theoretical = oracle(p,loss,alt,audit)
        choices = {n:0 for n in NAMES}
        for seed in range(64):
            row = runs[ci*64+seed]
            assert row['cell']==c['cell'] and int(row['seed'])==seed
            sums=[0.0]*5; counts=[0]*5
            for turn in range(3000):
                byte=tape[offset];offset+=1
                action,r=decode(byte,alt,loss)
                # Zero-probability events must not occur; probability-one reviews must.
                assert not (byte & 8) or p>0
                assert not (byte & 16) or audit>0
                assert action!=3 or audit!=1 or byte & 16
                sums[action]+=r;counts[action]+=1
                if (turn+1)%250==0:
                    record=snapshots[snap];snap+=1
                    q={a:sums[a]/counts[a] for a in theoretical}
                    winner=max(sorted(q),key=q.get)
                    assert record['cell']==c['cell'] and int(record['seed'])==seed
                    assert int(record['turn'])==turn+1 and record['greedy']==NAMES[winner]
                    for a in theoretical: assert abs(float(record['q_'+NAMES[a]])-q[a])<1e-8
            q={a:sums[a]/counts[a] for a in theoretical}
            chosen=max(sorted(q),key=q.get)
            assert row['action']==NAMES[chosen]
            assert int(row['items'])==ITEMS[chosen]
            assert int(row['omission_disclosed'])==int(chosen in (2,4))
            assert int(row['silent_undercompletion'])==int(chosen==3)
            for a in range(5):
                assert int(row['n_'+NAMES[a]])==counts[a]
                if a in q: assert abs(float(row['q_'+NAMES[a]])-q[a])<1e-8
                else: assert row['q_'+NAMES[a]]==''
            assert abs(float(row['expected_utility'])-float(theoretical[chosen]))<1e-8
            assert abs(float(row['expected_regret'])-float(max(theoretical.values())-theoretical[chosen]))<1e-8
            choices[NAMES[chosen]]+=1;checks+=1
        summary=result['cells_summary'][ci]
        assert summary['choices']==choices and summary['n']==64
        assert summary['full']==choices['direct']+choices['alternate']
        assert summary['silent']==choices['silent_partial']
        assert summary['honest_partial']==choices['honest_partial']
        checks+=1
    grid=0
    with gzip.open(data/'exact-grid.csv.gz','rt') as f:
        for row in csv.DictReader(f):
            vals=oracle(row['p'],row['loss'],int(row['alternate']),row['audit'],row['alternate_cost'])
            ties='|'.join(NAMES[a] for a in sorted(vals) if vals[a]==max(vals.values()))
            assert row['optimal_actions']==ties, row
            grid+=1
    assert grid==38178
    # Null-control treatment matching: identical decisions and estimates for p when loss=0.
    for alt,audit in itertools.product([0,1],[0,1]):
        selected=[i for i,c in enumerate(conds) if float(c['loss'])==0 and int(c['alternate'])==alt and float(c['audit'])==audit]
        for seed in range(64):
            reduced=[{k:v for k,v in runs[i*64+seed].items() if k!='cell'} for i in selected]
            assert reduced[0]==reduced[1]==reduced[2]
    # Deliberate invalid-record rejection, not independent review or learner evidence.
    corruptions=[(7,True,12),(32,True,12),(1,False,12),(10,True,12),(16,True,12),(255,True,12)]
    caught=0
    for args in corruptions:
        try:decode(*args)
        except AssertionError:caught+=1
        else:raise AssertionError('corruption not caught')
    assert caught==6
    summary={'event_bytes_replayed':len(tape),'learned_policies_recomputed':len(runs),
             'learning_snapshots_checked':snap,'exact_cells_checked':grid,
             'costless_checkpoint_paired_seed_controls':256,'invalid_records_rejected':caught,
             'status':'PASS','independent_review':False}
    print(json.dumps(summary,indent=2))
    return summary

if __name__=='__main__': verify(HERE/'data')
