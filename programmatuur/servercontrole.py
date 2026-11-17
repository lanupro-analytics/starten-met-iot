"""Begrensde verbindingstest zonder opgeslagen wachtwoorden."""
from pathlib import Path
import json
import re
import ipaddress
import secrets
import ssl
from threading import Event
import paho.mqtt.client as mqtt
import requests

def controleer(adres, deelnemer, ca, mqtt_wachtwoord, api_wachtwoord, mqtt_poort=8883, https_poort=443):
    adres=str(ipaddress.IPv4Address(adres))
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,62}',deelnemer):
        raise ValueError('Ongeldige deelnemerscode.')
    ca=Path(ca)
    if not ca.is_file():
        raise FileNotFoundError('Kopieer eerst ca.crt via de gecontroleerde SSH-verbinding.')
    context=ssl.create_default_context(cafile=str(ca))
    context.minimum_version=ssl.TLSVersion.TLSv1_2
    topic=f'practicum/{deelnemer}/controle/{secrets.token_hex(8)}'
    bericht=json.dumps({'controle':'verbinding','kenmerk':secrets.token_hex(16)})
    klaar,ontvangen=Event(),Event()
    fouten=[]
    client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,protocol=mqtt.MQTTv5)
    client.connect_timeout=10
    client.username_pw_set('eigenaar',mqtt_wachtwoord)
    client.tls_set_context(context)
    def verbonden(c,u,f,rc,p):
        if rc.is_failure:
            fouten.append('MQTT-aanmelding geweigerd. Controleer je eigen MQTT-wachtwoord.')
            klaar.set()
        else:
            c.subscribe(topic,qos=1)
    def geabonneerd(c,u,mid,redenen,p):
        if any(r.is_failure for r in redenen): fouten.append('Het MQTT-abonnement is geweigerd. Controleer de rechten.')
        klaar.set()
    def bericht_ontvangen(c,u,m):
        if m.topic==topic and m.payload.decode()==bericht: ontvangen.set()
    client.on_connect=verbonden
    client.on_subscribe=geabonneerd
    client.on_message=bericht_ontvangen
    try:
        client.connect(adres,mqtt_poort,keepalive=30)
        client.loop_start()
        if not klaar.wait(12): raise TimeoutError('Geen bevestiging van MQTT-aanmelding en abonnement ontvangen.')
        if fouten: raise ConnectionError(fouten[0])
        publicatie=client.publish(topic,bericht,qos=1,retain=False)
        publicatie.wait_for_publish(timeout=12)
        if not publicatie.is_published() or not ontvangen.wait(12):
            raise TimeoutError('Het controlebericht kwam niet terug. Controleer topicrechten en brokerlog.')
    finally:
        client.disconnect()
        client.loop_stop()
    antwoord=requests.get(f'https://{adres}:{https_poort}/gezondheid',auth=('eigenaar',api_wachtwoord),verify=str(ca),timeout=12,allow_redirects=False)
    if antwoord.status_code==401: raise PermissionError('HTTPS werkt, maar het API-wachtwoord is onjuist.')
    antwoord.raise_for_status()
    if antwoord.json()!={'status':'bereikbaar','dienst':'practicum'}:
        raise ValueError('De server geeft niet het verwachte controleantwoord.')
    return {'mqtt_tls':'geslaagd','mqtt_heen_en_terug':'geslaagd','https':'geslaagd','api_aanmelding':'geslaagd'}
