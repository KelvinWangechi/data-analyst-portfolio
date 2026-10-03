"""Produce disclosure-filtered tables and figures from a reviewed private run."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LOCATIONS = ['Turkana', 'Dadaab', 'Nairobi', 'Other Urban']
COLORS = {'A': '#176b70', 'B': '#bc6c25', 'O': '#777f88'}


def disclosure_tables(stats):
    """Suppress both components when either rests on fewer than five records.

    Age detail is withheld for the entire location/sample family if any age
    cell triggers, preventing recovery by subtracting released age bands.
    This is a project release rule, not a World Bank certification.
    """
    safe = stats.copy()
    safe['components_withheld'] = False
    for (_, _), group in safe.groupby(['location', 'sample']):
        allage = group[group.age_band == '6–17']
        detailed = group[group.age_band != '6–17']
        small_all = (allage[['A_n', 'B_n', 'C_n']] < 5).any(axis=None)
        small_age = (detailed[['A_n', 'B_n', 'C_n']] < 5).any(axis=None)
        if small_all:
            safe.loc[allage.index, ['A', 'B']] = np.nan
            safe.loc[allage.index, 'components_withheld'] = True
        if small_all or small_age:
            safe = safe.drop(detailed.index)
    cols = ['location', 'sample', 'age_band', 'eligible_n', 'classified_n',
            'A', 'B', 'C', 'O', 'missing_share', 'components_withheld']
    return safe[cols]


def style(ax):
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(axis='x', color='#dfe4e5', linewidth=.6)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, labelsize=10)


def main(private):
    stats = pd.read_csv(private / 'quality_and_components.csv')
    safe = disclosure_tables(stats)
    out = ROOT / 'outputs'
    figdir = ROOT / 'figures'
    figdir.mkdir(exist_ok=True)
    safe.to_csv(out / 'schooling_estimates.csv', index=False, float_format='%.6f', lineterminator='\n')
    overall = safe[safe.age_band == '6–17'].copy()
    full = stats[stats.age_band == '6–17'].set_index(['location', 'sample'])
    gaps = []
    for loc in LOCATIONS:
        ref, host = full.loc[(loc, 'refugee')], full.loc[(loc, 'host')]
        r = dict(location=loc, refugee_O=ref.O, host_O=host.O, gap_pp=ref.O-host.O)
        if loc in ['Turkana', 'Dadaab']:
            r.update(never_gap_pp=ref.A-host.A, previous_gap_pp=ref.B-host.B)
        gaps.append(r)
    pd.DataFrame(gaps).to_csv(out / 'location_gaps.csv', index=False, float_format='%.6f', lineterminator='\n')
    sensitivity = pd.read_csv(private / 'sensitivity_components.csv')
    sensitivity = sensitivity[sensitivity.age_band == '6–17'][['scenario','location','sample','O']]
    sensitivity.to_csv(out / 'sensitivity.csv', index=False, float_format='%.6f', lineterminator='\n')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'figure.facecolor': '#faf9f6',
                         'axes.facecolor': '#faf9f6', 'text.color': '#26343b',
                         'axes.labelcolor': '#26343b', 'savefig.facecolor': '#faf9f6'})
    fig, ax = plt.subplots(figsize=(11, 7.3))
    y = np.arange(len(overall))
    for i, r in enumerate(overall.itertuples()):
        if r.components_withheld:
            ax.barh(i,r.O,color=COLORS['O'],height=.58)
        else:
            ax.barh(i,r.A,color=COLORS['A'],height=.58)
            ax.barh(i,r.B,left=r.A,color=COLORS['B'],height=.58)
            if r.A > 7:
                ax.text(r.A/2,i,f'{r.A:.1f}',ha='center',va='center',color='white',fontsize=10)
        ax.text(r.O+.9,i,f'{r.O:.1f}%',va='center',fontweight='bold',fontsize=11)
    ax.set_yticks(y,[f"{r.location} · {'refugee sample' if r.sample=='refugee' else 'host sample'}" for r in overall.itertuples()])
    ax.invert_yaxis(); ax.set_xlim(0,70); ax.set_xlabel('Share of classified children aged 6–17 (%)',labelpad=12)
    style(ax)
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=COLORS['A'],label='No previous attendance'),
                        Patch(color=COLORS['B'],label='Previous attendance'),
                        Patch(color=COLORS['O'],label='Total only; components withheld')],
               loc='upper left',bbox_to_anchor=(.03,.86),frameon=False,ncol=2,fontsize=10)
    fig.suptitle('Exclusion is high on both sides of Dadaab',x=.03,ha='left',y=.98,fontsize=21,fontweight='bold')
    fig.text(.03,.91,'In Turkana, nearby host children face much higher exclusion than the refugee sample.',fontsize=11)
    fig.text(.03,.035,'K-LSRH Wave 1 · Household-weighted point estimates; no confidence intervals.\nTurkana refugees pool Kakuma and Kalobeyei. Urban host components withheld for small cells.',fontsize=9)
    fig.subplots_adjust(left=.29,right=.94,top=.74,bottom=.16)
    fig.savefig(figdir/'schooling_composition.png',dpi=180); plt.close(fig)

    panels=[('Dadaab','refugee'),('Dadaab','host'),('Nairobi','refugee')]
    fig, axes=plt.subplots(1,3,figsize=(12,6),sharey=True)
    for ax,(loc,sample) in zip(axes,panels):
        rows=safe[(safe.location==loc)&(safe['sample']==sample)&(safe.age_band!='6–17')]
        x=np.arange(3)
        ax.bar(x,rows.A,color=COLORS['A'],width=.6)
        ax.bar(x,rows.B,bottom=rows.A,color=COLORS['B'],width=.6)
        for j,r in enumerate(rows.itertuples()):
            ax.text(j,r.O+2,f'{r.O:.1f}%',ha='center',fontsize=11,fontweight='bold')
            if r.B>5:
                ax.text(j,r.A+r.B/2,f'{r.B:.1f}',ha='center',va='center',fontsize=10,color='white')
        ax.set_xticks(x,rows.age_band); ax.set_ylim(0,85)
        ax.set_title(f'{loc} · {sample} sample',fontsize=12,pad=15)
        for s in ax.spines.values():s.set_visible(False)
        ax.grid(axis='y',color='#dfe4e5',linewidth=.6); ax.set_axisbelow(True); ax.tick_params(length=0)
        ax.set_xlabel('Age group')
    axes[0].set_ylabel('Share of classified children (%)')
    fig.suptitle('Schooling history changes the response',x=.05,ha='left',y=.98,fontsize=21,fontweight='bold')
    fig.text(.05,.89,'Never-attendance dominates Dadaab; previous attendance matters more for Nairobi refugee teenagers.',fontsize=11)
    fig.legend(handles=[Patch(color=COLORS['A'],label='No previous attendance'),Patch(color=COLORS['B'],label='Previous attendance')],loc='upper left',bbox_to_anchor=(.045,.85),frameon=False,ncol=2)
    fig.text(.05,.025,'K-LSRH Wave 1 · Weighted cross-sectional age groups, not trajectories of the same children.\nNo causal or statistical-significance claim. Tables include the other publishable age groups.',fontsize=9)
    fig.subplots_adjust(top=.68,bottom=.19,left=.075,right=.98,wspace=.18)
    fig.savefig(figdir/'schooling_by_age.png',dpi=180);plt.close(fig)

    gap=pd.DataFrame(gaps)
    fig,ax=plt.subplots(figsize=(10,5.3))
    ax.barh(gap.location,gap.gap_pp,color=[COLORS['A'] if v<0 else COLORS['B'] for v in gap.gap_pp],height=.5)
    for i,v in enumerate(gap.gap_pp):
        ax.text(v+(.8 if v>=0 else -.8),i,f'{v:+.1f} pp',ha='left' if v>=0 else 'right',va='center',fontweight='bold')
    ax.axvline(0,color='#26343b',linewidth=.9);ax.invert_yaxis();ax.set_xlim(-48,23)
    style(ax);ax.set_xlabel('Refugee minus host out-of-school rate (percentage points)',labelpad=12)
    fig.suptitle('The direction of the gap depends on location',x=.04,ha='left',y=.97,fontsize=20,fontweight='bold')
    fig.text(.04,.87,'Negative: higher host exclusion. Positive: higher refugee exclusion.',fontsize=11)
    fig.text(.04,.025,'K-LSRH Wave 1 · Ages 6–17 · Weighted point estimates, not estimated effects of refugee status.',fontsize=9)
    fig.subplots_adjust(left=.17,right=.95,top=.77,bottom=.2)
    fig.savefig(figdir/'refugee_host_gaps.png',dpi=180);plt.close(fig)
    private_manifest=json.loads((private/'manifest.json').read_text())
    manifest={k:private_manifest[k] for k in ['source_sha256','source_file','release','script_version','python','pandas','numpy']}
    manifest.update({'matplotlib':matplotlib.__version__,'download_date':'2026-10-04',
                     'source_url':'https://microdata.worldbank.org/catalog/6409',
                     'disclosure_rule':'Components with fewer than 5 observations withheld together; all age detail withheld for affected location/sample families.',
                     'public_files_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in [out/'schooling_estimates.csv',out/'location_gaps.csv',out/'sensitivity.csv',*sorted(figdir.glob('*.png'))]}})
    (out/'release_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
    print('Published tables:',len(safe),'rows; figures: 3')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True)
    main(p.parse_args().private)
