"""Geïsoleerde MQTT/TLS- en kernelproef. Alleen in een wegwerp-Dockercontainer.

Gebruik de image van controles/server_03.Dockerfile. Geen toegang tot lesservers.
De test maakt uitsluitend tijdelijke accounts, certificaten en werkkopieën.
"""
from contextlib import closing
from pathlib import Path
import hashlib
import json
import os
import secrets
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'programmatuur'), str(ROOT/'server')]
from publiceren import MqttSessie, lees_metingen, meettopic, json_tekst, publiceer_selectie
from certificaat_maken import maak_certificaat


def verwacht(fout, functie):
    try:
        functie()
    except fout:
        return
    raise AssertionError('Verwachte fout ontbreekt: ' + fout.__name__)


def hokken_toevoegen(pad):
    with closing(sqlite3.connect(pad)) as db, db:
        db.execute('CREATE TABLE hokken(hok TEXT NOT NULL PRIMARY KEY, gebouw TEXT, afdeling INTEGER, oppervlakte_m2 REAL)')
        db.executemany('INSERT INTO hokken VALUES(?,?,?,?)', [(str(i),'M5',1,8.0) for i in range(1,11)])


def main():
    if not Path('/.dockerenv').exists():
        raise SystemExit('Gebruik een wegwerp-Dockercontainer. Deze proef is niet voor een lesserver.')
    import nbformat
    from nbclient import NotebookClient
    with tempfile.TemporaryDirectory(prefix='mqtt04-') as tmp:
        tmp = Path(tmp)
        certificaten = tmp/'certificaten'
        maak_certificaat(certificaten,'127.0.0.1','proef')
        eigenaar, lezer = secrets.token_urlsafe(24), secrets.token_urlsafe(24)
        wachtwoorden = tmp/'wachtwoorden'
        for naam, w in [('eigenaar',eigenaar),('lezer',lezer)]:
            args = ['mosquitto_passwd','-b'] + (['-c'] if naam=='eigenaar' else [])
            subprocess.run(args+[str(wachtwoorden),naam,w],check=True,capture_output=True)
        (tmp/'rechten').write_text('user eigenaar\ntopic readwrite practicum/proef/#\nuser lezer\ntopic read practicum/proef/metingen/#\ntopic read practicum/proef/controle/#\n')
        configuratie = (ROOT/'server/configuratie/mosquitto.conf').read_text()
        configuratie = configuratie.replace('0.0.0.0','127.0.0.1').replace('/etc/mosquitto/practicum.wachtwoorden',str(wachtwoorden)).replace('/etc/mosquitto/practicum.rechten',str(tmp/'rechten')).replace('/etc/mosquitto/certs/',str(certificaten)+'/')
        (tmp/'mosquitto.conf').write_text('user root\n'+configuratie)
        # root is uitsluitend voor deze wegwerpcontainer met tijdelijke bestanden.
        log = (tmp/'broker.log').open('w')
        broker = subprocess.Popen(['mosquitto','-c',str(tmp/'mosquitto.conf')],stdout=log,stderr=log)
        try:
            einde = time.monotonic()+10
            while True:
                try:
                    with socket.create_connection(('127.0.0.1',8883),timeout=.2): break
                except OSError:
                    if time.monotonic()>einde: raise TimeoutError('Testbroker start niet.')
                    time.sleep(.05)
            ca = certificaten/'ca.crt'
            def sessie(**kwargs):
                return MqttSessie('127.0.0.1',ca,eigenaar,**kwargs)
            verwacht(ConnectionError,lambda: MqttSessie('127.0.0.1',ca,'verkeerd',timeout=2).__enter__())
            with MqttSessie('127.0.0.1',ca,lezer,gebruiker='lezer') as c:
                verwacht(PermissionError,lambda: c.verstuur('practicum/proef/metingen/gewichten',{'test':1}))
            with sessie() as c:
                verwacht(PermissionError,lambda: c.verstuur('practicum/ander/metingen/gewichten',{'test':1}))
                verwacht(ValueError,lambda: c.verstuur('practicum/proef/#',{'test':1}))
            verwacht(ValueError,lambda: json_tekst({'waarde':float('nan')}))
            verwacht(ValueError,lambda: json_tekst({'waarde':'x'*60001}))
            import ssl
            with socket.create_connection(('127.0.0.1',8883),timeout=2) as sock:
                context=ssl.create_default_context(cafile=str(ca))
                verwacht(ssl.SSLCertVerificationError,lambda: context.wrap_socket(sock,server_hostname='127.0.0.2'))
            with socket.create_connection(('127.0.0.1',8883),timeout=2) as sock:
                verwacht(ssl.SSLCertVerificationError,lambda: ssl.create_default_context().wrap_socket(sock,server_hostname='127.0.0.1'))
            print('GESLAAGD: TLS, onbekende CA, verkeerd adres, accountrechten en strikte JSON.',flush=True)
            for rol,naam,veld,aantal in [('gewichten','asserva.db','VBW',80028),('voederopname','schauer.db','VFI',146649)]:
                werk = tmp/rol
                (werk/'gegevens/werk').mkdir(parents=True)
                (werk/'gegevens/inlevering').mkdir()
                (werk/'docent/notebooks').mkdir(parents=True)
                shutil.copytree(ROOT/'programmatuur',werk/'programmatuur')
                bron = werk/'gegevens/werk'/naam
                shutil.copyfile(ROOT/'gegevens/origineel'/naam,bron)
                hokken_toevoegen(bron)
                hash_voor = hashlib.sha256(bron.read_bytes()).hexdigest()
                records = list(lees_metingen(bron,rol,'proef',20))
                assert len(records)==20 and all(r['meetveld']==veld for r in records)
                assert all(r['record_id']==r['bronrecord']['ROW_ID'] for r in records)
                assert all(r['waarde']==r['bronrecord'][veld] for r in records)
                assert len({(r['bron'],r['record_id']) for r in records})==20
                # Controleer omzetting van ieder basisrecord, niet alleen de eerste twintig.
                assert sum(1 for _ in lees_metingen(bron,rol,'proef',None))==aantal
                verwacht(ValueError,lambda: list(lees_metingen(bron,'voederopname' if rol=='gewichten' else 'gewichten','proef',1)))
                topic = meettopic('proef',rol)
                administratie = tmp/(rol+'_publicaties.db')
                with sessie(abonnement='practicum/proef/metingen/+') as kijker, sessie() as zender:
                    resultaat = publiceer_selectie(zender,topic,records,administratie)
                    assert resultaat=={'geselecteerd':20,'bevestigd':20,'overgeslagen':0}
                    ontvangen=[kijker.lees()['payload'] for _ in records]
                    assert ontvangen==records
                    assert publiceer_selectie(zender,topic,records,administratie)['bevestigd']==0
                    assert publiceer_selectie(zender,topic,records,administratie,opnieuw=True)['bevestigd']==20
                    assert [kijker.lees()['payload'] for _ in records]==records
                    gewijzigd=dict(records[0],waarde=999)
                    verwacht(ValueError,lambda: publiceer_selectie(zender,topic,[gewijzigd],administratie))
                # Een nieuw proces/sessie herkent de opgeslagen administratie.
                with sessie() as zender:
                    assert publiceer_selectie(zender,topic,records,administratie)['overgeslagen']==20
                    grotere_selectie=list(lees_metingen(bron,rol,'proef',21))
                    assert publiceer_selectie(zender,topic,grotere_selectie,administratie)=={'geselecteerd':21,'bevestigd':1,'overgeslagen':20}
                # Een mislukte verzending wordt niet als bevestigd opgeslagen.
                class Uitval:
                    bestemming='testuitval:8883'
                    def verstuur(self,*args): raise TimeoutError('Gesimuleerde uitval')
                verwacht(TimeoutError,lambda: publiceer_selectie(Uitval(),topic,records,administratie))
                with closing(sqlite3.connect(administratie)) as db:
                    assert db.execute("SELECT COUNT(*) FROM publicaties WHERE bestemming='testuitval:8883'").fetchone()[0]==0
                subprocess.run(['git','init','-q','-b','student/proef',str(werk)],check=True)
                (werk/'gegevens/inlevering/01_werkplekcontrole.json').write_text(json.dumps({'deelnemerscode':'proef','branch':'student/proef','rol':rol,'bronbestand':naam}))
                (werk/'gegevens/werk/server.json').write_text(json.dumps({'deelnemerscode':'proef','ipv4':'127.0.0.1'}))
                shutil.copyfile(ca,werk/'gegevens/werk/ca.crt')
                nbpad=ROOT/'docent/notebooks/04_metingen_publiceren_met_mqtt.ipynb'
                for ronde in range(2):
                    nb=nbformat.read(nbpad,as_version=4)
                    nbformat.validate(nb)
                    setup=nbformat.v4.new_code_cell('import os\ngetpass = lambda prompt="": os.environ["MQTT_PROEFWACHTWOORD"]')
                    invoegpunt=next(i+1 for i,c in enumerate(nb.cells) if c.id=='werkplek')
                    nb.cells.insert(invoegpunt,setup)
                    omgeving=dict(os.environ,MQTT_PROEFWACHTWOORD=eigenaar)
                    NotebookClient(nb,timeout=60,kernel_name='python3',resources={'metadata':{'path':str(werk/'docent/notebooks')}}).execute(env=omgeving)
                    nb.cells.pop(invoegpunt)
                    for c in nb.cells[invoegpunt:]:
                        if c.cell_type=='code' and c.execution_count: c.execution_count-=1
                    resultaat=json.loads((werk/'gegevens/inlevering/04_publicatiecontrole.json').read_text())
                    assert resultaat['rol']==rol and resultaat['herpublicatie']['bevestigd']==20
                    assert resultaat['nieuwe_records']['bevestigd']==(20 if ronde==0 else 0)
                    assert resultaat['herhaling']['bevestigd']==0
                    assert hashlib.sha256(bron.read_bytes()).hexdigest()==hash_voor
                    uitvoer=Path(os.environ.get('UITVOER_04',str(tmp/'uitvoer')))
                    uitvoer.mkdir(exist_ok=True,parents=True)
                    doel=uitvoer/(rol+('_hervat' if ronde else '')+'.ipynb')
                    nbformat.write(nb,doel)
                    assert eigenaar not in doel.read_text() and lezer not in doel.read_text()
                print(f'GESLAAGD: {rol}, {aantal} records omgezet, 20 TLS-publicaties en volledige kerneluitvoering plus hervatten.',flush=True)
            print('Alle controles voor notebook 04 geslaagd.',flush=True)
        finally:
            broker.terminate()
            try: broker.wait(timeout=5)
            except subprocess.TimeoutExpired: broker.kill(); broker.wait()
            log.close()


if __name__=='__main__': main()
