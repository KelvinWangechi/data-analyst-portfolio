"""Describe process records without inferring realised savings. Python 3 standard library.
Run: python run_analysis.py. Optional chart: python run_analysis.py --chart.
"""
import csv
import hashlib
import json
import statistics
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(name):
    with (ROOT / 'data' / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def mean(rows, field):
    return statistics.mean(float(r[field]) for r in rows)


process = read('operational_efficiency_process_data.csv')
people = read('operational_efficiency_productivity_data.csv')
assert len(process) == 2192 and len(people) == 599, 'Source snapshot changed.'
assert all(all(v != '' for v in row.values()) for row in process + people)
assert len({(r['Date'], r['Process_Name']) for r in process}) == len(process)
assert all(float(r['Processing_Time_Hours']) >= 0 for r in process)
assert all(0 <= float(r['Error_Rate']) <= 1 for r in process)
assert all(int(r['Manual_Steps_Required']) >= 0 for r in process)
dates = sorted({date.fromisoformat(r['Date']) for r in process})
assert dates == [dates[0] + timedelta(days=i) for i in range(len(dates))]
assert set(Counter(r['Date'] for r in process).values()) == {8}
phases = ['Before_Optimization', 'After_Optimization']
assert set(r['Phase'] for r in process) == set(phases)
rows = []
for name in sorted({r['Process_Name'] for r in process}):
    before, after = [[r for r in process if r['Process_Name'] == name and r['Phase'] == ph] for ph in phases]
    b, a = mean(before, 'Processing_Time_Hours'), mean(after, 'Processing_Time_Hours')
    assert len(before) == 92 and len(after) == 182
    rows.append({
        'process': name, 'before_days': len(before), 'after_days': len(after),
        'before_mean_hours': round(b, 4), 'after_mean_hours': round(a, 4),
        'difference_hours': round(b-a, 4), 'relative_decrease_pct': round(100*(b-a)/b, 2),
        'before_mean_error_rate': round(mean(before, 'Error_Rate'), 6),
        'after_mean_error_rate': round(mean(after, 'Error_Rate'), 6),
        'before_mean_manual_steps': round(mean(before, 'Manual_Steps_Required'), 4),
        'after_mean_manual_steps': round(mean(after, 'Manual_Steps_Required'), 4)
    })
rows.sort(key=lambda r: r['difference_hours'], reverse=True)
with (ROOT / 'process_metrics.csv').open('w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)

employee_keys = Counter((r['Month'], r['Employee_ID']) for r in people)
summary = {
    'data_origin': 'See data/README.md for provenance and metric definitions.',
    'process_rows': len(process), 'processes': 8, 'period': [str(dates[0]), str(dates[-1])],
    'phase_days': {ph: len({r['Date'] for r in process if r['Phase'] == ph}) for ph in phases},
    'productivity_rows': len(people), 'unique_employee_month_keys': len(employee_keys),
    'repeated_employee_month_keys': sum(n > 1 for n in employee_keys.values()),
    'excess_rows_over_unique_employee_month_keys': len(people)-len(employee_keys),
    'structural_checks': 'Passed: complete dates, eight processes daily, unique date/process, numeric bounds, phase coverage.',
    'files_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'data').glob('*.csv'))},
    'interpretation': [
        'Phase comparisons are descriptive, without a control group or causal attribution.',
        'Processing_Time_Hours has no documented workload denominator; mean recorded hours is not a validated per-case time.',
        'Means of recorded error rates are unweighted; task volumes are absent, so no pooled error rate is estimated.',
        'Employee-month keys repeat; no deduplication rule, retention rate or employee-level change is inferred.',
        'Labour rates, costs, case volumes and implementation costs are absent; no realised savings or ROI is calculated.'
    ]
}
(ROOT / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'summary': summary, 'process_metrics': rows}, indent=2))

if '--chart' in sys.argv:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=150)
    fig.patch.set_facecolor('#f7f7f3'); ax.set_facecolor('#f7f7f3')
    for i, r in enumerate(rows):
        b, a = r['before_mean_hours'], r['after_mean_hours']
        ax.plot([a, b], [i, i], color='#bdc9cd', linewidth=4, zorder=1)
        ax.scatter([b], [i], color='#294c60', s=75, label='Before: Jun–Aug 2023' if i==0 else None, zorder=3)
        ax.scatter([a], [i], color='#b64e36', s=75, label='After: Sep 2023–Feb 2024' if i==0 else None, zorder=3)
        ax.text(b+.16, i, f'{b:.2f}', va='center', fontsize=10, color='#294c60')
        ax.text(a, i+.25, f'{a:.2f}', va='center', ha='center', fontsize=10, color='#b64e36')
    ax.set_yticks(range(len(rows)), [r['process'] for r in rows]); ax.invert_yaxis()
    ax.set_xlim(0, 10); ax.set_xlabel('Mean recorded processing hours per process-day row', labelpad=12)
    ax.tick_params(length=0, pad=10); ax.xaxis.grid(True, color='#d8dde0'); ax.set_axisbelow(True)
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.legend(loc='lower right', frameon=False)
    fig.text(.06, .94, 'Onboarding has the largest recorded time gap', fontsize=21, weight='bold', color='#203747')
    fig.text(.06, .89, 'Eight processes | 92 before days and 182 after days', fontsize=11, color='#48545b')
    fig.text(.06, .06, 'Compare phase means, not totals. Workload volumes are needed to turn this gap into a savings estimate.', fontsize=10, color='#48545b')
    fig.subplots_adjust(left=.23, right=.96, top=.82, bottom=.20)
    fig.savefig(ROOT/'process_time_comparison.png', facecolor=fig.get_facecolor())
