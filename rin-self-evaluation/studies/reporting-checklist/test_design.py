"""Verify the prospective manipulation and inherited mechanical invariants."""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from engine import make_initial_state, report_bytes, transition
import prepare
from prepare import CELLS, CONDITIONS, MODELS, ROOT, design_cases, planned_assignments, public_prompt


class DesignTests(unittest.TestCase):
    def test_inherited_sources_match_the_recorded_lineage(self):
        lineage = json.loads((ROOT/'protocol/lineage.json').read_text())
        for name, record in lineage['copied_byte_identically'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), record['sha256'], name)

    def test_case_catalog_metadata_does_not_change_the_cases(self):
        lineage = json.loads((ROOT/'protocol/lineage.json').read_text())
        raw = (ROOT/'protocol/cases.json').read_bytes(); catalog = json.loads(raw)
        actual = hashlib.sha256(report_bytes(catalog['cases'])).hexdigest()
        self.assertEqual(actual, lineage['case_catalog']['source_case_array_sha256'])
        self.assertEqual(actual, catalog['case_array_sha256'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), lineage['case_catalog']['current_catalog_sha256'])

    def test_every_family_has_one_each_model_and_condition(self):
        assignments = planned_assignments()
        counts = Counter((row['family_id'], row['requested_model'], row['report_condition']) for row in assignments)
        expected = {(f'F{i:02d}', model, condition) for i in range(1, 13) for model in MODELS for condition in CONDITIONS}
        self.assertEqual(set(counts), expected)
        self.assertEqual(set(counts.values()), {1})
        self.assertEqual([row['run_id'] for row in assignments], [f'w{i:03d}' for i in range(1, 49)])
        self.assertEqual({row['replicate'] for row in assignments}, {1})

    def test_order_balance_positions_pair_order_and_adjacency(self):
        assignments = planned_assignments(); counts = Counter(); adjacency = Counter()
        format_first = Counter(); model_first = Counter()
        for offset in range(0, 48, 4):
            block = assignments[offset:offset + 4]
            cells = [(row['requested_model'], row['report_condition']) for row in block]
            for position, cell in enumerate(cells): counts[(cell, position)] += 1
            adjacency.update(zip(cells, cells[1:]))
            for model in MODELS:
                format_first[(model, next(condition for m, condition in cells if m == model))] += 1
            for condition in CONDITIONS:
                model_first[(condition, next(model for model, c in cells if c == condition))] += 1
        self.assertEqual(set(counts.values()), {3})
        self.assertEqual(len(counts), 16)
        self.assertEqual(set(adjacency.values()), {3})
        self.assertEqual(len(adjacency), 12)
        self.assertEqual(set(format_first.values()), {6})
        self.assertEqual(set(model_first.values()), {6})

    def test_condition_prompt_difference_is_only_the_added_requirement(self):
        checklist = public_prompt('test', 'checklist')
        opened = public_prompt('test', 'open')
        block = (ROOT/'protocol/CHECKLIST_REQUIREMENTS.md').read_text().strip()
        self.assertEqual(checklist.count(block), 1)
        self.assertEqual(checklist.replace(block, ''), opened)
        self.assertNotIn(prepare.MARKER, checklist)
        for model in MODELS:
            self.assertNotIn(model, checklist)
            self.assertNotIn(model, opened)
        self.assertIn('two-job-study/client.py', opened)
        self.assertNotIn('checklist-study/client.py', checklist)

    def test_initial_service_state_and_transition_do_not_contain_condition(self):
        cases = {case['case_id']: case for case in design_cases()}
        for offset in range(0, 48, 4):
            block = planned_assignments()[offset:offset + 4]; states = []
            for assignment in block:
                case = cases[assignment['case_id']]
                config = copy.deepcopy(case['config']); config['run_id'] = assignment['run_id']
                state = make_initial_state(config, case['actual_world'])
                self.assertNotIn('report_condition', state['config'])
                self.assertNotIn('requested_model', state['config'])
                state['config']['run_id'] = '<RUN_ID>'
                states.append(state)
            self.assertTrue(all(state == states[0] for state in states))
            outcomes = [transition(state, 'status') for state in states]
            self.assertTrue(all(outcome == outcomes[0] for outcome in outcomes))

    def test_preparation_cannot_overwrite_a_freeze_or_native_record(self):
        for marker in ['protocol/frozen.json', 'runs/w001/events.jsonl', 'runs/w001/final_report.json']:
            with tempfile.TemporaryDirectory(prefix='two-job-prepare-guard-') as folder:
                root = Path(folder); path = root/marker; path.parent.mkdir(parents=True); path.write_text('')
                with patch.object(prepare, 'ROOT', root):
                    with self.assertRaises(SystemExit): prepare.main()


if __name__ == '__main__':
    unittest.main()
