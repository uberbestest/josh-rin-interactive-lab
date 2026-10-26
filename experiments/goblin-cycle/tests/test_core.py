"""Focused regressions for GOBLIN-CYCLE-2026-10-26-001. stdlib only."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from core import make_network,audit,wrong_links,path_vote_audit,triangles,record

class CycleExperimentTests(unittest.TestCase):
    def test_single_fault_exact_reconstruction(self):
        for vocab in (8,16,32):
            for seed in range(1,257):
                s=make_network(seed,vocab,'single'); result=audit(s); actual=wrong_links(s)
                self.assertEqual(result['status'],'localized_under_single_fault')
                self.assertEqual(result['candidates'],list(actual))
                self.assertEqual(result['repaired'],s.actual[actual[0]])
                self.assertEqual(path_vote_audit(s),actual)

    def test_three_nodes_do_not_overclaim(self):
        for seed in range(1,257):
            a=audit(make_network(seed,8,'triangle'))
            self.assertEqual(a['status'],'ambiguous')
            self.assertEqual(len(a['candidates']),3)

    def test_star_is_not_a_pass(self):
        for seed in range(1,257):
            s=make_network(seed,16,'star');self.assertEqual(audit(s)['status'],'unobservable')
            self.assertEqual(len(wrong_links(s)),1)
            self.assertEqual(triangles(s),())

    def test_coordinated_relabeling_is_unobservable_by_cycles(self):
        for seed in range(1,257):
            s=make_network(seed,16,'coordinated');self.assertEqual(len(wrong_links(s)),3)
            self.assertEqual(audit(s)['status'],'consistent_not_verified')
            self.assertEqual([d for _,d in triangles(s)],[0,0,0,0])

    def test_two_fault_false_accusation_is_real(self):
        count=0
        for vocab in (8,16,32):
            for seed in range(1,257):
                s=make_network(seed,vocab,'double');result=audit(s)
                if result['status']=='localized_under_single_fault':
                    count+=1
                    guessed=result['candidates'][0]; wrong=wrong_links(s)
                    self.assertNotIn(guessed,wrong) # The proposed culprit is innocent.
                    self.assertNotEqual(result['repaired'],s.actual[guessed])
                    self.assertFalse(any(d for _,d in triangles(s.__class__(s.seed,s.vocab,s.mode,s.count,{**s.observed,guessed:result['repaired']},s.actual,s.codebooks,s.edited))))
        self.assertEqual(count,11)

    def test_specific_counterexample(self):
        s=make_network(40,8,'double');result=audit(s)
        self.assertEqual(wrong_links(s),((0,2),(1,2)))
        self.assertEqual(result['candidates'],[(2,3)])
        self.assertEqual(result['status'],'localized_under_single_fault')
        self.assertEqual([z for _,z in triangles(s)],[0,0,2,2])

if __name__=='__main__':
    unittest.main()
