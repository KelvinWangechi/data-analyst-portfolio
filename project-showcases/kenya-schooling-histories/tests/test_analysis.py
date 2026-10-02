"""Artificial records test arithmetic only; these are not survey results."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pandas as pd
from analyze import classify, summarize, analyze, CORE

class ProtocolTests(unittest.TestCase):
    def test_classification(self):
        self.assertEqual([classify(1, 0), classify(1, 1), classify(0, 1),
                          classify(None, 1), classify(0, 0, True)], list('ABC UU'.replace(' ', '')))

    def test_weighted_common_denominator_and_bounds(self):
        d = pd.DataFrame({'weight': [1., 3., 6., 10.], 'state': list('ABCU'),
                          'a4_outofschool': [1., 1., 0., 1.]})
        r = summarize(d)
        self.assertEqual((r['A'], r['B'], r['C'], r['O']), (10, 30, 60, 40))
        self.assertEqual((r['missing_share'], r['direct_o']), (50, 70))
        self.assertEqual((r['A_bound_low'], r['A_bound_high']), (5, 55))

    def test_all_unclassified(self):
        r = summarize(pd.DataFrame({'weight': [2.], 'state': ['U'], 'a4_outofschool': [None]}))
        self.assertIsNone(r['A'])
        self.assertEqual(r['missing_share'], 100)

    def fixture(self):
        d = pd.DataFrame([{k: 1 for k in CORE} for _ in range(3)])
        d['hhmemid'] = [1, 2, 3]
        d['a4a_ageyrs'] = [6, 12, 18]
        d['weight'] = [1., 2., 3.]
        d['a4a_attendschool'] = 0
        return d

    def test_age_restriction(self):
        _, audit = analyze(self.fixture(), {'status_codes': {'1':'refugee'}})
        self.assertEqual(audit['eligible_n'], 2)

    def test_invalid_weight_and_duplicates_stop(self):
        d = self.fixture()
        d.loc[0, 'weight'] = 0
        with self.assertRaisesRegex(ValueError, 'weights'):
            analyze(d, {'status_codes': {'1':'refugee'}})
        d = self.fixture()
        d.loc[1, 'hhmemid'] = 1
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            analyze(d, {'status_codes': {'1':'refugee'}})

    def test_status_mismatch_stops(self):
        with self.assertRaisesRegex(ValueError, 'status'):
            analyze(self.fixture(), {'status_codes': {'1':'host'}})

if __name__ == '__main__':
    unittest.main()
