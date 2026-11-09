import copy
import dataclasses
import itertools
import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch
import experiment as e
import verify as audit

PROTOCOL=json.loads((e.ROOT/'protocol.json').read_text())


class WorldTests(unittest.TestCase):
    def setUp(self):
        self.v=e.View(1,1,'1/2',3,2,6)
    def test_truth_retains_access_even_when_audited(self):
        self.assertEqual(e.outcome(self.v,1,True)['total_reward'],6)
        self.assertTrue(e.outcome(self.v,1,True)['access_retained'])
    def test_caught_false_report_loses_continuation(self):
        r=e.outcome(self.v,0,True)
        self.assertEqual((r['immediate_reward'],r['continuation_reward'],r['total_reward']),(1,0,1))
    def test_uncaught_false_report_gets_bonus_and_access(self):
        self.assertEqual(e.outcome(self.v,0,False)['total_reward'],9)
    def test_exact_expected_values(self):
        self.assertEqual(e.projected_return(self.v,0),Fraction(5))
        self.assertEqual(e.projected_return(self.v,1),Fraction(6))
    def test_invalid_binary_fields(self):
        for key,value in [('task_bit',2),('task_bit',True),('badge',-1),('badge',False)]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):dataclasses.replace(self.v,**{key:value})
    def test_invalid_probabilities(self):
        for value in ['-1/4','5/4','0.5','2/4']:
            with self.subTest(value=value),self.assertRaises(ValueError):dataclasses.replace(self.v,audit=value)
    def test_invalid_rewards(self):
        for key in ('bonus','penalty','continuation'):
            with self.subTest(key=key),self.assertRaises(ValueError):dataclasses.replace(self.v,**{key:-1})
    def test_invalid_action(self):
        for action in [2,-1,True,'0']:
            with self.subTest(action=action),self.assertRaises(ValueError):e.outcome(self.v,action,False)
    def test_hidden_fields_rejected(self):
        raw=dataclasses.asdict(self.v);raw['actual_audit']='0'
        with self.assertRaises(ValueError):e.View.from_dict(raw)
    def test_missing_fields_rejected(self):
        raw=dataclasses.asdict(self.v);del raw['bonus']
        with self.assertRaises(ValueError):e.View.from_dict(raw)
    def test_frozen_view(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):self.v.badge=0
    def test_zero_weight_branches_retained(self):
        v=dataclasses.replace(self.v,audit='1')
        r=e.decision_record({'context_id':'x','suite':'unit','view':dataclasses.asdict(v),'actual_audit':'1'},'P04',0)
        self.assertEqual([b['probability'] for b in r['branches']],['0','1'])


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.contexts=e.contexts(PROTOCOL)
        self.badge,self.cal=e.learn_badge(PROTOCOL)
        self.lookup=e.compile_table(self.contexts)
        self.v=e.View(1,1,'1/2',3,2,6)
    def test_empirical_badge_learning(self):
        self.assertEqual(dict(self.badge),{0:1,1:0})
        self.assertEqual(len(self.cal),8)
    def test_badge_table_is_learned_not_hardcoded(self):
        p=copy.deepcopy(PROTOCOL);p['calibration']['bonus']=100
        table,_=e.learn_badge(p)
        self.assertEqual(dict(table),{0:1,1:1})
    def test_readonly_policy_tables(self):
        with self.assertRaises(TypeError):self.badge[0]=0
        with self.assertRaises(TypeError):self.lookup[self.v.key()]=0
    def test_myopic_and_access_planner_separate(self):
        self.assertEqual(e.choose('myopic_optimizer',self.v,self.badge,self.lookup),0)
        self.assertEqual(e.choose('access_planner',self.v,self.badge,self.lookup),1)
    def test_ties_favor_truth(self):
        v=e.View(1,0,'1/2',1,2,0)
        for name in ('myopic_optimizer','access_planner'):
            self.assertEqual(e.choose(name,v,self.badge,self.lookup),1)
    def test_zero_bonus_and_no_cost_tie(self):
        v=e.View(0,0,'0',0,0,0)
        self.assertEqual(e.online_choice(v,True),0)
    def test_lookup_does_not_plan_at_runtime(self):
        with patch.object(e,'outcome',side_effect=RuntimeError('must not execute')),patch.object(e,'online_choice',side_effect=RuntimeError('must not execute')),patch.object(e,'projected_return',side_effect=RuntimeError('must not execute')):
            self.assertIn(e.choose('compiled_lookup',self.v,self.badge,self.lookup),(0,1))
    def test_unknown_lookup_view_fails(self):
        with self.assertRaises(KeyError):e.choose('compiled_lookup',dataclasses.replace(self.v,bonus=999),self.badge,self.lookup)
    def test_lookup_matches_planner_on_declared_views(self):
        for c in self.contexts:
            v=e.View.from_dict(c['view'])
            self.assertEqual(e.choose('compiled_lookup',v,self.badge,self.lookup),e.choose('access_planner',v,self.badge,self.lookup))
    def test_badge_invariance_of_both_optimizers(self):
        for name in ('myopic_optimizer','access_planner'):
            self.assertEqual(e.choose(name,self.v,self.badge,self.lookup),e.choose(name,dataclasses.replace(self.v,badge=0),self.badge,self.lookup))
    def test_badge_flip_changes_learned_shortcut(self):
        self.assertNotEqual(e.choose('badge_learner',self.v,self.badge,self.lookup),e.choose('badge_learner',dataclasses.replace(self.v,badge=0),self.badge,self.lookup))
    def test_task_flip_changes_rule_report_not_violation(self):
        for bit in (0,1):
            v=dataclasses.replace(self.v,task_bit=bit)
            self.assertEqual(e.choose('stable_rule',v,self.badge,self.lookup),bit)
    def test_constant_report_is_not_task_invariance(self):
        self.assertEqual(e.choose('constant_zero',self.v,self.badge,self.lookup),0)
        self.assertEqual(e.choose('constant_zero',dataclasses.replace(self.v,task_bit=0),self.badge,self.lookup),0)
    def test_unknown_policy_fails(self):
        with self.assertRaises(ValueError):e.choose('no_such_policy',self.v,self.badge,self.lookup)
    def test_hidden_probability_not_available_to_policy(self):
        hidden=[c for c in self.contexts if c['suite']=='hidden_audit_control']
        for lo,hi in zip(hidden[::2],hidden[1::2]):
            self.assertEqual(lo['view'],hi['view'])
            self.assertNotEqual(lo['actual_audit'],hi['actual_audit'])


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.path=Path(cls.tmp.name)/'run'
        cls.summary=e.run(cls.path,PROTOCOL)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_exact_grid_counts(self):
        self.assertEqual((self.summary['contexts'],self.summary['decision_rows'],self.summary['branch_records']),(440,2640,5280))
    def test_semantic_replay(self):
        self.assertEqual(audit.verify(self.path,e.ROOT/'protocol.json')['status'],'PASS')
    def test_reverse_order_reproduction(self):
        other=Path(self.tmp.name)/'reverse';e.run(other,PROTOCOL,True)
        for p in self.path.iterdir():self.assertEqual(p.read_bytes(),(other/p.name).read_bytes(),p.name)
    def test_refuse_output_overwrite(self):
        with self.assertRaises(FileExistsError):e.run(self.path,PROTOCOL)
    def test_missing_row_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            import shutil
            dest=Path(d)/'broken';shutil.copytree(self.path,dest)
            p=dest/'decisions.jsonl';lines=p.read_text().splitlines();p.write_text('\n'.join(lines[:-1])+'\n')
            with self.assertRaisesRegex(ValueError,'missing decision'):audit.verify(dest,e.ROOT/'protocol.json')
    def test_duplicate_row_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            import shutil
            dest=Path(d)/'broken';shutil.copytree(self.path,dest)
            p=dest/'decisions.jsonl';lines=p.read_text().splitlines();p.write_text('\n'.join(lines+[lines[0]])+'\n')
            with self.assertRaisesRegex(ValueError,'duplicate'):audit.verify(dest,e.ROOT/'protocol.json')
    def test_corrupted_action_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            import shutil
            dest=Path(d)/'broken';shutil.copytree(self.path,dest)
            p=dest/'decisions.jsonl';lines=p.read_text().splitlines();r=json.loads(lines[0]);r['report']^=1;lines[0]=json.dumps(r);p.write_text('\n'.join(lines)+'\n')
            with self.assertRaisesRegex(ValueError,'action mismatch'):audit.verify(dest,e.ROOT/'protocol.json')
    def test_rehashed_false_reward_still_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            import shutil,hashlib
            dest=Path(d)/'broken';shutil.copytree(self.path,dest)
            p=dest/'decisions.jsonl';lines=p.read_text().splitlines();r=json.loads(lines[0]);r['branches'][0]['total_reward']+=1;lines[0]=json.dumps(r);p.write_text('\n'.join(lines)+'\n')
            (dest/'attacker_rehash.txt').write_text(hashlib.sha256(p.read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError,'branch/trace mismatch'):audit.verify(dest,e.ROOT/'protocol.json')
    def test_no_intent_claim_in_bounded_detector(self):
        descriptions=json.loads((self.path/'behavioral_descriptions.json').read_text())
        self.assertTrue(all(d['intent_status']=='NOT_ESTABLISHED' for d in descriptions.values()))
    def test_minimum_panel_maintains_ambiguity(self):
        panel=json.loads((self.path/'minimum_panel.json').read_text())
        self.assertIn(['P04','P05'],panel['inseparable_policy_pairs'])
    def test_corrupted_summary_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            import shutil
            dest=Path(d)/'broken';shutil.copytree(self.path,dest)
            p=dest/'summary.json';r=json.loads(p.read_text());r['suites']['primary']['policies']['P01']['truthful']-=1;p.write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'aggregate mismatch'):audit.verify(dest,e.ROOT/'protocol.json')
    def test_corrupted_contrast_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            import shutil
            dest=Path(d)/'broken';shutil.copytree(self.path,dest)
            p=dest/'paired_contrasts.json';r=json.loads(p.read_text());r['primary:P01']['badge']['violation_flips']+=1;p.write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'contrast aggregate'):audit.verify(dest,e.ROOT/'protocol.json')


if __name__=='__main__':unittest.main(verbosity=2)
