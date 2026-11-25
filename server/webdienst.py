"""Alleen-lezen meetgegevens-API op de bestaande HTTPS-verbinding uit notebook 03."""
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Annotated, Literal
import hashlib
import json
import sqlite3

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from toegang_api import geldig


def maak_app(database='/var/lib/iot/verzamelde_metingen.db', controle=None):
    """Maak de dienst. Alternatieve paden zijn uitsluitend voor geïsoleerde tests."""
    pad = Path(database).resolve()
    controle = controle or Path('/etc/iot/api.controlewaarde').read_text().strip()
    beveiliging = HTTPBasic()

    def aanmelden(inlog: HTTPBasicCredentials = Depends(beveiliging)):
        ok = len(inlog.password) <= 200 and geldig(inlog.password, controle)
        if not ok or inlog.username != 'eigenaar':
            raise HTTPException(401, 'Ongeldige aanmelding.', headers={'WWW-Authenticate':'Basic'})

    app = FastAPI(title='Meetgegevens bij biggen', version='1.0',
                  docs_url=None, redoc_url=None, openapi_url=None,
                  dependencies=[Depends(aanmelden)])

    @contextmanager
    def lezen():
        if not pad.is_file():
            raise HTTPException(503, 'Verzameldatabase ontbreekt. Rond notebook 05 af.')
        db = None
        try:
            db = sqlite3.connect(pad.as_uri()+'?mode=ro', uri=True, timeout=5)
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA query_only=ON')
            db.execute('BEGIN')
            yield db
        except sqlite3.Error:
            raise HTTPException(503, 'Database tijdelijk niet leesbaar. Controleer de ontvanger en probeer opnieuw.') from None
        finally:
            if db is not None: db.close()

    @app.middleware('http')
    async def geen_cache(request: Request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/gezondheid')
    def gezondheid():
        return {'status':'bereikbaar', 'dienst':'practicum', 'api_versie':1}

    @app.get('/openapi.json', include_in_schema=False)
    def documentatie():
        return JSONResponse(app.openapi())

    @app.get('/metadata')
    def metadata():
        """Aantallen en inhoudsvingerafdrukken voor één vaste bovengrens."""
        with lezen() as db:
            grens = db.execute('SELECT COALESCE(MAX(rowid),0) FROM metingen').fetchone()[0]
            bronnen = {}
            for bron in ('asserva', 'schauer'):
                h = hashlib.sha256(); aantal = 0
                for r in db.execute('SELECT record_id,inhoud_sha256 FROM metingen WHERE bron=? AND rowid<=? ORDER BY record_id',(bron,grens)):
                    h.update(f'{r[0]}:{r[1]}\n'.encode()); aantal += 1
                bronnen[bron] = {'aantal':aantal, 'sha256':h.hexdigest()}
            hokken = [r[0] for r in db.execute('SELECT DISTINCT hok FROM metingen WHERE rowid<=? ORDER BY hok',(grens,))]
        return {'api_versie':1, 'grens':grens, 'bronnen':bronnen, 'hokken':hokken,
                'eenheden':{'gewichten':'kg','voederopname':'g'},
                'datumveld':'bronrecord.DATE', 'tijdzone':'onbevestigd; vermoedelijk Europe/Brussels',
                'selectie':'Alle ontvangen bronrecords, inclusief kwaliteitsvlaggen.',
                'paginering':'Volg volgende_na met dezelfde grens en filters. Volgorde is opslagvolgorde, niet meettijd.'}

    @app.get('/metingen')
    def metingen(
        request: Request,
        meettype: Literal['gewichten','voederopname'] | None = None,
        hok: Annotated[str | None, Query(max_length=100)] = None,
        dier_id: Annotated[str | None, Query(max_length=100)] = None,
        vanaf: date | None = None, tot: date | None = None,
        limiet: Annotated[int, Query(ge=1,le=1000)] = 20,
        na: Annotated[int, Query(ge=0,le=9223372036854775807)] = 0,
        grens: Annotated[int | None, Query(ge=0,le=9223372036854775807)] = None,
    ):
        """Lees een pagina. Vanaf is inclusief, tot exclusief, op bronkalenderdatum."""
        toegelaten = {'meettype','hok','dier_id','vanaf','tot','limiet','na','grens'}
        if set(request.query_params)-toegelaten:
            raise HTTPException(422, 'Onbekende parameter. Raadpleeg de API-documentatie.')
        if any(len(request.query_params.getlist(k))>1 for k in request.query_params):
            raise HTTPException(422, 'Gebruik iedere parameter hoogstens één keer.')
        if vanaf is not None and tot is not None and vanaf >= tot:
            raise HTTPException(422, 'Vanaf moet vóór tot liggen.')
        with lezen() as db:
            maximum = db.execute('SELECT COALESCE(MAX(rowid),0) FROM metingen').fetchone()[0]
            if grens is None: grens = maximum
            if grens > maximum:
                raise HTTPException(409, 'De database is veranderd of vervangen. Begin opnieuw bij metadata.')
            voorwaarden = ['rowid>?','rowid<=?']; waarden = [na,grens]
            for kolom, waarde, op in [('meettype',meettype,'='),('hok',hok,'='),('dier_id',dier_id,'='),
                                      ('datum',vanaf.isoformat() if vanaf else None,'>='),
                                      ('datum',tot.isoformat() if tot else None,'<')]:
                if waarde is not None:
                    voorwaarden.append(f'{kolom}{op}?'); waarden.append(waarde)
            rijen = db.execute('SELECT rowid,inhoud_json FROM metingen WHERE '+
                               ' AND '.join(voorwaarden)+' ORDER BY rowid LIMIT ?',waarden+[limiet+1]).fetchall()
            pagina = rijen[:limiet]
            volgende = pagina[-1]['rowid'] if len(rijen)>limiet else None
        return {'api_versie':1, 'grens':grens, 'aantal':len(pagina), 'volgende_na':volgende,
                'metingen':[json.loads(r['inhoud_json']) for r in pagina]}

    return app
