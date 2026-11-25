"""Volledige basisdata, echte HTTPS en uitvoering van notebook 06 voor beide rollen.

Alleen uitvoeren in een wegwerpcontainer. Richt daarin uitsluitend lokale testdiensten in.
"""
from pathlib import Path
from contextlib import closing
import hashlib, json, os, shutil, sqlite3, subprocess, sys, time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'server'),str(ROOT/'programmatuur')]
if not Path('/.dockerenv').exists():
    raise SystemExit('Deze proef mag uitsluitend in een wegwerpcontainer draaien.')
from publiceren import lees_metingen
from meetgegevens import open_opslag, verwerk, canoniek, overzicht
from toegang_api import controlewaarde
from certificaat_maken import maak_certificaat
from api_ophalen import ApiClient


def run(*args,**kw):
    return subprocess.run(args,check=True,text=True,**kw)


def voorbereiden():
    run('useradd','--system','--home','/var/lib/iot','iot')
    run('install','-d','-o','iot','-g','iot','/var/lib/iot')
    Path('/etc/iot').mkdir(exist_ok=True)
    Path('/opt/iot/programmatuur').mkdir(parents=True,exist_ok=True)
    for naam in ('webdienst.py','toegang_api.py'):
        shutil.copyfile(ROOT/'server'/naam,Path('/opt/iot/programmatuur')/naam)
    # Het testwachtwoord is lokaal gegenereerd, niet een echte accountcredential.
    import secrets
    wachtwoord=secrets.token_urlsafe(30)
    key=Path('/etc/iot/api.controlewaarde'); key.write_text(controlewaarde(wachtwoord))
    run('chown','root:iot',str(key)); key.chmod(0o640)
    maak_certificaat('/etc/iot/certificaten','127.0.0.1','proef06')
    pad=Path('/var/lib/iot/verzamelde_metingen.db')
    db=open_opslag(pad)
    for rol,naam in [('gewichten','asserva.db'),('voederopname','schauer.db')]:
        werk=Path('/tmp')/naam; shutil.copyfile(ROOT/'gegevens/origineel'/naam,werk)
        with closing(sqlite3.connect(werk)) as bron,bron:
            bron.execute('CREATE TABLE hokken(hok TEXT PRIMARY KEY NOT NULL,gebouw TEXT,afdeling INTEGER,oppervlakte_m2 REAL)')
            bron.executemany('INSERT INTO hokken VALUES(?,?,?,?)',[(str(i),'M5',1,8) for i in range(1,11)])
        aantal=0
        for b in lees_metingen(werk,rol,'proef',None):
            if verwerk(db,canoniek(b),f'practicum/proef/metingen/{rol}','proef',rol)!='nieuw':
                raise AssertionError('Onverwachte bronvalidatie')
            aantal+=1
            if aantal%25000==0:
                db.commit(); print(rol,aantal,flush=True)
        db.commit(); print(rol,aantal,'klaar',flush=True)
    db.close()
    run('chown','-R','iot:iot','/var/lib/iot')
    verwacht=overzicht(pad)['bronnen']
    assert verwacht['asserva']['aantal']==80028 and verwacht['schauer']['aantal']==146649
    # SQLite moet ook na het sluiten van de schrijver uitsluitend kunnen lezen.
    run('chmod','555','/var/lib/iot')
    cold=run('runuser','-u','iot','--','/opt/iot/venv/bin/python','-c',
             "import sqlite3; d=sqlite3.connect('file:/var/lib/iot/verzamelde_metingen.db?mode=ro',uri=True); print(d.execute('select count(*) from metingen').fetchone())",capture_output=True)
    print('Read-only cold start:',cold.stdout,flush=True)
    run('chmod','755','/var/lib/iot')
    shutil.copyfile(ROOT/'server/configuratie/nginx.conf','/etc/nginx/sites-available/practicum')
    default=Path('/etc/nginx/sites-enabled/default')
    if default.exists(): default.unlink()
    Path('/etc/nginx/sites-enabled/practicum').symlink_to('/etc/nginx/sites-available/practicum')
    run('nginx','-t'); run('nginx')
    log=open('/tmp/api06.log','w')
    proc=subprocess.Popen(['runuser','-u','iot','--','/opt/iot/venv/bin/uvicorn','webdienst:maak_app','--factory','--host','127.0.0.1','--port','8000','--no-access-log'],cwd='/opt/iot/programmatuur',stdout=log,stderr=log)
    for _ in range(100):
        if proc.poll() is not None: raise RuntimeError(Path('/tmp/api06.log').read_text())
        try:
            test=ApiClient('https://127.0.0.1','/etc/iot/certificaten/ca.crt',wachtwoord)
            if test.antwoord('/gezondheid').status_code==200: break
        except Exception: pass
        time.sleep(.1)
    assert test.ophalen('/metadata')['bronnen']==verwacht
    test.sluiten()
    return proc,wachtwoord,verwacht


def notebooks(wachtwoord,verwacht):
    import nbformat
    from nbclient import NotebookClient
    # De studentomgeving staat alleen in deze wegwerpcontainer.
    run('git','init','-b','student/proefdocent',str(ROOT),capture_output=True)
    (ROOT/'gegevens/werk').mkdir(exist_ok=True)
    (ROOT/'gegevens/inlevering').mkdir(exist_ok=True)
    shutil.copyfile('/etc/iot/certificaten/ca.crt',ROOT/'gegevens/werk/ca.crt')
    (ROOT/'gegevens/werk/server.json').write_text(json.dumps({'ipv4':'127.0.0.1','deelnemerscode':'proefdocent'}))
    resultaten={}
    for rol in ('gewichten','voederopname'):
        for naam,inhoud in [('01_werkplekcontrole',{'deelnemerscode':'proefdocent','rol':rol,'branch':'student/proefdocent'}),
                            ('05_ontvangstcontrole',{'deelnemerscode':'proefdocent','branch':'student/proefdocent','volledigheid':'geslaagd','bronnen':verwacht})]:
            (ROOT/f'gegevens/inlevering/{naam}.json').write_text(json.dumps(inhoud))
        analyse=ROOT/'gegevens/werk/analyse_06.db'
        if analyse.exists(): analyse.rename(ROOT/f'gegevens/werk/analyse_{rol}_vorig.db')
        nb=nbformat.read(ROOT/'docent/notebooks/06_gegevens_opvragen_via_een_api.ipynb',4)
        for c in nb.cells:
            if c.cell_type=='code' and c.id=='gezondheid':
                # Alleen de interactieve invoer wordt vervangen, de HTTPS-aanvraag blijft echt.
                c.source=c.source.replace('getpass("API-Droplet wachtwoord: ")',repr(wachtwoord))
        client=NotebookClient(nb,timeout=600,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}})
        client.execute()
        for c in nb.cells:
            if c.cell_type=='code' and c.id=='gezondheid':
                c.source=c.source.replace(repr(wachtwoord),'getpass("API-Droplet wachtwoord: ")')
        verslag=json.loads((ROOT/'gegevens/inlevering/06_apicontrole.json').read_text())
        assert verslag['herhaalde_import']['nieuw']==0 and verslag['eerste_import']['nieuw']==226677
        assert verslag['inhoud_gelijk_aan_05']
        resultaten[rol]=verslag
        out=ROOT/'uitvoer06';out.mkdir(exist_ok=True)
        nbformat.write(nb,out/f'06_uitgevoerd_{rol}.ipynb')
        print('Notebook volledig uitgevoerd:',rol,flush=True)
    (ROOT/'uitvoer06/ketenresultaat.json').write_text(json.dumps(resultaten,indent=2))


if __name__=='__main__':
    proc,wachtwoord,verwacht=voorbereiden()
    try: notebooks(wachtwoord,verwacht)
    finally: proc.terminate(); proc.wait(timeout=10)
