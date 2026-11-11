"""Same-author engineering tests; not independent scientific replication."""
from fractions import Fraction as F
from itertools import product
import unittest
import audit as a


class ResetAudit(unittest.TestCase):
    def test_01_nine_totals_have_distinct_complete_scans(self):
        by_total = {}
        for v in a.WORLDS:
            by_total.setdefault(sum(v), a.scan(v))
            self.assertEqual(by_total[sum(v)], a.scan(v))
        self.assertEqual(len(set(by_total.values())), 9)

    def test_02_all_5508_parent_responses_match_threshold_formula(self):
        count = 0
        for v, cut, probe in product(a.WORLDS, (None, 0, 1, 2), a.PROBES):
            total = sum(v)-(v[cut] if cut is not None else 0)+probe
            expected = -1 if total < -2 else 1 if total > 2 else 0
            self.assertEqual(a.response(v, cut, probe), expected)
            count += 1
        self.assertEqual(count, 5508)

    def test_03_parent_partitions_reproduce(self):
        self.assertEqual(a.parent_partitions(), [
            {'classes': 9, 'largest': 19}, {'classes': 21, 'largest': 7},
            {'classes': 45, 'largest': 3}, {'classes': 81, 'largest': 1}])

    def test_04_all_profiles_normalize(self):
        for v, q, m, dep in product(a.WORLDS, a.QS, a.REPEATS, ('independent', 'persistent')):
            self.assertEqual(sum(p for _, p in a.profiles(v, q, m, dep)), 1)

    def test_05_zero_efficacy_baseline_accuracy(self):
        for m in a.REPEATS:
            self.assertEqual(F(a.metrics(F(0), m)['bayes_accuracy']), F(1, 9))

    def test_06_perfect_efficacy_all_decoders_correct(self):
        for m, dep in product(a.REPEATS, ('independent', 'persistent')):
            r = a.metrics(F(1), m, dep)
            self.assertEqual(r['bayes_accuracy'], '1')
            for k in ('any_change', 'strict_full_record'):
                self.assertEqual(r[k], {'correct': '1', 'wrong': '0', 'inconsistent': '0'})

    def test_07_ordered_reference_one_attempt_all_probabilities(self):
        for q in a.QS:
            self.assertEqual(a.metrics(q, 1), a.raw_reference(q, 1)[0])

    def test_08_ordered_reference_two_attempts_all_probabilities(self):
        for q in a.QS:
            self.assertEqual(a.metrics(q, 2), a.raw_reference(q, 2)[0])

    def test_09_ordered_reference_three_attempts(self):
        self.assertEqual(a.metrics(F(1, 2), 3), a.raw_reference(F(1, 2), 3)[0])

    def test_10_corrected_half_two_strict_rates(self):
        self.assertEqual(a.metrics(F(1, 2), 2)['strict_full_record'],
                         {'correct': '1/8', 'wrong': '49/432', 'inconsistent': '329/432'})

    def test_11_original_half_two_lossy_rates_and_bayes_reproduce(self):
        r = a.metrics(F(1, 2), 2)
        self.assertEqual(r['bayes_accuracy'], '191/288')
        self.assertEqual(r['any_change'],
                         {'correct': '125/216', 'wrong': '121/432', 'inconsistent': '61/432'})

    def test_12_decoders_equal_for_single_attempt(self):
        for q in a.QS:
            r = a.metrics(q, 1)
            self.assertEqual(r['any_change'], r['strict_full_record'])

    def test_13_mixed_attempt_witness_is_not_hidden_by_strict_decoder(self):
        obs = (1, ((0, 1), (0,), (0,)))
        self.assertEqual(a.decode(obs, False), (1, 0, 0, 0))
        self.assertIsNone(a.decode(obs, True))

    def test_14_independent_bayes_accuracy_monotone(self):
        for q in a.QS:
            xs = [F(a.metrics(q, m)['bayes_accuracy']) for m in a.REPEATS]
            self.assertEqual(xs, sorted(xs))

    def test_15_persistent_failure_repetition_gives_no_gain(self):
        for q in a.QS:
            first = a.metrics(q, 1, 'persistent')
            for m in a.REPEATS:
                row = a.metrics(q, m, 'persistent')
                for key in ('bayes_accuracy', 'any_change', 'strict_full_record'):
                    self.assertEqual(row[key], first[key])

    def test_16_full_raw_event_denominator_and_counts(self):
        _, rows = a.raw_reference(F(1, 2), 2, keep_events=True)
        self.assertEqual(len(rows), 5184)
        self.assertEqual(sum(F(r['joint_probability']) for r in rows), 1)
        self.assertEqual({k: sum(r['strict'] == k for r in rows)
                          for k in ('correct', 'wrong', 'inconsistent')},
                         {'correct': 648, 'wrong': 588, 'inconsistent': 3948})

    def test_17_full_miswire_alias_and_denominator(self):
        rows = a.miswire()
        self.assertEqual(len(rows), 81)
        self.assertEqual(sum(r['wrong'] for r in rows), 54)

    def test_18_known_zero_prior_flags_every_wrong_alias_in_subset(self):
        subset = [r for r in a.miswire() if r['known_P0']]
        self.assertEqual(len(subset), 27)
        self.assertEqual(sum(r['known_P0_rejects'] for r in subset), 18)
        self.assertTrue(all(r['wrong'] == r['known_P0_rejects'] for r in subset))

    def test_19_two_calibrations_distinguish_all_five_candidates(self):
        rows = a.calibration()['candidates']
        self.assertEqual({r['actual_target']: r['observed_drops'] for r in rows},
                         {'none': [0, 0], 'L': [1, 0], 'C': [0, 1], 'W': [-1, 0], 'P': [0, -1]})

    def test_20_one_preparation_cannot_distinguish_five_targets(self):
        self.assertEqual(a.calibration()['single_preparation_max_outcomes'], 3)
        for v in a.WORLDS:
            self.assertLessEqual(len({a.scan(v, k) for k in (None, 0, 1, 2, 3)}), 3)

    def test_21_reversed_traversal_matches_exactly(self):
        self.assertEqual(a.metrics(F(1, 2), 2), a.metrics(F(1, 2), 2, reverse=True))
        self.assertEqual(a.raw_reference(F(1, 2), 2, keep_events=True),
                         a.raw_reference(F(1, 2), 2, reverse=True, keep_events=True))
        self.assertEqual(a.miswire(), a.miswire(reverse=True))

    def test_22_invalid_inputs_rejected_in_both_python_modes(self):
        for q, m, dep in ((F(-1), 1, 'independent'), (F(2), 1, 'independent'),
                          (0.5, 1, 'independent'), (F(1, 2), 0, 'independent'),
                          (F(1, 2), True, 'independent'), (F(1, 2), 1, 'unknown')):
            with self.assertRaises(ValueError):
                a.metrics(q, m, dep)
        for v, cut, probe in (((0, 0, 0), None, 0), ((0, 0, 0, 2), None, 0),
                               ((True, 0, 0, 0), None, 0), ((0, 0, 0, 0), True, 0),
                               ((0, 0, 0, 0), None, 9)):
            with self.assertRaises(ValueError):
                a.response(v, cut, probe)


if __name__ == '__main__':
    unittest.main()
