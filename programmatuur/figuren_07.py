"""Kleine, vaste figuurfuncties met vergelijkbare assen voor alle hokken."""
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def hokvolgorde(waarden):
    return sorted(set(waarden),key=lambda x:(0,int(x)) if str(x).isdigit() else (1,str(x)))


def panelen(hokken,titel,ylabel):
    fig,assen=plt.subplots(math.ceil(len(hokken)/2),2,figsize=(11,2.35*math.ceil(len(hokken)/2)),
                           sharex=True,sharey=True,squeeze=False,layout='constrained')
    fig.suptitle(titel,fontsize=16)
    for ax,hok in zip(assen.flat,hokken):
        ax.set_title(f'Hok {hok}',loc='left',fontsize=11)
        ax.set_ylabel(ylabel); ax.grid(axis='y',alpha=.25)
        ax.spines[['top','right']].set_visible(False)
    for ax in list(assen.flat)[len(hokken):]: ax.set_visible(False)
    return fig,list(assen.flat)


def gewichtsfiguur(dag):
    hokken=hokvolgorde(dag.hok)
    fig,assen=panelen(hokken,'Gewichtsverloop per hok','Gewicht (kg)')
    for hok,ax in zip(hokken,assen):
        d=dag[dag.hok==hok].groupby('dag').gewicht_kg.agg(['mean','count'])
        d=d.reindex(pd.date_range(d.index.min(),d.index.max(),freq='D'))
        ax.plot(d.index,d['mean'],color='#176a89',linewidth=1.8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        ax.set_xlabel('Datum (2023)')
    return fig


def intervalfiguur(hok,soort='groei_voeder',kilogram=False):
    if soort not in ('groei_voeder','conversie'): raise ValueError('Onbekend figuurtype.')
    hokken=hokvolgorde(hok.hok)
    titel='Gemiddelde groei en voederopname per interval' if soort=='groei_voeder' else 'Voederconversie per interval'
    factor=1000 if kilogram else 1
    eenheid=('kg per dier per dag' if kilogram else 'g per dier per dag') if soort=='groei_voeder' else 'kg voeder / kg groei'
    fig,assen=panelen(hokken,titel,eenheid)
    for h,ax in zip(hokken,assen):
        d=hok[hok.hok==h].sort_values('interval')
        x=range(len(d)); labels=[f'{a:%d/%m}–{b:%d/%m}' for a,b in zip(d.vanaf,d.tot)]
        if soort=='groei_voeder':
            ax.plot(x,d.groei_g_dier_dag/factor,'o-',color='#176a89',label='Groei')
            ax.plot(x,d.voeder_g_dier_dag/factor,'s--',color='#c06b24',label='Voederopname')
        else:
            ax.plot(x,d.voederconversie,'o-',color='#6a4c93')
            for i,r in enumerate(d.itertuples()):
                if pd.notna(r.voederconversie): ax.annotate(f'n={r.dieren_bruikbaar}/{r.dieren_populatie}',(i,r.voederconversie),xytext=(0,8),textcoords='offset points',ha='center',fontsize=8)
        ax.set_xticks(list(x),labels,rotation=18,ha='right',fontsize=8)
        ax.set_xlabel('Interval (einddatum exclusief)')
    velden=['groei_g_dier_dag','voeder_g_dier_dag'] if soort=='groei_voeder' else ['voederconversie']
    maximum=hok[velden].max().max() / (factor if soort=='groei_voeder' else 1)
    assen[0].set_ylim(0,maximum*1.25 if pd.notna(maximum) and maximum>0 else 1)
    if soort=='groei_voeder': assen[0].legend(frameon=False,fontsize=9)
    return fig
