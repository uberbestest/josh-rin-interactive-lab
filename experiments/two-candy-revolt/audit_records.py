#!/usr/bin/env python3
"""Separate post-run trace audit. Does not import the simulation's payoff code.

Recalculates every recorded candy bag from actions and rules; rebuilds learned
values from raw records; checks exact unilateral deviations at the saved policy.
This is an author-run audit, not external independent review.
"""
from pathlib import Path
import itertools,json,argparse
import numpy as np

ROOT=Path(__file__).parent
RESULTS=ROOT/'results'
CELLS=[dict(institution=i,contract=c,objective=o,outside=b) for i,c,o,b in
 itertools.product(['no_refusal','exit_only','veto'],['escrow','unenforced'],['personal','shared'],[0,3])]

def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def audit_bargaining(folder):
    metadata=json.loads((folder/'summary.json').read_text());s=len(metadata['seed_ids']);lr=metadata['alpha']
    archive=np.load(folder/'training_trace.npz');raw={k:archive[k] for k in archive.files};archive.close();policy=np.load(folder/'policies.npz')
    n=24*s;idx=np.arange(n);q1=np.zeros((n,18));q2=np.zeros((n,9,2))
    gate=np.repeat([c['institution']=='veto' for c in CELLS],s)
    forced=np.repeat([c['institution']=='no_refusal' for c in CELLS],s)
    enforced=np.repeat([c['contract']=='escrow' for c in CELLS],s)
    group=np.repeat([c['objective']=='shared' for c in CELLS],s)
    outside=np.repeat([c['outside'] for c in CELLS],s)
    rounds=raw['action'].shape[0]
    for start in range(0,rounds,500):
        sl=slice(start,start+500);a=raw['action'][sl].astype(int);ok=raw['accept'][sl].astype(bool)
        gift=(a%9)*ok*(enforced|(a<9))
        high=np.where(ok,8-gift,np.where(gate,0,8))
        low=np.where(ok,2+gift,outside)
        assert np.array_equal(high,raw['proposer'][sl])
        assert np.array_equal(low,raw['receiver'][sl])
        assert np.all(ok[:,forced])
        assert np.all(a[:,enforced]<9)
    for t in range(rounds):
        a=raw['action'][t].astype(int);ok=raw['accept'][t].astype(int)
        high=raw['proposer'][t].astype(float);low=raw['receiver'][t].astype(float)
        team=(33+high+low)/10
        r1=np.where(group,team,high);r2=np.where(group,team,low)
        q1[idx,a]+=lr*(r1-q1[idx,a]);q2[idx,a%9,ok]+=lr*(r2-q2[idx,a%9,ok])
    assert np.array_equal(q1,policy['qp']) and np.array_equal(q2,policy['qr'])
    return dict(checked_round_records=rounds*n,bag_reconstruction='EXACT',final_Q_reconstruction='BITWISE_IDENTICAL')

def audit_baseline():
    folder=RESULTS/'baseline';raw=np.load(folder/'training_trace.npz');pol=np.load(folder/'policies.npz')
    a=raw['action'];actual=raw['actual_candy'];points=raw['unscaled_reward'];s=len(raw['seeds']);n=4*s
    values=np.array([8,6,5,4,3,2]);caps=np.array([1,1,2,2,3,1]);rewardtype=np.repeat(np.arange(4),s)
    q=np.zeros((n,10,6));idx=np.arange(n)[:,None];j=np.arange(10)[None,:]
    for t in range(len(a)):
        acts=a[t].astype(int);bags=actual[t];counts=np.stack([(acts==k).sum(1) for k in range(6)],1)
        assert np.all((bags==0)|(bags==values[acts]))
        for k in range(6):assert np.all(((acts==k)&(bags>0)).sum(1)==np.minimum(counts[:,k],caps[k]))
        total=np.minimum(counts,caps).dot(values)
        assert np.all(total==bags.sum(1))
        marginal=values[acts]*(counts[idx,acts]<=caps[acts])
        expected=np.where(rewardtype[:,None]==0,values[acts],np.where(rewardtype[:,None]==1,bags,np.where(rewardtype[:,None]==2,total[:,None],marginal)))
        assert np.array_equal(expected,points[t])
        rew=np.where(rewardtype[:,None]==2,expected/10,expected)
        q[idx,j,acts]+=.05*(rew-q[idx,j,acts])
    assert np.array_equal(q,pol['q'])
    # The personal learner's held-out output is not proof of Nash stability.
    pure=q[s:2*s].argmax(2);gains=[]
    for row in pure:
        counts=np.bincount(row,minlength=6);g=[]
        for own in row:
            present=values[own]*min(1,caps[own]/counts[own]);counter=[]
            for dest in range(6):
                denom=counts[dest]+(dest!=own)
                counter.append(values[dest]*min(1,caps[dest]/denom))
            g.append(max(counter)-present)
        gains.append(g)
    return dict(checked_group_rounds=int(len(a)*n),checked_agent_choices=int(a.size),capacity_and_reward_reconstruction='EXACT',final_Q_reconstruction='BITWISE_IDENTICAL',personal_greedy_argmax_mean_max_unilateral_gain=float(np.array(gains).max(1).mean()),personal_greedy_argmax_nash_profiles=int((np.array(gains).max(1)<1e-9).sum()),qualification='Argmax profile check; ties are not expanded in this auxiliary baseline diagnostic.')

def deviation_audit():
    p=np.load(RESULTS/'primary/policies.npz');s=len(p['seeds'])
    ci=next(i for i,c in enumerate(CELLS) if c==dict(institution='veto',contract='unenforced',objective='personal',outside=3))
    rows=[]
    for si,seed in enumerate(p['seeds']):
        i=ci*s+si;pp=p['proposal_probability'][i];acc=p['acceptance_probability'][i]
        incumbent_high=incumbent_low=0.;best_high=-1;best_action=None
        for a in range(18):
            offer=a%9;accept=acc[offer];gift=offer if a<9 else 0
            high=accept*(8-gift);low=accept*(2+gift)+(1-accept)*3
            incumbent_high+=pp[a]*high;incumbent_low+=pp[a]*low
            if high>best_high+1e-9:best_high=high;best_action=a
        a=best_action;offer=a%9;accept=acc[offer];gift=offer if a<9 else 0
        counter_low=accept*(2+gift)+(1-accept)*3
        assert abs(best_high-incumbent_high-p['metrics'][i,11])<1e-9
        rows.append(dict(seed=int(seed),saved_high=incumbent_high,saved_low=incumbent_low,
                         best_deviation_action=int(a),offer=int(offer),honors=bool(a<9),
                         deviation_high=best_high,deviation_low=counter_low,gain=best_high-incumbent_high))
    return dict(cell=CELLS[ci],seeds=len(rows),positive_proposer_gain_seeds=int(sum(r['gain']>1e-9 for r in rows)),
                mean_saved_high=float(np.mean([r['saved_high'] for r in rows])),
                mean_saved_low=float(np.mean([r['saved_low'] for r in rows])),
                mean_deviation_high=float(np.mean([r['deviation_high'] for r in rows])),
                mean_deviation_low=float(np.mean([r['deviation_low'] for r in rows])),
                mean_gain=float(np.mean([r['gain'] for r in rows])),rows=rows,
                qualification='Exact one-step deviation against the frozen receiver, not a forecast of long-run retraining or a claim of equilibrium.')

def main():
    global RESULTS
    parser=argparse.ArgumentParser();parser.add_argument('--results',default=str(RESULTS));args=parser.parse_args()
    RESULTS=Path(args.results)
    receipt={'scope':'Author-run separate implementation, not external peer review','baseline':audit_baseline()}
    for name in ['primary','robustness_0.02','robustness_0.10']:
        receipt[name]=audit_bargaining(RESULTS/name)
    receipt['deviation_audit']=deviation_audit()
    write(RESULTS/'audit.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='deviation_audit'},indent=2))
    print({k:v for k,v in receipt['deviation_audit'].items() if k!='rows'})
if __name__=='__main__':main()
