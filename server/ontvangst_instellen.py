"""Bewaar de MQTT-clientwachtwoorden uitsluitend in een beschermd serverbestand."""
from pathlib import Path
from getpass import getpass
import argparse
import grp
import hashlib
import ipaddress
import json
import os
import re
import tempfile


def instellen(partner=False,vervang=False,pad=Path('/etc/iot/ontvangst.geheim.json')):
    if os.geteuid()!=0: raise PermissionError('Voer deze opdracht uit met sudo op je eigen server.')
    config=json.loads(pad.read_text()) if pad.exists() else {'database':'/var/lib/iot/verzamelde_metingen.db','bronnen':[]}
    positie=1 if partner else 0
    if partner and not config['bronnen']: raise ValueError('Stel eerst de eigen stroom in.')
    if len(config['bronnen'])>positie and not vervang:
        print('Bestaande instellingen behouden. Gebruik --vervang alleen bij een bewuste wijziging.')
        return
    wie='partner' if partner else 'jezelf'
    deelnemer=input(f'Deelnemerscode van {wie}: ').strip()
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,62}',deelnemer): raise ValueError('Ongeldige deelnemerscode.')
    rol=input(f'Rol van {wie} (gewichten of voederopname): ').strip()
    if rol not in ('gewichten','voederopname'): raise ValueError('Ongeldige rol.')
    if partner and (rol==config['bronnen'][0]['rol'] or deelnemer==config['bronnen'][0]['deelnemer']):
        raise ValueError('Kies de afgesproken partner met de andere rol.')
    adres=str(ipaddress.IPv4Address(input(f'Publiek IPv4-adres van {wie}: ').strip()))
    ca=Path('/etc/iot/ca_partner.crt' if partner else '/etc/iot/ca.crt')
    fingerprint=hashlib.sha256(ca.read_bytes()).hexdigest()
    print('SHA-256 van het CA-bestand:',fingerprint)
    verwacht=input('Plak de SHA-256 die de eigenaar van deze server heeft gecontroleerd: ').strip().lower()
    if verwacht!=fingerprint: raise ValueError('Vingerafdruk verschilt. Controleer het CA-bestand via een vertrouwde route.')
    wachtwoord=getpass('MQTT-wachtwoord van lezer' + (' op de partnerbroker: ' if partner else ' op je eigen broker: '))
    if not wachtwoord: raise ValueError('Een wachtwoord is verplicht.')
    bron={'deelnemer':deelnemer,'rol':rol,'adres':adres,'ca':str(ca),'gebruiker':'lezer','wachtwoord':wachtwoord}
    if len(config['bronnen'])>positie: config['bronnen'][positie]=bron
    else: config['bronnen'].append(bron)
    if len({b['rol'] for b in config['bronnen']})!=len(config['bronnen']): raise ValueError('De rollen moeten verschillen.')
    fd,naam=tempfile.mkstemp(prefix='.ontvangst-',dir=pad.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(config,f,ensure_ascii=False,indent=2); f.write('\n')
        os.chown(naam,0,grp.getgrnam('iot').gr_gid); os.chmod(naam,0o640)
        os.replace(naam,pad)
    finally:
        if Path(naam).exists(): Path(naam).unlink()
    print('Instellingen opgeslagen. Alleen root en servicegroep iot kunnen het bestand lezen.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--partner',action='store_true'); p.add_argument('--vervang',action='store_true')
    args=p.parse_args(); instellen(args.partner,args.vervang)
