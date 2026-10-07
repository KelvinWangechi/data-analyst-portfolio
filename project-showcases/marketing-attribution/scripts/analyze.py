"""Reproduce event audits, attribution, sensitivity checks and SQL reconciliation."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import sqlite3
import sys
import numpy as np
import pandas as pd
from models import Journey, MODELS, allocations, bootstrap_markov, rule_weights
from download_data import SHA256

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results'
COLS = ['cookie','time','interaction','conversion','conversion_value','channel']

def load_data(path):
    if hashlib.sha256(path.read_bytes()).hexdigest() != SHA256:
        raise ValueError('Input SHA256 does not match the documented source')
    raw = pd.read_csv(path)
    if list(raw.columns) != COLS or raw.isna().any().any():
        raise ValueError('Unexpected columns or missing fields')
    if not raw.conversion.isin([0,1]).all() or (raw.conversion_value < 0).any():
        raise ValueError('Invalid conversion/value fields')
    if (raw.loc[raw.conversion.eq(0),'conversion_value'] != 0).any():
        raise ValueError('Value on a non-conversion requires a revised value definition')
    if not (raw.interaction.eq('conversion') == raw.conversion.eq(1)).all():
        raise ValueError('Interaction and conversion flag disagree')
    clean = raw.drop_duplicates().copy()
    raw['source_row'] = np.arange(len(raw))+2
    clean['source_row'] = clean.index+2
    for frame in [raw,clean]:
        frame['time'] = pd.to_datetime(frame.time,utc=True,errors='raise')
        frame.sort_values(['cookie','time','source_row'],kind='stable',inplace=True)
    gc = clean.groupby('cookie',sort=False)
    if (gc.conversion.sum() > 1).any():
        raise ValueError('Multiple conversions require a different journey protocol')
    if (gc.conversion.sum() != gc.conversion.last()).any():
        raise ValueError('Conversion is not terminal; revise journey construction')
    tied = clean.groupby(['cookie','time']).channel.nunique()
    ambiguous = set(tied[tied > 1].index.get_level_values(0))
    audit = {
        'sha256':SHA256,'raw_rows':len(raw),'clean_rows':len(clean),
        'exact_duplicates':len(raw)-len(clean),'cookies':gc.ngroups,
        'conversions':int(clean.conversion.sum()),'conversion_value':float(clean.conversion_value.sum()),
        'start':clean.time.min().isoformat(),'end':clean.time.max().isoformat(),
        'channels':sorted(clean.channel.unique()),'missing_fields':0,
        'ambiguous_cookies':len(ambiguous),'ambiguous_time_groups':int((tied>1).sum()),
        'ambiguous_converting_cookies':int(clean[clean.cookie.isin(ambiguous)].conversion.sum()),
        'conversion_duplicates':int(raw[raw.duplicated(COLS)].conversion.sum()),
        'conversions_per_cookie_max':int(gc.conversion.sum().max()),
        'interaction_counts':clean.interaction.value_counts().to_dict(),
    }
    return raw,clean,ambiguous,audit

def build_journeys(frame,days=None,impressions_only=False,exclude_cookies=None,start_after=None):
    journeys=[]
    unassigned=0
    cookies=frame.cookie.to_numpy()
    channels=frame.channel.to_numpy()
    times=list(frame.time)
    conversions=frame.conversion.to_numpy()
    values=frame.conversion_value.to_numpy()
    interactions=frame.interaction.to_numpy()
    boundaries=np.r_[0,np.flatnonzero(cookies[1:] != cookies[:-1])+1,len(frame)]
    for left,right in zip(boundaries[:-1],boundaries[1:]):
        cookie=cookies[left]
        if exclude_cookies and cookie in exclude_cookies:
            continue
        if start_after is not None and times[left] < start_after:
            continue
        converted=bool(conversions[right-1])
        value=float(values[right-1]) if converted else 0.
        anchor=times[right-1]
        start=times[left]
        cutoff=anchor-pd.Timedelta(days=days) if days is not None else None
        indices=[i for i in range(left,right) if (cutoff is None or times[i]>=cutoff)
                 and (not impressions_only or interactions[i]=='impression')]
        if not indices:
            unassigned+=int(converted)
            continue
        journeys.append(Journey(tuple(channels[i] for i in indices),tuple(times[i] for i in indices),converted,value,cookie,start))
    return journeys,unassigned

def comparison_rows(journeys,channels,scenario):
    count,value,markov=allocations(journeys,channels)
    nc=sum(j.converted for j in journeys)
    nv=sum(j.value for j in journeys)
    rows=[]
    for model,credits in count.items():
        if not np.isclose(credits.sum(),nc):
            raise AssertionError(f'{scenario} {model}: lost conversion credit')
        for rank,ix in enumerate(np.argsort(-credits),1):
            rows.append({'scenario':scenario,'model':model,'channel':channels[ix],
                         'credit':float(credits[ix]),'share':float(credits[ix]/nc),
                         'rank':rank,'eligible_conversions':nc,'journeys':len(journeys)})
    value_rows=[]
    for model,credits in value.items():
        if not np.isclose(credits.sum(),nv):
            raise AssertionError(f'{model}: lost conversion value')
        for ix,c in enumerate(channels):
            value_rows.append({'scenario':scenario,'model':model,'channel':c,
                               'value_credit':float(credits[ix]),'share':float(credits[ix]/nv)})
    if not np.isclose(markov['base'],nc/len(journeys),atol=1e-10):
        raise AssertionError('Markov base probability does not reconcile to observed conversion rate')
    return rows,value_rows,markov

def sql_reconcile(clean,comparison):
    with sqlite3.connect(':memory:') as connection:
        copy=clean.copy()
        copy['time']=copy.time.map(lambda t:t.isoformat())
        copy.to_sql('events',connection,index=False)
        sql=(ROOT/'queries.sql').read_text(encoding='utf-8')
        rows=pd.read_sql_query(sql,connection)
    py=comparison[comparison.scenario.eq('Full path') & comparison.model.isin(['First touch','Last touch'])]
    merged=rows.merge(py,on=['model','channel'],validate='one_to_one')
    if len(merged) != 2*clean.channel.nunique() or not np.allclose(merged.conversion_credit,merged.credit):
        raise AssertionError('Independent SQLite allocation disagrees')
    merged['difference']=merged.conversion_credit-merged.credit
    merged[['model','channel','conversion_credit','credit','difference']].to_csv(OUT/'sql-reconciliation.csv',index=False)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bootstrap',type=int,default=300)
    args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    raw,clean,ambiguous,audit=load_data(ROOT/'data'/'attribution_data.csv')
    channels=audit['channels']
    print('Audited source; constructing cookie journeys',flush=True)
    base,_=build_journeys(clean)
    specifications=[('Full path',base,0)]
    for days in [7,14,30]:
        js,missing=build_journeys(clean,days=days)
        specifications.append((f'{days}-day lookback',js,missing))
    js,missing=build_journeys(raw)
    specifications.append(('Duplicates retained',js,missing))
    js,missing=build_journeys(clean,exclude_cookies=ambiguous)
    specifications.append(('Ambiguous timestamps excluded',js,missing))
    js,missing=build_journeys(clean,impressions_only=True)
    specifications.append(('Impressions only',js,missing))
    js,missing=build_journeys(clean,start_after=pd.Timestamp('2018-07-08',tz='UTC'))
    specifications.append(('First seen July 8 onward',js,missing))
    all_rows=[]
    value_rows=[]
    specs=[]
    primary_markov=None
    for name,js,missing in specifications:
        print(f'Attribution: {name} ({len(js):,} paths)',flush=True)
        rows,values,mk=comparison_rows(js,channels,name)
        all_rows.extend(rows)
        value_rows.extend(values)
        specs.append({'scenario':name,'journeys':len(js),'eligible_conversions':sum(j.converted for j in js),
                      'unassigned_conversions':missing,'observed_conversion_rate':mk['base']})
        if name=='Full path':
            primary_markov=mk
    comparison=pd.DataFrame(all_rows)
    comparison.to_csv(OUT/'model-comparison.csv',index=False)
    pd.DataFrame(value_rows).to_csv(OUT/'value-attribution.csv',index=False)
    pd.DataFrame(specs).to_csv(OUT/'specifications.csv',index=False)
    print('Bootstrapping complete paths',flush=True)
    intervals=bootstrap_markov(base,channels,repetitions=args.bootstrap)
    pd.DataFrame({'channel':channels,'share':primary_markov['shares'],'lower':intervals[:,0],
                  'upper':intervals[:,1],'removal_effect':primary_markov['effects']}).to_csv(OUT/'markov-intervals.csv',index=False)
    states=['START']+channels+['CONVERSION','NULL']
    pd.DataFrame(primary_markov['matrix'],index=states,columns=states).to_csv(OUT/'transition-matrix.csv')
    converted=[j for j in base if j.converted]
    audit.update({'converted_single_event':sum(len(j.channels)==1 for j in converted),
                  'converted_multi_event':sum(len(j.channels)>1 for j in converted),
                  'converted_multi_channel':sum(len(set(j.channels))>1 for j in converted),
                  'nonconverting_paths':sum(not j.converted for j in base),
                  'single_event_paths':sum(len(j.channels)==1 for j in base),
                  'bootstrap_repetitions':args.bootstrap,'bootstrap_seed':20261007})
    roles=[]
    for c in channels:
        involving=[j for j in converted if c in j.channels]
        roles.append({'channel':c,'converting_paths_involving_channel':len(involving),
                      'first_event':sum(j.channels[0]==c for j in converted),
                      'last_event':sum(j.channels[-1]==c for j in converted),
                      'earlier_without_closing':sum(c in j.channels[:-1] and j.channels[-1]!=c for j in converted),
                      'impressions':int(clean[clean.channel.eq(c)].interaction.eq('impression').sum())})
    pd.DataFrame(roles).to_csv(OUT/'channel-roles.csv',index=False)
    # Equal credit across distinct channels: exposes repeat-event weighting.
    unique_credit=Counter()
    for j in converted:
        for c in set(j.channels):
            unique_credit[c]+=1/len(set(j.channels))
    pd.DataFrame([{'channel':c,'credit':unique_credit[c],'share':unique_credit[c]/len(converted)} for c in channels]).to_csv(OUT/'unique-channel-credit.csv',index=False)
    sql_reconcile(clean,comparison)
    examples=[]
    chosen=set()
    for j in converted:
        if 3 <= len(j.channels) <= 6 and len(set(j.channels))>=3 and j.channels[-1] not in chosen:
            chosen.add(j.channels[-1])
            rows=clean[clean.cookie.eq(j.cookie)].source_row.tolist()
            examples.append({'id':f'Path {len(examples)+1}','channels':list(j.channels),
                             'times':[t.isoformat() for t in j.times],'source_rows':rows,
                             'value':j.value,'weights':{m:rule_weights(j.channels,j.times,m).tolist() for m in MODELS[:-1]}})
            if len(examples)==4:
                break
    data={'audit':audit,'models':list(MODELS),'channels':channels,
          'comparison':comparison.to_dict(orient='records'),'specifications':specs,
          'intervals':[{'channel':c,'lower':float(intervals[i,0]),'upper':float(intervals[i,1])} for i,c in enumerate(channels)],
          'roles':roles,'examples':examples}
    (OUT/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    (OUT/'explorer-data.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    print(json.dumps(audit,indent=2),flush=True)
    from figures import make_figures
    make_figures(ROOT,comparison,channels)
    print('Outputs and independent SQL reconciliation complete',flush=True)

if __name__=='__main__':
    main()
