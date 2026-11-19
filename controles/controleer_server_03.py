"""Integratieproef uitsluitend in een lege Debian-testcontainer, nooit op een lesserver."""
from pathlib import Path
import sys, subprocess, shutil, secrets, socket, time, json, ssl
from threading import Event

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'server'),str(ROOT/'programmatuur')]
from certificaat_maken import maak_certificaat
from toegang_api import controlewaarde, geldig
from servercontrole import controleer
import requests
import paho.mqtt.client as mqtt

def run(*args,**kwargs):
    return subprocess.run(args,check=True,capture_output=True,text=True,**kwargs)

def wacht_poort(poort):
    einde=time.monotonic()+15
    while time.monotonic()<einde:
        try:
            with socket.create_connection(('127.0.0.1',poort),timeout=0.3): return
        except OSError: time.sleep(0.1)
    raise TimeoutError(f'Dienst op poort {poort} start niet.')

def mqtt_poging(naam,wachtwoord,topic):
    verbonden,klaar=Event(),Event()
    resultaat={}
    c=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,protocol=mqtt.MQTTv5)
    c.username_pw_set(naam,wachtwoord)
    c.tls_set(ca_certs='/etc/iot/certificaten/ca.crt')
    def connect(c,u,f,r,p): resultaat['connect']=r.value; verbonden.set()
    def publish(c,u,mid,r,p): resultaat['publish']=r.value; klaar.set()
    c.on_connect=connect; c.on_publish=publish
    try:
        c.connect('127.0.0.1',8883); c.loop_start()
        assert verbonden.wait(10),'Geen CONNACK'
        if resultaat['connect']==0:
            c.publish(topic,'controle',qos=1)
            assert klaar.wait(10),'Geen PUBACK'
        return resultaat
    finally: c.disconnect(); c.loop_stop()

def main():
    if not Path('/.dockerenv').exists() or Path('/etc/iot').exists():
        raise SystemExit('Deze proef vereist een NIEUWE, lege Docker-testcontainer.')
    run('useradd','--system','--user-group','--home-dir','/var/lib/iot','--create-home','--shell','/usr/sbin/nologin','iot')
    run(sys.executable,str(ROOT/'controles/test_serverinstellingen.py'))
    maak_certificaat('/etc/iot/certificaten','127.0.0.1','proef')
    Path('/opt/iot/programmatuur').mkdir(parents=True)
    for name in ('statusdienst.py','toegang_api.py'):
        shutil.copyfile(ROOT/'server'/name,Path('/opt/iot/programmatuur')/name)
    eigenaar,lezer,api=[secrets.token_urlsafe(24) for _ in range(3)]
    waarde=controlewaarde(api)
    assert geldig(api,waarde) and not geldig('verkeerd',waarde)
    Path('/etc/iot/api.controlewaarde').write_text(waarde+'\n')
    run('chown','root:iot','/etc/iot/api.controlewaarde')
    run('chmod','640','/etc/iot/api.controlewaarde')
    run('chmod','755','/etc/iot')
    for naam,w in [('eigenaar',eigenaar),('lezer',lezer)]:
        # Alleen tijdelijke willekeurige testwachtwoorden; nooit echte inloggegevens.
        args=['mosquitto_passwd','-b']
        if naam=='eigenaar': args+=['-c']
        run(*args,'/etc/mosquitto/practicum.wachtwoorden',naam,w)
    Path('/etc/mosquitto/practicum.rechten').write_text('user eigenaar\ntopic readwrite practicum/proef/#\n\nuser lezer\ntopic read practicum/proef/metingen/#\ntopic read practicum/proef/controle/#\n')
    for f in ('practicum.wachtwoorden','practicum.rechten'):
        run('chown','root:mosquitto','/etc/mosquitto/'+f); run('chmod','640','/etc/mosquitto/'+f)
    for f in ('server.key','server.crt'):
        shutil.copyfile('/etc/iot/certificaten/'+f,'/etc/mosquitto/certs/'+f)
        run('chown','root:mosquitto','/etc/mosquitto/certs/'+f); run('chmod','640','/etc/mosquitto/certs/'+f)
    shutil.copyfile(ROOT/'server/configuratie/mosquitto.conf','/etc/mosquitto/conf.d/practicum.conf')
    shutil.copyfile(ROOT/'server/configuratie/nginx.conf','/etc/nginx/sites-enabled/practicum')
    Path('/etc/nginx/sites-enabled/default').unlink()
    run('nginx','-t')
    shutil.copyfile(ROOT/'server/diensten/iot-status.service','/etc/systemd/system/iot-status.service')
    run('systemd-analyze','verify','/etc/systemd/system/iot-status.service')
    log=Path('/tmp/server03.log').open('w')
    processen=[]
    try:
        for args in (['mosquitto','-c','/etc/mosquitto/mosquitto.conf'],['runuser','-u','iot','--','/opt/iot/venv/bin/uvicorn','statusdienst:app','--host','127.0.0.1','--port','8000','--no-access-log'],['nginx','-g','daemon off;']):
            processen.append(subprocess.Popen(args,cwd='/opt/iot/programmatuur',stdout=log,stderr=log))
        for port in (8883,8000,443): wacht_poort(port)
        ca=Path('/etc/iot/certificaten/ca.crt')
        result=controleer('127.0.0.1','proef',ca,eigenaar,api)
        assert all(v=='geslaagd' for v in result.values())
        print('GESLAAGD: MQTT heen-en-terug en HTTPS met certificaatcontrole.')
        assert requests.get('https://127.0.0.1/gezondheid',verify=str(ca),timeout=5).status_code==401
        assert requests.get('https://127.0.0.1/gezondheid',auth=('eigenaar','verkeerd'),verify=str(ca),timeout=5).status_code==401
        try:
            requests.get('https://127.0.0.1/gezondheid',timeout=5)
            raise AssertionError('Onbekende CA werd aanvaard')
        except requests.exceptions.SSLError: pass
        context=ssl.create_default_context(cafile=str(ca))
        try:
            with socket.create_connection(('127.0.0.1',8883),timeout=5) as sock:
                context.wrap_socket(sock,server_hostname='127.0.0.2')
            raise AssertionError('Verkeerd IP werd aanvaard')
        except ssl.SSLCertVerificationError: pass
        assert mqtt_poging('eigenaar','verkeerd','practicum/proef/controle/test')['connect']!=0
        assert mqtt_poging('lezer',lezer,'practicum/proef/metingen/test')['publish']>=128
        assert mqtt_poging('eigenaar',eigenaar,'practicum/ander/metingen/test')['publish']>=128
        gereed,ontvangen=Event(),Event()
        topic='practicum/proef/controle/leestest'
        leesclient=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,protocol=mqtt.MQTTv5)
        leesclient.username_pw_set('lezer',lezer)
        leesclient.tls_set(ca_certs=str(ca))
        def aanmelden(c,u,f,r,p):
            if not r.is_failure: c.subscribe(topic,qos=1)
        def abonnement(c,u,mid,redenen,p):
            if not any(r.is_failure for r in redenen): gereed.set()
        def ontvangen_bericht(c,u,m):
            if m.topic==topic and m.payload==b'controle': ontvangen.set()
        leesclient.on_connect=aanmelden
        leesclient.on_subscribe=abonnement
        leesclient.on_message=ontvangen_bericht
        try:
            leesclient.connect('127.0.0.1',8883); leesclient.loop_start()
            assert gereed.wait(10),'Lezerabonnement niet bevestigd'
            assert mqtt_poging('eigenaar',eigenaar,topic)['publish']<128
            assert ontvangen.wait(10),'Lezer ontving het toegestane bericht niet'
        finally: leesclient.disconnect(); leesclient.loop_stop()
        print('GESLAAGD: verkeerde wachtwoorden, onbekende CA, verkeerd IP en verboden publicaties geweigerd.')
        print('GESLAAGD: afzonderlijk lezersaccount ontvangt een toegestaan bericht.')
        # Procesherstart; een echte systemd-/Dropletherstart wordt afzonderlijk getest.
        processen[0].terminate(); processen[0].wait(timeout=10)
        processen[0]=subprocess.Popen(['mosquitto','-c','/etc/mosquitto/mosquitto.conf'],stdout=log,stderr=log)
        wacht_poort(8883)
        controleer('127.0.0.1','proef',ca,eigenaar,api)
        print('GESLAAGD: verbinding na brokerprocesherstart.')
        # Voer notebookcellen tegen dezelfde echte diensten uit met tijdelijke invoer.
        if (ROOT/'docent/notebooks/03_eigen_server_inrichten.ipynb').exists():
            import nbformat
            from nbclient import NotebookClient
            werk=Path('/tmp/notebook03'); werk.mkdir()
            run('git','init','-q','-b','student/proef',str(werk))
            shutil.copytree(ROOT/'programmatuur',werk/'programmatuur')
            (werk/'gegevens/inlevering').mkdir(parents=True)
            (werk/'gegevens/werk').mkdir()
            (werk/'gegevens/inlevering/01_werkplekcontrole.json').write_text(json.dumps({'branch':'student/proef','deelnemerscode':'proef','rol':'gewichten','bronbestand':'asserva.db'}))
            (werk/'gegevens/werk/server.json').write_text(json.dumps({'ipv4':'127.0.0.1','deelnemerscode':'proef'}))
            shutil.copyfile(ca,werk/'gegevens/werk/ca.crt')
            nb=nbformat.read(ROOT/'docent/notebooks/03_eigen_server_inrichten.ipynb',as_version=4)
            # Geheime fixture bestaat uitsluitend in RAM; verwijder voor het bewaren.
            fixture=nbformat.v4.new_code_cell('_testinvoer=iter('+repr([eigenaar,api])+')\nget_ipython().kernel.getpass=lambda *a, **k: next(_testinvoer)')
            nb.cells.insert(0,fixture)
            NotebookClient(nb,timeout=60,kernel_name='python3',resources={'metadata':{'path':str(werk)}}).execute()
            nb.cells.pop(0)
            opgeslagen=json.loads((werk/'gegevens/inlevering/03_servercontrole.json').read_text())
            assert opgeslagen['deelnemerscode']=='proef'
            assert all(v=='geslaagd' for v in opgeslagen['verbindingen'].values())
            for c in nb.cells:
                if c.cell_type=='code' and c.execution_count: c.execution_count-=1
            out=ROOT/'gegevens/werk/controle03'; out.mkdir(parents=True,exist_ok=True)
            nbformat.write(nb,out/'03_uitgevoerd.ipynb')
            assert eigenaar not in (out/'03_uitgevoerd.ipynb').read_text() and api not in (out/'03_uitgevoerd.ipynb').read_text()
            print('GESLAAGD: volledige notebookuitvoering met echte kernel en tijdelijke lokale diensten.')
    finally:
        for p in processen:
            p.terminate()
            try: p.wait(timeout=10)
            except subprocess.TimeoutExpired: p.kill(); p.wait()
        log.close()

if __name__=='__main__': main()
