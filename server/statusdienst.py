"""Kleine beveiligde bereikbaarheidstest; de meetgegevens-API volgt in notebook 06."""
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from toegang_api import geldig

app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
beveiliging=HTTPBasic()
controlewaarde=Path('/etc/iot/api.controlewaarde').read_text().strip()

@app.get('/gezondheid')
def gezondheid(inlog: HTTPBasicCredentials=Depends(beveiliging)):
    wachtwoord_ok=geldig(inlog.password,controlewaarde)
    if not wachtwoord_ok or inlog.username!='eigenaar':
        raise HTTPException(status_code=401,detail='Ongeldige aanmelding',headers={'WWW-Authenticate':'Basic'})
    return {'status':'bereikbaar','dienst':'practicum'}
