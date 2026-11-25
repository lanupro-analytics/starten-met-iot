"""Drie vooraf beschreven verkenningen, zonder behandeling als invoerkenmerk."""
from pathlib import Path
from contextlib import closing
import sqlite3,sys,json
import pandas as pd
import numpy as np
P=Path(__file__).parent
R=P.parents[1]
sys.path.insert(0,str(R/'programmatuur'))
from analyse_07 import selecteer,daggewichten,bereken_intervallen,vat_hokken_samen

def data():
    cache=P/'selectie.pkl'
    if cache.exists():return pd.read_pickle(cache)
    frames=[]
    for bron,rol,veld in [('asserva','gewichten','VBW'),('schauer','voederopname','VFI')]:
        with closing(sqlite3.connect(R/f'gegevens/origineel/{bron}.db')) as db:
            d=pd.read_sql_query(f'SELECT ROW_ID,EID,PEN,DATE,TIMESTAMPstart,TIMESTAMPstop,{veld},ERROR,FILTER,DATAORIGIN FROM metingen',db)
        fmt='%Y%m%d%H%M%S' if rol=='gewichten' else '%Y-%m-%d %H:%M:%S'
        frames.append(pd.DataFrame({'bron':bron,'record_id':d.ROW_ID,'meettype':rol,'dier_id':d.EID,'hok':d.PEN,'datum':d.DATE,'waarde':d[veld],'eenheid':'kg' if bron=='asserva' else 'g','tijd':pd.to_datetime(d.TIMESTAMPstart,format=fmt),'einde':pd.to_datetime(d.TIMESTAMPstop,format=fmt),'foutcode':d.ERROR,'vlag':d.FILTER,'herkomst':d.DATAORIGIN}))
    out=pd.concat(frames,ignore_index=True);out.to_pickle(cache);return out

START=pd.Timestamp('2023-08-24')
def datum(d):return START+pd.Timedelta(days=d)

def helling(dag,voer,pop,a,b):
    rows=[]
    for dier,hok in pop.itertuples(index=False,name=None):
        w=dag[(dag.dier_id==dier)&(dag.tijd>=datum(a))&(dag.tijd<datum(b))]
        f=voer[(voer.dier_id==dier)&(voer.tijd>=datum(a))&(voer.tijd<datum(b))]
        if len(w)<max(3,np.ceil(.7*(b-a))) or f.tijd.dt.normalize().nunique()!=b-a:continue
        x=(w.tijd-datum(a)).dt.total_seconds()/86400
        groei=float(np.polyfit(x,w.gewicht_kg,1)[0])
        if groei<=0:continue
        rows.append({'hok':hok,'dier_id':dier,'groei':groei,'voer':f.waarde.sum()/1000/(b-a)})
    d=pd.DataFrame(rows)
    r=d.groupby('hok').agg(n=('dier_id','size'),groei=('groei','mean'),voer=('voer','mean'))
    r['conversie']=r.voer/r.groei
    return r

if __name__=='__main__':
    raw=data();g,v,pop,_,_=selecteer(raw);dag=daggewichten(g)
    dag.to_pickle(P/'dag.pkl');v.to_pickle(P/'voer.pkl');pop.to_pickle(P/'pop.pkl')
    # A: dezelfde eindpuntsmethode als 07, met grenzen bij de voerwissels.
    grenzen=[datum(i) for i in (1,10,18,27)]
    h=vat_hokken_samen(bereken_intervallen(dag,v,pop,grenzen))
    h.to_csv(P/'poging1_interpolatie.csv',index=False)
    print('POGING 1: d10-18',flush=True)
    print(h[h.interval==2][['hok','dieren_bruikbaar','groei_g_dier_dag','voeder_g_dier_dag','voederconversie']].sort_values('groei_g_dier_dag').to_string(index=False),flush=True)
    # B: trend over alle dagmedianen in hetzelfde interval, geen enkel eindpunt.
    alle=[]
    for a,b in [(1,10),(10,18),(18,27)]:
        r=helling(dag,v,pop,a,b).reset_index().assign(vanaf_dag=a,tot_dag=b);alle.append(r)
    out=pd.concat(alle);out.to_csv(P/'poging2_helling.csv',index=False)
    print('POGING 2: d10-18',flush=True)
    print(out[out.vanaf_dag==10].sort_values('groei').to_string(index=False),flush=True)
    # C: vierdaagse vensters rondom beide wisselmomenten, dezelfde methode als B.
    alle=[]
    for a,b in [(6,10),(10,14),(14,18),(18,22)]:
        alle.append(helling(dag,v,pop,a,b).reset_index().assign(vanaf_dag=a,tot_dag=b))
    out=pd.concat(alle);out.to_csv(P/'poging3_wissel.csv',index=False)
    print('POGING 3',flush=True)
    print(out.pivot(index='hok',columns='vanaf_dag',values=['groei','conversie']).round(3).to_string(),flush=True)
