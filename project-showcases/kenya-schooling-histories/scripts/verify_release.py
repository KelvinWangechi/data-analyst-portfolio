"""Independent SQL arithmetic and public-release checks against the local roster."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def verify(data, private):
    d = pd.read_stata(data, convert_categoricals=False)
    keep = ['a4a_ageyrs','strata_actual','weight','a4_outofschool',
            'a4a_everattendschool','a4a_attendschool']
    with sqlite3.connect(':memory:') as con:
        d[keep].to_sql('roster',con,index=False)
        sql = """
        WITH classified AS (
          SELECT *,
            CASE WHEN strata_actual IN (1,2,3) THEN 'Turkana'
                 WHEN strata_actual IN (4,5) THEN 'Dadaab'
                 WHEN strata_actual IN (6,7) THEN 'Nairobi' ELSE 'Other Urban' END AS location,
            CASE WHEN strata_actual IN (1,2,4,6,8) THEN 'refugee' ELSE 'host' END AS sample,
            CASE WHEN (a4_outofschool=0 AND a4a_everattendschool=0)
                       OR (a4_outofschool=1 AND a4a_attendschool=1) THEN 'U'
                 WHEN a4_outofschool=1 AND a4a_everattendschool=0 THEN 'A'
                 WHEN a4_outofschool=1 AND a4a_everattendschool=1 THEN 'B'
                 WHEN a4_outofschool=0 THEN 'C' ELSE 'U' END AS state,
            CASE WHEN a4a_ageyrs<=11 THEN '6–11'
                 WHEN a4a_ageyrs<=14 THEN '12–14' ELSE '15–17' END AS age_band
          FROM roster WHERE a4a_ageyrs BETWEEN 6 AND 17
        ), expanded AS (
          SELECT location,sample,age_band,weight,state FROM classified
          UNION ALL
          SELECT location,sample,'6–17',weight,state FROM classified
        )
        SELECT location,sample,age_band,COUNT(*) AS eligible_n,
          SUM(CASE WHEN state<>'U' THEN 1 ELSE 0 END) AS classified_n,
          SUM(CASE WHEN state<>'U' THEN weight ELSE 0 END) AS V,
          SUM(CASE WHEN state='A' THEN weight ELSE 0 END) AS WA,
          SUM(CASE WHEN state='B' THEN weight ELSE 0 END) AS WB,
          SUM(CASE WHEN state='C' THEN weight ELSE 0 END) AS WC
        FROM expanded GROUP BY location,sample,age_band
        """
        sql_stats=pd.read_sql_query(sql,con)
    keys=['location','sample','age_band']
    source=pd.read_csv(private/'quality_and_components.csv').set_index(keys).sort_index()
    sql_stats=sql_stats.set_index(keys).sort_index()
    for key in ['eligible_n','classified_n']:
        np.testing.assert_array_equal(source[key],sql_stats[key])
    for state in 'ABC':
        np.testing.assert_allclose(source[state],100*sql_stats['W'+state]/sql_stats.V,rtol=0,atol=1e-10)
    np.testing.assert_allclose(source.A+source.B+source.C,100,rtol=0,atol=1e-10)
    np.testing.assert_allclose(source.A+source.B,source.O,rtol=0,atol=1e-10)
    public=pd.read_csv(ROOT/'outputs/schooling_estimates.csv').set_index(keys)
    for state in 'ABCO':
        valid=public[state].notna()
        np.testing.assert_allclose(public.loc[valid,state],source.loc[public.index[valid],state],rtol=0,atol=0.00000051)
    for family,g in source.groupby(level=['location','sample']):
        overall=g.xs('6–17',level='age_band')
        age=g[g.index.get_level_values('age_band')!='6–17']
        small_overall=(overall[['A_n','B_n','C_n']]<5).any(axis=None)
        small_age=(age[['A_n','B_n','C_n']]<5).any(axis=None)
        if small_overall:
            assert public.loc[(*family,'6–17'),['A','B']].isna().all()
        if small_overall or small_age:
            assert all(i[2]=='6–17' for i in public.index if i[:2]==family)
    gap=pd.read_csv(ROOT/'outputs/location_gaps.csv')
    for r in gap.itertuples():
        expected=source.loc[(r.location,'refugee','6–17'),'O']-source.loc[(r.location,'host','6–17'),'O']
        assert abs(r.gap_pp-expected)<0.00000051
        if pd.notna(r.never_gap_pp):
            assert abs(r.never_gap_pp+r.previous_gap_pp-r.gap_pp)<0.000002
    manifest=json.loads((ROOT/'outputs/release_manifest.json').read_text())
    assert hashlib.sha256(data.read_bytes()).hexdigest()==manifest['source_sha256']
    for name,digest in manifest['public_files_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    # Check every percentage and denominator in the README's main results table.
    text=(ROOT/'README.md').read_text(encoding='utf-8')
    table=[line for line in text.splitlines() if line.startswith('| ') and (' — refugees |' in line or ' — hosts |' in line)]
    assert len(table)==8
    for line in table:
        values=[v.strip().replace('**','') for v in line.strip('|').split('|')]
        loc,label=values[0].split(' — ')
        r=public.loc[(loc,'refugee' if label=='refugees' else 'host','6–17')]
        assert values[1]==f'{int(r.classified_n):,}'
        for value,key in zip(values[2:],['A','B','O']):
            assert value==('Withheld' if pd.isna(r[key]) else f'{r[key]:.1f}%')
    print(f'PASS: independent SQL agrees for {len(source)} groups; {len(public)} public rows, gaps, suppression, table text and hashes verified.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--private',type=Path,required=True)
    a=p.parse_args();verify(a.data,a.private)
