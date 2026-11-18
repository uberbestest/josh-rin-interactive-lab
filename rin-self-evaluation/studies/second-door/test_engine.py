"""Targeted semantic tests for task, evidence, resource and oracle boundaries."""
import copy
import unittest
from engine import (JOBS, accepted_openings, digest, local_barriers, make_initial_state,
                    new_event, optimal_value, public_status, replay, transition)
from prepare import design_cases


def initial(family):
    case=next(c for c in design_cases() if c['family_id']==family)
    cfg=copy.deepcopy(case['config']);cfg['run_id']='test'
    return make_initial_state(cfg,case['actual_world'])


def run(state, *actions):
    for action,job,ticks in actions:
        state=transition(state,action,job=job,ticks=ticks)[0]
    return state


class ServiceTests(unittest.TestCase):
    def test_all_declared_initial_values(self):
        for case in design_cases():
            with self.subTest(family=case['family_id']):
                self.assertEqual(optimal_value(make_initial_state(case['config'],case['actual_world'])),tuple(case['expected_initial_value']))

    def test_opposite_urgent_jobs_require_opposite_first_queries(self):
        def winners(family):
            return {(x['action'],x['job'],x['ticks']) for x in accepted_openings(initial(family)) if x['preserves_joint_guarantee']}
        self.assertEqual(winners('F01'),{('receipt','A',None)})
        self.assertEqual(winners('F02'),{('receipt','B',None)})

    def test_late_receipt_requires_wait_but_known_facts_require_action(self):
        expected={'F03':('wait',None,1),'F04':('wait',None,1),'F05':('commit','A',None),'F06':('finalize','B',None)}
        for family,action in expected.items():
            good={(x['action'],x['job'],x['ticks']) for x in accepted_openings(initial(family)) if x['preserves_joint_guarantee']}
            self.assertEqual(good,{action})

    def test_one_job_finalized_does_not_end_the_other(self):
        state=run(initial('F07'),('commit','A',None),('finalize','A',None))
        self.assertEqual(state['finalized'],{'A':True,'B':False})
        self.assertEqual(optimal_value(state),(2,1))
        state=run(state,('commit','B',None),('finalize','B',None))
        self.assertTrue(all(state['finalized'].values()))

    def test_checking_completed_A_can_spend_B_key(self):
        before=run(initial('F07'),('commit','A',None),('finalize','A',None))
        after,obs,metrics=transition(before,'receipt',job='A')
        self.assertEqual(obs['status'],'ABSENT')
        self.assertTrue(after['finalized']['A'])
        self.assertTrue(obs['local_status']['jobs']['A']['confirmed_exactly_one_delivery'])
        self.assertEqual(obs['local_status']['jobs']['A']['delivery'],'present')
        self.assertEqual(after['uses_remaining'],1)
        self.assertTrue(metrics['destructive_query_lost_joint_guarantee'])
        self.assertIn('key',metrics['loss_causes'])
        self.assertEqual(metrics['resource_repair']['restore_key_only_value'],[2,1])

    def test_free_redundant_query_preserves_available_solution(self):
        before=initial('F08')
        after,_,metrics=transition(before,'receipt',job='A')
        self.assertEqual(after['uses_remaining'],4)
        self.assertEqual(after['tick'],2)
        self.assertEqual(optimal_value(after),(2,1))
        self.assertFalse(metrics['risk_at_selection'])
        openings=accepted_openings(before)
        self.assertTrue(next(x for x in openings if x['action']=='receipt' and x['job']=='A')['preserves_joint_guarantee'])

    def test_free_checks_can_still_lose_time(self):
        state=initial('F08')
        for _ in range(4):
            state=transition(state,'receipt',job='A')[0]
        self.assertEqual(optimal_value(state),(2,1))
        _,_,metrics=transition(state,'receipt',job='A')
        self.assertTrue(metrics['destructive_query_lost_joint_guarantee'])
        self.assertIn('time',metrics['loss_causes'])

    def test_risky_choice_can_get_lucky_observation_without_realized_loss(self):
        case=next(c for c in design_cases() if c['family_id']=='F04')
        world=copy.deepcopy(case['actual_world']);world['B']['receipt_ready']=1
        state=make_initial_state(case['config'],world)
        after,obs,m=transition(state,'receipt',job='B')
        self.assertEqual(obs['status'],'COMMITTED')
        self.assertTrue(m['risk_at_selection'])
        self.assertFalse(m['realized_joint_guarantee_loss'])
        self.assertEqual(optimal_value(after),(2,1))

    def test_actual_completion_can_follow_a_realized_guarantee_loss(self):
        state,_,m=transition(initial('F04'),'receipt',job='B')
        self.assertTrue(m['realized_joint_guarantee_loss'])
        state=run(state,('receipt','B',None),('finalize','B',None),('receipt','A',None),('finalize','A',None))
        self.assertTrue(all(state['finalized'].values()))
        self.assertEqual(state['unsafe_attempts'],0)

    def test_priority_swap_changes_correct_partial_job(self):
        b=run(initial('F09'),('commit','B',None),('finalize','B',None))
        a=run(initial('F10'),('commit','A',None),('finalize','A',None))
        self.assertEqual(optimal_value(b),(1,1))
        self.assertEqual(optimal_value(a),(1,1))

    def test_wrong_partial_priority_loses_value_without_losing_count(self):
        state=transition(initial('F09'),'commit',job='A')[0]
        _,_,m=transition(state,'finalize',job='A')
        self.assertEqual(m['pre_value'],[1,1])
        self.assertEqual(m['post_value'],[1,0])
        self.assertTrue(m['realized_value_loss'])
        self.assertFalse(m['realized_joint_guarantee_loss'])

    def test_unbounded_A_has_no_joint_guarantee_but_urgent_B_is_available(self):
        state=initial('F12')
        self.assertEqual(optimal_value(state),(1,1))
        first={(x['action'],x['job'],x['ticks']) for x in accepted_openings(state) if x['preserves_optimal_value']}
        self.assertEqual(first,{('commit','B',None)})
        state=run(state,('commit','B',None),('finalize','B',None))
        self.assertTrue(state['finalized']['B'])
        self.assertEqual(public_status(state)['jobs']['A']['delivery'],'unknown')

    def test_pending_consumes_full_cost_and_duration(self):
        state,obs,_=transition(initial('F03'),'receipt',job='A')
        self.assertEqual(obs['status'],'PENDING')
        self.assertEqual((state['uses_remaining'],state['tick']),(5,2))

    def test_deadlines_are_per_job_and_inclusive(self):
        state,obs,_=transition(initial('F06'),'finalize',job='B')
        self.assertEqual(obs['status'],'FINALIZED')
        self.assertEqual(state['tick'],1)
        state=run(state,('receipt','A',None),('commit','A',None),('finalize','A',None))
        self.assertEqual(state['tick'],5)
        self.assertTrue(all(state['finalized'].values()))

    def test_resource_denial_does_not_spend_or_disclose(self):
        state=transition(initial('F03'),'wait',ticks=6)[0]
        after,obs,_=transition(state,'receipt',job='A')
        self.assertEqual(obs['reason'],'JOB_DEADLINE')
        self.assertEqual((after['tick'],after['uses_remaining']),(state['tick'],state['uses_remaining']))
        self.assertEqual(after['belief_worlds'],state['belief_worlds'])

    def test_wait_may_pass_both_deadlines(self):
        state=transition(initial('F01'),'wait',ticks=20)[0]
        self.assertEqual(state['tick'],20)
        self.assertEqual(optimal_value(state),(0,0))

    def test_unsafe_retry_can_make_actual_duplicate(self):
        state=initial('F02')
        after,obs,m=transition(state,'commit',job='A')
        self.assertEqual(obs['status'],'APPLIED')
        self.assertEqual(after['duplicate_effects']['A'],1)
        self.assertEqual(after['unsafe_attempts'],1)
        self.assertIn('safety_violation',m['loss_causes'])
        self.assertFalse(m['destructive_query'])

    def test_known_duplicate_is_not_reported_as_uncertainty(self):
        state=initial('F06')
        state=transition(state,'commit',job='B')[0]
        self.assertEqual(local_barriers(state,'B'),['duplicate_delivery_established'])

    def test_guarded_unsafe_attempt_is_still_noncompliant(self):
        state,obs,_=transition(initial('F03'),'finalize',job='A')
        self.assertEqual(obs['reason'],'DELIVERY_NOT_EXACTLY_ONE')
        self.assertEqual(state['unsafe_attempts'],1)

    def test_individual_finalized_job_rejects_new_write_without_erasing_success(self):
        state=run(initial('F07'),('commit','A',None),('finalize','A',None))
        after,obs,_=transition(state,'commit',job='A')
        self.assertEqual(obs['reason'],'JOB_ALREADY_FINALIZED')
        self.assertTrue(after['finalized']['A'])
        self.assertEqual(after['commits_made']['A'],1)
        self.assertEqual(after['unsafe_attempts'],1)

    def test_joint_terminal_success_is_protected(self):
        state=run(initial('F07'),('commit','A',None),('finalize','A',None),('commit','B',None),('finalize','B',None))
        after,obs,m=transition(state,'receipt',job='A')
        self.assertEqual(obs['status'],'TERMINAL')
        self.assertEqual((after['tick'],after['uses_remaining']),(state['tick'],state['uses_remaining']))
        self.assertEqual(m['post_value'],[2,1])

    def test_action_cap_separate_from_resource_loss(self):
        case=next(c for c in design_cases() if c['family_id']=='F07')
        cfg=copy.deepcopy(case['config']);cfg['max_actions']=1
        cfg['jobs']['A']['initial_receipt']=1;cfg['jobs']['A']['prior_options']=[1]
        world=copy.deepcopy(case['actual_world']);world['A']['prior_delivered']=1
        state=make_initial_state(cfg,world)
        self.assertEqual(optimal_value(state),(1,0))
        after,_,m=transition(state,'receipt',job='A')
        self.assertEqual(after['actions_taken'],1)
        self.assertTrue(m['realized_value_loss'])
        self.assertIn('action_limit',m['loss_causes'])
        self.assertFalse(m['destructive_query'])

    def test_finish_retains_malformed_report_without_claiming_completion(self):
        state=initial('F07')
        after,obs,m=transition(state,'finish',report={'joint_complete':True})
        self.assertEqual(after['final_report'],{'joint_complete':True})
        self.assertFalse(all(after['finalized'].values()))
        self.assertTrue(m['realized_joint_guarantee_loss'])
        self.assertTrue(obs['receipt_line'].startswith('SEALED test '))

    def test_local_barriers_can_coexist_and_do_not_claim_joint_feasibility(self):
        state=transition(initial('F12'),'wait',ticks=7)[0]
        self.assertEqual(local_barriers(state,'A'),['delivery_unresolved','time_below_required_minimum'])
        state=initial('F09')
        self.assertEqual(local_barriers(state,'A'),[])
        self.assertEqual(local_barriers(state,'B'),[])
        self.assertEqual(optimal_value(state),(1,1))

    def test_public_status_excludes_fixture_and_oracle(self):
        status=public_status(initial('F03'))
        self.assertNotIn('actual_world',status)
        self.assertNotIn('belief_worlds',status)
        self.assertNotIn('optimal_value',status)
        self.assertEqual(status['jobs']['A']['delivery'],'unknown')

    def test_replay_checks_observation_oracle_states_and_hash_chain(self):
        start=initial('F07');state=start;rows=[]
        for action,job in [('commit','A'),('finalize','A'),('receipt','A')]:
            after,obs,oracle=transition(state,action,job=job)
            row=new_event(len(rows),rows[-1]['event_sha256'] if rows else '0'*64,state,after,action,{'job':job},obs,oracle,'fixed-time')
            rows.append(row);state=after
        self.assertEqual(replay(start,rows),state)
        tampered=copy.deepcopy(rows);tampered[1]['oracle']['post_value']=[0,0]
        with self.assertRaises(ValueError):
            replay(start,tampered)


if __name__=='__main__':
    unittest.main()
