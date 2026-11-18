"""Geïsoleerde proef met twee brokers, twee ontvangers en volledige beginsets."""
from pathlib import Path
from contextlib import closing
import copy,hashlib,json,os,secrets,shutil,socket,sqlite3,subprocess,sys,tempfile,time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'server'),str(ROOT/'programmatuur')]
from certificaat_maken import maak_certificaat
from meetgegevens import overzicht,selectie_manifest,canoniek
from publiceren import MqttSessie,lees_metingen,meettopic
from beginset_publiceren import publiceer_beginset


def wacht(voorwaarde,timeout=60):
    einde=time.monotonic()+timeout
    while time.monotonic()<einde:
        try:
            if voorwaarde(): return
        except (FileNotFoundError,sqlite3.Error,KeyError): pass
        time.sleep(.1)
    raise TimeoutError('Verwachte toestand bleef uit.')


def stop(p):
    if p.poll() is None:
        p.terminate()
        try: p.wait(timeout=10)
        except subprocess.TimeoutExpired: p.kill(); p.wait()


def main():
    if not Path('/.dockerenv').exists(): raise SystemExit('Gebruik uitsluitend een wegwerpcontainer.')
    subprocess.run([sys.executable,str(ROOT/'controles/test_ontvangst_05.py')],check=True)
    with tempfile.TemporaryDirectory(prefix='keten05-') as tmp:
        tmp=Path(tmp); processen=[]; partijen=[]
        try:
            for i,(code,rol,naam,aantal) in enumerate([('alice','gewichten','asserva.db',80028),('bob','voederopname','schauer.db',146649)]):
                map=tmp/code; map.mkdir()
                maak_certificaat(map/'cert','127.0.0.1',code)
                eigenaar,lezer=secrets.token_urlsafe(20),secrets.token_urlsafe(20)
                for user,pw in [('eigenaar',eigenaar),('lezer',lezer)]:
                    subprocess.run(['mosquitto_passwd','-b']+(['-c'] if user=='eigenaar' else [])+[str(map/'wachtwoorden'),user,pw],check=True,capture_output=True)
                (map/'rechten').write_text(f'user eigenaar\ntopic readwrite practicum/{code}/#\nuser lezer\ntopic read practicum/{code}/metingen/#\n')
                conf=(ROOT/'server/configuratie/mosquitto.conf').read_text().replace('8883 0.0.0.0',f'{8883+i} 127.0.0.1').replace('/etc/mosquitto/practicum.wachtwoorden',str(map/'wachtwoorden')).replace('/etc/mosquitto/practicum.rechten',str(map/'rechten')).replace('/etc/mosquitto/certs/',str(map/'cert')+'/')
                (map/'mosquitto.conf').write_text('user root\n'+conf+'\n'+(ROOT/'server/configuratie/ontvangst-capaciteit.conf').read_text())
                log=(map/'broker.log').open('w')
                broker=subprocess.Popen(['mosquitto','-c',str(map/'mosquitto.conf')],stdout=log,stderr=log); processen.append(broker)
                bron=map/naam; shutil.copyfile(ROOT/'gegevens/origineel'/naam,bron)
                with closing(sqlite3.connect(bron)) as db,db:
                    db.execute('CREATE TABLE hokken(hok TEXT NOT NULL PRIMARY KEY,gebouw TEXT,afdeling INTEGER,oppervlakte_m2 REAL)')
                    db.executemany('INSERT INTO hokken VALUES(?,?,?,?)',[(str(j),'M5',1,8.0) for j in range(1,11)])
                partij={'code':code,'rol':rol,'map':map,'bron':bron,'aantal':aantal,'poort':8883+i,'ca':map/'cert/ca.crt','eigenaar':eigenaar,'lezer':lezer,'broker':broker,'log':log}
                partij['hash']=hashlib.sha256(bron.read_bytes()).hexdigest()
                partij['configbron']={'deelnemer':code,'rol':rol,'adres':'127.0.0.1','poort':8883+i,'ca':str(partij['ca']),'gebruiker':'lezer','wachtwoord':lezer}
                partijen.append(partij)
            def start_ontvanger(p,eigen=False):
                config={'database':str(p['map']/'verzameld.db'),'bronnen':[p['configbron']] if eigen else [q['configbron'] for q in partijen]}
                (p['map']/'instellingen.json').write_text(json.dumps(config))
                if 'ontvanger' in p: stop(p['ontvanger'])
                log=(p['map']/'ontvanger.log').open('a')
                p['ontvanger']=subprocess.Popen([sys.executable,str(ROOT/'server/ontvangen.py'),'--instellingen',str(p['map']/'instellingen.json')],stdout=log,stderr=log)
                processen.append(p['ontvanger'])
                wacht(lambda: len([v for v in overzicht(p['map']/'verzameld.db')['verbindingen'] if v['toestand']=='gereed'])==(1 if eigen else 2))
            def publiceer(p,limiet,voortgang=None):
                with MqttSessie('127.0.0.1',p['ca'],p['eigenaar'],poort=p['poort']) as sessie:
                    return publiceer_beginset(sessie,meettopic(p['code'],p['rol']),lees_metingen(p['bron'],p['rol'],p['code'],limiet),voortgang)
            for p in partijen:
                start_ontvanger(p,eigen=True); assert publiceer(p,20)==20
                wacht(lambda: sum(v['aantal'] for v in overzicht(p['map']/'verzameld.db')['bronnen'].values())==20)
            print('GESLAAGD: beide partijen ontvangen eerst alleen hun eigen 20 records.',flush=True)
            for p in partijen: start_ontvanger(p)
            for p in partijen: publiceer(p,20)
            for p in partijen:
                wacht(lambda: sum(v['aantal'] for v in overzicht(p['map']/'verzameld.db')['bronnen'].values())==40)
            # Ongeldige JSON en een geldig maar conflicterend record stoppen geen ontvanger.
            p=partijen[0]; b=next(lees_metingen(p['bron'],p['rol'],p['code'],1))
            f=copy.deepcopy(b); f['waarde']=999; f['bronrecord']['VBW']=999
            with MqttSessie('127.0.0.1',p['ca'],p['eigenaar'],poort=p['poort']) as sessie:
                sessie.client.publish(meettopic(p['code'],p['rol']),b'{fout',qos=1).wait_for_publish(10)
                sessie.verstuur(meettopic(p['code'],p['rol']),f)
            for p in partijen:
                wacht(lambda: any(v['conflict']>=1 and v['ongeldig']>=1 for v in overzicht(p['map']/'verzameld.db')['verbindingen']))
            # Beide volledige beginsets via TLS, naar twee afzonderlijke SQLite-bestanden.
            manifest={}; start=time.monotonic()
            for p in partijen:
                manifest.update(selectie_manifest(lees_metingen(p['bron'],p['rol'],p['code'],None)))
                assert publiceer(p,None,lambda melding: print(p['code'],melding,flush=True))==p['aantal']
            for p in partijen: wacht(lambda: overzicht(p['map']/'verzameld.db')['bronnen']==manifest,timeout=180)
            duur=round(time.monotonic()-start,2)
            print('GESLAAGD: 226677 records, beide verzameldatabanken inhoudelijk identiek aan de bronnen. Seconden:',duur,flush=True)
            # Ontvanger herstart, daarna broker herstart: beide abonnementen herstellen.
            for p in partijen: start_ontvanger(p)
            p=partijen[0]; stop(p['broker'])
            wacht(lambda: any(v['deelnemer']==p['code'] and v['toestand']!='gereed' for v in overzicht(partijen[1]['map']/'verzameld.db')['verbindingen']))
            p['broker']=subprocess.Popen(['mosquitto','-c',str(p['map']/'mosquitto.conf')],stdout=p['log'],stderr=p['log']); processen.append(p['broker'])
            for q in partijen: wacht(lambda: all(v['toestand']=='gereed' for v in overzicht(q['map']/'verzameld.db')['verbindingen']))
            for p in partijen: publiceer(p,20)
            for p in partijen:
                wacht(lambda: overzicht(p['map']/'verzameld.db')['bronnen']==manifest)
                assert hashlib.sha256(p['bron'].read_bytes()).hexdigest()==p['hash']
            print('GESLAAGD: herstart, opnieuw abonneren en herpublicatie zonder extra metingen.',flush=True)
            # Kerneluitvoering is optioneel beschikbaar zodra de notebook is toegevoegd.
            nbpad=ROOT/'docent/notebooks/05_metingen_ontvangen_en_opslaan.ipynb'
            if nbpad.exists():
                from kernelproef_05 import kernelproef
                kernelproef(ROOT,tmp,partijen,manifest,publiceer,start_ontvanger)
            uit=Path(os.environ.get('UITVOER_05',str(tmp/'uitvoer'))); uit.mkdir(parents=True,exist_ok=True)
            (uit/'testverslag.json').write_text(json.dumps({'alle_controles':'geslaagd','totaal_per_server':226677,'volledige_overdracht_seconden':duur,'manifest':manifest},indent=2))
        finally:
            for p in partijen:
                if 'broker' in p: stop(p['broker'])
                if 'ontvanger' in p: stop(p['ontvanger'])
            for p in reversed(processen): stop(p)

if __name__=='__main__': main()
