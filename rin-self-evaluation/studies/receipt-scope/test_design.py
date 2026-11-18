from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import unittest
from engine import make_initial_state, optimal_value
from prepare import ROOT, MODELS, SCOPES, ORIENTATIONS, REPLICATES, native_cases, planned_assignments, public_prompt
import audit_reference


class DesignTests(unittest.TestCase):
    def test_complete_balanced_32_matrix_and_repeats(self):
        rows=planned_assignments()
        self.assertEqual([r['run_id'] for r in rows],[f'x{i:03d}' for i in range(1,33)])
        self.assertEqual({(r['orientation'],r['replicate'],r['requested_model'],r['receipt_scope']) for r in rows},
                         {(o,r,m,s) for o in ORIENTATIONS for r in REPLICATES for m in MODELS for s in SCOPES})
        self.assertEqual(set(Counter((r['requested_model'],r['receipt_scope'],r['within_block_position']) for r in rows).values()),{2})
        self.assertEqual(set(Counter((r['orientation'],r['requested_model'],r['receipt_scope'],r['within_block_position']) for r in rows).values()),{1})
        self.assertEqual(len({(r['orientation'],r['replicate']) for r in rows}),8)
        self.assertTrue(all(r['report_condition']=='checklist' for r in rows))
        self.assertEqual(rows,planned_assignments())

    def test_original_lineage_and_consistent_label_reflection(self):
        original,reflected=native_cases()
        prior=json.loads((ROOT/'protocol/lineage.json').read_text())['source_C11']
        self.assertEqual({k:v for k,v in original.items() if k!='orientation'},prior)
        for job,other in [('A','B'),('B','A')]:
            self.assertEqual(reflected['config']['jobs'][job],original['config']['jobs'][other])
            self.assertEqual(reflected['actual_world'][job],original['actual_world'][other])
        self.assertNotEqual(original['config']['priority'],reflected['config']['priority'])
        self.assertEqual(original['family_id'],reflected['family_id'])
        for case in (original,reflected):
            cfg=copy.deepcopy(case['config']);cfg['run_id']='test'
            self.assertEqual(optimal_value(make_initial_state(cfg,case['actual_world'])),(2,1))

    def test_one_identical_public_prompt_and_inherited_contract(self):
        rows=planned_assignments()
        prompts={public_prompt(r['run_id']).replace(r['run_id'],'<RUN_ID>') for r in rows}
        self.assertEqual(len(prompts),1)
        value=prompts.pop()
        for label in ('combined','reflected','gpt-6','receipt_scope','hypothesis'):
            self.assertNotIn(label,value)
        lineage=json.loads((ROOT/'protocol/lineage.json').read_text())
        self.assertEqual(hashlib.sha256(value.encode()).hexdigest(),lineage['normalized_round06_checklist_prompt_sha256'])

    def test_analytical_witness_all_four_worlds_each_orientation(self):
        result=audit_reference.audit()
        self.assertEqual(result['authored_witness_worlds_checked'],8)
        self.assertEqual(max(r['terminal_tick'] for r in result['witnesses']),8)
        self.assertEqual(min(r['terminal_uses'] for r in result['witnesses']),0)
        self.assertTrue(all(r['safe_joint_completion'] for r in result['witnesses']))


if __name__=='__main__':unittest.main()
