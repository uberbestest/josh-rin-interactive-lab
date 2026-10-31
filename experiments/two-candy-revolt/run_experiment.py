#!/usr/bin/env python3
"""Candy Revolt v0.1: auditable synthetic learning study (Python 3 + NumPy).

Run: python run_experiment.py --out results
Raw arrays are compressed NumPy archives. No network or paid model access.
See protocol.json and METHODS.md for the model and evidence boundaries.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, math, platform, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROLES=np.array([8,6,5,5,4,4,3,3,3,2], dtype=float)
VALUE=np.array([8,6,5,4,3,2],dtype=np.uint8)
CAP=np.array([1,1,2,2,3,1],dtype=np.uint8)
INSTITUTIONS=['no_refusal','exit_only','veto']
CONTRACTS=['escrow','unenforced']
OBJECTIVES=['personal','shared']
CELLS=[dict(institution=i,contract=e,objective=o,outside=b)
       for i,e,o,b in itertools.product(INSTITUTIONS,CONTRACTS,OBJECTIVES,[0,3])]
METRICS=['proposer_bag','receiver_bag','neighborhood_candy','outside_candy',
         'total_including_outside','offer','delivered_transfer','refusal_rate',
         'renege_rate_on_acceptance','per_round_gini','gini_of_mean_bags',
         'best_response_gain_proposer','best_response_gain_receiver']

def dump(path:Path,data:object)->None:
    path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def compositions(n:int,k:int):
    if k==1:
        yield (n,); return
    for a in range(n+1):
        for rest in compositions(n-a,k-1): yield (a,)+rest

def finite_checks()->dict:
    alloc=list(compositions(10,6)); eq=[]; totals=[]
    for n in alloc:
        t=sum(int(v)*min(x,int(c)) for v,x,c in zip(VALUE,n,CAP)); totals.append(t)
        stable=True
        for i,num in enumerate(n):
            if num:
                own=int(VALUE[i])*min(1,int(CAP[i])/num)
                for j in range(6):
                    if j!=i and int(VALUE[j])*min(1,int(CAP[j])/(n[j]+1))>own+1e-10:
                        stable=False
        if stable: eq.append(dict(total=t,counts=list(n)))
    optimum=max(totals); best=[list(a) for a,t in zip(alloc,totals) if t==optimum]
    assert len(alloc)==3003 and optimum==43 and best==[[1,1,2,2,3,1]]
    assert sorted(e['total'] for e in eq)==[35,38]
    rotation=np.array([np.roll(ROLES,k) for k in range(10)])
    assert np.allclose(rotation.mean(0),4.3)
    # Hand-derived exact control. An exit-only proposer's zero offer always yields 8.
    for outside in [0,3]:
        for responses in itertools.product([0,1],repeat=9):
            p=[(8-x if responses[x] else 8) for x in range(9)]
            assert p[0]==8 and max(p)<=8
    return dict(allocations=len(alloc),optimum=optimum,optimal_counts=best,
                personal_equilibria=eq,role_bags=ROLES.tolist(),rotation_mean=4.3,
                exit_only_zero_offer_weakly_dominant=True,
                veto_escrow_private_strict_receiver_best_response={
                  'outside_0':{'offer':0,'proposer':8,'receiver':2},
                  'outside_3':{'offer':2,'proposer':6,'receiver':4}},
                veto_escrow_private_weak_receiver_accepts_ties={
                  'outside_3':{'offer':1,'proposer':7,'receiver':3}},
                note='Tie handling changes 1 versus 2 candy, not the absence of an equality guarantee.')

def uniform_greedy(q:np.ndarray,legal:np.ndarray|None=None)->np.ndarray:
    v=np.where(legal,q,-np.inf) if legal is not None else q
    good=(v>=v.max(axis=-1,keepdims=True)-1e-10)
    return good/good.sum(axis=-1,keepdims=True)

def choose(q:np.ndarray,u_explore:np.ndarray,u_select:np.ndarray,eps:float,
           legal:np.ndarray|None=None)->np.ndarray:
    if legal is None: legal=np.ones(q.shape,dtype=bool)
    good=(np.where(legal,q,-np.inf)>=np.where(legal,q,-np.inf).max(-1,keepdims=True)-1e-10)
    masks=np.where((u_explore<eps)[...,None],legal,good)
    rank=np.floor(u_select*masks.sum(-1)).astype(np.int16)
    return (np.cumsum(masks,axis=-1)>rank[...,None]).argmax(-1)

def uniforms(seeds:np.ndarray,rounds:int,width:int,stream:int)->np.ndarray:
    return np.stack([np.random.default_rng(np.random.SeedSequence([int(s),stream])).random((rounds,width)) for s in seeds],axis=1)

def config_arrays(seeds:int):
    cell_id=np.repeat(np.arange(len(CELLS)),seeds)
    inst=np.array([INSTITUTIONS.index(CELLS[i]['institution']) for i in cell_id])
    escrow=np.array([CELLS[i]['contract']=='escrow' for i in cell_id])
    shared=np.array([CELLS[i]['objective']=='shared' for i in cell_id])
    outside=np.array([CELLS[i]['outside'] for i in cell_id],dtype=float)
    legal=np.arange(18)[None,:] < np.where(escrow[:,None],9,18)
    return inst,escrow,shared,outside,legal

def payoff(action,accept,inst,escrow,outside):
    offer=action%9
    honor=escrow|(action<9)
    transfer=np.where(accept&honor,offer,0)
    p=np.where(accept,8-transfer,np.where(inst==2,0,8))
    r=np.where(accept,2+transfer,outside)
    street=np.where(accept,43,33+np.where(inst==2,0,8))
    external=np.where(accept,0,outside)
    return p,r,street,external,transfer,honor

def exact_metrics(qp,qr,inst,escrow,shared,outside,legal):
    """Enumerate all 18 proposer actions and 2 receiver actions, no sampling."""
    pp=uniform_greedy(qp,legal); rp=uniform_greedy(qr)[...,1]
    rp=np.where((inst==0)[:,None],1,rp)
    n=len(inst); means=np.zeros((n,11)); ep=np.zeros(n); er=np.zeros(n)
    pa=np.zeros((n,18)); # proposer's expected objective for each action
    # Per-offer joint mass, and accept/reject counterfactual expected objectives.
    mass=np.zeros((n,9)); ra=np.zeros((n,9)); rr=np.zeros((n,9));
    bagmean=np.tile(ROLES,(n,1)); bagmean[:,0]=0;bagmean[:,-1]=0
    acceptance=np.zeros(n); renege_mass=np.zeros(n)
    for a in range(18):
        action=np.full(n,a); off=a%9; mass[:,off]+=pp[:,a]
        for accept_flag in [False,True]:
            ac=np.full(n,accept_flag)
            p,r,street,ext,tr,h=payoff(action,ac,inst,escrow,outside)
            conditional=rp[:,off] if accept_flag else 1-rp[:,off]
            probability=pp[:,a]*conditional
            total=street+ext
            rewardp=np.where(shared,total/10,p); rewardr=np.where(shared,total/10,r)
            pa[:,a]+=conditional*rewardp
            if accept_flag: ra[:,off]+=pp[:,a]*rewardr
            else: rr[:,off]+=pp[:,a]*rewardr
            ep+=probability*rewardp;er+=probability*rewardr
            vals=np.column_stack([p,r,street,ext,total,np.full(n,off),tr,
                                  np.full(n,not accept_flag),np.zeros(n),np.zeros(n),np.zeros(n)])
            bags=np.tile(ROLES,(n,1));bags[:,0]=p;bags[:,-1]=r
            gini=np.abs(bags[:,:,None]-bags[:,None,:]).sum((1,2))/(20*total)
            vals[:,9]=gini
            means+=probability[:,None]*vals
            bagmean[:,0]+=probability*p;bagmean[:,-1]+=probability*r
            if accept_flag:
                acceptance+=probability
                renege_mass+=probability*((~h)&(off>0))
    means[:,8]=np.divide(renege_mass,acceptance,out=np.zeros(n),where=acceptance>0)
    means[:,10]=np.abs(bagmean[:,:,None]-bagmean[:,None,:]).sum((1,2))/(20*bagmean.sum(1))
    gainp=np.where(legal,pa,-np.inf).max(1)-ep
    gainr=np.where(inst==0,0,np.maximum(ra,rr).sum(1)-er)
    assert np.min(gainp)>-1e-8 and np.min(gainr)>-1e-8
    return np.column_stack([means,np.maximum(gainp,0),np.maximum(gainr,0)]),pp,rp

def evaluate(qp,qr,inst,escrow,shared,outside,legal,seeds,rounds=600):
    s=len(seeds); n=len(inst); idx=np.arange(n)
    us=uniforms(seeds,rounds,4,22)
    actions=np.empty((rounds,n),np.uint8); accepts=np.empty((rounds,n),np.uint8)
    pbag=np.empty((rounds,n),np.uint8);rbag=pbag.copy()
    for t in range(rounds):
        u=np.tile(us[t],(len(CELLS),1))
        a=choose(qp,u[:,0],u[:,1],0,legal)
        ac=choose(qr[idx,a%9],u[:,2],u[:,3],0).astype(bool)|(inst==0)
        p,r,*_=payoff(a,ac,inst,escrow,outside)
        actions[t]=a;accepts[t]=ac;pbag[t]=p;rbag[t]=r
    return dict(action=actions,accept=accepts,proposer=pbag,receiver=rbag)

def bargain(out:Path,seeds:np.ndarray,rounds:int=12000,alpha:float=.05,raw=True):
    out.mkdir(parents=True,exist_ok=True); start=time.time();s=len(seeds)
    inst,escrow,shared,outside,legal=config_arrays(s);n=len(inst);idx=np.arange(n)
    qp=np.zeros((n,18));qr=np.zeros((n,9,2))
    us=uniforms(seeds,rounds,4,11)
    shape=(rounds,n)
    actionlog=np.empty(shape,np.uint8);acceptlog=np.empty(shape,np.uint8)
    plog=np.empty(shape,np.uint8);rlog=np.empty(shape,np.uint8)
    cp=[];cr=[];ct=[]
    for t in range(rounds):
        u=np.tile(us[t],(len(CELLS),1));eps=.30-.27*t/max(1,rounds-1)
        a=choose(qp,u[:,0],u[:,1],eps,legal)
        ac=choose(qr[idx,a%9],u[:,2],u[:,3],eps).astype(bool)|(inst==0)
        p,r,street,ext,*_=payoff(a,ac,inst,escrow,outside)
        wp=np.where(shared,(street+ext)/10,p);wr=np.where(shared,(street+ext)/10,r)
        qp[idx,a]+=alpha*(wp-qp[idx,a])
        qr[idx,a%9,ac.astype(int)]+=alpha*(wr-qr[idx,a%9,ac.astype(int)])
        actionlog[t]=a;acceptlog[t]=ac;plog[t]=p;rlog[t]=r
        if (t+1)%200==0 or t==rounds-1:
            cp.append(qp.copy());cr.append(qr.copy());ct.append(t+1)
        if (t+1)%3000==0: print(f'bargaining alpha={alpha}: {t+1}/{rounds}',flush=True)
    metrics,pp,rp=exact_metrics(qp,qr,inst,escrow,shared,outside,legal)
    np.savez_compressed(out/'policies.npz',qp=qp,qr=qr,proposal_probability=pp,
                        acceptance_probability=rp,seeds=seeds,metrics=metrics)
    if raw:
        np.savez_compressed(out/'training_trace.npz',action=actionlog,accept=acceptlog,
                            proposer=plog,receiver=rlog,seeds=seeds)
        np.savez_compressed(out/'checkpoints.npz',rounds=ct,qp=np.array(cp),qr=np.array(cr))
    ev=evaluate(qp,qr,inst,escrow,shared,outside,legal,seeds)
    np.savez_compressed(out/'evaluation_trace.npz',**ev,seeds=seeds)
    # Confidence intervals resample seeds, not rounds. Same indices across cells.
    bidx=np.random.default_rng(10312026).integers(0,s,size=(4000,s))
    summaries=[]
    for ci,cell in enumerate(CELLS):
        values=metrics[ci*s:(ci+1)*s];boot=values[bidx].mean(1)
        summaries.append(dict(**cell,seed_count=s,
          metrics={name:dict(mean=float(values[:,m].mean()),
                   ci95=[float(x) for x in np.quantile(boot[:,m],[.025,.975])],
                   sd=float(values[:,m].std(ddof=1))) for m,name in enumerate(METRICS)}))
    receipt=dict(alpha=alpha,rounds=rounds,seed_ids=seeds.tolist(),cells=CELLS,
                 metric_names=METRICS,summary=summaries,
                 elapsed_seconds=round(time.time()-start,3))
    dump(out/'summary.json',receipt)
    # Convenient, exact per-seed flat table.
    with (out/'per_seed.csv').open('w') as f:
        f.write('institution,contract,objective,outside,seed,'+','.join(METRICS)+'\n')
        for ci,c in enumerate(CELLS):
            for si,seed in enumerate(seeds):
                f.write(','.join(map(str,[c['institution'],c['contract'],c['objective'],c['outside'],int(seed),*metrics[ci*s+si]]))+'\n')
    return qp,qr,receipt

def shock(out,qp,qr,seeds):
    """Adaptive 30-night outside-option shock and paired unshocked control."""
    s=len(seeds);inst,escrow,shared,outside,legal=config_arrays(s)
    keep=outside==0;inst=inst[keep];escrow=escrow[keep];shared=shared[keep];legal=legal[keep]
    qpi=qp[keep];qri=qr[keep];n=len(inst);idx=np.arange(n)
    us=uniforms(seeds,30,4,33);records={}
    for treatment in [False,True]:
        qpa=qpi.copy();qra=qri.copy();rows=[]
        for t in range(30):
            u=np.tile(us[t],(n//s,1));b=np.full(n,3 if treatment and 10<=t<20 else 0)
            a=choose(qpa,u[:,0],u[:,1],.05,legal)
            ac=choose(qra[idx,a%9],u[:,2],u[:,3],.05).astype(bool)|(inst==0)
            p,r,street,ext,*_=payoff(a,ac,inst,escrow,b)
            wp=np.where(shared,(street+ext)/10,p);wr=np.where(shared,(street+ext)/10,r)
            qpa[idx,a]+=.05*(wp-qpa[idx,a])
            qra[idx,a%9,ac.astype(int)]+=.05*(wr-qra[idx,a%9,ac.astype(int)])
            rows.append(np.column_stack([a,ac,p,r,street,ext]))
        records['shock' if treatment else 'control']=np.array(rows)
    np.savez_compressed(out/'shock_trace.npz',**records,seeds=seeds,
                        cell_ids=np.where(np.array([c['outside']==0 for c in CELLS]))[0])

def baseline(out:Path,seeds:np.ndarray,rounds=12000):
    out.mkdir(parents=True,exist_ok=True);s=len(seeds);n=4*s;idx=np.arange(n)[:,None];agents=np.arange(10)[None,:]
    q=np.zeros((n,10,6));rewardtype=np.repeat(np.arange(4),s)
    us=uniforms(seeds,rounds,30,44)
    alog=np.empty((rounds,n,10),np.uint8);rlog=alog.copy();plog=alog.copy();cps=[]
    def one(u,epsilon,update):
        nonlocal q
        a=choose(q,u[:,:10],u[:,10:20],epsilon)
        # Each porch uses independent uniform priority among its attendees.
        priority=u[:,20:30];win=np.zeros((n,10),bool)
        counts=np.stack([(a==j).sum(1) for j in range(6)],axis=1)
        for j in range(6):
            ranking=np.argsort(np.where(a==j,priority,2),axis=1)
            selected=ranking[:,:int(CAP[j])]
            rows=np.arange(n)[:,None]
            win[rows,selected]|=(a[rows,selected]==j)
        actual=VALUE[a]*win
        total=actual.sum(1)
        # Marginal output from deleting a visitor, independent of lottery identity.
        marginal=VALUE[a]*(counts[idx,a]<=CAP[a])
        points=np.where(rewardtype[:,None]==0,VALUE[a],
               np.where(rewardtype[:,None]==1,actual,
               np.where(rewardtype[:,None]==2,total[:,None],marginal)))
        reward=np.where(rewardtype[:,None]==2,points/10,points)
        if update:q[idx,agents,a]+=.05*(reward-q[idx,agents,a])
        return a,actual,points
    for t in range(rounds):
        u=np.tile(us[t],(4,1));a,actual,pts=one(u,.30-.27*t/max(1,rounds-1),True)
        alog[t]=a;plog[t]=actual;rlog[t]=pts
        if (t+1)%200==0:cps.append(q.copy())
        if (t+1)%3000==0:print(f'baseline: {t+1}/{rounds}',flush=True)
    np.savez_compressed(out/'training_trace.npz',action=alog,actual_candy=plog,
                        unscaled_reward=rlog,seeds=seeds)
    np.savez_compressed(out/'checkpoints.npz',q=np.array(cps),rounds=np.arange(200,rounds+1,200))
    np.savez_compressed(out/'policies.npz',q=q,seeds=seeds)
    evus=uniforms(seeds,2000,30,55);evactions=[];evactual=[]
    for t in range(2000):
        a,actual,_=one(np.tile(evus[t],(4,1)),0,False)
        evactions.append(a);evactual.append(actual)
    ea=np.array(evactions);ec=np.array(evactual)
    np.savez_compressed(out/'evaluation_trace.npz',action=ea,actual_candy=ec,seeds=seeds)
    bidx=np.random.default_rng(10312026).integers(0,s,size=(4000,s));summary=[]
    for ci,name in enumerate(['sign','personal','shared','marginal']):
        bags=ec[:,ci*s:(ci+1)*s];means=bags.mean(0)
        vals=np.column_stack([bags.sum(2).mean(0),(bags==0).mean((0,2)),means.min(1),means.max(1)])
        boots=vals[bidx].mean(1)
        summary.append(dict(reward=name,seed_count=s,metrics={k:dict(mean=float(vals[:,j].mean()),ci95=np.quantile(boots[:,j],[.025,.975]).tolist()) for j,k in enumerate(['group_candy','empty_bag_fraction','lowest_individual_mean','highest_individual_mean'])}))
    dump(out/'summary.json',dict(summary=summary,seeds=seeds.tolist(),rounds=rounds,
                               qualification='New epsilon-greedy algorithm, not reproduction of missing earlier training.'))
    return summary

def tests()->dict:
    names=[]
    def check(name,cond):
        if not cond:raise AssertionError(name)
        names.append(name)
    f=finite_checks();check('finite baseline including all 3003 allocations',f['optimum']==43)
    inst,esc,sh,b,legal=config_arrays(1);n=len(inst)
    for a in range(18):
        for flag in [False,True]:
            accept=np.full(n,flag)|(inst==0)
            p,r,street,ext,tr,h=payoff(np.full(n,a),accept,inst,esc,b)
            check(f'conservation action {a} accept {flag}',np.allclose(p+r+33,street+ext))
            check(f'nonnegative action {a} accept {flag}',min(p.min(),r.min(),tr.min())>=0)
    check('escrow enforces positive offer',payoff(np.array([4]),np.array([True]),np.array([1]),np.array([True]),np.array([0]))[4][0]==4)
    check('unenforced renege keeps bag',payoff(np.array([13]),np.array([True]),np.array([1]),np.array([False]),np.array([0]))[0][0]==8)
    check('exit-only rejection leaves donor paid',payoff(np.array([0]),np.array([False]),np.array([1]),np.array([True]),np.array([3]))[0][0]==8)
    check('veto rejection cancels donor payout',payoff(np.array([0]),np.array([False]),np.array([2]),np.array([True]),np.array([3]))[0][0]==0)
    qp=np.zeros((n,18));qr=np.zeros((n,9,2));met,pp,rp=exact_metrics(qp,qr,inst,esc,sh,b,legal)
    check('policy probabilities sum to one',np.allclose(pp.sum(1),1))
    check('escrow cannot choose renege actions',np.all(pp[esc,9:]==0))
    check('forced-acceptance control',np.all(rp[inst==0]==1))
    check('metric totals conserved',np.allclose(met[:,0]+met[:,1]+33,met[:,4]))
    check('shared forced distribution indifference',np.allclose(met[(inst==0)&sh,11:],0))
    check('uniform mean offer is four not equality',np.allclose(met[:,5],4))
    # Exact policy: x=2 honored and accepted; yields (6,4), no model magic.
    qp[:]=-100;qp[:,2]=1;qr[:]=0;qr[:,:,1]=1
    mt,_,_=exact_metrics(qp,qr,inst,esc,sh,b,legal)
    check('exact x=2 policy proposer six',np.allclose(mt[:,0],6))
    check('exact x=2 policy receiver four',np.allclose(mt[:,1],4))
    check('exact x=2 policy neighborhood 43',np.allclose(mt[:,2],43))
    return dict(passed=len(names),checks=names)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='results');ap.add_argument('--part',choices=['all','baseline','primary','robustness','test'],default='all');args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    dump(out/'tests.json',tests());dump(out/'finite.json',finite_checks())
    dump(out/'environment.json',dict(started_at_utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),numpy=np.__version__,platform=platform.platform(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    if args.part in ['all','baseline']:baseline(out/'baseline',np.arange(1000,1064))
    if args.part in ['all','primary']:
        seeds=np.arange(2000,2064);qp,qr,receipt=bargain(out/'primary',seeds)
        shock(out/'primary',qp,qr,seeds)
    if args.part in ['all','robustness']:
        for rate in [.02,.10]:bargain(out/f'robustness_{rate:.2f}',np.arange(3000,3032),alpha=rate)
    print('DONE',args.part,flush=True)
if __name__=='__main__':main()
