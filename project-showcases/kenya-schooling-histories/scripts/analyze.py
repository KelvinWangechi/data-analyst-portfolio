"""K-LSRH weighted schooling-history analysis. No microdata are distributed here.

Outputs are PRIVATE review aggregates, not automatically publication approved.
Run from the project directory. Requires a completed validation.json.
"""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import subprocess
import pandas as pd
import numpy as np

VERSION = '1.0.0'
GROUPS = {1: ('Turkana', 'refugee'), 2: ('Turkana', 'refugee'),
          3: ('Turkana', 'host'), 4: ('Dadaab', 'refugee'),
          5: ('Dadaab', 'host'), 6: ('Nairobi', 'refugee'),
          7: ('Nairobi', 'host'), 8: ('Other Urban', 'refugee'),
          9: ('Other Urban', 'host')}
CORE = ['hhid', 'hhmemid', 'a4a_ageyrs', 'a1a_status', 'strata_actual',
        'weight', 'a4a_everattendschool', 'a4_outofschool',
        'a4a_schoolenrolment', 'a4a_attendschool', 'a4a_reasonnotattend',
        'a4a_planattendschool']


def classify(out, ever, unresolved=False):
    """C does not imply daily attendance. Diagnostic combinations await review."""
    if unresolved:
        return 'U'
    if out == 1 and ever == 0:
        return 'A'
    if out == 1 and ever == 1:
        return 'B'
    if out == 0:
        return 'C'
    return 'U'


def summarize(g):
    w = g.weight.astype('float64')
    v = g.state.isin(['A', 'B', 'C'])
    W, V, U = float(w.sum()), float(w[v].sum()), float(w[~v].sum())
    r = dict(eligible_n=len(g), classified_n=int(v.sum()),
             unclassified_n=int((~v).sum()), eligible_weight=W,
             classified_weight=V, missing_share=100 * U / W)
    for state in 'ABC':
        n = float(w[g.state == state].sum())
        r[state + '_n'] = int((g.state == state).sum())
        r[state + '_weight'] = n
        r[state] = 100 * n / V if V else None
        r[state + '_bound_low'] = 100 * n / W
        r[state + '_bound_high'] = 100 * (n + U) / W
    r['O'] = r['A'] + r['B'] if V else None
    r['O_n'] = r['A_n'] + r['B_n']
    r['O_bound_low'] = 100 * (r['A_weight'] + r['B_weight']) / W
    r['O_bound_high'] = 100 * (r['A_weight'] + r['B_weight'] + U) / W
    valid_o = g.a4_outofschool.isin([0, 1])
    wo = float(w[valid_o].sum())
    r['direct_o_n'] = int(valid_o.sum())
    r['direct_o_weight'] = wo
    r['direct_o'] = 100 * float(w[g.a4_outofschool == 1].sum()) / wo if wo else None
    r['small_cell_review'] = bool(len(g) < 30 or v.sum() < 30)
    if V and not np.isclose(r['A'] + r['B'] + r['C'], 100):
        raise ValueError('Composition does not reconcile')
    assert r['eligible_n'] == r['classified_n'] + r['unclassified_n']
    return r


def analyze(df, cfg):
    missing = set(CORE) - set(df.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    if df[['hhid', 'hhmemid']].isna().any().any() or df.duplicated(['hhid', 'hhmemid']).any():
        raise ValueError('Missing or duplicate household/member keys')
    # Raw Stata objects remain in the source dataframe and local import audit.
    n = df.copy()
    for col in CORE[2:]:
        n[col] = pd.to_numeric(n[col], errors='coerce')
    age = n.a4a_ageyrs
    if (age.notna() & ((age < 0) | (age > 120) | (age % 1 != 0))).any():
        raise ValueError('Invalid ages require review; do not silently exclude')
    n = n.loc[age.between(6, 17)].copy()
    if not len(n):
        raise ValueError('No eligible children')
    if (~np.isfinite(n.weight) | (n.weight <= 0)).any():
        raise ValueError('Eligible children have invalid weights')
    if not n.strata_actual.isin(GROUPS).all():
        raise ValueError('Missing or unsupported location')
    n['location'] = n.strata_actual.map(lambda x: GROUPS[x][0])
    n['sample'] = n.strata_actual.map(lambda x: GROUPS[x][1])
    status = {float(k): v for k, v in cfg['status_codes'].items()}
    status_mismatch = ~n.a1a_status.map(status).eq(n['sample'])
    if status_mismatch.any() and cfg.get('reporting_basis') != 'released_location_strata':
        raise ValueError('Sample status disagrees with location mapping')
    if not n.a1a_status.map(status).isin(['refugee', 'host']).all():
        raise ValueError('Unknown sample status code')
    contradictions = ((n.a4_outofschool.eq(0) & n.a4a_everattendschool.eq(0)) |
                      (n.a4_outofschool.eq(1) & n.a4a_attendschool.eq(1)))
    # Retain diagnostics in U until an analyst documents a different rule.
    n['state'] = [classify(o, e, bad) for o, e, bad in
                  zip(n.a4_outofschool, n.a4a_everattendschool, contradictions)]
    n['age_band'] = pd.cut(n.a4a_ageyrs, [5, 11, 14, 17], labels=['6–11', '12–14', '15–17'])
    rows = []
    for loc in ['Turkana', 'Dadaab', 'Nairobi', 'Other Urban']:
        for sample in ['refugee', 'host']:
            group = n.loc[(n.location == loc) & (n['sample'] == sample)]
            for band in ['6–17', '6–11', '12–14', '15–17']:
                g = group if band == '6–17' else group.loc[group.age_band == band]
                if len(g):
                    rows.append(dict(location=loc, sample=sample, age_band=band, **summarize(g)))
    audit = {'roster_n': len(df), 'age_missing_n': int(age.isna().sum()),
             'eligible_n': len(n), 'diagnostic_unresolved_n': int(contradictions.sum()),
             'status_location_mismatch_n': int(status_mismatch.sum()),
             'not_age_eligible_n': int((~age.between(6, 17) & age.notna()).sum())}
    return pd.DataFrame(rows), audit


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--validation', type=Path, required=True)
    p.add_argument('--out', type=Path, default=Path('outputs/private'))
    a = p.parse_args()
    cfg = json.loads(a.validation.read_text())
    gates = ['access_terms_reviewed', 'release_labels_verified', 'indicator_definition_reviewed',
             'routing_reviewed', 'weight_verified']
    if any(cfg.get(k) is not True for k in gates) or not cfg.get('reviewer') or not cfg.get('evidence_notes'):
        raise SystemExit('BLOCKED: finish the documented validation gates before calculation')
    if a.out.exists() and any(a.out.iterdir()):
        raise SystemExit('Use an empty output directory to preserve previous run evidence')
    raw = pd.read_stata(a.data, convert_categoricals=False, convert_missing=True)
    stats, audit = analyze(raw, cfg)
    a.out.mkdir(parents=True, exist_ok=True)
    raw_codes = {c: raw[c].astype(str).value_counts(dropna=False).to_dict() for c in CORE[2:]}
    (a.out / 'raw_code_counts.json').write_text(json.dumps(raw_codes, indent=2))
    stats.to_csv(a.out / 'quality_and_components.csv', index=False)
    rows, gaps = [], []
    for _, r in stats.iterrows():
        for state in ['A', 'B', 'C', 'O']:
            rows.append(dict(result_id=f"{r.location}:{r['sample']}:{r.age_band}:{state}",
                group=f"{r.location}/{r['sample']}/{r.age_band}", outcome=state,
                numerator_rule=f'state={state}' if state != 'O' else 'state in A,B',
                denominator_rule='states A,B,C; eligible ages 6–17 in reporting group',
                unweighted_n=r.classified_n, weight_sum=r.classified_weight,
                estimate=r[state], unit='percent', lower=None, upper=None,
                uncertainty_method='Not estimated: design variance information unresolved',
                missing_share=r.missing_share, script_version=VERSION, source_file=a.data.name))
    for (loc, band), g in stats.groupby(['location', 'age_band']):
        if set(g['sample']) != {'refugee', 'host'}:
            continue
        g = g.set_index('sample')
        delta = {k: (g.loc['refugee', k] - g.loc['host', k])
                 if pd.notna(g.loc['refugee', k]) and pd.notna(g.loc['host', k]) else np.nan
                 for k in ['A', 'B', 'O']}
        if pd.notna(delta['O']) and not np.isclose(delta['A'] + delta['B'], delta['O']):
            raise ValueError('Gap identity failed')
        gaps.append(dict(location=loc, age_band=band, delta_A=delta['A'], delta_B=delta['B'],
                         delta_O=delta['O'], unit='percentage points'))
    pd.DataFrame(rows).to_csv(a.out / 'estimates.csv', index=False)
    pd.DataFrame(gaps).to_csv(a.out / 'gaps.csv', index=False)
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = 'not available'
    manifest = dict(status='PRIVATE aggregates awaiting disclosure and analyst review',
        source_sha256=hashlib.sha256(a.data.read_bytes()).hexdigest(), source_file=a.data.name,
        release='KEN_2022_K-LSRH_v01_M', script_version=VERSION, commit=commit,
        python=platform.python_version(), pandas=pd.__version__, numpy=np.__version__,
        validation=cfg, audit=audit)
    (a.out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print('Private aggregates produced. Review small cells and disclosure by subtraction before release.')


if __name__ == '__main__':
    main()
