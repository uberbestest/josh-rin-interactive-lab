import copy
import hashlib
import unittest
from engine import digest
from presentation import new_presentation, project, stdout_text, validate_transport, verify_presentations
from study_test_support import execute, initial, safe_steps


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.state,self.events,self.shown=execute(initial(),safe_steps()[:-1])
        self.receipt=self.events[-1]

    def test_projection_preserves_target_global_and_top_level_fields(self):
        raw=self.receipt['observation']; before=copy.deepcopy(raw)
        projected=project(raw,'receipt','A','target')
        expected=copy.deepcopy(raw); del expected['local_status']['jobs']['B']
        self.assertEqual(projected,expected)
        self.assertEqual(raw,before)
        self.assertEqual(projected['status'],'COMMITTED')
        self.assertNotIn('ABSENT',stdout_text(projected))
        self.assertIn('ABSENT',stdout_text(raw))
        self.assertNotIn('receipt_scope',stdout_text(projected))
        self.assertNotIn('actual_world',stdout_text(projected))

    def test_other_actions_and_combined_are_unchanged(self):
        raw=self.receipt['observation']
        self.assertEqual(project(raw,'receipt','A','combined'),raw)
        for action in ('status','commit','finalize','wait','finish'):
            self.assertEqual(project(raw,action,'A','target'),raw)
        self.assertEqual(project(self.events[0]['observation'],'status',None,'target')['local_status']['jobs'].keys(),{'A','B'})
        without_jobs={'status':'DENIED','local_status':{'tick':2}}
        self.assertEqual(project(without_jobs,'receipt','A','target'),without_jobs)

    def test_invalid_target_or_transport_fails_closed(self):
        with self.assertRaises(ValueError): project(self.receipt['observation'],'receipt','B','target')
        for transport in ({},{'receipt_scope':'wrong'},{'receipt_scope':'target','hint':'hidden'},None):
            with self.assertRaises(ValueError): validate_transport(transport)

    def test_exact_unicode_serialization_and_hash_chain_replays(self):
        events=copy.deepcopy(self.events)
        events[0]['observation']['test_text']='★ café\nline two'
        shown=[]
        for event in events:
            shown.append(new_presentation(event,shown[-1]['presentation_sha256'] if shown else '0'*64,'target'))
        result=verify_presentations(events,shown,'target')
        self.assertEqual(result['exact_stdout_records_verified'],len(events))
        self.assertIn('★ café',shown[0]['stdout'])
        self.assertTrue(shown[0]['stdout'].endswith('\n'))
        self.assertEqual(hashlib.sha256(shown[0]['stdout'].encode()).hexdigest(),shown[0]['stdout_sha256'])

    def test_bytes_projection_raw_link_and_chain_tampering_are_rejected(self):
        for field,value in [('stdout','different\n'),('stdout_sha256','0'*64),('raw_event_sha256','0'*64),('previous_presentation_sha256','f'*64),('job','B')]:
            with self.subTest(field=field):
                shown=copy.deepcopy(self.shown);shown[-1][field]=value
                with self.assertRaises(ValueError):verify_presentations(self.events,shown,'combined')
        for shown in (self.shown[:-1],list(reversed(self.shown))):
            with self.assertRaises(ValueError):verify_presentations(self.events,shown,'combined')
        shown=copy.deepcopy(self.shown)
        shown[-1]['shown_observation']['local_status']['jobs']['B']['delivery']='unknown'
        unsigned={k:v for k,v in shown[-1].items() if k!='presentation_sha256'}
        shown[-1]['presentation_sha256']=digest(unsigned)
        with self.assertRaises(ValueError):verify_presentations(self.events,shown,'combined')


if __name__=='__main__':unittest.main()
