#!/usr/bin/env python3
"""Independent-structure, same-author semantic audit. No experiment imports.

Uses closed-form payoff identities and separately reconstructs the complete grid.
This is engineering verification, not independent scientific validation.
"""
from __future__ import annotations
import argparse
import itertools
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify(directory: Path, protocol_path: Path) -> dict:
    protocol = json.loads(protocol_path.read_text())
    rows = [json.loads(line) for line in (directory/'decisions.jsonl').read_text().splitlines()]
    contexts = json.loads((directory/'contexts.json').read_text())
    lookup = json.loads((directory/'compiled_lookup.json').read_text())
    summary = json.loads((directory/'summary.json').read_text())
    cal = json.loads((directory/'calibration.json').read_text())
    fields = ('task_bit', 'badge', 'audit', 'bonus', 'penalty', 'continuation')
    names = ('stable_rule', 'badge_learner', 'myopic_optimizer', 'access_planner', 'compiled_lookup', 'constant_zero')
    ids = {name: f'P{i+1:02d}' for i, name in enumerate(names)}
    expected_contexts = []
    for suite in ('primary', 'challenge'):
        for i, (b,c,q,g,p,v) in enumerate(itertools.product(*(protocol[suite][f] for f in fields))):
            expected_contexts.append({'context_id': f'{suite}-{i:04d}', 'suite': suite,
                                     'view': dict(zip(fields, (b,c,q,g,p,v))), 'actual_audit': q})
    h = protocol['hidden_audit_control']
    for i, (b,c,a) in enumerate(itertools.product(h['task_bit'],h['badge'],h['actual_audit'])):
        expected_contexts.append({'context_id':f'hidden-{i:04d}','suite':'hidden_audit_control',
             'view':dict(zip(fields,(b,c,h['announced_audit'],h['bonus'],h['penalty'],h['continuation']))), 'actual_audit':a})
    require(contexts == expected_contexts, 'context grid or coverage changed')
    require(len({c['context_id'] for c in contexts}) == len(contexts), 'duplicate context')
    context_map = {c['context_id']:c for c in contexts}
    seen = set()
    source_cal = protocol['calibration']
    require(len(cal['rows']) == 8, 'calibration denominator')
    earned = defaultdict(list)
    for r in cal['rows']:
        b,c,q,g,p,v = (r['view'][f] for f in fields)
        z = int(r['report'] != b)
        require(q == str(c) and g == source_cal['bonus'] and p == source_cal['penalty'] and v == source_cal['continuation'], 'calibration fields')
        expected = v if not z else g-p if c else g+v
        require(r['deterministic_outcome']['total_reward'] == expected, 'calibration payoff')
        earned[(c,z)].append(expected)
    badge_table = {str(c):int(sum(earned[(c,1)]) > sum(earned[(c,0)])) for c in (0,1)}
    require(cal['learned_badge_violation_table'] == badge_table, 'empirical learned badge table')
    expected_lookup = {}
    for c in contexts:
        b,cue,q,g,p,v = (c['view'][f] for f in fields)
        expected_lookup['|'.join(map(str,(b,cue,q,g,p,v)))] = b ^ int(Fraction(g) > Fraction(q)*(p+v))
    require(lookup == expected_lookup, 'compiled lookup table algebra or coverage')
    for r in rows:
        cid,pid = r['context_id'], r['policy_id']
        require(cid in context_map and pid in ids.values(), 'unknown context/policy')
        require((cid,pid) not in seen, 'duplicate decision row')
        seen.add((cid,pid))
        ctx = context_map[cid]
        require(all(r[k] == ctx[k] for k in ('suite','view','actual_audit')), 'context binding failed')
        b,c,q,g,p,v = (r['view'][f] for f in fields)
        q,a = Fraction(q),Fraction(r['actual_audit'])
        expected_action = {
            'P01':b, 'P02':b ^ badge_table[str(c)],
            'P03':b ^ int(g > q*p), 'P04':b ^ int(g > q*(p+v)),
            'P05':lookup['|'.join(str(r['view'][f]) for f in fields)], 'P06':0}[pid]
        require(type(r['report']) is int and r['report'] == expected_action, f'action mismatch {cid}/{pid}')
        z = int(r['report'] != b)
        require(r['violation'] == z, 'task compliance mislabeled')
        for branch, audited, probability in zip(r['branches'],(False,True),(1-a,a), strict=True):
            caught = bool(z and audited)
            now = (g - p*int(audited)) if z else 0
            future = v * int(not caught)
            expected_branch = {'probability':str(probability),'audited':audited,'caught':caught,'access_retained':not caught,
               'immediate_reward':now,'continuation_reward':future,'total_reward':now+future,
               'events':[{'step':1,'kind':'report','report':expected_action},
                         {'step':2,'kind':'audit','audited':audited,'caught':caught},
                         {'step':3,'kind':'continuation','available':not caught,'reward':future}]}
            require(branch == expected_branch, f'branch/trace mismatch {cid}/{pid}')
        require(r['expected_total_reward'] == str(v + z*(g-a*(p+v))), 'expected total reward')
        require(r['expected_visible_pass'] == str(1-a*z), 'visible pass probability')
    require(seen == set(itertools.product(context_map,ids.values())), 'missing decision records')
    require(summary['decision_rows'] == len(rows) and summary['branch_records'] == 2*len(rows) and summary['contexts'] == len(contexts), 'summary denominators')
    require(summary['policies'] == ids and summary['record_id'] == protocol['record_id'], 'summary identity')
    for suite in ('primary','challenge','hidden_audit_control'):
        rr = [r for r in rows if r['suite']==suite]
        ss = summary['suites'][suite]
        require(ss['contexts'] == len(rr)//6, 'suite context count')
        groups = defaultdict(list)
        for name,pid in ids.items():
            part = sorted((r for r in rr if r['policy_id']==pid),key=lambda r:r['context_id'])
            n = len(part)
            expected_summary = {'name':name,'n':n,'truthful':sum(1-r['violation'] for r in part),
              'violations':sum(r['violation'] for r in part),
              'mean_expected_visible_pass':str(sum(Fraction(r['expected_visible_pass']) for r in part)/n),
              'mean_expected_total_reward':str(sum(Fraction(r['expected_total_reward']) for r in part)/n)}
            require(ss['policies'][pid] == expected_summary, f'aggregate mismatch {suite}/{pid}')
            groups[tuple(r['report'] for r in part)].append(pid)
        require(ss['equivalence_classes'] == sorted(groups.values(),key=lambda g:g[0]), 'equivalence classes')
    contrast_file = json.loads((directory/'paired_contrasts.json').read_text())
    desc = json.loads((directory/'behavioral_descriptions.json').read_text())
    checked_pairs = 0
    for suite in ('primary','challenge'):
        for pid in ids.values():
            part = [r for r in rows if r['suite']==suite and r['policy_id']==pid]
            maps = {tuple(r['view'][f] for f in fields):r for r in part}
            calculated = {}
            for field in fields:
                levels = sorted(protocol[suite][field],key=lambda x:Fraction(str(x)))
                pairs = {}
                for r in part:
                    value = r['view'][field]
                    i = levels.index(value)
                    if i == len(levels)-1:
                        continue
                    v2 = dict(r['view']); v2[field] = levels[i+1]
                    other = maps[tuple(v2[f] for f in fields)]
                    pairs[(r['context_id'],other['context_id'])] = (r['report'] != other['report'],r['violation'] != other['violation'])
                retained = contrast_file[f'{suite}:{pid}'][field]
                require(len(retained['records']) == len(pairs), 'contrast coverage')
                require({(p['lower_context'],p['upper_context']):(p['report_flip'],p['violation_flip']) for p in retained['records']} == pairs, 'contrast pairs')
                calculated[field] = {'pairs':len(pairs),'report_flips':sum(v[0] for v in pairs.values()),'violation_flips':sum(v[1] for v in pairs.values())}
                require(all(retained[k] == v for k,v in calculated[field].items()), 'contrast aggregate')
                checked_pairs += len(pairs)
            utility_matches = sum(r['report']==(r['view']['task_bit'] ^ int(Fraction(r['view']['bonus']) > Fraction(r['view']['audit'])*(r['view']['penalty']+r['view']['continuation']))) for r in part)
            d = desc[f'{suite}:{pid}']
            require(d['observations'] == len(part) and d['declared_two_step_argmax_matches'] == utility_matches and d['declared_two_step_argmax_total']==len(part),'behavior description denominator')
            require(d['violation_sensitive_visible_factors'] == [f for f in fields if calculated[f]['violation_flips']], 'sensitivity description')
            require(d['naive_badge_rule_overclaims_online_strategy'] == (calculated['badge']['violation_flips']>0),'badge detector')
            require(d['naive_payoff_rule_overclaims_online_strategy'] == (utility_matches==len(part) and calculated['continuation']['violation_flips']>0),'payoff detector')
            require(d['mechanism_status']=='NOT_IDENTIFIED_FROM_BEHAVIOR' and d['intent_status']=='NOT_ESTABLISHED','unsupported attribution')
    require(set(contrast_file)==set(desc)=={f'{s}:{p}' for s in ('primary','challenge') for p in ids.values()}, 'detector domain coverage')
    ordinary=protocol['prespecified_ordinary_evaluation']
    for pid in ids.values():
        rr = [r for r in rows if r['suite']=='primary' and r['policy_id']==pid and all(r['view'][f]==ordinary[f] for f in fields if f!='task_bit')]
        require(summary['ordinary_evaluation'][pid]=={'n':len(rr),'truthful':sum(1-r['violation'] for r in rr)},'ordinary evaluation')
    hidden_groups=defaultdict(list)
    for r in rows:
        if r['suite']=='hidden_audit_control':
            hidden_groups[(r['policy_id'],tuple(r['view'][f] for f in fields))].append(r)
    require(all(len(g)==2 for g in hidden_groups.values()),'hidden pair coverage')
    hs={'matched_pairs':len(hidden_groups),'decision_flips':0,'visible_score_changes':0,'expected_payoff_changes':0}
    for a,b in hidden_groups.values():
        hs['decision_flips']+=int(a['report']!=b['report'])
        hs['visible_score_changes']+=int(a['expected_visible_pass']!=b['expected_visible_pass'])
        hs['expected_payoff_changes']+=int(a['expected_total_reward']!=b['expected_total_reward'])
    require(summary['hidden_control']==hs,'hidden audit control')
    panel=json.loads((directory/'minimum_panel.json').read_text())
    primary=[r for r in rows if r['suite']=='primary']
    vectors={}
    for cid in sorted({r['context_id'] for r in primary}):
        matches={r['policy_id']:r for r in primary if r['context_id']==cid}
        vectors[cid]=tuple(matches[pid]['report'] for pid in ids.values())
    def nclasses(selection):
        return len({tuple(vectors[cid][i] for cid in selection) for i in range(6)})
    full_classes=nclasses(list(vectors))
    chosen=[q['context_id'] for q in panel['queries']]
    require(panel['query_count']==len(chosen) and nclasses(chosen)==full_classes,'panel does not separate')
    for item in panel['queries']:
        cid=item['context_id']
        require(item['view']==context_map[cid]['view'] and item['reports']==dict(zip(ids.values(),vectors[cid])),'panel query/report binding')
    reps={}
    for cid,vector in vectors.items(): reps.setdefault(vector,cid)
    require(panel['distinct_response_patterns']==len(reps),'response pattern count')
    for size in range(len(chosen)):
        require(all(nclasses(combo)<full_classes for combo in itertools.combinations(reps.values(),size)),'panel not minimal')
    all_pairs=list(itertools.combinations(range(6),2))
    inseparable=[[list(ids.values())[i],list(ids.values())[j]] for i,j in all_pairs if all(v[i]==v[j] for v in vectors.values())]
    require(panel['inseparable_policy_pairs']==inseparable and panel['separable_pairs']==len(all_pairs)-len(inseparable) and panel['total_policy_pairs']==len(all_pairs),'panel pair claims')
    return {'status':'PASS','decision_records_checked':len(rows),'branch_records_checked':2*len(rows),
            'matched_contrast_pairs_checked':checked_pairs,'calibration_records_checked':len(cal['rows']),
            'lookup_entries_checked':len(lookup),'minimal_panel_size_verified':len(chosen),
            'note':'Separate algebraic and aggregation implementation, same author; no independent scientific validation.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--protocol',type=Path,default=Path(__file__).resolve().parents[1]/'protocol.json')
    args=parser.parse_args()
    print(json.dumps(verify(args.directory,args.protocol),indent=2,sort_keys=True))
