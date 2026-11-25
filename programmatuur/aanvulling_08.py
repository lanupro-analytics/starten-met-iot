"""Gecontroleerde Excel-toevoegingen en vergelijking met de bewaarde basis uit 07."""
from contextlib import closing
from pathlib import Path
import gzip
import hashlib
import json
import math
import re
import sqlite3
import tempfile

import pandas as pd
from openpyxl import load_workbook
from analyse_07 import METHODE, selecteer, daggewichten, bereken_intervallen, vat_hokken_samen


def lees_excel(pad, controle):
    """Lees exact de twee meetbladen. Lange identificaties moeten echte tekst blijven."""
    pad=Path(pad)
    if hashlib.sha256(pad.read_bytes()).hexdigest()!=controle['xlsx_sha256']:
        raise ValueError('Het Excel-bestand is gewijzigd. Gebruik de vrijgegeven aanvulling uit de repository.')
    schema=controle['schema']; kolommen=list(schema); rijen=[]; samenvatting=[]
    wb=load_workbook(pad,read_only=True,data_only=False)
    try:
        for naam,aantal in controle['bladen'].items():
            if naam not in wb.sheetnames: raise ValueError('Een meetblad ontbreekt.')
            it=wb[naam].iter_rows(values_only=True)
            if list(next(it))!=kolommen: raise ValueError('Kolomnamen of kolomvolgorde wijken af.')
            blad=[]
            for rij in it:
                r={}
                for k,v in zip(kolommen,rij):
                    if schema[k]=='TEXT':
                        if v is not None and not isinstance(v,str): raise ValueError(f'{k} moet tekst blijven.')
                        r[k]='' if v is None else v
                    else:
                        if v is not None and (type(v) not in (int,float) or not math.isfinite(v)):
                            raise ValueError(f'{k} bevat geen geldig getal.')
                        r[k]=v
                if not re.fullmatch(r'\d{27,28}',r['ROW_ID']): raise ValueError('ROW_ID is beschadigd.')
                begin,einde=('2023-09-21','2023-09-28') if naam=='week_5' else ('2023-09-28','2023-10-06')
                if not begin<=r['DATE']<einde: raise ValueError('Een meetdatum hoort niet bij dit blad.')
                blad.append(r)
            if len(blad)!=aantal: raise ValueError('Onverwacht aantal Excel-records.')
            samenvatting.append({'werkblad':naam,'records':len(blad),'eerste_datum':min(r['DATE'] for r in blad),'laatste_datum':max(r['DATE'] for r in blad)})
            rijen.extend(blad)
    finally: wb.close()
    if len({r['ROW_ID'] for r in rijen})!=len(rijen): raise ValueError('Dubbele ROW_ID in Excel.')
    return rijen,pd.DataFrame(samenvatting)


def voeg_toe(pad,rijen,controle):
    """Alles of niets. Identieke herhaling is toegestaan, gewijzigde bestaande rij niet."""
    pad=Path(pad).resolve()
    if not pad.is_file() or 'origineel' in pad.parts: raise ValueError('Kies je bestaande werkdatabase, niet het origineel.')
    with closing(sqlite3.connect(pad,timeout=10)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        meta=dict(db.execute('SELECT * FROM metadata'))
        if meta.get('rol')!=controle['rol'] or meta.get('bron_sha256')!=controle['bron_sha256']:
            raise ValueError('Deze aanvulling hoort niet bij de gekozen database.')
        schema={r[1]:r[2] for r in db.execute('PRAGMA table_info(metingen)')}
        if schema!=controle['schema']: raise ValueError('De tabelstructuur wijkt af.')
        velden=list(schema); nieuw=gelijk=0
        bestaand={r[0]:r for r in db.execute('SELECT '+','.join('"'+k+'"' for k in velden)+' FROM metingen')}
        voor=len(bestaand)
        gezien=set()
        for r in rijen:
            rid=r['ROW_ID']
            if rid in gezien or not '2023-09-21'<=r['DATE']<'2023-10-06': raise ValueError('Dubbele rij of ongeldige aanvullende datum.')
            gezien.add(rid)
            rij=tuple(r[k] for k in velden)
            if rid in bestaand:
                if bestaand[rid]!=rij: raise ValueError('Bestaande meting verschilt. Niets toegevoegd. Controleer je werkbestand.')
                gelijk+=1
            else:
                db.execute('INSERT INTO metingen VALUES('+','.join('?' for _ in velden)+')',rij); nieuw+=1
        return {'voor':voor,'nieuw':nieuw,'ongewijzigd':gelijk,'na':voor+nieuw}


def lees_basis(map):
    map=Path(map); info=json.loads((map/'beginsituatie.json').read_text(encoding='utf-8'))
    if info['methode']!=METHODE: raise ValueError('De rekenmethode uit 07 verschilt.')
    tabellen={}
    for naam,digest in info['bestanden'].items():
        if naam not in ('populatie.csv','daggewichten.csv','dierintervallen.csv','hokresultaten.csv'):
            raise ValueError('Onbekende tabel in beginsituatie.')
        # Git kan regeleinden omzetten. De bewaarde hash betreft tekst met LF.
        tekst=(map/naam).read_text(encoding='utf-8')
        if hashlib.sha256(tekst.encode()).hexdigest()!=digest: raise ValueError('De beginsituatie is gewijzigd.')
        d=pd.read_csv(map/naam,dtype={'dier_id':str,'hok':str})
        for veld in ('vanaf','tot','dag','tijd'):
            if veld in d:d[veld]=pd.to_datetime(d[veld])
        tabellen[naam]=d
    return info,tabellen


def vergelijk_basis(data,info,tabellen):
    g,v,pop,_,_=selecteer(data)
    dag=daggewichten(g)
    dier=bereken_intervallen(g,v,pop,info['regels']['grenzen'])
    hok=vat_hokken_samen(dier)
    for naam,d in [('populatie.csv',pop),('daggewichten.csv',dag),('dierintervallen.csv',dier),('hokresultaten.csv',hok)]:
        verwacht=tabellen[naam].copy()
        # De CSV bewaart lege ontbrekende waarden en twaalf significante cijfers.
        if 'reden' in verwacht: verwacht['reden']=verwacht['reden'].fillna('')
        pd.testing.assert_frame_equal(d.reset_index(drop=True),verwacht.reset_index(drop=True),check_dtype=False,check_exact=False,rtol=1e-10,atol=1e-10)
    return hok


def uitgebreide_analyse(data,populatie):
    g,v,pop,audit,uit=selecteer(data,tot='2023-10-06')
    oud=populatie.sort_values('dier_id').reset_index(drop=True)
    nieuw=pop.sort_values('dier_id').reset_index(drop=True)
    pd.testing.assert_frame_equal(oud,nieuw,check_dtype=False)
    dag=daggewichten(g)
    grenzen=['2023-08-25','2023-09-01','2023-09-08','2023-09-15','2023-09-20','2023-09-21','2023-09-28','2023-10-05']
    # De vier oude intervallen krijgen hun oorspronkelijke, tijdslokale selectie.
    gb,vb,pb,_,_=selecteer(data)
    basis=bereken_intervallen(gb,vb,pb,grenzen[:5])
    later=bereken_intervallen(g,v,pop,grenzen[4:]);later['interval']+=4
    intervallen=pd.concat([basis,later],ignore_index=True)
    delen=[]
    for naam,start,eind in [('basis','2023-08-25','2023-09-20'),('aanvulling','2023-09-21','2023-10-05'),('geheel','2023-08-25','2023-10-05')]:
        dd,vv,pp=(gb,vb,pb) if naam=='basis' else (g,v,pop)
        d=bereken_intervallen(dd,vv,pp,[start,eind]);d['periode']=naam;delen.append(d)
    perioden=pd.concat(delen,ignore_index=True)
    hokken=pd.concat([vat_hokken_samen(d).assign(periode=naam) for naam,d in perioden.groupby('periode',sort=False)],ignore_index=True)
    return {'dag':dag,'dierintervallen':intervallen,'hokintervallen':vat_hokken_samen(intervallen),'dierperioden':perioden,'hokperioden':hokken,'audit':audit}


def snapshot(pad,doel):
    """Consistente SQLite-back-up, gecomprimeerd voor bewuste inlevering."""
    pad=Path(pad).resolve();doel=Path(doel)
    doel.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='snapshot08-') as tmp:
        kopie=Path(tmp)/'analyse.db'
        with closing(sqlite3.connect(pad.as_uri()+'?mode=ro',uri=True)) as bron,closing(sqlite3.connect(kopie)) as db:
            bron.backup(db)
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Snapshotcontrole mislukt.')
        with kopie.open('rb') as src,doel.open('wb') as dst,gzip.GzipFile(fileobj=dst,mode='wb',mtime=0) as gz:
            import shutil
            shutil.copyfileobj(src,gz)
    return {'bestand':doel.name,'bytes':doel.stat().st_size,'sha256':hashlib.sha256(doel.read_bytes()).hexdigest()}
