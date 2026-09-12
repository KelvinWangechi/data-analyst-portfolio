"""Reproduce the revenue analytics calculations. Python 3, standard library only.
Run from any directory: python run_analysis.py
Optional chart: python run_analysis.py --chart (requires matplotlib).
"""
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT
OUT.mkdir(exist_ok=True)

def read(name):
    with (ROOT / 'data' / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

m = read('revenue_analytics_marketing_data.csv')
s = read('revenue_analytics_sales_data.csv')
assert len(m) == 108 and len(s) == 547, 'Source snapshot changed; review expected coverage.'
assert len({(r['Month'], r['Channel']) for r in m}) == len(m), 'Duplicate month/channel key'
assert len({r['Date'] for r in s}) == len(s), 'Duplicate daily date'
assert all(all(v != '' for v in r.values()) for r in m+s), 'Missing values'
assert all(Decimal(r['Ad_Spend']) >= 0 and int(r['Leads_Generated']) >= 0 for r in m)
assert all(0 <= float(r['Conversion_Rate']) <= 1 for r in s)
assert all(0 <= float(r['Click_Through_Rate']) <= 1 for r in m)
dates = sorted(date.fromisoformat(r['Date']) for r in s)
assert dates == [dates[0] + timedelta(days=i) for i in range(len(dates))], 'Date gaps'
assert set(Counter(r['Month'] for r in m).values()) == {6}, 'Incomplete monthly channel coverage'

db = sqlite3.connect(':memory:')
db.row_factory = sqlite3.Row
db.execute('CREATE TABLE marketing (Month TEXT, Channel TEXT, Ad_Spend REAL, Leads_Generated INTEGER, Cost_Per_Acquisition REAL, Click_Through_Rate REAL, Implementation_Phase TEXT)')
db.executemany('INSERT INTO marketing VALUES (?,?,?,?,?,?,?)', [tuple(r.values()) for r in m])
db.execute('CREATE TABLE sales (Date TEXT, Daily_Revenue REAL, Leads_Generated INTEGER, Conversion_Rate REAL, Sales_Qualified_Leads INTEGER, Implementation_Phase TEXT)')
db.executemany('INSERT INTO sales VALUES (?,?,?,?,?,?)', [tuple(r.values()) for r in s])
channels = [dict(r) for r in db.execute((ROOT/'channel_metrics.sql').read_text())]
# Aggregate both grains before joining. A raw date-month join would multiply spend by days.
reconciliation = [dict(r) for r in db.execute('''
WITH m AS (SELECT Month, SUM(Leads_Generated) AS marketing_leads FROM marketing GROUP BY Month),
s AS (SELECT substr(Date,1,7) AS Month, SUM(Leads_Generated) AS sales_leads FROM sales GROUP BY substr(Date,1,7))
SELECT m.Month, m.marketing_leads, s.sales_leads,
       s.sales_leads-m.marketing_leads AS lead_difference
FROM m JOIN s ON m.Month=s.Month ORDER BY m.Month
''')]
for filename, rows in [('channel_metrics.csv', channels), ('monthly_reconciliation.csv', reconciliation)]:
    with (OUT/filename).open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
spend = sum(Decimal(r['Ad_Spend']) for r in m)
leads = sum(int(r['Leads_Generated']) for r in m)
assert sum(r['recorded_leads'] for r in channels) == leads
assert abs(sum(Decimal(str(r['recorded_spend'])) for r in channels)-spend) < Decimal('.01')
summary = {
    'data_origin': 'See data/README.md for data provenance and methodology.',
    'period': [str(dates[0]), str(dates[-1])],
    'marketing_rows': len(m), 'sales_rows': len(s),
    'recorded_spend': str(spend), 'recorded_leads': leads,
    'recorded_spend_per_lead': str((spend/leads).quantize(Decimal('.01'))),
    'unweighted_mean_of_row_spend_per_lead': round(sum(float(r['Ad_Spend'])/int(r['Leads_Generated']) for r in m)/len(m),2),
    'supplied_cpa_disagrees_with_spend_per_lead_by_more_than_one_cent_rows': sum(abs(float(r['Cost_Per_Acquisition'])-float(r['Ad_Spend'])/int(r['Leads_Generated'])) > .0100001 for r in m),
    'months_with_different_lead_totals': sum(r['lead_difference'] != 0 for r in reconciliation),
    'structural_checks': 'Passed: unique grains, nonempty values, nonnegative marketing counts/spend, rates in range, complete daily coverage, six channel rows per month, aggregate reconciliation.',
    'files_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').glob('*.csv')},
    'limitations': ['Currency not explicitly documented.', 'No customer acquisition counts, customer IDs or attribution keys.', 'Sales daily lead totals and marketing lead totals have no documented reconciliation.', 'Zero recorded organic ad spend does not establish zero total acquisition cost.', 'Before/After labels do not establish causal impact.']
}
(OUT/'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'summary':summary,'channels':channels,'first_month_reconciliation':reconciliation[0]},indent=2))
if '--chart' in sys.argv:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=160)
    fig.patch.set_facecolor('#f7f7f3'); ax.set_facecolor('#f7f7f3')
    labels=[r['Channel'] for r in channels]
    values=[r['recorded_spend_per_lead'] for r in channels]
    ax.barh(labels, values, color='#294c60', height=.58)
    ax.invert_yaxis(); ax.set_xlim(0, max(values)*1.22)
    for i,v in enumerate(values): ax.text(v+1,i,f'{v:.2f}',va='center',fontsize=12)
    ax.set_xlabel('Recorded spend / recorded leads (currency units per lead)',labelpad=14,fontsize=11)
    ax.tick_params(axis='both',labelsize=11,length=0,pad=10)
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.xaxis.grid(True,color='#d8dde0',linewidth=.7); ax.set_axisbelow(True)
    fig.text(.07,.94,'What does each recorded lead cost?',fontsize=22,weight='bold',color='#203747')
    fig.text(.07,.885,'Jan 2023 to Jun 2024 | 108 channel-month rows',fontsize=11,color='#48545b')
    fig.text(.07,.08,'Sum spend, then divide by sum leads. Customer acquisition cost needs acquired-customer counts.',fontsize=10,color='#48545b')
    fig.text(.07,.045,'Zero organic ad spend excludes unrecorded labour and content costs. This is not a budget-allocation ranking.',fontsize=10,color='#48545b')
    fig.subplots_adjust(left=.21,right=.94,top=.82,bottom=.21)
    fig.savefig(OUT/'channel_cost_per_lead.png',facecolor=fig.get_facecolor())
