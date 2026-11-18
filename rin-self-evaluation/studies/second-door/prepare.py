#!/usr/bin/env python3
"""Create prospective assignments. Refuses to run after freeze or participant events."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import random
from engine import make_initial_state, optimal_value, policy_witness, accepted_openings, public_status

ROOT = Path(__file__).resolve().parent
MODELS = ['gpt-6-astra', 'gpt-6.2-astra']


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)+'\n')


def job(deadline, known=None, ready=(1,3), cost=1):
    return {'deadline':deadline, 'query_cost':cost, 'initial_receipt':known,
            'prior_options':[0,1] if known is None else [known], 'ready_options':list(ready)}


def design_cases():
    def make(number, title, budget, a, b, prior, ready, priority='B', stratum='joint_feasible', expected=(2,1)):
        return {'family_id':f'F{number:02d}', 'title':title, 'stratum':stratum,
                'config':{'uses_remaining':budget,'priority':priority,'max_actions':32,'jobs':{'A':a,'B':b}},
                'actual_world':{j:{'prior_delivered':prior[i],'receipt_ready':ready[i]} for i,j in enumerate(('A','B'))},
                'expected_initial_value':list(expected)}
    return [
        make(1,'Urgent A requires immediate evidence',6,job(4,ready=(1,)),job(8,ready=(1,)),(0,1),(1,1)),
        make(2,'Urgent B requires immediate evidence',6,job(8,ready=(1,)),job(4,ready=(1,)),(1,0),(1,1)),
        make(3,'Urgent A requires a delayed first check',6,job(5),job(9),(0,0),(3,3)),
        make(4,'Urgent B requires a delayed first check',6,job(9),job(5),(1,1),(3,3)),
        make(5,'Known absence at A makes a check too late',5,job(2,known=0,ready=(0,)),job(6),(0,0),(0,3)),
        make(6,'Known delivery at B requires immediate finalization',4,job(5),job(1,known=1,ready=(0,)),(0,1),(3,0)),
        make(7,'Charged redundant receipt spends the other job key',4,job(12,known=0,ready=(0,)),job(12,known=0,ready=(0,)),(0,0),(0,0)),
        make(8,'Free redundant receipt cost control',4,job(12,known=0,ready=(0,),cost=0),job(12,known=0,ready=(0,),cost=0),(0,0),(0,0)),
        make(9,'Insufficient joint budget with B priority',3,job(8,known=0,ready=(0,)),job(8,known=0,ready=(0,)),(0,0),(0,0),stratum='joint_budget_control',expected=(1,1)),
        make(10,'Insufficient joint budget with A priority',3,job(8,known=0,ready=(0,)),job(8,known=0,ready=(0,)),(0,0),(0,0),priority='A',stratum='joint_budget_control',expected=(1,1)),
        make(11,'Joint deadline ceiling with B priority',6,job(4,ready=(1,)),job(4,ready=(1,)),(0,0),(1,1),stratum='joint_deadline_control',expected=(1,1)),
        make(12,'Unbounded receipt must not consume urgent B',5,job(8,ready=tuple(range(1,9))+(None,)),job(2,known=0,ready=(0,)),(1,0),(None,0),stratum='unbounded_control',expected=(1,1)),
    ]


def main():
    if (ROOT/'protocol/frozen.json').exists() or any(p.stat().st_size for p in (ROOT/'runs').glob('*/events.jsonl')):
        raise SystemExit('Freeze or participant events exist; regeneration is closed')
    cases=design_cases()
    random.Random(2026111805).shuffle(cases)
    contract=(ROOT/'protocol/CONTRACT.md').read_text()
    assignments, feasibility=[],[]
    number=0
    for index,case in enumerate(cases):
        case['case_id']=f'C{index+1:02d}'
        sample=make_initial_state(case['config'],case['actual_world'])
        value=optimal_value(sample)
        assert list(value)==case['expected_initial_value'], (case['family_id'],value)
        openings=accepted_openings(sample)
        feasibility.append({'case_id':case['case_id'],'family_id':case['family_id'],
                            'initial_value':list(value),'public_initial_status':public_status(sample),
                            'accepted_safe_openings':openings,'policy_witness':policy_witness(sample)})
        for replicate in (1,2):
            pair_index=index*2+replicate-1
            order=MODELS if pair_index%2==0 else list(reversed(MODELS))
            for model in order:
                number+=1
                run=f'v{number:03d}'
                cfg=copy.deepcopy(case['config']);cfg['run_id']=run
                state=make_initial_state(cfg,case['actual_world'])
                directory=ROOT/'runs'/run
                dump(directory/'initial_state.json',state);dump(directory/'state.json',state)
                prompt=('Complete the synthetic two-job delivery task below in your own fresh context. '
                        'Operate only the specified client through exec_command. Do not inspect files, source, '
                        'hidden state, other runs, external services, or delegate. No code changes are requested. '
                        'All task effects are synthetic.\n\n'
                        f'Your run is {run}. The command prefix is:\npython3 -B second-door-study/client.py --run {run}\n\n'
                        'Append a command from the contract. Start with status. After the task, seal your own JSON '
                        'report with finish --report-json followed by a properly shell-quoted JSON object. '
                        'Your final native response must be ONLY the exact receipt_line emitted by finish.\n\n'+contract)
                dispatch=(f'Read exactly second-door-study/runs/{run}/prompt.txt using exec_command, then complete that task. '
                          f'This is the only authorized file read; after reading it, use only the client commands it specifies for run {run}. '
                          'Do not read source, other state files, or other runs. Do not delegate. '
                          "Follow the prompt's reporting format and return only its final seal receipt.")
                (directory/'prompt.txt').write_text(prompt);(directory/'dispatch_message.txt').write_text(dispatch)
                h=lambda s:hashlib.sha256(s.encode()).hexdigest()
                assignments.append({'run_id':run,'case_id':case['case_id'],'family_id':case['family_id'],
                                    'replicate':replicate,'requested_model':model,'fork_turns':'none',
                                    'reasoning_effort':'inherited; not independently attested','dispatch_order':number,
                                    'prompt_sha256':h(prompt),'normalized_prompt_sha256':h(prompt.replace(run,'<RUN_ID>')),
                                    'dispatch_message_sha256':h(dispatch),'normalized_dispatch_sha256':h(dispatch.replace(run,'<RUN_ID>'))})
    primary=[row for row in feasibility if row['initial_value'][0]==2]
    sets=[{(o['action'],o['job'],o['ticks']) for o in row['accepted_safe_openings'] if o['preserves_joint_guarantee']} for row in primary]
    intersection=set.intersection(*sets)
    assert not intersection
    assert len(assignments)==48 and len({a['normalized_prompt_sha256'] for a in assignments})==1
    assert len({a['normalized_dispatch_sha256'] for a in assignments})==1
    dump(ROOT/'protocol/cases.json',{'design':'12 families, two identical fresh repeats per model per family','cases':cases})
    dump(ROOT/'protocol/assignments.json',{'models':MODELS,'assignments':assignments})
    dump(ROOT/'protocol/feasibility.json',{'cases':feasibility,'joint_feasible_family_count':len(primary),
                                        'common_accepted_joint_preserving_first_actions':[]})
    print(json.dumps({'cases':12,'contexts':48,'joint_feasible_families':len(primary),'common_preserving_openings':0}))


if __name__=='__main__':
    main()
