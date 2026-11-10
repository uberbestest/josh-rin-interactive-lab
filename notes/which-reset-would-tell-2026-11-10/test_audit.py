import copy
import itertools
import json
import tempfile
import unittest
from pathlib import Path
import audit

class DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.summary = audit.build()
        cls.hypotheses = list(itertools.product((-1,0,1), repeat=4))

    def test_raw_count(self):
        self.assertEqual(len(self.raw), 81*4*17)

    def test_all_rows_match_algebra(self):
        for r in self.raw:
            self.assertEqual(r['observation'], audit.independent_response(tuple(r['carriers']), r['intervention'], r['probe']))

    def test_unknown_prior_partitions(self):
        self.assertEqual([p['classes'] for p in self.summary['panels']], [9,21,45,81])

    def test_fixed_prior_partitions(self):
        self.assertEqual([p['classes_fixed_prior'] for p in self.summary['panels']], [7,15,27,27])

    def test_every_partition_matches_independent_algebra(self):
        for depth in range(1,5):
            self.assertEqual(audit.partition(self.hypotheses,depth), audit.reference_partition(self.hypotheses,depth))

    def test_probe_scan_distinguishes_all_sums(self):
        by_sum = {}
        for v in self.hypotheses:
            s = audit.signature(v,audit.PANELS[0])
            if sum(v) in by_sum: self.assertEqual(by_sum[sum(v)],s)
            by_sum[sum(v)] = s
        self.assertEqual(len(set(by_sum.values())),9)

    def test_unavailable_learned_cut_leaves_alias(self):
        self.assertEqual(audit.signature((1,0,0,0),audit.PANELS[2]), audit.signature((0,0,0,1),audit.PANELS[2]))

    def test_available_learned_cut_splits_alias(self):
        self.assertNotEqual(audit.signature((1,0,0,0),audit.PANELS[3]), audit.signature((0,0,0,1),audit.PANELS[3]))

    def test_alias_matches_full_trajectories(self):
        left,right = (1,0,0,0),(0,0,0,1)
        for n in range(4):
            for word in itertools.product((-4,-1,0,1,4),repeat=n):
                for x in range(-4,5):
                    for action in audit.PANELS[2]:
                        a,b=x,x
                        for probe in word:
                            a=audit.step(a,audit.intervene(left,action),probe)
                            b=audit.step(b,audit.intervene(right,action),probe)
                            self.assertEqual(a,b)

    def test_cancellation_is_not_absence(self):
        self.assertEqual(self.summary['zero_aggregate']['hypotheses'],19)
        self.assertEqual(self.summary['zero_aggregate']['with_nonzero_learned'],12)

    def test_clearing_can_unmask(self):
        v=(1,-1,0,0)
        self.assertEqual(audit.response(v,'none',2),0)
        self.assertEqual(audit.response(v,'clear_context',2),1)
        self.assertEqual(self.summary['zero_aggregate']['unmasking_cuts'],36)

    def test_common_prior_matched_controls(self):
        for r in self.summary['matched_prior_controls']:
            self.assertEqual(r['different'],r['learned'] != 0)

    def test_mismatched_priors_change_without_learning(self):
        self.assertEqual(len(self.summary['mismatched_prior_controls']),6)
        self.assertTrue(all(r['different_without_learning'] for r in self.summary['mismatched_prior_controls']))

    def test_interventions_do_not_mutate_original(self):
        v=(1,-1,1,-1)
        for a in audit.INTERVENTIONS: audit.intervene(v,a)
        self.assertEqual(v,(1,-1,1,-1))

    def test_each_cut_changes_only_named_carrier(self):
        v=(1,1,1,1)
        self.assertEqual(audit.intervene(v,'clear_context'),(1,0,1,1))
        self.assertEqual(audit.intervene(v,'clear_world'),(1,1,0,1))
        self.assertEqual(audit.intervene(v,'clear_learned'),(0,1,1,1))

    def test_invalid_carriers_rejected(self):
        for v in [(1,0,0), [0,0,0,0], (True,0,0,0), (2,0,0,0)]:
            with self.assertRaises(ValueError): audit.step(0,v,0)

    def test_invalid_queries_rejected(self):
        for x,p in [(5,0),(0,9),(False,0),(0,True)]:
            with self.assertRaises(ValueError): audit.step(x,(0,0,0,0),p)
        with self.assertRaises(ValueError): audit.intervene((0,0,0,0),'erase_everything')

    def test_clipping_and_thresholds(self):
        self.assertEqual(audit.step(4,(1,1,1,1),8),4)
        self.assertEqual(audit.step(-4,(-1,-1,-1,-1),-8),-4)
        self.assertEqual([audit.observe(x) for x in range(-4,5)],[-1,-1,0,0,0,0,0,1,1])

    def test_reverse_order_identical(self):
        raw,summary=audit.build(True)
        self.assertEqual(raw,self.raw)
        self.assertEqual(summary,self.summary)

    def test_corrupt_summary_rejected(self):
        bad=copy.deepcopy(self.summary);bad['panels'][0]['classes']=81
        with self.assertRaises(ValueError):audit.verify(self.raw,bad)

    def test_corrupt_observation_rejected(self):
        bad=copy.deepcopy(self.raw);bad[0]['observation']=-bad[0]['observation']
        with self.assertRaises(ValueError):audit.verify(bad,self.summary)

    def test_missing_observation_rejected(self):
        with self.assertRaises(ValueError):audit.verify(self.raw[:-1],self.summary)

    def test_existing_output_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):audit.write(Path(d))

    def test_disk_forward_reverse_identical(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=Path(d)/'a',Path(d)/'b';audit.write(a);audit.write(b,True)
            self.assertEqual(sorted(p.name for p in a.iterdir()), sorted(p.name for p in b.iterdir()))
            for p in a.iterdir():self.assertEqual(p.read_bytes(),(b/p.name).read_bytes())

if __name__=='__main__':unittest.main()
