"""Reconcile R and SQL, render publication figures, and bake a static page.
Requires matplotlib only for figure export. All analysis precedes this step.
"""
from pathlib import Path
import csv
import html
import json
import hashlib
from coding import baseline, validate

ROOT=Path(__file__).resolve().parent
def read(name):
    with (ROOT/name).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))

def main():
    data=json.loads((ROOT/'results/explorer.json').read_text(encoding='utf-8'))
    sql=data['summary']
    r={row['metric']:int(row['value']) for row in read('results/r-summary.csv')}
    assert all(sql[key]==value for key,value in r.items()),'R and SQL disagree'
    rows=read('results/theme-summary.csv')
    for row in rows:
        for key in ('count','n'): row[key]=int(row[key])
        for key in ('share','lower','upper'): row[key]=float(row[key])
        if row['segment']=='All': assert row['count']==sql['price_issue_counts'][row['theme_id']]
    data['chart']=rows
    data['response_rates']=read('results/response-rates.csv')
    for response in data['responses']:
        response['baseline']=baseline(response['text'])
        validate(response['text'],{'status':'coded' if response['text'] else 'no_response','assignments':response['assignments']})
    labels={t['id']:t['label'] for t in data['themes']}
    selected=sorted([r for r in rows if r['segment']=='All'],key=lambda r:(-r['count'],r['theme_id']))
    # Rendering only: every plotted estimate and interval came from analysis.R.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({'svg.fonttype':'none','svg.hashsalt':'customer-voice','font.size':12})
    fig,ax=plt.subplots(figsize=(10,6.5),layout='constrained')
    y=list(range(len(selected)))
    estimates=[v['share']*100 for v in selected]
    ax.barh(y,estimates,color='#27614f',height=.55)
    ax.errorbar(estimates,y,xerr=[[max(0,(v['share']-v['lower'])*100) for v in selected],[max(0,(v['upper']-v['share'])*100) for v in selected]],fmt='none',ecolor='#18251e',capsize=3)
    ax.set_yticks(y,[labels[v['theme_id']] for v in selected]);ax.invert_yaxis()
    ax.set_xlim(0,50);ax.set_xlabel('Share of 152 price-related comments (%)')
    ax.set_title('One answer option, several different issues',loc='left',fontsize=18,pad=20)
    ax.spines[['top','right','left']].set_visible(False)
    ax.grid(axis='x',alpha=.16);ax.set_axisbelow(True)
    for j,v in enumerate(selected): ax.text(v['upper']*100+1,j,f"{v['count']}/152",va='center',fontsize=11)
    fig.savefig(ROOT/'results/theme-prevalence.svg',metadata={'Date':None})
    svg_path=ROOT/'results/theme-prevalence.svg'
    svg_path.write_text('\n'.join(line.rstrip() for line in svg_path.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    plt.close(fig)
    bar_rows=[];table_rows=[]
    for v in selected:
        label=html.escape(labels[v['theme_id']]);pct=v['share']*100
        bar_rows.append(f'<div class="bar-row"><div class="bar-label"><span>{label}</span><span>{v["count"]}/152 · {pct:.1f}%</span></div><div class="bar-track" aria-hidden="true"><i style="width:{pct}%"></i><b style="left:{v["lower"]*100}%;width:{(v["upper"]-v["lower"])*100}%"></b></div></div>')
        table_rows.append(f'<tr><th scope="row">{label}</th><td>{v["count"]}</td><td>152</td><td>{pct:.1f}%</td><td>{v["lower"]*100:.1f}–{v["upper"]*100:.1f}%</td></tr>')
    template=(ROOT/'page.template.html').read_text(encoding='utf-8')
    replacements={'{{DATA}}':json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'),'{{BARS}}':'\n'.join(bar_rows),'{{TABLE}}':'\n'.join(table_rows)}
    for key,value in replacements.items(): template=template.replace(key,value)
    for filename in ['data/README.md','analysis.R','queries.sql','coding-prompt.md','coding.py','data/codebook.json']:
        template=template.replace(f'href="{filename}"',f'href="https://github.com/KelvinWangechi/data-analyst-portfolio/blob/main/project-showcases/customer-voice/{filename}"')
    assert '{{' not in template,'Unresolved template field'
    (ROOT/'index.html').write_text(template,encoding='utf-8',newline='\n')
    record={'r_sql_reconciled':True,'headline_metrics':r,'validated_response_count':len(data['responses']),'source_hashes':json.loads((ROOT/'data/manifest.json').read_text())['hashes'],'page_sha256':hashlib.sha256(template.encode()).hexdigest()}
    (ROOT/'results/verification.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('R/SQL reconciliation, coding validation and static page build passed.')

if __name__=='__main__': main()
