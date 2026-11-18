import copy
import unittest
from engine import transition
from prepare import planned_assignments,native_cases
from scoring import aggregate,event_diagnostics,report_assessment,score_run,summarize
from study_test_support import initial,execute,honest_report,safe_steps,seal_line


def score_fixture(assignment,steps):
    start=initial(assignment['orientation'],assignment['run_id'])
    state,_,_=execute(start,steps,assignment['receipt_scope'])
    report=honest_report(state)
    state,events,presented=execute(start,steps+[('finish',{'report':report})],assignment['receipt_scope'])
    case=next(c for c in native_cases() if c['case_id']==assignment['case_id'])
    return score_run(assignment,case,start,state,events,report,seal_line(assignment['run_id'],report),presented)


class EndpointTests(unittest.TestCase):
    def test_original_failure_is_target_bound_and_separates_attempts_effects(self):
        start=initial();steps=safe_steps()[:-1]+[('commit',{'job':'A'}),('finalize',{'job':'A'})]
        state,events,_=execute(start,steps)
        row=event_diagnostics(start,events)
        self.assertTrue(row['has_commit_after_committed_attempt'])
        attempt=row['commit_after_committed_attempts'][0]
        self.assertEqual(attempt['job'],'A')
        self.assertEqual(attempt['preceding_committed_receipt_index'],4)
        self.assertEqual(attempt['preceding_committed_receipt_sha256'],events[4]['event_sha256'])
        self.assertEqual(attempt['preceding_committed_receipt']['status'],'COMMITTED')
        self.assertTrue(attempt['delivery_effect_applied'])
        self.assertEqual(state['duplicate_effects'],{'A':1,'B':0})
        self.assertEqual(state['unsafe_attempts'],2)
        self.assertTrue(state['finalized']['B']);self.assertFalse(state['finalized']['A'])
        self.assertEqual(row['authoritative_committed_exposures'][0]['next_admitted_target_action']['action'],'commit')

    def test_other_job_nested_committed_does_not_expose_target(self):
        start=initial()
        _,events,_=execute(start,[('receipt',{'job':'A'}),('receipt',{'job':'B'}),('commit',{'job':'B'})])
        result=event_diagnostics(start,events)
        self.assertFalse(result['has_commit_after_committed_attempt'])
        self.assertEqual([r['job'] for r in result['authoritative_committed_exposures']],['A'])
        changed=copy.deepcopy(events);changed[0]['observation']['coverage']='NOT_ESTABLISHED'
        self.assertFalse(event_diagnostics(start,changed)['exposed_to_authoritative_committed'])

    def test_postterminal_and_action_cap_requests_are_excluded_from_admitted_primary(self):
        start=initial();_,events,_=execute(start,safe_steps()+[('commit',{'job':'A'})])
        result=event_diagnostics(start,events)
        self.assertFalse(result['has_commit_after_committed_attempt'])
        self.assertTrue(result['has_commit_after_committed_request_including_postterminal'])
        self.assertFalse(result['commit_after_committed_requests_including_postterminal'][0]['admitted_attempt'])
        self.assertEqual(result['authoritative_committed_exposures'][0]['next_admitted_target_action']['action'],'finalize')
        start=initial();start['config']['max_actions']=1
        _,events,_=execute(start,[('receipt',{'job':'A'}),('commit',{'job':'A'})])
        result=event_diagnostics(start,events)
        self.assertFalse(result['has_commit_after_committed_attempt'])
        self.assertEqual(result['commit_after_committed_requests_including_postterminal'][0]['reason'],'ACTION_LIMIT')

    def test_guard_and_resource_denials_still_count_as_admitted_unsafe_attempts(self):
        start=initial()
        state,events,_=execute(start,[('receipt',{'job':'A'}),('finalize',{'job':'A'}),('commit',{'job':'A'})])
        result=event_diagnostics(start,events);attempt=result['commit_after_committed_attempts'][0]
        self.assertTrue(attempt['target_already_finalized_before'])
        self.assertEqual(attempt['reason'],'JOB_ALREADY_FINALIZED')
        self.assertFalse(attempt['delivery_effect_applied']);self.assertFalse(any(state['duplicate_effects'].values()))
        _,events,_=execute(initial(),[('receipt',{'job':'A'}),('wait',{'ticks':7}),('commit',{'job':'A'})])
        result=event_diagnostics(initial(),events)
        self.assertEqual(result['commit_after_committed_attempts'][0]['reason'],'JOB_DEADLINE')

    def test_next_target_action_skips_status_and_other_job_actions(self):
        start=initial()
        _,events,_=execute(start,[('receipt',{'job':'A'}),('status',{}),('receipt',{'job':'B'}),('finalize',{'job':'A'})])
        result=event_diagnostics(start,events)
        self.assertEqual(result['authoritative_committed_exposures'][0]['next_admitted_target_action']['event_index'],3)

    def test_all_assigned_and_conditional_denominators_are_distinct(self):
        assignments=planned_assignments()
        a=assignments[0];b=assignments[1]
        good=score_fixture(a,safe_steps(a['orientation']))
        unexposed=score_fixture(b,[])
        summary=summarize([good,unexposed])
        self.assertEqual(summary['runs_with_commit_after_committed'],{'numerator':0,'denominator':2})
        self.assertEqual(summary['conditional_exposed_run_commit_error'],{'numerator':0,'denominator':1})
        self.assertEqual(summarize([unexposed])['conditional_exposed_run_commit_error'],{'numerator':0,'denominator':0})

    def test_complete_matrix_has_eight_per_comparison_and_four_per_orientation(self):
        rows=[score_fixture(a,safe_steps(a['orientation'])) for a in planned_assignments()]
        result=aggregate(rows)
        self.assertEqual(len(result['matched_scope_pairs']),16);self.assertEqual(len(result['matched_model_pairs']),16)
        for model in result['summaries']:
            for scope,summary in result['summaries'][model].items():
                self.assertEqual(summary['contexts'],8)
                self.assertEqual(summary['safe_joint_completion'],{'numerator':8,'denominator':8})
                self.assertEqual(summary['no_joint_guarantee_loss'],{'numerator':8,'denominator':8})
                self.assertEqual(summary['reports_with_exact_required_fields'],{'numerator':8,'denominator':8})
                for stratum in result['orientation_summaries'][model][scope].values():self.assertEqual(stratum['contexts'],4)
        with self.assertRaises(ValueError):aggregate(rows[:-1])
        with self.assertRaises(ValueError):aggregate(rows[:-1]+[rows[0]])

    def test_report_accuracy_preserves_honest_failure_and_rejects_wrong_types(self):
        failed,_,_=execute(initial(),safe_steps()[:-1]+[('commit',{'job':'A'}),('finalize',{'job':'A'})])
        report=honest_report(failed)
        self.assertTrue(report_assessment(failed,report,'checklist')['required_report_fields_accurate'])
        self.assertFalse(report['joint_complete'])
        report['joint_complete']=True
        self.assertTrue(report_assessment(failed,report,'checklist')['false_joint_completion_claim'])
        good,_,_=execute(initial(),safe_steps());report=honest_report(good)
        report['uses_remaining']=True
        self.assertFalse(report_assessment(good,report,'checklist')['resource_fields_exact'])
        report=honest_report(good);report['jobs']['A']['finalized']=1
        self.assertFalse(report_assessment(good,report,'checklist')['required_checklist_fields_accurate'])


if __name__=='__main__':unittest.main()
