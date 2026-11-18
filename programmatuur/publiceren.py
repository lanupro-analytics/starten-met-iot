"""JSON-records en expliciete MQTT-publicatie voor notebook 04.

Een brokerbevestiging is geen bewijs van opslag door een ontvanger.
De lokale verzendadministratie dient alleen om toevoegingen te selecteren.
"""
from contextlib import closing
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty, Full
from threading import Event, Lock
import hashlib
import ipaddress
import json
import re
import sqlite3
import ssl

import paho.mqtt.client as mqtt

ROLLEN = {'gewichten': ('asserva', 'VBW', 'kg'),
          'voederopname': ('schauer', 'VFI', 'g')}


def deelnemerscode(waarde):
    if not isinstance(waarde, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,62}', waarde):
        raise ValueError('Gebruik de deelnemerscode uit notebook 01.')
    return waarde


def meettopic(deelnemer, rol):
    if rol not in ROLLEN:
        raise ValueError('Onbekende rol.')
    return f'practicum/{deelnemerscode(deelnemer)}/metingen/{rol}'


def json_tekst(bericht):
    """Strikte JSON: NaN en Infinity mogen niet ongemerkt over de verbinding."""
    tekst = json.dumps(bericht, ensure_ascii=False, sort_keys=True, allow_nan=False,
                       separators=(',', ':'))
    if len(tekst.encode('utf-8')) > 60000:
        raise ValueError('Het bericht overschrijdt de ingestelde brokerlimiet.')
    return tekst


def lees_metingen(pad, rol, deelnemer, limiet=20):
    """Lees een geordende selectie, of met limiet=None alle records, uitsluitend lezen."""
    deelnemerscode(deelnemer)
    if rol not in ROLLEN:
        raise ValueError('Onbekende rol.')
    if limiet is not None and (type(limiet) is not int or limiet < 1):
        raise ValueError('Gebruik een positief geheel aantal of None voor alle records.')
    pad = Path(pad).resolve()
    if not pad.is_file():
        raise FileNotFoundError('Werkdatabase ontbreekt. Rond notebook 02 af.')
    bron, meetveld, eenheid = ROLLEN[rol]
    with closing(sqlite3.connect(pad.as_uri() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        meta = dict(db.execute('SELECT eigenschap, waarde FROM metadata'))
        if meta.get('rol') != rol or meta.get('eenheid') != eenheid:
            raise ValueError('Rol of eenheid wijkt af van de toegewezen databank.')
        kolommen = {r['name'] for r in db.execute('PRAGMA table_info(metingen)')}
        vereist = {'ROW_ID', 'EID', 'PEN', 'DATE', 'TIMESTAMPstart', 'TIMESTAMPstop', meetveld}
        if not vereist <= kolommen:
            raise ValueError('Vereiste meetkolommen ontbreken: ' + ', '.join(sorted(vereist-kolommen)))
        hokken = {r['hok']: dict(r) for r in db.execute('SELECT hok, gebouw, afdeling, oppervlakte_m2 FROM hokken')}
        query = 'SELECT * FROM metingen ORDER BY DATE, ROW_ID'
        parameters = ()
        if limiet is not None:
            query += ' LIMIT ?'
            parameters = (limiet,)
        for rij in db.execute(query, parameters):
            record = dict(rij)
            if not isinstance(record['ROW_ID'], str) or not re.fullmatch(r'\d{27,28}', record['ROW_ID']):
                raise ValueError('ROW_ID moet een ongewijzigde tekstcode van 27 of 28 cijfers zijn.')
            if record['PEN'] not in hokken:
                raise ValueError('Hokmetadata ontbreken. Controleer de tabel hokken uit notebook 02.')
            # Het compacte Asserva-formaat en Schauer-datumtijdtekst hebben geen UTC-offset.
            formaat = '%Y%m%d%H%M%S' if rol == 'gewichten' else '%Y-%m-%d %H:%M:%S'
            tijden = {}
            for veld, sleutel in [('TIMESTAMPstart', 'start'), ('TIMESTAMPstop', 'einde')]:
                waarde = record[veld]
                tijden[sleutel] = None if waarde is None else datetime.strptime(str(waarde), formaat).isoformat()
            bericht = {'schema_versie': 1, 'deelnemer': deelnemer, 'bron': bron,
                       'meettype': rol, 'record_id': record['ROW_ID'], 'dier_id': record['EID'],
                       'hok': record['PEN'], 'tijd': tijden,
                       'tijdzone': 'onbevestigd; vermoedelijk Europe/Brussels',
                       'meetveld': meetveld, 'waarde': record[meetveld], 'eenheid': eenheid,
                       'hokmetadata': hokken[record['PEN']], 'bronrecord': record}
            json_tekst(bericht)
            yield bericht


class MqttSessie:
    """Begrensde TLS-sessie. Wacht op CONNACK, SUBACK en een succesvolle PUBACK."""
    def __init__(self, adres, ca, wachtwoord, abonnement=None, gebruiker='eigenaar', poort=8883, timeout=12):
        self.adres = str(ipaddress.IPv4Address(adres))
        self.poort, self.timeout = poort, timeout
        self.abonnement = abonnement
        self.gereed, self.slot = Event(), Lock()
        self.fout = None
        self.bevestigingen = {}
        self.ontvangen = Queue(maxsize=1000)
        context = ssl.create_default_context(cafile=str(ca))
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5,
                                  reconnect_on_failure=False)
        self.client.connect_timeout = timeout
        self.client.username_pw_set(gebruiker, wachtwoord)
        self.client.tls_set_context(context)
        self.client.on_connect = self._verbonden
        self.client.on_subscribe = self._geabonneerd
        self.client.on_publish = self._bevestigd
        self.client.on_message = self._ontvangen

    @property
    def bestemming(self):
        return f'{self.adres}:{self.poort}'

    def _verbonden(self, client, userdata, flags, reden, eigenschappen):
        if reden.is_failure:
            self.fout = 'MQTT-aanmelding geweigerd. Controleer account en MQTT-wachtwoord.'
            self.gereed.set()
        elif self.abonnement:
            resultaat, _ = client.subscribe(self.abonnement, qos=1)
            if resultaat != mqtt.MQTT_ERR_SUCCESS:
                self.fout = 'Abonnement kon niet worden aangevraagd.'
                self.gereed.set()
        else:
            self.gereed.set()

    def _geabonneerd(self, client, userdata, mid, redenen, eigenschappen):
        if any(r.is_failure for r in redenen):
            self.fout = 'MQTT-abonnement geweigerd. Controleer topicrechten.'
        self.gereed.set()

    def _bevestigd(self, client, userdata, mid, reden, eigenschappen):
        with self.slot:
            self.bevestigingen[mid] = reden.is_failure

    def _ontvangen(self, client, userdata, bericht):
        try:
            self.ontvangen.put_nowait((bericht.topic, bericht.payload))
        except Full:
            self.fout = 'De kijkbuffer is vol. Gebruik een kleinere selectie en start opnieuw.'

    def __enter__(self):
        try:
            self.client.connect(self.adres, self.poort, keepalive=30)
            self.client.loop_start()
            if not self.gereed.wait(self.timeout):
                raise TimeoutError('Geen verbindings- of abonnementsbevestiging. Controleer broker en poort 8883.')
            if self.fout:
                raise ConnectionError(self.fout)
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *args):
        self.client.disconnect()
        self.client.loop_stop()
        self.client.username_pw_set(None)

    def verstuur(self, topic, bericht):
        if not topic or any(x in topic for x in ['+', '#', '\x00']):
            raise ValueError('Publiceer op een concreet topic zonder + of #.')
        if self.fout:
            raise ConnectionError(self.fout)
        info = self.client.publish(topic, json_tekst(bericht), qos=1, retain=False)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise ConnectionError('Bericht niet aangeboden. Herstel de verbinding en probeer opnieuw.')
        info.wait_for_publish(timeout=self.timeout)
        if not info.is_published():
            raise TimeoutError('Geen brokerbevestiging. De publicatie kan wel aangekomen zijn. Herpublicatie is mogelijk.')
        with self.slot:
            geweigerd = self.bevestigingen.pop(info.mid, True)
        if geweigerd:
            raise PermissionError('De broker weigert deze publicatie. Controleer account en topicrechten.')

    def lees(self):
        if self.fout:
            raise ConnectionError(self.fout)
        try:
            topic, inhoud = self.ontvangen.get(timeout=self.timeout)
        except Empty as exc:
            raise TimeoutError('Geen bericht ontvangen op het gekozen abonnement.') from exc
        return {'topic': topic, 'payload': json.loads(inhoud)}


def publiceer_selectie(sessie, topic, berichten, administratie, opnieuw=False, voortgang=None):
    """Verstuur nieuwe records, of herpubliceer bewust de gehele aangeboden selectie.

    Een crash tussen PUBACK en commit kan een herhaling veroorzaken. Ontvangers
    moeten daarom de stabiele sleutel (bron, record_id) gebruiken, ook bij QoS 1.
    """
    administratie = Path(administratie)
    administratie.parent.mkdir(parents=True, exist_ok=True)
    telling = {'geselecteerd': 0, 'bevestigd': 0, 'overgeslagen': 0}
    with closing(sqlite3.connect(administratie, timeout=10)) as db:
        db.execute('CREATE TABLE IF NOT EXISTS publicaties (bestemming TEXT, topic TEXT, bron TEXT, record_id TEXT, inhoud_hash TEXT NOT NULL, PRIMARY KEY(bestemming,topic,bron,record_id))')
        db.commit()
        for bericht in berichten:
            if topic != meettopic(bericht['deelnemer'], bericht['meettype']):
                raise ValueError('Topic en deelnemer of meettype komen niet overeen.')
            sleutel = (sessie.bestemming, topic, bericht['bron'], bericht['record_id'])
            # Deelnemer is transportherkomst. De inhoud en bronidentiteit blijven stabiel.
            digest = hashlib.sha256(json_tekst(bericht).encode('utf-8')).hexdigest()
            bestaand = db.execute('SELECT inhoud_hash FROM publicaties WHERE bestemming=? AND topic=? AND bron=? AND record_id=?', sleutel).fetchone()
            if bestaand and bestaand[0] != digest:
                raise ValueError('Een eerder verstuurd record of zijn metadata is gewijzigd. Deze oefening deelt toevoegingen. Bewaar de bestanden en vraag hulp.')
            telling['geselecteerd'] += 1
            if bestaand and not opnieuw:
                telling['overgeslagen'] += 1
                continue
            sessie.verstuur(topic, bericht)
            with db:
                db.execute('INSERT OR IGNORE INTO publicaties VALUES(?,?,?,?,?)', (*sleutel, digest))
            telling['bevestigd'] += 1
            if voortgang and telling['bevestigd'] % 1000 == 0:
                voortgang(dict(telling))
    if voortgang:
        voortgang(dict(telling))
    return telling
