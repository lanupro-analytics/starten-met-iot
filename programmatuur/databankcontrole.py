"""Leescontroles en veilige overname van het werkbestand voor notebook 02."""
from pathlib import Path
from contextlib import closing
import hashlib
import json
import sqlite3

ROLLEN = {'gewichten': ('asserva.db', 'VBW', 80028), 'voederopname': ('schauer.db', 'VFI', 146649)}



def openen(pad):
    pad = Path(pad).resolve()
    if not pad.is_file():
        raise FileNotFoundError(f'Bestand ontbreekt: {pad.name}. Controleer de uploadmap en de bestandsnaam.')
    for suffix in ('-wal', '-shm', '-journal'):
        if Path(str(pad) + suffix).exists():
            raise ValueError('Sluit de database eerst in DB Browser en upload de gesloten database opnieuw.')
    return sqlite3.connect(pad.as_uri() + '?mode=ro', uri=True)


def inhoud_hash(db, tabel, sleutel):
    # Tabel en sleutel zijn interne vaste namen, geen invoer van gebruikers.
    digest = hashlib.sha256()
    for row in db.execute(f'SELECT * FROM "{tabel}" ORDER BY "{sleutel}"'):
        digest.update((json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n').encode())
    return digest.hexdigest()


def inspecteer(pad, rol):
    if rol not in ROLLEN:
        raise ValueError('Onbekende rol; controleer notebook 01.')
    naam, meetveld, verwacht = ROLLEN[rol]
    try:
        with closing(openen(pad)) as db:
            if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise ValueError('De databasecontrole mislukt. Upload een onbeschadigde kopie.')
            meta = dict(db.execute('SELECT eigenschap, waarde FROM metadata'))
            if meta.get('rol') != rol:
                raise ValueError(f'Verkeerde databank voor jouw rol. Gebruik {naam}.')
            schema = db.execute('PRAGMA table_info(metingen)').fetchall()
            idveld = next((r for r in schema if r[1] == 'ROW_ID'), None)
            if idveld is None or idveld[2].upper() != 'TEXT' or idveld[5] != 1 or idveld[3] != 1:
                raise ValueError('ROW_ID moet TEXT PRIMARY KEY NOT NULL zijn.')
            aantal, begin, einde = db.execute('SELECT COUNT(*), MIN(DATE), MAX(DATE) FROM metingen').fetchone()
            buiten = db.execute("SELECT COUNT(*) FROM metingen WHERE DATE IS NULL OR DATE < '2023-08-24' OR DATE >= '2023-09-21'").fetchone()[0]
            if aantal != verwacht or buiten or begin != '2023-08-24' or einde != '2023-09-20':
                raise ValueError('De startperiode of het aantal meetrecords wijkt af. Gebruik de vierweekse startdatabank.')
            if db.execute("SELECT COUNT(*) FROM metingen WHERE typeof(ROW_ID) != 'text' OR length(ROW_ID) NOT IN (27,28)").fetchone()[0]:
                raise ValueError('Een lange recordidentificatie is beschadigd.')
            return {'rol': rol, 'bestand': naam, 'meetveld': meetveld, 'aantal_metingen': aantal,
                    'eerste_datum': begin, 'laatste_datum': einde,
                    'kolommen': len(schema), 'metingen_sha256': inhoud_hash(db, 'metingen', 'ROW_ID'),
                    'metadata_sha256': inhoud_hash(db, 'metadata', 'eigenschap'),
                    'schema': schema, 'metadata': meta}
    except sqlite3.DatabaseError as exc:
        raise ValueError('Dit bestand is geen geldige lesdatabase. Gebruik het aangeleverde .db-bestand, geen CSV of SQL-tekst.') from exc


def controleer_aanvulling(origineel, kandidaat, rol):
    basis = inspecteer(origineel, rol)
    nieuw = inspecteer(kandidaat, rol)
    for key in ('schema', 'metingen_sha256', 'metadata_sha256'):
        if basis[key] != nieuw[key]:
            raise ValueError('De oorspronkelijke meetgegevens of metadata zijn gewijzigd. Bewerk alleen de tabel hokken.')
    with closing(openen(kandidaat)) as db:
        schema = db.execute('PRAGMA table_info(hokken)').fetchall()
        if [(r[1], r[2].upper()) for r in schema] != [('hok','TEXT'), ('gebouw','TEXT'), ('afdeling','INTEGER'), ('oppervlakte_m2','REAL')]:
            raise ValueError('Maak hokken met de vier voorgeschreven kolommen en gegevenstypen.')
        if schema[0][5] != 1 or schema[0][3] != 1:
            raise ValueError('Vink PK en NN aan bij hok in hokken.')
        rows = db.execute('SELECT hok, gebouw, afdeling, oppervlakte_m2 FROM hokken ORDER BY hok').fetchall()
        verwacht = [(r[0], 'M5', 1, 8.0) for r in db.execute('SELECT DISTINCT PEN FROM metingen ORDER BY PEN')]
        if rows != verwacht:
            raise ValueError('De hokmetadata wijken af. Neem elk hoknummer uit metingen precies eenmaal op, met gebouw M5, afdeling 1 en oppervlakte 8 m². Sla wijzigingen op.')
    return {k:v for k,v in nieuw.items() if k not in ('schema','metadata','metadata_sha256')} | {'aantal_hokken':len(rows)}



def bewaar_werkbestand(origineel, kandidaat, doel, rol):
    verslag = controleer_aanvulling(origineel, kandidaat, rol)
    doel = Path(doel)
    if doel.exists():
        # Vergelijk de volledige database logisch: ook latere tabellen mogen niet verloren gaan.
        with closing(openen(doel)) as bestaand, closing(openen(kandidaat)) as nieuw:
            if list(bestaand.iterdump()) != list(nieuw.iterdump()):
                raise FileExistsError('Er bestaat al een andere werkdatabase. Die is behouden. Bewaar haar apart en controleer welke versie de nieuwste is.')
        return verslag | {'werkbestand':doel.name, 'overname':'bestaande identieke werkdatabase behouden'}
    doel.parent.mkdir(parents=True, exist_ok=True)
    # Exclusieve aanmaak voorkomt dat een bestaande werkdatabase wordt overschreven.
    with doel.open('xb'):
        pass
    try:
        with closing(openen(kandidaat)) as bron, closing(sqlite3.connect(doel)) as kopie:
            bron.backup(kopie)
    except Exception:
        doel.unlink()  # Alleen het zojuist door deze functie aangemaakte bestand.
        raise
    return verslag | {'werkbestand':doel.name, 'overname':'gecontroleerde werkdatabase aangemaakt'}
