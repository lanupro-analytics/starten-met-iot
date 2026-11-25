"""Volledige aanvulling via echte TLS-MQTT en HTTPS, in een wegwerpcontainer.

De al geteste basis uit 06 wordt als fixture geladen. Nieuwe records passeren
de echte broker, twee ontvangprogramma's, API en beide notebookkernels.
"""
from pathlib import Path
from contextlib import closing
import hashlib,json,os,secrets,shutil,sqlite3,subprocess,sys,tempfile,time
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'programmatuur'),str(ROOT/'server'),str(ROOT/'controles')]
from kernelproef_07 import fixture
from meetgegevens import open_opslag,verwerk,canoniek,overzicht,selectie_manifest
from publiceren import lees_metingen,MqttSessie,meettopic
from beginset_publiceren import publiceer_beginset
from aanvulling_08 import lees_excel,voeg_toe
from certificaat_maken import maak_certificaat
from toegang_api import controlewaarde
from controleer_keten_05 import wacht,stop

def main():
    if not Path('/.dockerenv').exists():raise SystemExit('Gebruik uitsluitend een wegwerpcontainer.')
    out=ROOT/'uitvoer08';out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='iot08-') as tmp:
        tmp=Path(tmp);processen=[]
        try:
            base=tmp/'basis';manifest=fixture(base)
            opslag=tmp/'basis_server.db';db=open_opslag(opslag)
            for rol,bron in [('gewichten','asserva'),('voederopname','schauer')]:
                for b in lees_metingen(base/f'gegevens/werk/{bron}.db',rol,'proefdocent',None):
                    assert verwerk(db,canoniek(b),meettopic('proefdocent',rol),'proefdocent',rol)=='nieuw'
                db.commit()
            db.close()
            # Bereken 07 eenmaal met de echte basisdata, vóór de aanvulling.
            for naam in ('programmatuur','server'):shutil.copytree(ROOT/naam,base/naam,ignore=shutil.ignore_patterns('__pycache__'))
            subprocess.run(['git','init','-q','-b','student/proefdocent',str(base)],check=True)
            inv=base/'gegevens/inlevering';inv.mkdir()
            (inv/'01_werkplekcontrole.json').write_text(json.dumps({'deelnemerscode':'proefdocent','branch':'student/proefdocent','rol':'gewichten'}))
            (inv/'06_apicontrole.json').write_text(json.dumps({'deelnemerscode':'proefdocent','branch':'student/proefdocent','inhoud_gelijk_aan_05':True,'herhaalde_import':{'bronnen':manifest}}))
            nb=nbformat.read(ROOT/'docent/notebooks/07_voederconversie_berekenen_en_visualiseren.ipynb',4)
            NotebookClient(nb,timeout=600,kernel_name='python3',resources={'metadata':{'path':str(base)}}).execute()
            print('Basis 07 gereed',flush=True)
            controle=json.loads((ROOT/'gegevens/aanvulling/maakcontrole.json').read_text())
            partnerdir=tmp/'partner';partnerdir.mkdir();verwacht={}
            for rol,bron in [('gewichten','asserva'),('voederopname','schauer')]:
                p=partnerdir/f'{bron}.db';shutil.copyfile(base/f'gegevens/werk/{bron}.db',p)
                rows,_=lees_excel(ROOT/f'gegevens/aanvulling/{bron}_aanvullende_metingen.xlsx',controle[bron])
                assert voeg_toe(p,rows,controle[bron])['nieuw']==controle[bron]['aantal']
                verwacht.update(selectie_manifest(lees_metingen(p,rol,'proefdocent',None)))
            maak_certificaat(tmp/'cert','127.0.0.1','proef08')
            pw=secrets.token_urlsafe(30)
            subprocess.run(['mosquitto_passwd','-b','-c',str(tmp/'wachtwoorden'),'eigenaar',pw],check=True,capture_output=True)
            (tmp/'rechten').write_text('user eigenaar\ntopic readwrite practicum/#\n')
            conf=(ROOT/'server/configuratie/mosquitto.conf').read_text().replace('8883 0.0.0.0','8883 127.0.0.1').replace('/etc/mosquitto/practicum.wachtwoorden',str(tmp/'wachtwoorden')).replace('/etc/mosquitto/practicum.rechten',str(tmp/'rechten')).replace('/etc/mosquitto/certs/',str(tmp/'cert')+'/')
            (tmp/'mosquitto.conf').write_text('user root\n'+conf+'\n'+(ROOT/'server/configuratie/ontvangst-capaciteit.conf').read_text())
            log=(tmp/'diensten.log').open('w')
            processen.append(subprocess.Popen(['mosquitto','-c',str(tmp/'mosquitto.conf')],stdout=log,stderr=log))
            servers=[]
            for i in range(2):
                p=tmp/f'server{i}.db'
                with closing(sqlite3.connect(opslag)) as a,closing(sqlite3.connect(p)) as b:a.backup(b)
                config={'database':str(p),'bronnen':[{'deelnemer':'proefdocent','rol':rol,'adres':'127.0.0.1','poort':8883,'ca':str(tmp/'cert/ca.crt'),'gebruiker':'eigenaar','wachtwoord':pw} for rol in ('gewichten','voederopname')]}
                c=tmp/f'config{i}.json';c.write_text(json.dumps(config))
                processen.append(subprocess.Popen([sys.executable,str(ROOT/'server/ontvangen.py'),'--instellingen',str(c)],stdout=log,stderr=log))
                wacht(lambda:len([v for v in overzicht(p)['verbindingen'] if v['toestand']=='gereed'])==2)
                servers.append(p)
            # Eén HTTPS-testdienst per ontvanger, direct via uvicorn met TLS.
            for i,p in enumerate(servers):
                runner=tmp/f'api{i}.py'
                runner.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT/'server'))+')\nfrom webdienst import maak_app\nimport uvicorn\nuvicorn.run(maak_app('+repr(str(p))+','+repr(controlewaarde(pw))+'),host="127.0.0.1",port='+str(8443+i)+',ssl_keyfile='+repr(str(tmp/'cert/server.key'))+',ssl_certfile='+repr(str(tmp/'cert/server.crt'))+',access_log=False)')
                processen.append(subprocess.Popen([sys.executable,str(runner)],stdout=log,stderr=log))
            for index,(rol,bron) in enumerate([('gewichten','asserva'),('voederopname','schauer')]):
                werk=tmp/f'codespace{index}';shutil.copytree(base,werk,ignore=shutil.ignore_patterns('.git','__pycache__'))
                subprocess.run(['git','init','-q','-b','student/proefdocent',str(werk)],check=True)
                shutil.copytree(ROOT/'gegevens/aanvulling',werk/'gegevens/aanvulling')
                inv=werk/'gegevens/inlevering';w=werk/'gegevens/werk'
                (inv/'01_werkplekcontrole.json').write_text(json.dumps({'deelnemerscode':'proefdocent','branch':'student/proefdocent','rol':rol}))
                (w/'server.json').write_text(json.dumps({'ipv4':'127.0.0.1','deelnemerscode':'proefdocent'}))
                shutil.copyfile(tmp/'cert/ca.crt',w/'ca.crt')
                andere='schauer' if bron=='asserva' else 'asserva';andere_rol='voederopname' if rol=='gewichten' else 'gewichten'
                (w/'08_partner_broncontrole.json').write_text(json.dumps({'deelnemerscode':'partnerproef','rol':andere_rol,'bronnen':{andere:verwacht[andere]}}))
                baseline={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (inv/'beginsituatie_07').iterdir()}
                with MqttSessie('127.0.0.1',tmp/'cert/ca.crt',pw) as sessie:
                    publiceer_beginset(sessie,meettopic('proefdocent',andere_rol),(b for b in lees_metingen(partnerdir/f'{andere}.db',andere_rol,'proefdocent',None) if b['bronrecord']['DATE']>='2023-09-21'))
                nb=nbformat.read(ROOT/'docent/notebooks/08_nieuwe_gegevens_toevoegen_en_interpreteren.ipynb',4)
                plek=next(i+1 for i,c in enumerate(nb.cells) if c.id=='werkplek')
                nb.cells.insert(plek,nbformat.v4.new_code_cell('import os\ngetpass=lambda prompt="":os.environ["TEST08_PASSWORD"]\n_OrigApi=ApiClient\nApiClient=lambda url,ca,pw:_OrigApi(url+":'+str(8443+index)+'",ca,pw)'))
                def hook(cell,cell_index,**kw):
                    if cell.id=='ontvangst-controle':
                        for p in servers:wacht(lambda:overzicht(p)['bronnen']==verwacht,timeout=180)
                NotebookClient(nb,timeout=1200,kernel_name='python3',on_cell_start=hook,resources={'metadata':{'path':str(werk)}}).execute(env=dict(os.environ,TEST08_PASSWORD=pw))
                nb.cells.pop(plek)
                for c in nb.cells[plek:]:
                    if c.cell_type=='code' and c.execution_count:c.execution_count-=1
                nbformat.write(nb,out/f'08_uitgevoerd_{rol}.ipynb')
                verslag=json.loads((inv/'08_eindcontrole.json').read_text())
                assert verslag['api_import']['nieuw']==139146 and verslag['api_herhaling']['nieuw']==0
                assert verslag['basis_ongewijzigd'] and verslag['server_gelijk_aan_bronnen']
                assert verslag['bruikbare_dieren_per_interval']=={'1': 98, '2': 99, '3': 99, '4': 99, '5': 94, '6': 99, '7': 99}
                import pandas as pd
                h=pd.read_csv(inv/'resultaten_08/hokperioden.csv',dtype={'hok':str})
                assert h.loc[h.periode.eq('aanvulling'),'dieren_bruikbaar'].sum()==99
                assert abs(h.loc[h.hok.eq('4') & h.periode.eq('aanvulling'),'voederconversie'].iloc[0]-1.384690752)<.000001
                assert baseline=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (inv/'beginsituatie_07').iterdir()}
                assert pw not in (out/f'08_uitgevoerd_{rol}.ipynb').read_text()
                shutil.copytree(inv,out/rol,dirs_exist_ok=True)
                print('GESLAAGD volledige notebook08:',rol,flush=True)
            (out/'ketenresultaat.json').write_text(json.dumps({'status':'geslaagd','bronnen':verwacht,'rollen':['gewichten','voederopname'],'nieuwe_records':139146,'totaal':365823},indent=2))
        finally:
            for p in reversed(processen):stop(p)

if __name__=='__main__':main()
