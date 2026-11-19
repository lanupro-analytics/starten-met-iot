"""Gevalideerde berichtinhoud, SQLite-opslag en controle van volledige beginsets."""
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import math
import re
import sqlite3

ROLLEN={'gewichten':('asserva','VBW','kg'), 'voederopname':('schauer','VFI','g')}
VELDEN={'schema_versie','deelnemer','bron','meettype','record_id','dier_id','hok','tijd','tijdzone','meetveld','waarde','eenheid','hokmetadata','bronrecord'}


def nu():
    return datetime.now(timezone.utc).isoformat()


def canoniek(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


def inhoud(bericht):
    return canoniek({k:v for k,v in bericht.items() if k!='deelnemer'})


def inhoud_hash(bericht):
    return hashlib.sha256(inhoud(bericht).encode()).hexdigest()


def _paren(items):
    d={}
    for k,v in items:
        if k in d: raise ValueError('dubbele_json_sleutel')
        d[k]=v
    return d


def _getal(v):
    return type(v) in (int,float) and math.isfinite(v)


def valideer(payload,topic,deelnemer,rol):
    """Weiger schemafouten, behoud echte nulwaarden en kwaliteitsvlaggen."""
    if len(payload)>60000: raise ValueError('bericht_te_groot')
    def ongeldig(x): raise ValueError('ongeldig_json_getal')
    try:
        b=json.loads(payload,object_pairs_hook=_paren,parse_constant=ongeldig)
        if not isinstance(b,dict) or set(b)!=VELDEN: raise ValueError('berichtvelden')
        if type(b['schema_versie']) is not int or b['schema_versie']!=1: raise ValueError('schema_versie')
        if rol not in ROLLEN: raise ValueError('meettype')
        bron,veld,eenheid=ROLLEN[rol]
        if topic!=f'practicum/{deelnemer}/metingen/{rol}' or b['deelnemer']!=deelnemer: raise ValueError('topic_of_deelnemer')
        if (b['bron'],b['meettype'],b['meetveld'],b['eenheid'])!=(bron,rol,veld,eenheid): raise ValueError('bron_of_eenheid')
        if not isinstance(b['record_id'],str) or not re.fullmatch(r'[0-9]{27,28}',b['record_id']): raise ValueError('record_id')
        if b['dier_id'] is not None and not isinstance(b['dier_id'],str): raise ValueError('dier_id')
        if not isinstance(b['hok'],str) or not b['hok']: raise ValueError('hok')
        if b['waarde'] is not None and not _getal(b['waarde']): raise ValueError('meetwaarde')
        if b['tijdzone']!='onbevestigd; vermoedelijk Europe/Brussels': raise ValueError('tijdzone')
        raw=b['bronrecord']; h=b['hokmetadata']
        if not isinstance(raw,dict) or any(isinstance(v,(dict,list,bool)) for v in raw.values()): raise ValueError('bronrecord')
        for k,v in raw.items():
            if type(v) in (float,int) and not _getal(v): raise ValueError('brongetal')
        for key,alias in [('ROW_ID','record_id'),('EID','dier_id'),('PEN','hok'),(veld,'waarde')]:
            if key not in raw or raw[key]!=b[alias]: raise ValueError('bronrecord_verschilt')
        datetime.strptime(raw['DATE'],'%Y-%m-%d')
        if not isinstance(b['tijd'],dict) or set(b['tijd'])!={'start','einde'}: raise ValueError('tijd')
        fmt='%Y%m%d%H%M%S' if rol=='gewichten' else '%Y-%m-%d %H:%M:%S'
        for src,dst in [('TIMESTAMPstart','start'),('TIMESTAMPstop','einde')]:
            t=None if raw[src] is None else datetime.strptime(raw[src],fmt).isoformat()
            if t!=b['tijd'][dst]: raise ValueError('tijd_verschilt')
        if not isinstance(h,dict) or set(h)!={'hok','gebouw','afdeling','oppervlakte_m2'}: raise ValueError('hokmetadata')
        if h['hok']!=b['hok'] or not isinstance(h['gebouw'],str) or not h['gebouw']: raise ValueError('gebouw_of_hok')
        if type(h['afdeling']) is not int or h['afdeling']<1 or not _getal(h['oppervlakte_m2']) or h['oppervlakte_m2']<=0: raise ValueError('afdeling_of_oppervlakte')
        inhoud(b)
        return b
    except (ValueError,TypeError,KeyError,UnicodeError,RecursionError,OverflowError) as exc:
        # Alleen vaste categorieën loggen, nooit de externe payload of wachtwoorden.
        raise ValueError('ongeldig_bericht') from exc


def open_opslag(pad):
    pad=Path(pad); pad.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(pad,timeout=10)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=FULL')
    db.executescript('''
CREATE TABLE IF NOT EXISTS metingen(
 bron TEXT NOT NULL, record_id TEXT NOT NULL, meettype TEXT NOT NULL,
 dier_id TEXT, hok TEXT NOT NULL, datum TEXT NOT NULL, waarde REAL, eenheid TEXT NOT NULL,
 eerste_deelnemer TEXT NOT NULL, inhoud_json TEXT NOT NULL, inhoud_sha256 TEXT NOT NULL,
 ontvangen_op TEXT NOT NULL, PRIMARY KEY(bron,record_id));
CREATE INDEX IF NOT EXISTS metingen_selectie ON metingen(meettype,datum,dier_id);
CREATE TABLE IF NOT EXISTS verbindingen(
 deelnemer TEXT NOT NULL, rol TEXT NOT NULL, toestand TEXT NOT NULL,
 nieuw INTEGER NOT NULL DEFAULT 0, dubbel INTEGER NOT NULL DEFAULT 0,
 ongeldig INTEGER NOT NULL DEFAULT 0, conflict INTEGER NOT NULL DEFAULT 0,
 bijgewerkt_op TEXT NOT NULL, PRIMARY KEY(deelnemer,rol));
CREATE TABLE IF NOT EXISTS ontvanger(id INTEGER PRIMARY KEY CHECK(id=1), bijgewerkt_op TEXT NOT NULL);
''')
    return db


def verwerk(db,payload,topic,deelnemer,rol):
    try:
        b=valideer(payload,topic,deelnemer,rol)
        tekst=inhoud(b); digest=hashlib.sha256(tekst.encode()).hexdigest()
        rij=db.execute('SELECT inhoud_sha256 FROM metingen WHERE bron=? AND record_id=?',(b['bron'],b['record_id'])).fetchone()
        if rij:
            uitkomst='dubbel' if rij[0]==digest else 'conflict'
        else:
            db.execute('INSERT INTO metingen VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                       (b['bron'],b['record_id'],rol,b['dier_id'],b['hok'],b['bronrecord']['DATE'],b['waarde'],b['eenheid'],deelnemer,tekst,digest,nu()))
            uitkomst='nieuw'
    except ValueError:
        uitkomst='ongeldig'
    # Kolomnaam is een interne keuze uit vier vaste waarden.
    db.execute(f'UPDATE verbindingen SET {uitkomst}={uitkomst}+1, bijgewerkt_op=? WHERE deelnemer=? AND rol=?',(nu(),deelnemer,rol))
    return uitkomst


def selectie_manifest(berichten):
    groepen={}
    for b in berichten:
        groepen.setdefault(b['bron'],[]).append((b['record_id'],inhoud_hash(b)))
    resultaat={}
    for bron,rijen in groepen.items():
        h=hashlib.sha256()
        for rid,digest in sorted(rijen): h.update(f'{rid}:{digest}\n'.encode())
        resultaat[bron]={'aantal':len(rijen),'sha256':h.hexdigest()}
    return resultaat


def overzicht(pad):
    pad=Path(pad).resolve()
    if not pad.is_file(): raise FileNotFoundError('De verzameldatabase is nog niet aangemaakt.')
    with closing(sqlite3.connect(pad.as_uri()+'?mode=ro',uri=True,timeout=10)) as db:
        db.row_factory=sqlite3.Row
        db.execute('BEGIN')
        bronnen={}
        for bron, in db.execute('SELECT DISTINCT bron FROM metingen ORDER BY bron'):
            h=hashlib.sha256(); aantal=0
            for rij in db.execute('SELECT record_id,inhoud_sha256 FROM metingen WHERE bron=? ORDER BY record_id',(bron,)):
                h.update(f'{rij[0]}:{rij[1]}\n'.encode()); aantal+=1
            bronnen[bron]={'aantal':aantal,'sha256':h.hexdigest()}
        heartbeat=db.execute('SELECT bijgewerkt_op FROM ontvanger WHERE id=1').fetchone()
        return {'gemaakt_op':nu(),'ontvanger_bijgewerkt_op':heartbeat[0] if heartbeat else None,
                'bronnen':bronnen,'verbindingen':[dict(r) for r in db.execute('SELECT * FROM verbindingen ORDER BY deelnemer,rol')]}
