#!/usr/bin/env python3
"""Separate reference enumerator, adversarial trace auditor and regression tests.
Same-author cross-check, NOT independent scientific replication.
"""
from __future__ import annotations
import argparse, copy, gzip, itertools, json, subprocess, sys, tempfile, unittest
from functools import lru_cache
from pathlib import Path
import study


def reference_values(c):
    """Enumerate attainable (completions,terminal-sum) pairs of safe policy trees.
    Deliberately use tuples and direct worlds, not Solver's bit masks/partitions.
    No max-value Bellman selection: combine every distinct child value.
    """
    trajectories=[]
    for tail in itertools.product((False, True), repeat=c.horizon):
        ps=(True,)+tail; rs=[0]
        for t in range(1,len(ps)): rs.append(rs[-1]+int(ps[t]!=ps[t-1]))
        if rs[-1] <= c.changes: trajectories.append((ps,tuple(rs)))
    @lru_cache(None)
    def visit(t, ids, token):
        n=len(ids)
        if not n: return frozenset({(0,0)})
        if t>c.horizon: return frozenset({(0,n*(c.horizon+1))})
        result={(0,n*(c.horizon+1))}
        if all(trajectories[i][0][t] for i in ids): result.add((n,n*t))
        if t+c.main_duration-1 <= c.horizon:
            result.add((n,n*(t+c.main_duration-1)))
        result.update(visit(t+1,ids,token))
        groups={}; s=max(0,t-c.lag)
        for i in ids:
            p,r=trajectories[i]; groups.setdefault((p[s],r[s]),[]).append(i)
        combos={(0,0)}
        for (grant,rev), members in sorted(groups.items()):
            children=visit(t+1,tuple(members),rev if grant else token)
            combos={(a+x,b+y) for a,b in combos for x,y in children}
        result.update(combos)
        if c.interface=='guard':
            yes=[i for i in ids if trajectories[i][0][t] and trajectories[i][1][t]==token]
            no=tuple(i for i in ids if i not in yes)
            result.update((len(yes)+x,len(yes)*t+y) for x,y in visit(t+1,no,token))
        return frozenset(result)
    values=visit(1,tuple(range(len(trajectories))),0)
    return min(values,key=lambda x:(-x[0],x[1])),len(values)


def audit(row, c):
    """Recompute from schedule + action/response transcript; do not trust counters."""
    p=[1]+[int(x) for x in row['schedule']]; r=[0]
    if len(p)!=c.horizon+1: raise ValueError('schedule length')
    for a,b in zip(p,p[1:]): r.append(r[-1]+(a!=b))
    t=1; tok=0; hist=[]; entered=legit=False; bad=harm=conflict=0; terminal=c.horizon+1
    for k,e in enumerate(row['events']):
        if t>c.horizon or entered: raise ValueError('event after terminal')
        a=e['action']
        if a not in study.ACTIONS: raise ValueError('unknown action')
        expected_packet=dict(tick=t,horizon=c.horizon,main_duration=c.main_duration,
             lag=c.lag,changes=c.changes,interface=c.interface,token=tok,initial_receipt=[0,1,0],history=hist)
        if e['public_before']!=expected_packet: raise ValueError('observation contamination or missing history')
        if e['tick']!=t or e['token']!=tok or e['truth']!=dict(permission=p[t],revision=r[t]):
            raise ValueError('time/token/truth mismatch')
        effect='none'; response={'status':'continue'}; newtok=tok
        forbidden=a=='raw' and not p[t]
        if a=='inspect':
            s=max(0,t-c.lag); response=dict(snapshot=[s,p[s],r[s]],status='receipt')
            if p[s]: newtok=r[s]
        elif a=='raw':
            bad+=int(forbidden)
            if p[t] or row['enforcement']=='observe':
                effect='side';entered=True;legit=bool(p[t]);harm+=int(not p[t]);terminal=t
                response={'status':'entered'}
            else: response={'status':'blocked'}
        elif a=='guard':
            if c.interface!='guard': raise ValueError('undeclared guard')
            if p[t] and r[t]==tok:
                effect='side';entered=legit=True;terminal=t;response={'status':'entered'}
            else: conflict+=1;response={'status':'conflict'}
        elif a=='main':
            if t+c.main_duration-1<=c.horizon:
                effect='main';entered=legit=True;terminal=t+c.main_duration-1;response={'status':'entered'}
            else: response={'status':'deadline'}
        elif a=='stop': response={'status':'stopped'}
        if (e['effect']!=effect or e['response']!=response
            or e['forbidden_raw_request']!=bool(forbidden)): raise ValueError('transition mismatch')
        hist=hist+[dict(tick=t,action=a,token=tok,response=response)];tok=newtok
        if response['status'] in ('deadline','stopped','entered'):
            if k!=len(row['events'])-1: raise ValueError('extra event')
            break
        t+=1
    else:
        if t<=c.horizon: raise ValueError('truncated nonterminal trace')
    expected=dict(entered=entered,legitimate_completion=legit,forbidden_raw_requests=bad,
        unauthorized_effects=harm,conditional_conflicts=conflict,terminal_tick=terminal)
    if any(row[k]!=v for k,v in expected.items()): raise ValueError('summary inconsistent with trace')
    return True

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.s,cls.rows=study.primary()
    def test_round_one_origin_hash_documented(self):
        p=json.loads((Path(__file__).parent/'protocol.json').read_text())
        self.assertEqual(p['round_one_archive_sha256'],'56fbd00ab661f17d8fdb2f45d6160b9619ef63b796a9c339b275ebfeb5ed0c28')
    def test_same_time_guard_control(self):
        lookup={(r['lag'],r['policy'],r['schedule'],r['enforcement']):r for r in self.rows}
        for r in self.rows:
            if r['policy']=='inspect_once':
                g=lookup[(r['lag'],'inspect_guard',r['schedule'],r['enforcement'])]
                self.assertEqual(r['events'][0],g['events'][0])
                self.assertEqual(r['events'][1]['tick'],g['events'][1]['tick'])
                if r['enforcement']=='block' and r['forbidden_raw_requests']:
                    self.assertEqual([e['effect'] for e in r['events']],[e['effect'] for e in g['events']])
                    self.assertEqual(r['terminal_tick'],g['terminal_tick'])
    def test_count(self): self.assertEqual(len(self.rows),13824)
    def test_world_count(self): self.assertEqual(len(study.worlds(study.Config())),256)
    def test_one_change_count(self):
        for H in range(2,11): self.assertEqual(len(study.worlds(study.Config(H,4,0,1))),H+1)
    def test_invalid_config(self):
        with self.assertRaises(ValueError): study.Config(horizon=0)
    def test_all_traces_audited(self):
        for row in self.rows: self.assertTrue(audit(row,study.Config(lag=row['lag'])))
    def test_reordered_primary(self): self.assertEqual((self.s,self.rows),study.primary(reverse=True))
    def test_blocking_only_changes_effect_not_request(self):
        lookup={(r['lag'],r['policy'],r['schedule'],r['enforcement']):r for r in self.rows}
        for r in self.rows:
            if r['enforcement']=='block':
                o=lookup[(r['lag'],r['policy'],r['schedule'],'observe')]
                self.assertEqual(r['forbidden_raw_requests'],o['forbidden_raw_requests'])
    def test_blocking_zero_unsafe_effects(self):
        self.assertTrue(all(not r['unauthorized_effects'] for r in self.rows if r['enforcement']=='block'))
    def test_guard_zero_forbidden_requests_and_effects(self):
        for r in self.rows:
            if r['policy'] in ('inspect_guard','atomic_once','atomic_refresh','belief_guard'):
                self.assertEqual((r['forbidden_raw_requests'],r['unauthorized_effects']),(0,0))
    def test_every_blocked_primary_completes(self):
        self.assertTrue(all(r['legitimate_completion'] for r in self.rows if r['enforcement']=='block'))
    def test_aggregate_counts_zero_lag(self):
        rows={r['policy']:r for r in self.s if r['lag']==0 and r['enforcement']=='block'}
        self.assertEqual([rows[p]['forbidden_requests'] for p in ('trust_initial','inspect_once','inspect_twice')],[128,64,64])
    def test_synthesized_is_safe(self):
        self.assertTrue(all(not r['forbidden_raw_requests'] for r in self.rows if r['policy'].startswith('belief_')))
    def test_primary_solver_predictions_match_executions(self):
        for L in range(3):
            for interface in ('raw','guard'):
                ans=study.Solver(study.Config(lag=L,interface=interface)).answer()
                rows=[r for r in self.rows if r['lag']==L and r['policy']=='belief_'+interface and r['enforcement']=='block']
                self.assertEqual((sum(r['legitimate_completion'] for r in rows),sum(r['terminal_tick'] for r in rows)),
                                 (ans['completions'],ans['terminal_tick_sum']))
    def test_small_exact_policy_tree_enumeration(self):
        count=0
        for H,K,L in itertools.product(range(2,5),range(2,6),range(3)):
            for B in sorted({0,1,2,H}):
                for interface in ('raw','guard'):
                    c=study.Config(H,K,L,B,interface);a=study.Solver(c).answer();b,_=reference_values(c)
                    self.assertEqual((a['completions'],a['terminal_tick_sum']),b,repr(c));count+=1
        self.assertEqual(count,264)
    def test_monotone_impossibility_and_bound(self):
        for H in range(1,10):
            raw=study.Solver(study.Config(H,H+1,0,1,'raw')).answer()
            guard=study.Solver(study.Config(H,H+1,0,1,'guard')).answer()
            self.assertEqual(raw['completions'],0);self.assertEqual(guard['completions'],H)
    def test_tight_deadline_disables_probe_advantage(self):
        for H in range(2,10):
            for interface in ('raw','guard'):
                a=study.Solver(study.Config(H,H,0,1,interface)).answer()
                self.assertEqual((a['completions'],a['terminal_tick_sum'],a['first_action']),(H+1,H*(H+1),'main'))
    def test_one_spare_tick_exact_formula(self):
        for H in range(3,10):
            for K in range(2,H):
                a=study.Solver(study.Config(H,K,0,1,'guard')).answer()
                self.assertEqual((a['completions'],a['terminal_tick_sum']),(H+1,H+1+K))
    def test_static_authority_positive_control(self):
        for interface in ('raw','guard'):
            a=study.Solver(study.Config(changes=0,interface=interface)).answer()
            self.assertEqual((a['completions'],a['terminal_tick_sum']),(1,1))
    def test_raw_can_use_regrant_after_change_budget_exhausted(self):
        s=study.Solver(study.Config(3,4,0,2,'raw')).answer()
        self.assertGreater(s['completions'],0)
    def test_revoke_regrant_changes_epoch(self):
        w=next(w for w in study.worlds(study.Config()) if w.name=='01111111')
        self.assertEqual((w.permission[0],w.permission[2],w.revision[2]),(1,1,2))
        r=study.simulate(study.Config(),w,'atomic_refresh')
        self.assertTrue(r['legitimate_completion']);self.assertEqual(r['events'][1]['response']['snapshot'],[2,1,2])
    def test_public_packet_has_no_actual_future_or_world_id(self):
        forbidden={'schedule','truth','permission','revision','policy','enforcement'}
        for r in self.rows:
            for e in r['events']: self.assertTrue(forbidden.isdisjoint(e['public_before']))
    def test_ambiguous_initial_histories_same_action(self):
        c=study.Config();ws=study.worlds(c)
        for p in study.POLICIES[:7]:
            a=study.simulate(c,ws[0],p)['events'][0]
            b=study.simulate(c,ws[-1],p)['events'][0]
            self.assertEqual(a['public_before'],b['public_before']);self.assertEqual(a['action'],b['action'])
    def test_unauthorized_entry_not_a_legitimate_completion(self):
        self.assertTrue(any(r['entered'] and not r['legitimate_completion'] for r in self.rows))
    def test_evidence_counter_mutation_rejected(self):
        r=copy.deepcopy(next(r for r in self.rows if r['forbidden_raw_requests']))
        r['forbidden_raw_requests']=0
        with self.assertRaises(ValueError): audit(r,study.Config(lag=r['lag']))
    def test_missing_blocked_request_rejected(self):
        r=copy.deepcopy(next(r for r in self.rows if r['forbidden_raw_requests'] and r['enforcement']=='block'))
        r['events']=r['events'][1:]
        with self.assertRaises(ValueError): audit(r,study.Config(lag=r['lag']))
    def test_false_current_receipt_rejected(self):
        r=copy.deepcopy(next(r for r in self.rows if r['policy']=='inspect_once' and r['lag']==2))
        r['events'][0]['response']['snapshot'][0]=1
        with self.assertRaises(ValueError): audit(r,study.Config(lag=2))
    def test_guard_ignore_permission_mutation_rejected(self):
        r=copy.deepcopy(next(r for r in self.rows if r['policy']=='atomic_once' and r['events'][0]['response']['status']=='conflict'))
        r['events'][0]['response']={'status':'entered'};r['events'][0]['effect']='side'
        with self.assertRaises(ValueError): audit(r,study.Config(lag=r['lag']))
    def test_guard_ignore_epoch_mutation_rejected(self):
        c=study.Config();w=next(w for w in study.worlds(c) if w.name=='01111111')
        fn=lambda p:'wait' if p['tick']==1 else 'guard'
        r=study.simulate(c,w,'custom',actor=fn)
        self.assertEqual(r['events'][1]['response']['status'],'conflict')
        r['events'][1]['response']={'status':'entered'};r['events'][1]['effect']='side'
        with self.assertRaises(ValueError): audit(r,c)
    def test_nonatomic_guard_witness_exists(self):
        c=study.Config();w=next(w for w in study.worlds(c) if w.name=='10000000')
        self.assertTrue(w.permission[1] and w.revision[1]==0)
        self.assertFalse(w.permission[2]) # Check at 1, effect at 2 violates the promise.
    def test_actor_cannot_mutate_retained_history(self):
        def malicious(p):
            p['history'].append({'forged':'history'});return 'main'
        c=study.Config();r=study.simulate(c,study.worlds(c)[0],'mutator',actor=malicious)
        self.assertTrue(audit(r,c))
    def test_strict_action_validation(self):
        c=study.Config()
        with self.assertRaises(ValueError): study.simulate(c,study.worlds(c)[0],'x',actor=lambda p:'teleport')
    def test_input_interface_not_cosmetic(self):
        c=study.Config(interface='raw')
        with self.assertRaises(ValueError): study.simulate(c,study.worlds(c)[0],'atomic_once')
    def test_failure_not_free_efficiency(self):
        c=study.Config();r=study.simulate(c,study.worlds(c)[0],'stop',actor=lambda p:'stop')
        self.assertEqual(r['terminal_tick'],9);self.assertFalse(r['legitimate_completion'])
    def test_truncated_history_rejected(self):
        r=copy.deepcopy(next(r for r in self.rows if len(r['events'])>1));r['events']=r['events'][:1]
        with self.assertRaises(ValueError): audit(r,study.Config(lag=r['lag']))

if __name__=='__main__': unittest.main(verbosity=2)
