"""Maak een eigen oefen-CA en een servercertificaat voor een vast IPv4-adres."""
from pathlib import Path
import ipaddress
import json
import re
import subprocess
import argparse
import os


def controleer_invoer(adres, code):
    try:
        adres = str(ipaddress.IPv4Address(adres))
    except ipaddress.AddressValueError as exc:
        raise ValueError('Gebruik uitsluitend het IPv4-adres van je server.') from exc
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,62}', code):
        raise ValueError('Gebruik je deelnemerscode uit notebook 01.')
    return adres, code


def maak_certificaat(map, adres, code):
    adres, code = controleer_invoer(adres, code)
    map = Path(map)
    instellingen = {'ipv4': adres, 'deelnemerscode': code}
    if map.exists():
        pad = map / 'instellingen.json'
        if not pad.exists() or json.loads(pad.read_text()) != instellingen:
            raise FileExistsError('Bestaande certificaatmap behouden. Controleer adres en deelnemerscode; vervang geen certificaten zonder herstelplan.')
        for name in ('ca.crt', 'ca.key', 'server.crt', 'server.key'):
            if not (map / name).is_file():
                raise FileExistsError('Onvolledige certificaatmap. Bewaar deze en vraag hulp voordat je opnieuw begint.')
        subprocess.run(['openssl','x509','-in',str(map/'server.crt'),'-checkend','86400','-noout'],check=True,capture_output=True)
        print('Bestaande geldige certificaten behouden.')
        return
    map.mkdir(mode=0o700, parents=True)
    old = os.umask(0o077)
    def uitvoeren(*args):
        subprocess.run(['openssl',*args],cwd=map,check=True,capture_output=True)
    try:
        uitvoeren('req','-x509','-newkey','rsa:3072','-noenc','-keyout','ca.key','-out','ca.crt','-days','365','-subj',f'/CN=Practicum {code} CA','-addext','basicConstraints=critical,CA:TRUE,pathlen:0','-addext','keyUsage=critical,keyCertSign,cRLSign')
        uitvoeren('req','-new','-newkey','rsa:3072','-noenc','-keyout','server.key','-out','server.csr','-subj',f'/CN={adres}')
        (map/'uitbreidingen.cnf').write_text(f'basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName=IP:{adres}\n')
        uitvoeren('x509','-req','-in','server.csr','-CA','ca.crt','-CAkey','ca.key','-CAcreateserial','-out','server.crt','-days','90','-sha256','-extfile','uitbreidingen.cnf')
        uitvoeren('verify','-CAfile','ca.crt','-verify_ip',adres,'server.crt')
        (map/'instellingen.json').write_text(json.dumps(instellingen,indent=2)+'\n')
    finally:
        os.umask(old)
    print('Certificaten gemaakt: servercertificaat 90 dagen geldig; privésleutels blijven op de server.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--adres',required=True)
    p.add_argument('--deelnemer',required=True)
    p.add_argument('--map',type=Path,default=Path('/etc/iot/certificaten'))
    a=p.parse_args()
    maak_certificaat(a.map,a.adres,a.deelnemer)
