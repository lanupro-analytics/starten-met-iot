"""Achtergrondontvanger met twee onafhankelijke MQTT/TLS-abonnementen."""
from pathlib import Path
from queue import Queue,Empty,Full
from threading import Event
import argparse
import json
import logging
import signal
import ssl
import ipaddress
import re

import paho.mqtt.client as mqtt
from meetgegevens import open_opslag,verwerk,nu,ROLLEN

LOG=logging.getLogger('ontvangst')


def lees_instellingen(pad):
    config=json.loads(Path(pad).read_text(encoding='utf-8'))
    bronnen=config['bronnen']
    if not isinstance(bronnen,list) or not 1<=len(bronnen)<=2: raise ValueError('Gebruik een eigen bron en eventueel één partnerbron.')
    gezien=set()
    for b in bronnen:
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,62}',b['deelnemer']) or b['rol'] not in ROLLEN: raise ValueError('Ongeldige deelnemer of rol.')
        ipaddress.IPv4Address(b['adres'])
        if b['gebruiker'] not in ('eigenaar','lezer') or not b['wachtwoord']: raise ValueError('Controleer het MQTT-account.')
        if not Path(b['ca']).is_file(): raise ValueError('CA-bestand ontbreekt.')
        if b['rol'] in gezien: raise ValueError('Kies één bron per rol.')
        gezien.add(b['rol'])
    return config


def draaien(config,stop=None):
    stop=stop or Event(); wachtrij=Queue(maxsize=1000); fataal=Event(); clients=[]
    db=open_opslag(config['database'])
    with db:
        # Alleen actieve verbindingen resetten. Meetrecords blijven behouden.
        db.execute("UPDATE verbindingen SET toestand='niet_ingesteld'")
        for b in config['bronnen']:
            db.execute("INSERT INTO verbindingen(deelnemer,rol,toestand,bijgewerkt_op) VALUES(?,?,'verbinden',?) ON CONFLICT(deelnemer,rol) DO UPDATE SET toestand='verbinden',bijgewerkt_op=excluded.bijgewerkt_op",(b['deelnemer'],b['rol'],nu()))
    def gebeurtenis(item):
        try: wachtrij.put(item,timeout=5)
        except Full: fataal.set(); LOG.error('Wachtrij vol. Herpubliceer na herstel.')
    def maak_client(b):
        topic=f"practicum/{b['deelnemer']}/metingen/{b['rol']}"
        c=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,protocol=mqtt.MQTTv5,manual_ack=True)
        c.username_pw_set(b['gebruiker'],b['wachtwoord'])
        context=ssl.create_default_context(cafile=b['ca']); context.minimum_version=ssl.TLSVersion.TLSv1_2
        c.tls_set_context(context); c.connect_timeout=10; c.reconnect_delay_set(1,30)
        def verbonden(c,u,f,rc,p):
            if rc.is_failure:
                gebeurtenis(('staat',b,'aanmelding_geweigerd')); LOG.warning('Aanmelding geweigerd: %s',b['deelnemer'])
            else:
                gebeurtenis(('staat',b,'abonneren')); c.subscribe(topic,qos=1)
        def geabonneerd(c,u,mid,rc,p):
            status='geweigerd' if any(r.is_failure for r in rc) else 'gereed'
            gebeurtenis(('staat',b,status))
            LOG.info('ABONNEMENT %s: %s %s',status.upper(),b['deelnemer'],b['rol'])
        def verbroken(c,u,f,rc,p): gebeurtenis(('staat',b,'verbroken'))
        def mislukt(c,u): gebeurtenis(('staat',b,'onbereikbaar'))
        def bericht(c,u,m): gebeurtenis(('bericht',b,c,m))
        c.on_connect=verbonden; c.on_subscribe=geabonneerd; c.on_disconnect=verbroken
        c.on_connect_fail=mislukt; c.on_message=bericht
        c.connect_async(b['adres'],b.get('poort',8883),keepalive=30)
        return c
    try:
        for b in config['bronnen']:
            c=maak_client(b); clients.append(c); c.loop_start()
        while not stop.is_set():
            if fataal.is_set(): raise RuntimeError('Ontvangst onderbroken. Herpubliceer na herstel.')
            batch=[]
            try: batch.append(wachtrij.get(timeout=1))
            except Empty: pass
            while len(batch)<100:
                try: batch.append(wachtrij.get_nowait())
                except Empty: break
            acknowledgements=[]
            with db:
                for item in batch:
                    soort,b=item[:2]
                    if soort=='staat':
                        db.execute('UPDATE verbindingen SET toestand=?,bijgewerkt_op=? WHERE deelnemer=? AND rol=?',(item[2],nu(),b['deelnemer'],b['rol']))
                    else:
                        _,_,c,m=item
                        resultaat=verwerk(db,m.payload,m.topic,b['deelnemer'],b['rol'])
                        if resultaat in ('ongeldig','conflict'): LOG.warning('Bericht %s: %s %s',resultaat,b['deelnemer'],b['rol'])
                        acknowledgements.append((c,m.mid,m.qos))
                db.execute('INSERT INTO ontvanger VALUES(1,?) ON CONFLICT(id) DO UPDATE SET bijgewerkt_op=excluded.bijgewerkt_op',(nu(),))
            for c,mid,qos in acknowledgements: c.ack(mid,qos)
    finally:
        for c in clients: c.disconnect()
        for c in clients: c.loop_stop(); c.username_pw_set(None)
        with db:
            db.execute("UPDATE verbindingen SET toestand='gestopt' WHERE toestand!='niet_ingesteld'")
        db.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instellingen',default='/etc/iot/ontvangst.geheim.json')
    args=parser.parse_args()
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    stop=Event()
    signal.signal(signal.SIGTERM,lambda *_:stop.set()); signal.signal(signal.SIGINT,lambda *_:stop.set())
    draaien(lees_instellingen(args.instellingen),stop)
