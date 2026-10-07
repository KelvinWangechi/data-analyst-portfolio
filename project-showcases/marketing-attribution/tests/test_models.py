"""Independent small examples exercise model behavior and conservation."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from models import Journey, rule_weights, collapse, allocations, bootstrap_markov

T=datetime(2018,7,1,tzinfo=timezone.utc)

def journey(channels,converted=True,value=10):
    return Journey(tuple(channels),tuple(T+timedelta(days=i) for i in range(len(channels))),converted,value if converted else 0)

class CreditRules(unittest.TestCase):
    def test_short_position_paths(self):
        for n,expected in [(1,[1]),(2,[.5,.5]),(3,[.4,.2,.4]),(4,[.4,.1,.1,.4])]:
            js=journey(['A']*n)
            np.testing.assert_allclose(rule_weights(js.channels,js.times,'Position based'),expected)

    def test_half_life(self):
        times=(T,T+timedelta(days=7))
        np.testing.assert_allclose(rule_weights(('A','B'),times,'Time decay'),[1/3,2/3])

    def test_repeated_events_keep_linear_credit(self):
        count,values,_=allocations([journey(['A','A','B'],value=12)],['A','B'])
        np.testing.assert_allclose(count['Linear'],[2/3,1/3])
        np.testing.assert_allclose(values['Linear'],[8,4])
        self.assertEqual(collapse(('A','A','B','A','A')),('A','B','A'))

    def test_all_rules_conserve_count_and_value(self):
        js=[journey(['A']),journey(['A','B','C'],value=7),journey(['C'],False)]
        counts,values,mk=allocations(js,['A','B','C'])
        for credit in counts.values():
            self.assertAlmostEqual(credit.sum(),2)
        for credit in values.values():
            self.assertAlmostEqual(credit.sum(),17)
        self.assertAlmostEqual(mk['base'],2/3)

class MarkovBehavior(unittest.TestCase):
    def test_nonconverters_change_transition_network(self):
        # START -> A or B equally. A -> B. B converts half the time.
        # Redirecting entries to A loses half the base probability;
        # redirecting entries to B loses all of it. Shares = 1/3, 2/3.
        js=[journey(['A','B']),journey(['B'],False)]
        counts,_,mk=allocations(js,['A','B'])
        self.assertAlmostEqual(mk['base'],.5)
        np.testing.assert_allclose(mk['effects'],[.5,1])
        np.testing.assert_allclose(mk['shares'],[1/3,2/3])

    def test_self_loops_do_not_create_extra_conversions(self):
        js=[journey(['A','A','B']),journey(['A','A'],False)]
        _,_,mk=allocations(js,['A','B'])
        self.assertAlmostEqual(mk['base'],.5)
        np.testing.assert_allclose(mk['matrix'].sum(axis=1),1)

    def test_unobserved_channel_gets_no_credit(self):
        _,_,mk=allocations([journey(['A']),journey(['A'],False)],['A','B'])
        np.testing.assert_allclose(mk['shares'],[1,0])

    def test_zero_conversion_paths(self):
        counts,_,mk=allocations([journey(['A'],False)],['A','B'])
        self.assertEqual(mk['base'],0)
        np.testing.assert_allclose(counts['Markov'],[0,0])

    def test_bootstrap_is_reproducible(self):
        js=[journey(['A']),journey(['B']),journey(['A','B'],False)]*10
        np.testing.assert_allclose(bootstrap_markov(js,['A','B'],20,41),bootstrap_markov(js,['A','B'],20,41))

if __name__=='__main__':
    unittest.main()
