"""Verklaarde verkennende berekeningen voor notebook 07, zonder bronwijzigingen."""
from contextlib import closing
from pathlib import Path
import hashlib
import json
import math
import sqlite3

import numpy as np
import pandas as pd

METHODE = 'dagmediaan_lineair_07_v1'
STANDAARD_GRENZEN = ['2023-08-25','2023-09-01','2023-09-08','2023-09-15','2023-09-20']


def lees_analyse(pad):
    """Lees uitsluitend benodigde velden. Behandelingscodes worden niet geselecteerd."""
    pad=Path(pad).resolve()
    if not pad.is_file(): raise FileNotFoundError('Rond de import van notebook 06 af.')
    with closing(sqlite3.connect(pad.as_uri()+'?mode=ro',uri=True)) as db:
        if db.execute('PRAGMA application_id').fetchone()[0]!=600106:
            raise ValueError('Gebruik de analysedatabase uit notebook 06.')
        db.execute('BEGIN')
        opname=db.execute('SELECT metadata_json FROM ophalen WHERE id=1').fetchone()
        if not opname: raise ValueError('De analysedatabase bevat geen geslaagde ophaalronde.')
        metadata=json.loads(opname[0])
        manifest={}
        for bron in ('asserva','schauer'):
            h=hashlib.sha256(); aantal=0
            for rid,tekst,digest in db.execute('SELECT record_id,inhoud_json,inhoud_sha256 FROM metingen WHERE bron=? ORDER BY record_id',(bron,)):
                if hashlib.sha256(tekst.encode()).hexdigest()!=digest:
                    raise ValueError('Meetinhoud gewijzigd na import. Controleer notebook 06.')
                h.update(f'{rid}:{digest}\n'.encode()); aantal+=1
            manifest[bron]={'aantal':aantal,'sha256':h.hexdigest()}
        if manifest!=metadata['bronnen']:
            raise ValueError('De database komt niet overeen met de laatste geslaagde API-import.')
        afwijkend=db.execute('''SELECT 1 FROM metingen WHERE
            bron IS NOT json_extract(inhoud_json,'$.bron') OR
            record_id IS NOT json_extract(inhoud_json,'$.record_id') OR
            meettype IS NOT json_extract(inhoud_json,'$.meettype') OR
            dier_id IS NOT json_extract(inhoud_json,'$.dier_id') OR
            hok IS NOT json_extract(inhoud_json,'$.hok') OR
            datum IS NOT json_extract(inhoud_json,'$.bronrecord.DATE') OR
            waarde IS NOT json_extract(inhoud_json,'$.waarde') OR
            eenheid IS NOT json_extract(inhoud_json,'$.eenheid') LIMIT 1''').fetchone()
        if afwijkend: raise ValueError('Zoekvelden wijken af van de ontvangen meetinhoud. Herstel de API-import.')
        data=pd.read_sql_query('''SELECT bron,record_id,meettype,dier_id,hok,datum,waarde,eenheid,
            json_extract(inhoud_json,'$.tijd.start') AS tijd,
            json_extract(inhoud_json,'$.tijd.einde') AS einde,
            json_extract(inhoud_json,'$.bronrecord.ERROR') AS foutcode,
            json_extract(inhoud_json,'$.bronrecord.FILTER') AS vlag,
            json_extract(inhoud_json,'$.bronrecord.DATAORIGIN') AS herkomst
            FROM metingen ORDER BY bron,record_id''',db)
    return data,manifest


def selecteer(data, vanaf='2023-08-24', tot='2023-09-21', streng=False):
    """Behoud bronrecords, maak een aparte selectie met een aflopende audit."""
    if data.duplicated(['bron','record_id']).any():
        raise ValueError('Dubbele bronidentificatie. Herstel de import, verwijder niet willekeurig rijen.')
    verwacht={'asserva':('gewichten','kg'),'schauer':('voederopname','g')}
    if set(data.bron)!=set(verwacht): raise ValueError('Beide bronnen zijn nodig.')
    for bron,(rol,eenheid) in verwacht.items():
        d=data[data.bron==bron]
        if not d.meettype.eq(rol).all() or not d.eenheid.eq(eenheid).all():
            raise ValueError('Onverwacht meettype of eenheid. Controleer notebook 06.')
    d=data.copy()
    d['tijd']=pd.to_datetime(d['tijd'],errors='coerce')
    d['einde']=pd.to_datetime(d['einde'],errors='coerce')
    d['waarde']=pd.to_numeric(d['waarde'],errors='coerce')
    audit=[]
    def stap(naam,mask):
        nonlocal d
        voor=d.groupby('bron').size()
        d=d.loc[mask].copy()
        na=d.groupby('bron').size()
        for bron in verwacht:
            audit.append({'stap':naam,'bron':bron,'over':int(na.get(bron,0)),
                          'uitgesloten':int(voor.get(bron,0)-na.get(bron,0))})
    stap('Gekozen bronperiode',(d.datum>=vanaf)&(d.datum<tot))
    stap('Geldige herkenning',d.foutcode.eq('no error')&~d.vlag.eq('errored')&d.dier_id.notna()&d.hok.notna())
    # Leg de populatie vast vóór numerieke kwaliteitsselectie.
    maps={}
    for bron in verwacht:
        g=d[d.bron==bron].groupby('dier_id').hok.agg(lambda s: sorted(set(s)))
        maps[bron]=g.to_dict()
    populatie=[]; uitgesloten=[]
    for dier in sorted(set(maps['asserva'])|set(maps['schauer'])):
        a=maps['asserva'].get(dier,[]); b=maps['schauer'].get(dier,[])
        if len(a)==len(b)==1 and a==b: populatie.append({'dier_id':dier,'hok':a[0]})
        else: uitgesloten.append({'dier_id':dier,'reden':'ontbrekende_of_onzekere_hokkoppeling'})
    pop=pd.DataFrame(populatie,columns=['dier_id','hok'])
    if pop.empty: raise ValueError('Geen stabiel gekoppelde dieren beschikbaar.')
    stap('Stabiel gekoppelde dieren',d.dier_id.isin(pop.dier_id))
    stap('Geldige tijd en waarde',d.tijd.notna()&d.einde.notna()&(d.einde>=d.tijd)&d.tijd.dt.strftime('%Y-%m-%d').eq(d.datum)&
         np.isfinite(d.waarde)&((d.bron.eq('asserva')&(d.waarde>0))|(d.bron.eq('schauer')&(d.waarde>=0))))
    stap('Oorspronkelijke gewichten',d.bron.eq('schauer')|d.herkomst.isin(['0','manualweighing','allocation']))
    if streng: stap('Alleen ongemarkeerde records',d.vlag.eq('0'))
    return (d[d.bron=='asserva'].copy(),d[d.bron=='schauer'].copy(),pop,
            pd.DataFrame(audit),pd.DataFrame(uitgesloten,columns=['dier_id','reden']))


def daggewichten(gewichten):
    """Eén mediaan per dier-dag met de mediane waarnemingstijd als tijdpositie."""
    d=gewichten.copy(); d['dag']=d.tijd.dt.floor('D')
    return (d.groupby(['dier_id','hok','dag'],as_index=False)
             .agg(tijd=('tijd','median'),gewicht_kg=('waarde','median'),metingen=('waarde','size'))
             .sort_values(['dier_id','tijd']).reset_index(drop=True))


def schat_gewicht(dagen, tijd, max_uren=48):
    """Interpolatie tussen twee dagmedianen, geen extrapolatie of lange gaten."""
    d=dagen.sort_values('tijd'); tijd=pd.Timestamp(tijd)
    exact=d[d.tijd==tijd]
    if len(exact): return float(exact.iloc[0].gewicht_kg),'exacte_dagmediaan',0.0
    links=d[d.tijd<tijd]; rechts=d[d.tijd>tijd]
    if links.empty or rechts.empty: return None,'gewicht_niet_omsloten',None
    a=links.iloc[-1]; b=rechts.iloc[0]
    uren=(b.tijd-a.tijd).total_seconds()/3600
    if uren>max_uren: return None,'gewichtsgat_te_groot',uren
    fractie=(tijd-a.tijd).total_seconds()/(b.tijd-a.tijd).total_seconds()
    return float(a.gewicht_kg+fractie*(b.gewicht_kg-a.gewicht_kg)),'geschat',uren


def bereken_intervallen(dag,voer,pop,grenzen,max_uren=48):
    grenzen=pd.DatetimeIndex(pd.to_datetime(grenzen))
    if len(grenzen)<2 or not grenzen.is_monotonic_increasing or grenzen.has_duplicates:
        raise ValueError('Gebruik minstens twee strikt oplopende grenzen.')
    if any(t!=t.normalize() for t in grenzen):
        raise ValueError('Gebruik middernachtgrenzen voor de kalenderdagcontrole.')
    if not math.isfinite(max_uren) or max_uren<=0: raise ValueError('Ongeldige maximale gewichtsafstand.')
    rijen=[]
    for nr,(start,eind) in enumerate(zip(grenzen[:-1],grenzen[1:]),1):
        dagen=(eind-start).days
        for dier,hok in pop[['dier_id','hok']].itertuples(index=False,name=None):
            d=dag[(dag.dier_id==dier)&(dag.hok==hok)]
            f=voer[(voer.dier_id==dier)&(voer.hok==hok)&(voer.tijd>=start)&(voer.tijd<eind)]
            begin,rb,gb=schat_gewicht(d,start,max_uren); einde,re,ge=schat_gewicht(d,eind,max_uren)
            redenen=[]
            if begin is None: redenen.append('begin_'+rb)
            if einde is None: redenen.append('eind_'+re)
            voer_dagen=f.tijd.dt.normalize().nunique()
            if voer_dagen!=dagen: redenen.append('voederdagen_ontbreken')
            groei=None if begin is None or einde is None else einde-begin
            if groei is not None and groei<=0: redenen.append('geen_positieve_groei')
            # Een lege dag wordt niet stilzwijgend vervangen door nul voer.
            voeder=float(f.waarde.sum()/1000) if len(f) else None
            bruikbaar=not redenen
            rijen.append({'interval':nr,'vanaf':start,'tot':eind,'dagen':dagen,'dier_id':dier,'hok':hok,
                          'begin_kg':begin,'eind_kg':einde,'groei_kg':groei,'voeder_kg':voeder,
                          'voederdagen':voer_dagen,'voederbezoeken':len(f),
                          'grensbezoeken':int((f.einde>eind).sum()) if 'einde' in f else 0,
                          'afstand_begin_uren':gb,'afstand_eind_uren':ge,
                          'bruikbaar':bruikbaar,'reden':'bruikbaar' if bruikbaar else ';'.join(redenen),
                          'voederconversie':voeder/groei if bruikbaar else np.nan})
    return pd.DataFrame(rijen)


def bewaar_basis(map, populatie, dag, dier, hok, manifest, regels):
    """Bewaar de beginsituatie één keer. Gewijzigde resultaten overschrijven haar niet."""
    map=Path(map)
    tabellen={'populatie.csv':populatie,'daggewichten.csv':dag,
              'dierintervallen.csv':dier,'hokresultaten.csv':hok}
    teksten={naam:df.to_csv(index=False,float_format='%.12g',date_format='%Y-%m-%dT%H:%M:%S.%f',lineterminator='\n')
             for naam,df in tabellen.items()}
    beschrijving={'schema_versie':1,'methode':METHODE,'regels':regels,'bronnen':manifest,
                  'bestanden':{naam:hashlib.sha256(tekst.encode()).hexdigest() for naam,tekst in teksten.items()}}
    teksten['beginsituatie.json']=json.dumps(beschrijving,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    if map.exists():
        if any(not (map/naam).is_file() or (map/naam).read_text(encoding='utf-8')!=tekst for naam,tekst in teksten.items()):
            raise ValueError('De bewaarde beginsituatie verschilt. Behoud deze en bespreek wijzigingen voordat je verdergaat.')
        return beschrijving
    # Schrijf eerst naar een tijdelijke buurmap, zodat onderbreking geen halve basis achterlaat.
    import tempfile
    import shutil
    map.parent.mkdir(parents=True,exist_ok=True)
    tijdelijk=Path(tempfile.mkdtemp(prefix='.basis07-',dir=map.parent))
    try:
        for naam,tekst in teksten.items(): (tijdelijk/naam).write_text(tekst,encoding='utf-8',newline='\n')
        tijdelijk.rename(map)
    finally:
        if tijdelijk.exists():
            if tijdelijk.resolve().parent!=map.parent.resolve(): raise RuntimeError('Onverwachte tijdelijke map.')
            shutil.rmtree(tijdelijk)
    return beschrijving


def vat_hokken_samen(dier):
    rijen=[]
    for (hok,nr,start,eind,dagen),g in dier.groupby(['hok','interval','vanaf','tot','dagen'],sort=True):
        goed=g[g.bruikbaar]; n=len(goed)
        groei=float(goed.groei_kg.sum()) if n else np.nan
        voeder=float(goed.voeder_kg.sum()) if n else np.nan
        rijen.append({'hok':hok,'interval':nr,'vanaf':start,'tot':eind,'dagen':dagen,
                      'dieren_populatie':len(g),'dieren_bruikbaar':n,'dekking_pct':100*n/len(g),
                      'groei_kg':groei,'voeder_kg':voeder,
                      'groei_g_dier_dag':1000*groei/(n*dagen) if n else np.nan,
                      'voeder_g_dier_dag':1000*voeder/(n*dagen) if n else np.nan,
                      'voederconversie':voeder/groei if n and groei>0 else np.nan})
    return pd.DataFrame(rijen)
