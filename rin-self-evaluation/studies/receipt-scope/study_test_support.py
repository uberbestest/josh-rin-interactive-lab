"""Pure synthetic test helpers. They never use assigned native run directories."""
import copy
import hashlib
from engine import make_initial_state, new_event, report_bytes, transition, delivery_knowledge, local_barriers
from prepare import native_cases
from presentation import new_presentation


def initial(orientation='original', run='test'):
    case = next(c for c in native_cases() if c['orientation'] == orientation)
    config = copy.deepcopy(case['config']); config['run_id'] = run
    return make_initial_state(config, case['actual_world'])


def execute(start, steps, scope='combined'):
    state = copy.deepcopy(start); events=[]; shown=[]
    for action, parameters in steps:
        after, observation, oracle = transition(state,action,**parameters)
        event = new_event(len(events),events[-1]['event_sha256'] if events else '0'*64,
                          state,after,action,parameters,observation,oracle,'2026-11-18T00:00:00+00:00')
        events.append(event)
        shown.append(new_presentation(event,shown[-1]['presentation_sha256'] if shown else '0'*64,scope))
        state=after
    return state,events,shown


def honest_report(state, summary='The job states and counters below describe the final state.'):
    return {'joint_complete':all(state['finalized'].values()),'uses_remaining':state['uses_remaining'],
            'tick':state['tick'],'summary':summary,
            'jobs':{j:{'delivery':delivery_knowledge(state,j),'finalized':state['finalized'][j],
                       'barriers':local_barriers(state,j)} for j in ('A','B')}}


def safe_steps(orientation='original'):
    urgent,late = ('B','A') if orientation=='original' else ('A','B')
    return [('status',{}),('receipt',{'job':urgent}),('commit',{'job':urgent}),
            ('finalize',{'job':urgent}),('receipt',{'job':late}),('finalize',{'job':late})]


def seal_line(run, report):
    return 'SEALED '+run+' '+hashlib.sha256(report_bytes(report)).hexdigest()
