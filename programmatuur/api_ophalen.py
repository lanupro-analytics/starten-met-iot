"""HTTPS-aanvragen en gecontroleerde, herhaalbare import voor notebook 06."""
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import hashlib
import json
import sqlite3
import time

import requests
from meetgegevens import canoniek, inhoud_hash, valideer

APP_ID = 600106


class ApiClient:
    def __init__(self, basisurl, ca, wachtwoord):
        u = urlsplit(basisurl)
        if u.scheme != 'https' or not u.hostname or u.username or u.password or u.query or u.fragment or u.path not in ('','/'):
            raise ValueError('Gebruik alleen het HTTPS-adres van je eigen server.')
        self.basisurl = basisurl.rstrip('/')
        self.sessie = requests.Session()
        self.sessie.auth = ('eigenaar', wachtwoord)
        self.sessie.verify = str(ca)
        self.laatste = 0.0

    def antwoord(self, pad, parameters=None):
        if pad not in ('/gezondheid','/metadata','/metingen','/openapi.json'):
            raise ValueError('Kies een gedocumenteerd API-pad.')
        time.sleep(max(0, .25-(time.monotonic()-self.laatste)))
        try:
            r = self.sessie.get(self.basisurl+pad, params=parameters, timeout=(5,30), allow_redirects=False)
        except requests.exceptions.SSLError:
            raise RuntimeError('Certificaatcontrole mislukt. Controleer ca.crt en het serveradres.') from None
        except requests.exceptions.RequestException:
            raise RuntimeError('Geen volledig API-antwoord. Controleer je verbinding en hervat de cel.') from None
        finally:
            self.laatste = time.monotonic()
        return r

    def ophalen(self, pad, parameters=None):
        r = self.antwoord(pad, parameters)
        if r.status_code != 200:
            raise RuntimeError(f'API geeft HTTP {r.status_code}. Controleer de foutentabel in notebook 06.')
        try: return r.json()
        except ValueError:
            raise RuntimeError('Het API-antwoord is geen geldige JSON.') from None

    def sluiten(self):
        self.sessie.auth = None
        self.sessie.close()


def analyse_overzicht(db):
    resultaat = {}
    for bron in ('asserva','schauer'):
        h=hashlib.sha256(); aantal=0
        for rid, digest in db.execute('SELECT record_id,inhoud_sha256 FROM metingen WHERE bron=? ORDER BY record_id',(bron,)):
            h.update(f'{rid}:{digest}\n'.encode()); aantal += 1
        resultaat[bron]={'aantal':aantal,'sha256':h.hexdigest()}
    return resultaat


def werk_analyse_bij(ophalen, pad, voortgang=print):
    """Lees beide stromen volledig. Bij een fout wordt de import teruggedraaid."""
    meta=ophalen('/metadata')
    if not isinstance(meta,dict) or meta.get('api_versie')!=1 or type(meta.get('grens')) is not int or meta['grens']<0:
        raise ValueError('Ongeldige API-metadata.')
    verwacht=meta.get('bronnen')
    if not isinstance(verwacht,dict) or set(verwacht)!={'asserva','schauer'}:
        raise ValueError('Beide bronnen moeten in de metadata staan.')
    for bron, info in verwacht.items():
        if type(info.get('aantal')) is not int or info['aantal']<1:
            raise ValueError(f'Bron {bron} is nog leeg. Rond de volledige ontvangst in notebook 05 af.')
        if not isinstance(info.get('sha256'),str) or len(info['sha256'])!=64:
            raise ValueError('Ongeldige inhoudsvingerafdruk.')
    pad=Path(pad).resolve()
    if pad.exists():
        with closing(sqlite3.connect(pad.as_uri()+'?mode=ro',uri=True)) as bestaand:
            if bestaand.execute('PRAGMA application_id').fetchone()[0]!=APP_ID:
                raise ValueError('Dit is geen analysedatabase van notebook 06. Kies een apart nieuw bestand.')
    pad.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(pad,timeout=10)) as db:
        db.executescript(f'''
PRAGMA application_id={APP_ID};
CREATE TABLE IF NOT EXISTS metingen(
 bron TEXT NOT NULL, record_id TEXT NOT NULL, meettype TEXT NOT NULL,
 dier_id TEXT, hok TEXT NOT NULL, datum TEXT NOT NULL, waarde REAL, eenheid TEXT NOT NULL,
 inhoud_json TEXT NOT NULL, inhoud_sha256 TEXT NOT NULL, PRIMARY KEY(bron,record_id));
CREATE TABLE IF NOT EXISTS ophalen(id INTEGER PRIMARY KEY CHECK(id=1), gecontroleerd_op TEXT, metadata_json TEXT);
''')
        nieuw=0; gelijk=0; na=0; totaal=0; pagina_nr=0
        with db:
            db.execute('BEGIN')
            db.execute('CREATE TEMP TABLE gezien(bron TEXT, record_id TEXT, PRIMARY KEY(bron,record_id))')
            while True:
                pagina=ophalen('/metingen',{'grens':meta['grens'],'na':na,'limiet':1000})
                if (not isinstance(pagina,dict) or pagina.get('api_versie')!=1 or pagina.get('grens')!=meta['grens']
                    or not isinstance(pagina.get('metingen'),list) or pagina.get('aantal')!=len(pagina['metingen'])
                    or len(pagina['metingen'])>1000):
                    raise ValueError('Ongeldige API-pagina.')
                for b in pagina['metingen']:
                    if not isinstance(b,dict): raise ValueError('Ongeldig meetrecord.')
                    rol=b.get('meettype')
                    # Gebruik dezelfde inhoudscontrole als de MQTT-ontvanger.
                    controle=dict(b,deelnemer='api')
                    valideer(canoniek(controle),f'practicum/api/metingen/{rol}','api',rol)
                    if 'deelnemer' in b: raise ValueError('Onverwacht transportveld in API-record.')
                    digest=inhoud_hash(b)
                    try: db.execute('INSERT INTO gezien VALUES(?,?)',(b['bron'],b['record_id']))
                    except sqlite3.IntegrityError:
                        raise ValueError('De API herhaalt een record binnen dezelfde overdracht.') from None
                    vorig=db.execute('SELECT inhoud_sha256 FROM metingen WHERE bron=? AND record_id=?',(b['bron'],b['record_id'])).fetchone()
                    if vorig:
                        if vorig[0]!=digest: raise ValueError('Een bestaande meting heeft andere inhoud. Bespreek dit vóór je verdergaat.')
                        gelijk+=1
                    else:
                        db.execute('INSERT INTO metingen VALUES(?,?,?,?,?,?,?,?,?,?)',
                                   (b['bron'],b['record_id'],rol,b['dier_id'],b['hok'],b['bronrecord']['DATE'],b['waarde'],b['eenheid'],canoniek(b),digest))
                        nieuw+=1
                totaal+=len(pagina['metingen']); pagina_nr+=1
                if totaal>sum(v['aantal'] for v in verwacht.values()): raise ValueError('Meer records dan aangekondigd.')
                if pagina_nr%25==0: voortgang(f'{totaal:,} records gecontroleerd')
                volgende=pagina.get('volgende_na')
                if volgende is None: break
                if type(volgende) is not int or not na<volgende<=meta['grens'] or not pagina['metingen']:
                    raise ValueError('De paginering gaat niet vooruit.')
                na=volgende
            werkelijk=analyse_overzicht(db)
            if totaal!=sum(v['aantal'] for v in verwacht.values()) or werkelijk!=verwacht:
                raise ValueError('Aantallen of inhoud verschillen. Import teruggedraaid. Controleer de server en probeer opnieuw.')
            tijd=datetime.now(timezone.utc).isoformat()
            db.execute('INSERT OR REPLACE INTO ophalen VALUES(1,?,?)',(tijd,json.dumps(meta)))
        voortgang(f'Klaar: {nieuw:,} nieuwe records, {gelijk:,} ongewijzigde records.')
    return {'gecontroleerd_op_utc':tijd,'nieuw':nieuw,'ongewijzigd':gelijk,'bronnen':werkelijk,'grens':meta['grens']}
