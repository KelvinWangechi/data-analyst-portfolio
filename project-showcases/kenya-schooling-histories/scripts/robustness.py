"""Recalculate point estimates under explicit classification/sample alternatives."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from analyze import analyze, GROUPS


def run(data, validation, out):
    cfg = json.loads(validation.read_text(encoding='utf-8'))
    d = pd.read_stata(data, convert_categoricals=False)
    eligible = d.a4a_ageyrs.between(6, 17)
    child = d.loc[eligible]
    mismatch = d.a1a_status.ne(d.strata_actual.map(
        lambda x: 1 if GROUPS[x][1] == 'refugee' else 2))
    exit_signal = d.a4a_everattendschool.eq(1) & (
        d.a4a_reasonnotattend.eq(2) |
        (d.a4a_reasonnotattend.eq(1) & d.a4a_planattendschool.eq(0)))
    alternatives = {'released_indicator': d,
                    'exclude_status_disagreements': d.loc[~mismatch].copy()}
    alternative = d.copy()
    alternative.loc[exit_signal, 'a4_outofschool'] = 1
    alternatives['include_reported_exit_or_no_return_plan'] = alternative
    tables = []
    for name, frame in alternatives.items():
        stats, _ = analyze(frame, cfg)
        tables.append(stats.assign(scenario=name))
    combined = pd.concat(tables, ignore_index=True)
    combined.to_csv(out / 'sensitivity_components.csv', index=False)
    # Only counts, never record identifiers, enter the private diagnostic tables.
    routing = ['batch', 'a4_outofschool', 'a4a_everattendschool',
               'a4a_schoolenrolment', 'a4a_attendschool',
               'a4a_reasonnotattend', 'a4a_planattendschool']
    child[routing].value_counts(dropna=False).rename('n').reset_index().to_csv(
        out / 'routing_by_batch.csv', index=False)
    reconstructed = (child.a4a_everattendschool.eq(0) |
                     child.a4a_schoolenrolment.eq(3)).astype(int)
    report = {
        'eligible_n': int(eligible.sum()),
        'status_disagreement_n': int((eligible & mismatch).sum()),
        'additional_exit_signal_n': int((eligible & exit_signal & d.a4_outofschool.eq(0)).sum()),
        'indicator_reconstruction_disagreement_n': int(reconstructed.ne(child.a4_outofschool).sum()),
        'age_missing_n': int(d.a4a_ageyrs.isna().sum()),
        'age_missing_with_months_1_to_12_n': int((d.a4a_ageyrs.isna() & d.a4a_agemonths.between(1,12)).sum()),
        'roster_households_n': int(d.hhid.nunique()),
        'child_households_n': int(child.hhid.nunique()),
        'batch_n': int(child.batch.nunique()),
    }
    (out / 'diagnostics.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--validation', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    run(a.data, a.validation, a.out)
