"""Maak de vierweekse lesdatabanken; behoud alle rijen en kwaliteitsvlaggen.

Gebruik: python hulpmiddelen/maak_startdatabanken.py --gewichten BRON.csv
    --voederopname BRON.csv --uitvoer gegevens/origineel
De bronnen en bestaande uitvoer worden nooit overschreven.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import sqlite3
from contextlib import closing

BEGIN = '2023-08-24'
EIND = '2023-09-21'
BRONNEN = {
    'gewichten': ('asserva.db', 'VBW', 80028, 132222),
    'voederopname': ('schauer.db', 'VFI', 146649, 233601),
}
GETALLEN = {'VBW', 'VFI', 'VD', 'VFIS', 'PROCESSTIME', 'TRIALDAY', 'DTMARKER', 'DTMARKER_INT'}


def maak(bron, doel, rol):
    naam, meetveld, verwacht, totaal = BRONNEN[rol]
    if doel.exists():
        raise FileExistsError(f'Bestaand bestand behouden: {doel}')
    bronhash = hashlib.sha256(bron.read_bytes()).hexdigest()
    with bron.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        velden = reader.fieldnames
        assert velden and meetveld in velden and 'ROW_ID' in velden
        regels = list(reader)
    assert len(regels) == totaal, 'Onverwacht aantal bronrecords; inspecteer de bron opnieuw.'
    assert len({r['ROW_ID'] for r in regels}) == totaal, 'Dubbele bronidentificatie.'
    basis = [r for r in regels if BEGIN <= r['DATE'] < EIND]
    later = [r for r in regels if EIND <= r['DATE'] <= '2023-10-05']
    assert len(basis) == verwacht and len(basis) + len(later) == totaal
    assert not ({r['ROW_ID'] for r in basis} & {r['ROW_ID'] for r in later})
    doel.parent.mkdir(parents=True, exist_ok=True)
    types = {v: 'REAL' if v in GETALLEN else 'TEXT' for v in velden}
    kolommen = ', '.join(f'"{v}" {types[v]}' + (' PRIMARY KEY NOT NULL' if v == 'ROW_ID' else '') for v in velden)
    with closing(sqlite3.connect(doel)) as db, db:
        db.execute(f'CREATE TABLE metingen ({kolommen})')
        rows = [tuple(float(r[v]) if v in GETALLEN and r[v] != '' else (None if v in GETALLEN else r[v]) for v in velden) for r in basis]
        db.executemany('INSERT INTO metingen VALUES (' + ','.join('?' for _ in velden) + ')', rows)
        db.execute('CREATE TABLE metadata (eigenschap TEXT PRIMARY KEY NOT NULL, waarde TEXT NOT NULL)')
        info = {'rol': rol, 'bronbestand': bron.name, 'bron_sha256': bronhash,
                'basis_vanaf': BEGIN, 'basis_tot_exclusief': EIND, 'aantal_basisrecords': str(len(basis)),
                'aantal_gereserveerde_records': str(len(later)), 'meetveld': meetveld,
                'eenheid': 'kg' if rol == 'gewichten' else 'g',
                'tijdzone': 'vermoedelijk Belgische lokale tijd; geen offset in bron; niet omgerekend',
                'selectie': 'DATE; alle kwaliteitsvlaggen en alle dieren behouden',
                'schema': 'onderwijsmodel versie 1; oorspronkelijke kolomnamen behouden'}
        db.executemany('INSERT INTO metadata VALUES (?,?)', info.items())
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        opgeslagen = dict((r[0], r[1:]) for r in db.execute('SELECT * FROM metingen'))
        assert all(opgeslagen[r[0]] == r[1:] for r in rows)
    return {'bestand': naam, 'rol': rol, 'basisrecords': len(basis), 'gereserveerde_records': len(later),
            'bron_sha256': bronhash, 'database_sha256': hashlib.sha256(doel.read_bytes()).hexdigest(),
            'kolommen': types}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gewichten', type=Path, required=True)
    parser.add_argument('--voederopname', type=Path, required=True)
    parser.add_argument('--uitvoer', type=Path, required=True)
    args = parser.parse_args()
    for rol, (naam, *_) in BRONNEN.items():
        if (args.uitvoer / naam).exists():
            raise FileExistsError(f'Bestaande uitvoer behouden: {naam}')
    verslag = [maak(getattr(args, rol), args.uitvoer / BRONNEN[rol][0], rol) for rol in BRONNEN]
    (args.uitvoer / 'maakcontrole.json').write_text(json.dumps(verslag, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(verslag, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
