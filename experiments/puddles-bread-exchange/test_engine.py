"""Same-author unit checks. Independent review is not claimed."""
from fractions import Fraction as F
import unittest
import engine as E

class EngineTests(unittest.TestCase):
    def test_single_sensor(self):
        self.assertEqual(E.independent_posterior(1,1,F(1,5)),F(4,5))
    def test_single_negative(self):
        self.assertEqual(E.independent_posterior(0,1,F(1,5)),F(1,5))
    def test_ten_positive(self):
        self.assertEqual(E.independent_posterior(10,10,F(1,5)),F(1048576,1048577))
    def test_tie(self):
        self.assertEqual(E.independent_posterior(5,10,F(1,5)),F(1,2))
    def test_marginal_control(self):
        for r in E.MARGINAL_ERRORS:
            for a in E.SHARED_FRACTIONS:
                q=r*a; e=E.local_error(r,q)
                self.assertEqual(q+(1-2*q)*e,r)
    def test_copy_illusion(self):
        p=E.predict([1],[10],F(1,5),F(0))
        self.assertGreater(p['headcount'],F(99999,100000))
        self.assertEqual(p['receipts'],F(4,5))
    def test_loud_minority(self):
        p=E.predict([1,0,0],[8,1,1],F(1,5),F(0))
        self.assertEqual(p['headcount'],F(4096,4097))
        self.assertEqual(p['receipts'],F(1,5))
    def test_copy_invariance(self):
        a=E.predict([1,0,0],[8,1,1],F(1,5),F(1,10))
        b=E.predict([1,0,0],[1,1,8],F(1,5),F(1,10))
        self.assertNotEqual(a['headcount'],b['headcount'])
        for r in ('receipts','shared_cause'): self.assertEqual(a[r],b[r])
    def test_no_shared_fault(self):
        for bits in ([1],[1,0,0],[1]*10):
            p=E.predict(bits,[1]*len(bits),F(1,5),F(0))
            self.assertEqual(p['receipts'],p['shared_cause'])
    def test_all_rules_independent(self):
        p=E.predict([1]*8+[0]*2,[1]*10,F(1,5),F(0))
        self.assertEqual(len(set(p.values())),1)
    def test_shared_ceiling(self):
        q=F(3,20); p=E.predict([1]*10,[1]*10,F(1,5),q)
        self.assertLess(p['shared_cause'],1-q)
        self.assertEqual(E.decide(p['shared_cause']),'hold')
    def test_shared_floor(self):
        q=F(3,20); p=E.predict([0]*10,[1]*10,F(1,5),q)
        self.assertGreater(p['shared_cause'],q)
    def test_complement(self):
        a=E.predict([1,1,0],[4,3,3],F(1,5),F(1,10))
        b=E.predict([0,0,1],[4,3,3],F(1,5),F(1,10))
        for r in E.RULES: self.assertEqual(a[r]+b[r],1)
    def test_boundaries(self):
        for p,act in [(F(9,10),'buy'),(F(1,10),'reject'),(F(1,2),'hold'),(F(899,1000),'hold')]:
            self.assertEqual(E.decide(p),act)
    def test_payoffs(self):
        self.assertEqual(E.payoff('buy',1),1)
        self.assertEqual(E.payoff('buy',0),-9)
        self.assertEqual(E.payoff('reject',0),1)
        self.assertEqual(E.payoff('reject',1),-9)
        self.assertEqual(E.payoff('hold',1),0)
    def test_grid(self):
        self.assertEqual(len(list(E.cells())),72)
        self.assertTrue(all(sum(c.copies)==10 for c in E.cells()))
    def test_mass(self):
        c=E.Cell('mixed',F(1,5),F(3,4))
        self.assertEqual(sum(r['weight'] for r in E.histories(c)),1)
    def test_zero_mass_excluded(self):
        c=E.Cell('choir',F(1,5),F(0))
        rows=list(E.histories(c))
        self.assertEqual(len(rows),4)
        self.assertTrue(all(r['weight']>0 and r['shared_fault']==0 for r in rows))
    def test_latent_truth_signal(self):
        c=E.Cell('mixed',F(1,5),F(1,2))
        for r in E.histories(c):
            self.assertEqual(r['bits'],tuple(r['truth']^r['shared_fault']^e for e in r['local_errors']))
    def test_known_summary(self):
        c=E.Cell('choir',F(1,5),F(0)); m=E.summarize(c,E.histories(c))['metrics']
        self.assertEqual(m['headcount']['exact']['wrong_mass'],'1/5')
        self.assertEqual(m['receipts']['exact']['brier'],'4/25')
        self.assertIsNone(m['receipts']['decisive_accuracy'])
    def test_invalid_bits(self):
        for b in ([],[2],[True],['1']):
            with self.assertRaises(ValueError): E.predict(b,[1]*len(b),F(1,5),F(0))
    def test_invalid_weights(self):
        for w in ([],[0],[-1],[1.5]):
            with self.assertRaises(ValueError): E.predict([1],w,F(1,5),F(0))
    def test_invalid_rate(self):
        for r,q in [(F(1,2),F(0)),(F(1,5),F(1,5)),(F(1,5),F(-1,10))]:
            with self.assertRaises(ValueError): E.local_error(r,q)
    def test_invalid_probability(self):
        for p in (F(-1),F(2)):
            with self.assertRaises(ValueError): E.decide(p)

if __name__=='__main__': unittest.main()
