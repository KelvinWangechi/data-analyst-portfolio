import csv
import json
import unittest
from pathlib import Path
from coding import baseline,validate

ROOT=Path(__file__).resolve().parent
class EvidenceTests(unittest.TestCase):
    def test_fabricated_quote_is_rejected(self):
        with self.assertRaises(ValueError):
            validate('Let me skip a week.',{'status':'coded','assignments':[{'theme_id':'pause_control','evidence_quote':'cannot afford it','sentiment':'negative'}]})
    def test_empty_response_cannot_receive_a_theme(self):
        with self.assertRaises(ValueError):
            validate('',{'status':'coded','assignments':[]})
        self.assertEqual(validate('',{'status':'no_response','assignments':[]})['status'],'no_response')
    def test_duplicate_theme_rejected(self):
        item={'theme_id':'pause_control','evidence_quote':'skip a week','sentiment':'negative'}
        with self.assertRaises(ValueError): validate('Let me skip a week',{'status':'coded','assignments':[item,item]})
    def test_positive_is_not_negative(self):
        d=json.loads((ROOT/'results/explorer.json').read_text())
        r=next(r for r in d['responses'] if r['response_id']=='R010')
        self.assertEqual({a['theme_id'] for a in r['assignments'] if a['sentiment']=='negative'},{'portion_size'})
    def test_keyword_baseline_exposes_negation_failure(self):
        self.assertIn('affordability',baseline('I can afford it; I just do not think it is worth the price.'))
    def test_r_sql_and_export_counts_agree(self):
        sql=json.loads((ROOT/'results/sql-summary.json').read_text())
        with (ROOT/'results/r-summary.csv').open() as f: r={v['metric']:int(v['value']) for v in csv.DictReader(f)}
        self.assertTrue(all(sql[k]==v for k,v in r.items()))
        d=json.loads((ROOT/'results/explorer.json').read_text())
        eligible=[r for r in d['responses'] if r['reason']=='Too expensive' and r['text'].strip()]
        self.assertEqual(len(eligible),sql['price_with_text'])
        for theme,count in sql['price_issue_counts'].items():
            actual=sum(any(a['theme_id']==theme and a['sentiment']=='negative' for a in r['assignments']) for r in eligible)
            self.assertEqual(actual,count)
    def test_intervals_and_denominators(self):
        with (ROOT/'results/theme-summary.csv').open() as f:
            for r in csv.DictReader(f):
                self.assertLessEqual(int(r['count']),int(r['n']))
                self.assertLessEqual(float(r['lower']),float(r['share'])+1e-12)
                self.assertGreaterEqual(float(r['upper']),float(r['share'])-1e-12)
                self.assertLessEqual(float(r['upper']),1)

if __name__=='__main__': unittest.main()
