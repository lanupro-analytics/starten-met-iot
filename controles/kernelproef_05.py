"""Voer notebook 05 uit met echte lokale diensten en gecontroleerde handmatige pauzes."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,time
import nbformat
from nbclient import NotebookClient
from meetgegevens import overzicht


def kernelproef(root,tmp,partijen,manifest,publiceer,start_ontvanger):
    from controleer_keten_05 import wacht,stop
    for index,p in enumerate(partijen):
        partner=partijen[1-index]
        werk=tmp/('codespace-'+p['code']); (werk/'gegevens/werk').mkdir(parents=True)
        (werk/'gegevens/inlevering').mkdir(); (werk/'docent/notebooks').mkdir(parents=True)
        shutil.copytree(root/'programmatuur',werk/'programmatuur')
        shutil.copytree(root/'server',werk/'server')
        subprocess.run(['git','init','-q','-b','student/'+p['code'],str(werk)],check=True)
        shutil.copyfile(p['bron'],werk/'gegevens/werk'/p['bron'].name)
        shutil.copyfile(p['ca'],werk/'gegevens/werk/ca.crt')
        shutil.copyfile(partner['ca'],werk/'gegevens/werk/ca_partner.crt')
        (werk/'gegevens/inlevering/01_werkplekcontrole.json').write_text(json.dumps({'deelnemerscode':p['code'],'branch':'student/'+p['code'],'rol':p['rol'],'bronbestand':p['bron'].name}))
        (werk/'gegevens/werk/server.json').write_text(json.dumps({'deelnemerscode':p['code'],'ipv4':'127.0.0.1'}))
        (werk/'gegevens/werk/partner.json').write_text(json.dumps({'deelnemerscode':partner['code'],'rol':partner['rol'],'ipv4':'127.0.0.1'}))
        partnerbron='schauer' if p['rol']=='gewichten' else 'asserva'
        (werk/'gegevens/werk/partner_broncontrole.json').write_text(json.dumps({'deelnemerscode':partner['code'],'rol':partner['rol'],'bronnen':{partnerbron:manifest[partnerbron]}}))
        nb=nbformat.read(root/'docent/notebooks/05_metingen_ontvangen_en_opslaan.ipynb',4)
        plaats=next(i+1 for i,c in enumerate(nb.cells) if c.id=='werkplek')
        setup=nbformat.v4.new_code_cell('''import os
from functools import partial
getpass = lambda prompt="": os.environ["MQTT_PROEFWACHTWOORD"]
input = lambda prompt="": os.environ["PARTNER_CA_HASH"]
MqttSessie = partial(MqttSessie, poort=int(os.environ["MQTT_PROEFPOORT"]))''')
        nb.cells.insert(plaats,setup)
        def momentopname(bestand):
            s=overzicht(p['map']/'verzameld.db')
            (werk/'gegevens/werk'/bestand).write_text(json.dumps(s))
        def handmatige_stap(cell,cell_index,**kwargs):
            if cell.id=='eigen-controle':
                wacht(lambda: all(v['toestand']=='gereed' for v in overzicht(p['map']/'verzameld.db')['verbindingen']))
                momentopname('05_eigen_ontvangst.json')
            if cell.id=='volledige-controle':
                wacht(lambda: overzicht(p['map']/'verzameld.db')['bronnen']==manifest,timeout=120)
                momentopname('05_ontvangstcontrole.json')
            if cell.id=='herhaling-controle':
                voor=json.loads((werk/'gegevens/werk/05_ontvangstcontrole.json').read_text())
                v=next(x for x in voor['verbindingen'] if x['deelnemer']==p['code'])
                def klaar():
                    na=overzicht(p['map']/'verzameld.db'); n=next(x for x in na['verbindingen'] if x['deelnemer']==p['code'])
                    return n['dubbel']>=v['dubbel']+20 and n['ongeldig']>=v['ongeldig']+1
                wacht(klaar); momentopname('05_na_herhaling.json')
            if cell.id=='herstel-controle':
                start_ontvanger(p)
                stop(p['broker'])
                wacht(lambda: any(v['deelnemer']==p['code'] and v['toestand']!='gereed' for v in overzicht(partner['map']/'verzameld.db')['verbindingen']))
                p['broker']=subprocess.Popen(['mosquitto','-c',str(p['map']/'mosquitto.conf')],stdout=p['log'],stderr=p['log'])
                for q in partijen:
                    wacht(lambda: all(v['toestand']=='gereed' for v in overzicht(q['map']/'verzameld.db')['verbindingen']))
                momentopname('05_na_herstel.json')
        omgeving=dict(os.environ,MQTT_PROEFWACHTWOORD=p['eigenaar'],MQTT_PROEFPOORT=str(p['poort']),PARTNER_CA_HASH=hashlib.sha256(partner['ca'].read_bytes()).hexdigest())
        NotebookClient(nb,timeout=1200,kernel_name='python3',on_cell_start=handmatige_stap,resources={'metadata':{'path':str(werk/'docent/notebooks')}}).execute(env=omgeving)
        nb.cells.pop(plaats)
        for c in nb.cells[plaats:]:
            if c.cell_type=='code' and c.execution_count: c.execution_count-=1
        verslag=json.loads((werk/'gegevens/inlevering/05_ontvangstcontrole.json').read_text())
        assert verslag['volledigheid']=='geslaagd' and verslag['bronnen']==manifest
        assert verslag['ongeldig_bericht_afgewezen'] and verslag['herhaling_zonder_extra_metingen']
        assert hashlib.sha256((werk/'gegevens/werk'/p['bron'].name).read_bytes()).hexdigest()==p['hash']
        uit=Path(os.environ.get('UITVOER_05',str(tmp/'uitvoer'))); uit.mkdir(parents=True,exist_ok=True)
        pad=uit/(p['rol']+'.ipynb'); nbformat.write(nb,pad)
        for q in partijen: assert q['eigenaar'] not in pad.read_text() and q['lezer'] not in pad.read_text()
        print('GESLAAGD: volledige notebookkernel voor',p['rol'],'met echte MQTT-ontvangst en serveroverzichten.',flush=True)
