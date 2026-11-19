"""Bewaar uitsluitend een controlewaarde voor een interactief ingevoerd API-wachtwoord."""
from pathlib import Path
import getpass
import hashlib
import os
import re

def controlewaarde(wachtwoord):
    if not wachtwoord.isascii() or not 20 <= len(wachtwoord) <= 200:
        raise ValueError('Gebruik 20 tot 200 ASCII-tekens, bij voorkeur willekeurig uit je wachtwoordmanager.')
    salt=os.urandom(16).hex()
    digest=hashlib.scrypt(wachtwoord.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()
    return salt+':'+digest

def geldig(wachtwoord, opgeslagen):
    import hmac
    if not re.fullmatch(r'[0-9a-f]{32}:[0-9a-f]{128}',opgeslagen):
        raise ValueError('Ongeldige API-controlewaarde.')
    salt,verwacht=opgeslagen.split(':')
    gevonden=hashlib.scrypt(wachtwoord.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()
    return hmac.compare_digest(gevonden,verwacht)

if __name__=='__main__':
    pad=Path('/etc/iot/api.controlewaarde')
    if pad.exists():
        raise SystemExit('Bestaande API-toegang behouden. Vraag hulp als je het wachtwoord wilt wijzigen.')
    wachtwoord=getpass.getpass('Nieuw afzonderlijk API-wachtwoord (minimaal 20 tekens): ')
    if wachtwoord!=getpass.getpass('Herhaal API-wachtwoord: '):
        raise SystemExit('De invoer verschilt; niets opgeslagen.')
    waarde=controlewaarde(wachtwoord)
    old=os.umask(0o077)
    try:
        with pad.open('x') as f: f.write(waarde+'\n')
    finally: os.umask(old)
    print('Controlewaarde opgeslagen; het wachtwoord wordt niet afgedrukt.')
