"""Kleine, vaste figuurfuncties met vergelijkbare assen voor alle hokken."""
import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Vast nulpunt voor deze lesdataset. Notebooks berekenen dit ook uit beide bronnen.
PROCESSTART = pd.Timestamp('2023-08-24 12:00:00')


def procestijd(tijden, start=PROCESSTART):
    """Verstreken dagen inclusief uren en minuten, zonder afronding op kalenderdagen."""
    return (pd.to_datetime(tijden) - pd.Timestamp(start)) / pd.Timedelta(days=1)


def procesas(ax, vanaf, tot):
    """Dagenas met dezelfde wisselmomenten voor alle hokken."""
    links=min(0,float(vanaf)); rechts=max(18,float(tot))
    ticks=sorted(set(np.arange(0,np.floor(rechts/5)*5+1,5).tolist()+[10,18]))
    ax.set_xticks(ticks)
    ax.set_xlim(links-.3,rechts+.5)
    ax.set_xlabel('Procestijd (dagen na eerste meetpunt)')
    ax.tick_params(axis='x',labelbottom=True)
    for dag in (10,18):
        ax.axvline(dag,color='#777777',linestyle=':',linewidth=1)
        ax.text(dag,.98,f'dag {dag}',transform=ax.get_xaxis_transform(),
                rotation=90,ha='right',va='top',fontsize=8,color='#555555')


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


def gewichtsfiguur(dag,start=PROCESSTART):
    hokken=hokvolgorde(dag.hok)
    fig,assen=panelen(hokken,'Gewichtsverloop per hok','Gewicht (kg)')
    for hok,ax in zip(hokken,assen):
        d=dag[dag.hok==hok].groupby('dag').agg(gewicht=('gewicht_kg','mean'),tijd=('tijd','median'))
        d=d.reindex(pd.date_range(d.index.min(),d.index.max(),freq='D'))
        # Houd ontbrekende dagen als gaten in de lijn, niet als interpolaties.
        tijden=d.tijd.fillna(pd.Series(d.index+pd.Timedelta(hours=12),index=d.index))
        ax.plot(procestijd(tijden,start),d.gewicht,color='#176a89',linewidth=1.8)
        procesas(ax,procestijd(dag.tijd.min(),start),procestijd(dag.tijd.max(),start))
    return fig


def intervalfiguur(hok,soort='groei_voeder',kilogram=False,start=PROCESSTART):
    if soort not in ('groei_voeder','conversie'): raise ValueError('Onbekend figuurtype.')
    hokken=hokvolgorde(hok.hok)
    titel='Gemiddelde groei en voederopname per interval' if soort=='groei_voeder' else 'Voederconversie per interval'
    factor=1000 if kilogram else 1
    eenheid=('kg per dier per dag' if kilogram else 'g per dier per dag') if soort=='groei_voeder' else 'kg voeder / kg groei'
    fig,assen=panelen(hokken,titel,eenheid)
    for h,ax in zip(hokken,assen):
        d=hok[hok.hok==h].sort_values('interval')
        begin=procestijd(d.vanaf,start)
        einde=procestijd(d.tot,start)
        x=(begin+einde)/2
        if soort=='groei_voeder':
            ax.plot(x,d.groei_g_dier_dag/factor,'o-',color='#176a89',label='Groei')
            ax.plot(x,d.voeder_g_dier_dag/factor,'s--',color='#c06b24',label='Voederopname')
        else:
            ax.plot(x,d.voederconversie,'o-',color='#6a4c93')
            for i,r in enumerate(d.itertuples()):
                if pd.notna(r.voederconversie): ax.annotate(f'{r.dieren_bruikbaar}/{r.dieren_populatie} dieren',(x.iloc[i],r.voederconversie),xytext=(0,8),textcoords='offset points',ha='center',fontsize=8)
        waarden=[(d.groei_g_dier_dag/factor,'#176a89'),(d.voeder_g_dier_dag/factor,'#c06b24')] if soort=='groei_voeder' else [(d.voederconversie,'#6a4c93')]
        for y,kleur in waarden: ax.hlines(y,begin,einde,color=kleur,alpha=.35,linewidth=2)
        procesas(ax,procestijd(hok.vanaf.min(),start),procestijd(hok.tot.max(),start))
    velden=['groei_g_dier_dag','voeder_g_dier_dag'] if soort=='groei_voeder' else ['voederconversie']
    maximum=hok[velden].max().max() / (factor if soort=='groei_voeder' else 1)
    assen[0].set_ylim(0,maximum*1.25 if pd.notna(maximum) and maximum>0 else 1)
    if soort=='groei_voeder': assen[0].legend(frameon=False,fontsize=9)
    return fig
