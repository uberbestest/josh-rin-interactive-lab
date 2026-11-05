"""Verify exact recorded support, joint posteriors, metrics, and model controls.

This verifier reconstructs P(truth=1 | root bits) by grouping raw joint mass,
not by using the closed-form posterior function. Same author, separate route.
"""
from __future__ import annotations
import csv, gzip, hashlib, json
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
import engine as E

HERE=Path(__file__).resolve().parent

def verify() -> dict:
    if not __debug__:
        raise RuntimeError('Run verification without -O: its checks use assertions.')
    results=json.loads((HERE/'results.json').read_text())
    assert results['protocol_sha256']==hashlib.sha256((HERE/'protocol.json').read_bytes()).hexdigest()
    cellmap={c.id:c for c in E.cells()}
    stored={c['id']:c for c in results['cells']}
    rows_by_cell=defaultdict(list)
    seen=set()
    with gzip.open(HERE/'histories.csv.gz','rt',encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f):
            key=(row['cell'],row['truth'],row['shared_fault'],row['local_errors'])
            assert key not in seen, ('duplicate',key)
            seen.add(key)
            rows_by_cell[row['cell']].append(row)
    posterior_checks=0
    for cid,cell in cellmap.items():
        rows=rows_by_cell[cid]
        expected={(str(r['truth']),str(r['shared_fault']),''.join(map(str,r['local_errors']))):r for r in E.histories(cell)}
        assert len(rows)==len(expected)
        group=defaultdict(lambda:[F(0),F(0)])
        reconstructed=[]
        for row in rows:
            r=expected[(row['truth'],row['shared_fault'],row['local_errors'])]
            assert F(row['weight'])==r['weight']
            assert row['root_bits']==''.join(map(str,r['bits']))
            group[row['root_bits']][int(row['truth'])]+=F(row['weight'])
            reconstructed.append(r)
        assert sum(sum(v) for v in group.values())==1
        for row in rows:
            w=group[row['root_bits']]
            independent=w[1]/sum(w)
            assert independent==F(row['p_shared_cause']),('posterior',cid,row['root_bits'])
            ps=E.predict([int(x) for x in row['root_bits']],cell.copies,cell.marginal,cell.shared)
            for rule in E.RULES:
                assert ps[rule]==F(row['p_'+rule])
                assert E.decide(ps[rule])==row['action_'+rule]
            assert cell.shared<=independent<=1-cell.shared
            posterior_checks+=1
        rebuilt=E.summarize(cell,reconstructed)
        assert rebuilt['metrics']==stored[cid]['metrics']
        m=rebuilt['metrics']
        for other in ('headcount','receipts'):
            assert F(m['shared_cause']['exact']['brier'])<=F(m[other]['exact']['brier'])
            assert F(m['shared_cause']['exact']['payoff'])>=F(m[other]['exact']['payoff'])
        if cell.shared==0:
            assert m['receipts']==m['shared_cause']
            if cell.topology=='ten_roots': assert m['headcount']==m['receipts']
    assert len(seen)==results['history_count']==45612
    assert results['rule_evaluations']==3*len(seen)
    receipt={'status':'PASS','cells':len(cellmap),'positive_probability_histories':len(seen),
        'joint_mass_posterior_checks':posterior_checks,'rule_evaluations':3*len(seen),
        'all_probability_masses_one':True,'all_marginal_accuracies_preserved':True,
        'all_metrics_reconstructed':True,'oracle_brier_and_utility_controls':True,
        'scope':'Same-author deterministic verification, not independent review.'}
    print(json.dumps(receipt,indent=2))
    return receipt

if __name__=='__main__': verify()
