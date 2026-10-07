"""Standalone publication figures from the saved model outputs."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

GREEN='#27614f'
INK='#17261f'
MUTED='#65776d'
PAPER='#f6f7f5'

def style():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'text.color':INK,
        'axes.labelcolor':INK,'xtick.color':MUTED,'ytick.color':INK,
        'axes.edgecolor':'#c7d1c9','axes.spines.top':False,'axes.spines.right':False,
        'axes.spines.left':False,'figure.facecolor':PAPER,'axes.facecolor':PAPER,
        'svg.fonttype':'none','svg.hashsalt':'marketing-attribution'})

def save(fig,root,name):
    svg=root/'results'/f'{name}.svg'
    fig.savefig(svg,bbox_inches='tight',metadata={'Date':None})
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
    fig.savefig(root/'results'/f'{name}.png',dpi=170,bbox_inches='tight')
    plt.close(fig)

def make_figures(root,comparison,channels):
    style()
    base=comparison[comparison.scenario.eq('Full path')]
    methods=['First touch','Last touch','Linear','Position based','Time decay','Markov']
    order=list(base[base.model.eq('Last touch')].sort_values('rank').channel)
    pivot=base.pivot(index='channel',columns='model',values='share').loc[order,methods]*100
    fig,ax=plt.subplots(figsize=(11,5))
    ax.imshow(pivot.values,cmap='Greens',vmin=0,vmax=35,aspect='auto')
    for y in range(len(order)):
        for x in range(len(methods)):
            v=pivot.iloc[y,x]
            ax.text(x,y,f'{v:.1f}%',ha='center',va='center',color='white' if v>25 else INK,fontweight='bold')
    ax.set_xticks(range(len(methods)),['First\ntouch','Last\ntouch','Linear','Position\nbased','Time\ndecay','Markov'])
    ax.set_yticks(range(len(order)),order)
    ax.tick_params(length=0,pad=12)
    ax.set_title('Who gets credit when the rule changes?',loc='left',fontweight='bold',fontsize=20,pad=42)
    fig.text(.125,.88,'Share of 17,639 observed conversions. Full recorded cookie paths.',color=MUTED,fontsize=11)
    fig.text(.125,.015,'Markov uses all 240,108 paths; its removal scores are normalized to conversion credit.',color=MUTED,fontsize=10)
    save(fig,root,'model-comparison')

    chosen=['Full path','7-day lookback','14-day lookback','Impressions only']
    fig,axes=plt.subplots(1,2,figsize=(11,5.8),sharey=True)
    for ax,method in zip(axes,['Last touch','Markov']):
        endpoints=[]
        for y,c in enumerate(order):
            vals=[float(comparison[(comparison.scenario==s)&(comparison.model==method)&(comparison.channel==c)].share.iloc[0])*100 for s in chosen]
            ax.plot(range(len(chosen)),vals,lw=1,color=GREEN,alpha=.3)
            ax.scatter(range(len(chosen)),vals,color=GREEN,s=30)
            endpoints.append((vals[-1],c))
        previous=-100.
        for value,c in sorted(endpoints):
            label_y=max(value,previous+1.65)
            ax.plot([3,3.25],[value,label_y],color=GREEN,lw=.6)
            ax.text(3.32,label_y,c,fontsize=9,va='center')
            previous=label_y
        ax.set_xticks(range(4),['Full','7 days','14 days','Impressions\nonly'])
        ax.set_xlim(-.2,4.8)
        ax.set_title(method,loc='left',fontweight='bold')
        ax.set_ylim(0,37)
    axes[0].set_ylabel('Share of eligible conversion credit (%)')
    fig.suptitle('The journey definition can move more credit than the model',x=.1,ha='left',fontweight='bold',fontsize=18)
    fig.text(.1,.01,'Impressions-only excludes conversions with no prior recorded impression. See specifications.csv for denominators.',fontsize=9,color=MUTED)
    fig.subplots_adjust(top=.83,bottom=.17,wspace=.08)
    save(fig,root,'journey-sensitivity')

    intervals=pd.read_csv(root/'results'/'markov-intervals.csv').set_index('channel').loc[order]
    last=base[base.model.eq('Last touch')].set_index('channel').loc[order].share*100
    fig,ax=plt.subplots(figsize=(10,5.6))
    y=np.arange(len(order))
    for k in y:
        ax.plot([last.iloc[k],intervals.share.iloc[k]*100],[k,k],color='#c7d1c9',lw=2)
    ax.scatter(last,y,s=75,facecolor=PAPER,edgecolor=INK,label='Last touch',zorder=3)
    ax.errorbar(intervals.share*100,y,xerr=np.vstack([(intervals.share-intervals.lower)*100,(intervals.upper-intervals.share)*100]),fmt='o',color=GREEN,label='Markov with 95% bootstrap interval',capsize=3,zorder=4)
    ax.set_yticks(y,order)
    ax.invert_yaxis()
    ax.set_xlim(0,40)
    ax.set_xlabel('Share of observed conversion credit (%)')
    ax.set_title('Small intervals do not settle the attribution question',loc='left',fontsize=19,fontweight='bold',pad=36)
    ax.legend(frameon=False,loc='lower right',fontsize=10)
    fig.text(.125,.89,'300 resamples of complete cookie paths. Conditional on one journey definition and removal convention.',fontsize=10,color=MUTED)
    save(fig,root,'credit-shift')
