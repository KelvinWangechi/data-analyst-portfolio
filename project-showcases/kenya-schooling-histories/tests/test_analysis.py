"""Artificial records test arithmetic only; these are not survey results."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pandas as pd
from analyze import classify, summarize, analyze, CORE
from build_release import disclosure_tables
import numpy as np

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

    def test_reviewed_stratum_basis_records_disagreement(self):
        stats, audit = analyze(self.fixture(), {'status_codes': {'1':'host'},
            'reporting_basis':'released_location_strata'})
        self.assertEqual(audit['status_location_mismatch_n'], 2)
        self.assertEqual(set(stats['sample']), {'refugee'})

    def test_unknown_status_not_allowed_under_stratum_basis(self):
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            analyze(self.fixture(), {'status_codes': {'2':'host'},
                'reporting_basis':'released_location_strata'})

    def test_planned_enrolment_is_not_daily_attendance(self):
        d=self.fixture()
        d['a4_outofschool']=0
        d['a4a_schoolenrolment']=2
        d['a4a_attendschool']=0
        stats,_=analyze(d,{'status_codes':{'1':'refugee'}})
        self.assertTrue((stats.C==100).all())

    def test_contradiction_stays_unclassified(self):
        d=self.fixture()
        d.loc[0,'a4_outofschool']=0
        d.loc[0,'a4a_everattendschool']=0
        stats,audit=analyze(d,{'status_codes':{'1':'refugee'}})
        r=stats[stats.age_band=='6–17'].iloc[0]
        self.assertEqual((audit['diagnostic_unresolved_n'],r.unclassified_n),(1,1))
        self.assertAlmostEqual(r.O_bound_low,200/3)
        self.assertEqual(r.O_bound_high,100)

    def test_float32_weights_accumulate_in_float64(self):
        d=pd.DataFrame({'weight':np.array([100000000,1,1],dtype=np.float32),
                        'state':list('ABC'),'a4_outofschool':[1,1,0]})
        self.assertEqual(summarize(d)['eligible_weight'],100000002)

    def test_age_suppression_prevents_subtraction(self):
        rows=[]
        for band,n in [('6–17',9),('6–11',2),('12–14',3),('15–17',4)]:
            rows.append(dict(location='X',sample='refugee',age_band=band,A_n=n,B_n=30,C_n=40,
                eligible_n=100,classified_n=100,A=9.,B=30.,C=61.,O=39.,missing_share=0.))
        result=disclosure_tables(pd.DataFrame(rows))
        self.assertEqual(result.age_band.tolist(),['6–17'])
        self.assertEqual(result.iloc[0].A,9.)

    def test_small_component_withholds_both_components(self):
        d=pd.DataFrame([dict(location='X',sample='host',age_band='6–17',A_n=2,B_n=30,C_n=68,
            eligible_n=100,classified_n=100,A=2.,B=30.,C=68.,O=32.,missing_share=0.)])
        r=disclosure_tables(d).iloc[0]
        self.assertTrue(pd.isna(r.A) and pd.isna(r.B))
        self.assertEqual(r.O,32.)

if __name__ == '__main__':
    unittest.main()
