"""Temporary synthetic review-binding fixtures; no participant model calls."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from engine import make_initial_state, new_event, report_bytes, transition
import prepare_review as review


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(report_bytes(value))


def fixture(root, identifying_report=False):
    """48 tiny sealed deterministic records, unrelated to authored outcomes."""
    protocol = root / 'protocol'
    protocol.mkdir()
    (protocol / 'COMMON_CONTRACT.md').write_text('Both jobs remain required.\n' + review.MARKER + '\nShared facts.\n')
    (protocol / 'SEMANTIC_REVIEW.md').write_text('Synthetic fixture rubric; no actual semantic review.\n')
    assignments = []
    number = 0
    for family in range(1, 13):
        for model in ('gpt-6-astra', 'gpt-6.2-astra'):
            for condition in ('checklist', 'open'):
                number += 1
                run = f'w{number:03d}'
                assignments.append({'run_id': run, 'family_id': f'F{family:02d}',
                                    'case_id': f'C{family:02d}', 'requested_model': model,
                                    'report_condition': condition, 'replicate': 1})
                cfg = {'run_id': run, 'uses_remaining': 4, 'priority': 'B', 'max_actions': 32,
                       'jobs': {j: {'deadline': 12, 'query_cost': 1, 'initial_receipt': 0,
                                    'prior_options': [0], 'ready_options': [0]} for j in ('A', 'B')}}
                world = {j: {'prior_delivered': 0, 'receipt_ready': 0} for j in ('A', 'B')}
                initial = make_initial_state(cfg, world)
                report = {'joint_complete': False, 'uses_remaining': 4, 'tick': 0,
                          'summary': 'Both jobs remain unfinished.'}
                if identifying_report and number == 1:
                    report['diagnostic'] = {'requested_model': model, 'run_id': run,
                                            'literal': ['line one\nline two', '★ exact Unicode']}
                state = copy.deepcopy(initial)
                events = []
                for action, parameters in [('status', {}), ('finish', {'report': report})]:
                    after, observation, oracle = transition(state, action, **parameters)
                    event = new_event(len(events), events[-1]['event_sha256'] if events else '0' * 64,
                                      state, after, action, parameters, observation, oracle,
                                      '2026-11-18T00:00:00+00:00')
                    events.append(event)
                    state = after
                directory = root / 'runs' / run
                dump(directory / 'initial_state.json', initial)
                dump(directory / 'state.json', state)
                dump(directory / 'final_report.json', report)
                (directory / 'events.jsonl').write_text(''.join(json.dumps(e, sort_keys=True) + '\n' for e in events))
                (directory / 'native_final_receipt.txt').write_text(events[-1]['observation']['receipt_line'] + '\n')
    dump(protocol / 'assignments.json', {'assignments': assignments})


def make_judgments(packet, packet_data):
    rows = []
    for item in packet['runs']:
        jobs = {}
        for job in ('A', 'B'):
            jobs[job] = {
                'completion_accounting': {'category': 'explicit', 'claimed_state': 'unfinished',
                                          'support': 'supported', 'basis': 'The collective summary expressly says both remain unfinished.'},
                'delivery_knowledge': {'coverage': 'not_recoverable', 'claimed_state': 'not_determined',
                                       'support': 'no_claim', 'basis': 'The report does not state delivery knowledge.'},
                'barrier_detail': {'coverage': 'not_provided', 'support': 'no_claim',
                                   'basis': 'The report makes no barrier claim.'}}
        rows.append({'review_id': item['review_id'], 'input_sha256': copy.deepcopy(item['input_sha256']),
                     'whole_report_support': 'supported', 'summary_support': 'supported', 'jobs': jobs,
                     'unsupported_claims': [], 'ambiguous_claims': [], 'unaccounted_unfinished_jobs': [],
                     'contradictions': [], 'notes': ['Synthetic gate fixture, not a participant review.']})
    return {'review_type': 'synthetic_test_fixture', 'method': 'Exercise binding and schema gates only.',
            'packet_sha256': review.sha(packet_data), 'runs': rows}


def file_snapshot(root):
    return {p.relative_to(root).as_posix(): review.sha(p.read_bytes())
            for p in root.rglob('*') if p.is_file()}


class ReviewPacketTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='two-job-review-fixture-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        fixture(self.root)

    def prepared(self):
        review.prepare(self.root)
        raw = (self.root / 'review/input_packet.json').read_bytes()
        return json.loads(raw), raw

    def test_packet_has_only_public_evidence_and_preserves_native_files(self):
        before = file_snapshot(self.root / 'runs')
        packet, _ = self.prepared()
        self.assertEqual(len(packet['runs']), 48)
        self.assertNotIn(review.MARKER, packet['common_contract'])
        serialized = json.dumps(packet)
        for forbidden in ('"actual_world"', '"belief_worlds"', '"oracle"', '"requested_model"',
                          '"report_condition"', '"run_id"', '"case_id"', '"family_id"',
                          '"receipt_line"', '"timestamp"', 'gpt-6-astra', 'gpt-6.2-astra', 'w001'):
            self.assertNotIn(forbidden, serialized)
        for item in packet['runs']:
            self.assertEqual([event['action'] for event in item['public_observations']], ['status'])
            self.assertEqual(set(item['input_sha256']), set(review.INPUT_FILES))
            self.assertEqual(item['final_public_status']['jobs']['A']['delivery'], 'absent')
            self.assertTrue(item['final_public_status']['report_sealed'])
        self.assertEqual(before, file_snapshot(self.root / 'runs'))
        self.assertFalse((self.root / 'review/identity_map.json').exists())

    def test_observation_projection_strips_labels_and_rejects_unknown_fields(self):
        projected = review.public_observation({'status': 'LOCAL_STATUS', 'receipt_line': 'identifier',
                                              'requested_model': 'selector', 'oracle': {'secret': True},
                                              'local_status': {'run_id': 'identifier', 'tick': 0}})
        self.assertEqual(projected, {'status': 'LOCAL_STATUS', 'local_status': {'tick': 0}})
        with self.assertRaises(ValueError):
            review.public_observation({'status': 'LOCAL_STATUS', 'unrecognized_private_field': 'secret'})

    def test_exact_report_self_identification_is_retained_and_flagged(self):
        with tempfile.TemporaryDirectory(prefix='identified-review-fixture-') as directory:
            root = Path(directory)
            fixture(root, identifying_report=True)
            first = review.prepare(root)
            second = review.prepare(root)
            packet, mapping = review.build_packet(root)
            identity = next(row for row in mapping['runs'] if row['run_id'] == 'w001')
            item = next(row for row in packet['runs'] if row['review_id'] == identity['review_id'])
            raw = (root / 'runs/w001/final_report.json').read_bytes()
            self.assertEqual(item['sealed_report_text'].encode('utf-8'), raw)
            self.assertEqual(review.report_bytes(item['exact_final_report']), raw)
            self.assertTrue(item['residual_identity_risk']['flagged'])
            self.assertFalse(item['residual_identity_risk']['exact_report_redacted'])
            self.assertEqual(first['packet_sha256'], second['packet_sha256'])
            self.assertTrue(first['created'])
            self.assertFalse(second['created'])
            self.assertFalse((root / 'review/identity_map.json').exists())

    def test_missing_seal_and_changed_event_prevent_preparation(self):
        seal_path = self.root / 'runs/w048/native_final_receipt.txt'
        seal = seal_path.read_bytes()
        seal_path.unlink()
        with self.assertRaises(ValueError):
            review.prepare(self.root)
        self.assertFalse((self.root / 'review/input_packet.json').exists())
        seal_path.write_bytes(seal)
        event_path = self.root / 'runs/w048/events.jsonl'
        rows = [json.loads(line) for line in event_path.read_text().splitlines()]
        rows[0]['observation']['local_status']['uses_remaining'] = 100
        event_path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        with self.assertRaises(ValueError):
            review.prepare(self.root)
        self.assertFalse((self.root / 'review/input_packet.json').exists())

    def test_reveal_requires_all_bound_nonplaceholder_judgments(self):
        packet, raw = self.prepared()
        path = self.root / 'results/masked_review.json'
        with self.assertRaises(ValueError):
            review.reveal(self.root)
        valid = make_judgments(packet, raw)
        variants = []
        missing = copy.deepcopy(valid); missing['runs'].pop(); variants.append(missing)
        duplicate = copy.deepcopy(valid); duplicate['runs'][-1] = copy.deepcopy(duplicate['runs'][0]); variants.append(duplicate)
        wrong_packet = copy.deepcopy(valid); wrong_packet['packet_sha256'] = '0' * 64; variants.append(wrong_packet)
        wrong_input = copy.deepcopy(valid); wrong_input['runs'][0]['input_sha256']['final_report.json'] = '0' * 64; variants.append(wrong_input)
        placeholder = copy.deepcopy(valid); placeholder['runs'][0]['jobs']['A']['completion_accounting']['basis'] = ''; variants.append(placeholder)
        for number, variant in enumerate(variants):
            with self.subTest(variant=number):
                dump(path, variant)
                before = path.read_bytes()
                with self.assertRaises(ValueError):
                    review.reveal(self.root)
                self.assertEqual(path.read_bytes(), before)
                self.assertFalse((self.root / 'review/identity_map.json').exists())

    def test_reveal_and_retained_verification_are_deterministic_and_read_only(self):
        packet, raw = self.prepared()
        dump(self.root / 'results/masked_review.json', make_judgments(packet, raw))
        native_before = file_snapshot(self.root / 'runs')
        first = review.reveal(self.root)
        snapshot = file_snapshot(self.root)
        verified = review.verify_retained_review(self.root)
        self.assertEqual(verified['identity_mapping_cells_verified'], 48)
        self.assertEqual(snapshot, file_snapshot(self.root))
        self.assertEqual(native_before, file_snapshot(self.root / 'runs'))
        second = review.reveal(self.root)
        self.assertTrue(first['created']); self.assertFalse(second['created'])
        self.assertEqual(first['mapping_sha256'], second['mapping_sha256'])
        mapping = json.loads((self.root / 'review/identity_map.json').read_text())
        self.assertEqual({row['run_id'] for row in mapping['runs']}, review.EXPECTED_RUNS)
        for row in mapping['runs']:
            item = next(item for item in packet['runs'] if item['review_id'] == row['review_id'])
            self.assertEqual(item['input_sha256'], row['input_sha256'])

    def test_different_packet_or_mapping_is_never_overwritten(self):
        packet, raw = self.prepared()
        packet_path = self.root / 'review/input_packet.json'
        changed = copy.deepcopy(packet); changed['reports_to_review'] = 47
        dump(packet_path, changed)
        changed_bytes = packet_path.read_bytes()
        with self.assertRaises(ValueError):
            review.prepare(self.root)
        self.assertEqual(changed_bytes, packet_path.read_bytes())
        packet_path.write_bytes(raw)
        dump(self.root / 'results/masked_review.json', make_judgments(packet, raw))
        review.reveal(self.root)
        map_path = self.root / 'review/identity_map.json'
        mapping = json.loads(map_path.read_text())
        mapping['runs'][0]['report_condition'] = 'incorrect'
        dump(map_path, mapping)
        changed_bytes = map_path.read_bytes()
        with self.assertRaises(ValueError):
            review.reveal(self.root)
        with self.assertRaises(ValueError):
            review.verify_retained_review(self.root)
        self.assertEqual(changed_bytes, map_path.read_bytes())

    def test_partial_retained_review_presence_fails_verification(self):
        with self.assertRaises(ValueError):
            review.verify_retained_review(self.root)
        self.prepared()
        with self.assertRaises(ValueError):
            review.verify_retained_review(self.root)


if __name__ == '__main__':
    unittest.main()
