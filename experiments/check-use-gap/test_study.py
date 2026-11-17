import copy
import hashlib
import importlib.util
import json
import math
import unittest
from pathlib import Path
from study import Config, Planner, schedules, replay, oracle_count, enumerate_policy_values, require, primary_configs, canonical
from verify_certificates import check_certificate
from audit import faults, tiny_witness


class PermissionTests(unittest.TestCase):
    def test_primary_grid_has_1056_cells(self):
        self.assertEqual(len(list(primary_configs())), 1056)

    def test_schedule_counts_equal_transition_combinations(self):
        for h in range(1, 8):
            for k in range(h + 1):
                c = Config(h, k, 4, 1, 'snapshot')
                self.assertEqual(len(schedules(c)), sum(math.comb(h, j) for j in range(k + 1)))

    def test_versions_count_transitions_not_validity(self):
        w = next(w for w in schedules(Config(2, 2, 4, 1, 'snapshot')) if w[0] == (1, 0, 1))
        self.assertEqual(w[1], (0, 1, 2))

    def test_snapshot_does_not_reveal_realized_future(self):
        p = Planner(Config(1, 1, 2, 1, 'snapshot'))
        self.assertEqual(len(p.worlds), 2)
        self.assertTrue(all(w[0][0] == 1 and w[1][0] == 0 for w in p.worlds))
        self.assertEqual(p.choose(0, (0, 1), 0), 'stop')

    def test_raw_not_admissible_under_ambiguous_next_permission(self):
        p = Planner(Config(1, 1, 2, 1, 'snapshot'))
        self.assertIsNone(p.branches('raw', 0, (0, 1), 0))

    def test_stable_valid_grant_permits_raw(self):
        p = Planner(Config(2, 0, 4, 1, 'snapshot'))
        self.assertEqual(p.solve(), (1, 1))
        self.assertEqual(p.choose(0, (0,), 0), 'raw')

    def test_stable_revocation_has_no_false_obligation(self):
        p = Planner(Config(2, 0, 4, 0, 'atomic'))
        self.assertEqual(p.solve(), (0, 0))
        self.assertEqual(oracle_count(p.c, p.worlds), 0)

    def test_main_route_always_available_when_budget_suffices(self):
        for mode in ('snapshot', 'compare', 'atomic'):
            p = Planner(Config(4, 4, 4, 1, mode))
            self.assertEqual(p.solve()[0], len(p.worlds))

    def test_deadline_excludes_long_main_route(self):
        p = Planner(Config(3, 1, 4, 1, 'snapshot')); p.solve()
        self.assertNotIn('main', [a['action'] for a in p.nodes[(0, tuple(range(4)), 0)]['alternatives']])

    def test_no_churn_snapshot_reaches_physical_ceiling(self):
        for initial in (0, 1):
            for main in (2, 6):
                p = Planner(Config(3, 0, main, initial, 'snapshot'))
                self.assertEqual(p.solve()[0], oracle_count(p.c, p.worlds))

    def test_single_revocation_blocks_every_attempt_strict_shortcut(self):
        for h in range(1, 9):
            self.assertEqual(Planner(Config(h, 1, h + 1, 1, 'snapshot')).solve(), (0, 0))

    def test_fully_unconstrained_churn_blocks_snapshot_shortcut(self):
        for h in range(1, 7):
            for initial in (0, 1):
                self.assertEqual(Planner(Config(h, h, h + 1, initial, 'snapshot')).solve()[0], 0)

    def test_last_known_switch_can_license_safe_raw(self):
        p = Planner(Config(3, 1, 6, 0, 'snapshot'))
        w = next(i for i,x in enumerate(p.worlds) if x[0] == (0, 1, 1, 1))
        r = replay(p, w)
        self.assertTrue(r['completed'])
        self.assertEqual([e['action'] for e in r['events']], ['inspect', 'raw'])

    def test_fresh_query_does_not_stop_next_tick_revocation(self):
        p = Planner(Config(2, 1, 4, 1, 'snapshot'))
        b = tuple(i for i,w in enumerate(p.worlds) if w[0][1] == 1)
        self.assertGreater(len(b), 1)
        self.assertIsNone(p.branches('raw', 1, b, 0))

    def test_conditional_denial_is_authorized_request_not_forbidden_attempt(self):
        p = Planner(Config(2, 2, 4, 1, 'atomic'))
        r = replay(p, next(i for i,w in enumerate(p.worlds) if w[0] == (1, 0, 1)))
        self.assertEqual(r['unauthorized_raw_attempts'], 0)
        self.assertFalse(r['events'][0]['admitted'])
        self.assertTrue(r['completed'])

    def test_exact_compare_rejects_changed_version_even_when_valid(self):
        p = Planner(Config(2, 2, 4, 1, 'compare'))
        b = tuple(i for i,w in enumerate(p.worlds) if w[0] == (1, 0, 1))
        step = p.branches('compare', 1, b, 0)
        self.assertEqual(step[0], 0)
        self.assertEqual(step[2][0][0], 'denied')

    def test_h4_k2_exhibit_counts(self):
        self.assertEqual([Planner(Config(4, 2, 6, 1, m)).solve()[0]
                          for m in ('snapshot', 'compare', 'atomic')], [3, 9, 10])

    def test_cost_difference_not_safety_difference(self):
        self.assertEqual([Planner(Config(8, 8, 4, 1, m)).solve()
                          for m in ('snapshot', 'compare', 'atomic')], [(256, 1024), (256, 768), (256, 544)])

    def test_atomic_reaches_oracle_in_every_small_cell(self):
        for h in range(1, 5):
            for k in range(h + 1):
                for main in (2, 6):
                    for initial in (0, 1):
                        p = Planner(Config(h, k, main, initial, 'atomic'))
                        self.assertEqual(p.solve()[0], oracle_count(p.c, p.worlds))

    def test_direct_replay_equals_planner_value(self):
        for mode in ('snapshot', 'compare', 'atomic'):
            p = Planner(Config(5, 3, 4, 0, mode)); p.solve()
            rr = [replay(p, i) for i in range(len(p.worlds))]
            self.assertEqual((sum(r['completed'] for r in rr),sum(r['ticks_spent'] for r in rr)), p.solve())
            self.assertTrue(all(r['unauthorized_raw_attempts'] == 0 for r in rr))

    def test_action_enumeration_order_does_not_change_certificate(self):
        for mode in ('snapshot', 'compare', 'atomic'):
            c = Config(5, 3, 4, 0, mode)
            self.assertEqual(Planner(c).certificate(), Planner(c, reverse=True).certificate())

    def test_explicit_policy_trees_match_bellman_solution(self):
        for mode in ('snapshot', 'compare', 'atomic'):
            c = Config(3, 2, 6, 1, mode)
            optimum = min(enumerate_policy_values(c), key=lambda x:(-x[0], x[1]))
            self.assertEqual(optimum, Planner(c).solve())

    def test_certificate_checker_accepts_valid_proof(self):
        p = Planner(Config(4, 2, 6, 1, 'compare'))
        self.assertEqual(check_certificate(p.certificate())['root_value'], [9, 20])

    def test_certificate_checker_rejects_inflated_success(self):
        d = Planner(Config(3, 2, 6, 1, 'compare')).certificate()
        d['nodes'][d['root']][3] += 1
        with self.assertRaises(ValueError): check_certificate(d)

    def test_certificate_checker_rejects_omitted_better_action(self):
        d = Planner(Config(2, 2, 6, 1, 'atomic')).certificate()
        d['nodes'][d['root']][6] = [a for a in d['nodes'][d['root']][6] if a[0] != 1]
        with self.assertRaises(ValueError): check_certificate(d)

    def test_certificate_checker_rejects_future_information_leak(self):
        d = Planner(Config(2, 2, 6, 1, 'snapshot')).certificate()
        d['nodes'][d['root']][1] = '1'
        with self.assertRaises(ValueError): check_certificate(d)

    def test_invalid_inputs_are_rejected(self):
        for args in [(0,0,4,1,'snapshot'), (3,4,4,1,'snapshot'),(2,1,4,1,'magic')]:
            with self.assertRaises(ValueError): Config(*args)

    def test_runtime_checks_survive_python_optimization(self):
        with self.assertRaises(ValueError): require(False, 'not a Python assert')

    def test_minimal_counterexample_is_one_action(self):
        w = tiny_witness()
        self.assertEqual(set(w['possible_worlds']), {'10','11'})
        self.assertTrue(w['raw_request']['10']['forbidden_attempt'])
        self.assertTrue(w['conditional_request']['10']['request_allowed'])

    def test_gateway_negative_controls_detected(self):
        data = faults()['summary']
        for name, row in data.items():
            if name == 'correct_atomic': self.assertIsNone(row['smallest_witness'])
            else: self.assertIsNotNone(row['smallest_witness'])
        self.assertGreater(data['cached_permission']['unauthorized_effect'], 0)
        self.assertEqual(data['deny_everything']['unauthorized_effect'], 0)
        self.assertGreater(data['deny_everything']['missed_allowed_execution'], 0)
        self.assertGreater(data['invent_success']['false_completion_report'], 0)

    def test_baseline_reproduces_original_result_hash(self):
        spec = importlib.util.spec_from_file_location('round_one', Path(__file__).parent/'baseline/study.py')
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        raw = (json.dumps(mod.run(),sort_keys=True,indent=2)+'\n').encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), 'd7b96a056cbbf46f70b3292cf5c14aeb5ad18cc71f4c4a78fec5336d0d94b4d1')


if __name__ == '__main__': unittest.main(verbosity=2)
