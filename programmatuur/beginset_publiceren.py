"""Bewuste herpublicatie in begrensde groepen, zonder de administratie uit 04."""
from itertools import islice
import paho.mqtt.client as mqtt
from publiceren import json_tekst,meettopic


def publiceer_beginset(sessie,topic,berichten,voortgang=print):
    totaal=0
    iterator=iter(berichten)
    while True:
        groep=list(islice(iterator,100))
        if not groep: break
        teksten=[]
        for b in groep:
            if topic!=meettopic(b['deelnemer'],b['meettype']): raise ValueError('Topic en bron komen niet overeen.')
            teksten.append(json_tekst(b))
        # De bestaande sessie bewaakt CONNACK, TLS en MQTT-5-PUBACK-redenen.
        publicaties=[]
        for tekst in teksten:
            p=sessie.client.publish(topic,tekst,qos=1,retain=False)
            if p.rc!=mqtt.MQTT_ERR_SUCCESS: raise ConnectionError('Publicatie onderbroken. Herpubliceer na herstel.')
            publicaties.append(p)
        for p in publicaties:
            p.wait_for_publish(timeout=sessie.timeout)
            if not p.is_published(): raise TimeoutError('Geen brokerbevestiging. Herpubliceer na herstel.')
            with sessie.slot: geweigerd=sessie.bevestigingen.pop(p.mid,True)
            if geweigerd: raise PermissionError('Publicatie geweigerd. Controleer MQTT-topicrechten.')
        totaal+=len(groep)
        if voortgang and totaal%5000==0: voortgang(f'{totaal} publicaties door de broker bevestigd')
    if voortgang: voortgang(f'Gereed: {totaal} publicaties bevestigd. Controleer nu de opslag op beide servers.')
    return totaal
