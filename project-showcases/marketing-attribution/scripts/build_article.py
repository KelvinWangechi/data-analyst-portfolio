"""Build the readable default article from the same saved analysis outputs."""
from pathlib import Path
import json
from html import escape

ROOT=Path(__file__).resolve().parents[1]

def main():
    data=json.loads((ROOT/'results'/'explorer-data.json').read_text(encoding='utf-8'))
    example=data['examples'][0]
    path=''.join(f'<li><span>{escape(c)}</span><small>{t[5:10]}<br>{"Conversion" if i==len(example["channels"])-1 else "Impression"}</small></li>' for i,(c,t) in enumerate(zip(example['channels'],example['times'])))
    path_credit='<div class="allocation-row"><span>Instagram</span><strong>100.0%</strong></div>'
    base=[r for r in data['comparison'] if r['scenario']=='Full path']
    markov=sorted([r for r in base if r['model']=='Markov'],key=lambda r:r['rank'])
    last={r['channel']:r['share'] for r in base if r['model']=='Last touch'}
    bars=''.join(f'<div class="credit-row"><div class="credit-label"><span>{escape(r["channel"])}</span><span>{r["share"]*100:.1f}% | last {last[r["channel"]]*100:.1f}%</span></div><div class="credit-line" aria-hidden="true"><i style="width:{r["share"]/0.4*100:.4f}%"></i><b style="left:{last[r["channel"]]/0.4*100:.4f}%"></b></div></div>' for r in markov)
    methods=data['models']
    cells={(r['channel'],r['model']):r['share'] for r in base}
    table=''.join('<tr><th scope="row">'+escape(c)+'</th>'+''.join(f'<td>{cells[c,m]*100:.1f}%</td>' for m in methods)+'</tr>' for c in sorted(last,key=last.get,reverse=True))
    replacements={'@@PATH@@':path,'@@PATH_CREDIT@@':path_credit,'@@BARS@@':bars,'@@TABLE@@':table,
                  '@@DATA@@':json.dumps(data,separators=(',',':')).replace('<','\\u003c')}
    html=(ROOT/'article.template.html').read_text(encoding='utf-8')
    for marker,value in replacements.items():
        html=html.replace(marker,value)
    if '@@' in html:
        raise ValueError('Unresolved article marker')
    if '\u2014' in html or '\u2013' in html:
        raise ValueError('Unexpected display punctuation')
    (ROOT/'index.html').write_text(html,encoding='utf-8')
    print('Built article with saved path weights and model shares')

if __name__=='__main__':
    main()
