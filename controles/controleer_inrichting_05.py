"""Controleer configuratierechten, servicebestand en notebookstructuur in Docker."""
from pathlib import Path
from unittest.mock import patch
import ast,grp,hashlib,json,os,stat,subprocess,sys,tempfile
import nbformat
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'server'))
from ontvangst_instellen import instellen

def main():
    if not Path('/.dockerenv').exists(): raise SystemExit('Gebruik een wegwerpcontainer.')
    try: grp.getgrnam('iot')
    except KeyError: subprocess.run(['groupadd','--system','iot'],check=True)
    map=Path('/etc/iot'); map.mkdir(exist_ok=True)
    ca=map/'ca.crt'; partner=map/'ca_partner.crt'
    if ca.exists() or partner.exists(): raise SystemExit('Gebruik een nieuwe container zonder bestaande certificaten.')
    ca.write_text('uitsluitend configuratietest'); partner.write_text('andere configuratietest')
    cfg=map/'ontvangst.geheim.json'
    if cfg.exists(): raise SystemExit('Bestaande configuratie blijft behouden.')
    with patch('builtins.input',side_effect=['alice','gewichten','127.0.0.1',hashlib.sha256(ca.read_bytes()).hexdigest()]),patch('ontvangst_instellen.getpass',return_value='tijdelijk-proefgeheim'):
        instellen()
    assert stat.S_IMODE(cfg.stat().st_mode)==0o640
    assert cfg.stat().st_uid==0 and cfg.stat().st_gid==grp.getgrnam('iot').gr_gid
    oud=cfg.read_bytes()
    with patch('builtins.input',side_effect=AssertionError('Hervatten mag niet opnieuw vragen')): instellen()
    assert oud==cfg.read_bytes()
    with patch('builtins.input',side_effect=['bob','voederopname','127.0.0.2','onjuiste-vingerafdruk']):
        try: instellen(partner=True)
        except ValueError: pass
        else: raise AssertionError('Verkeerde CA aanvaard')
    assert oud==cfg.read_bytes()
    with patch('builtins.input',side_effect=['bob','voederopname','127.0.0.2',hashlib.sha256(partner.read_bytes()).hexdigest()]),patch('ontvangst_instellen.getpass',return_value='ander-proefgeheim'):
        instellen(partner=True)
    assert len(json.loads(cfg.read_text())['bronnen'])==2
    assert stat.S_IMODE(cfg.stat().st_mode)==0o640
    nb=nbformat.read(ROOT/'docent/notebooks/05_metingen_ontvangen_en_opslaan.ipynb',4); nbformat.validate(nb)
    aantal_bash=0
    for c in nb.cells:
        if c.cell_type=='code': ast.parse(c.source)
        if '```bash' in c.source:
            assert c.source.startswith('```bash\n') and c.source.endswith('```') and c.source.count('```')==2
            subprocess.run(['bash','-n'],input=c.source[8:-3],text=True,check=True)
            aantal_bash+=1
    service=ROOT/'server/diensten/iot-ontvanger.service'
    subprocess.run(['systemd-analyze','verify',str(service)],check=True)
    print('GESLAAGD: beschermde configuratie, behoud bij hervatten en verkeerde CA, service en',aantal_bash,'losse bash-cellen.')

if __name__=='__main__': main()
