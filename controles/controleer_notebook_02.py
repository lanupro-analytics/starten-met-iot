"""Controleer beide lesdatabanken en de uitvoering van notebook 02 in tijdelijke werkplekken."""
from pathlib import Path
from contextlib import closing, redirect_stdout
import csv
import hashlib
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'programmatuur'))
from databankcontrole import ROLLEN, OEFENRIJEN, inspecteer, controleer_aanvulling, bewaar_werkbestand

DDL = 'CREATE TABLE oefen_hokken(hok TEXT NOT NULL PRIMARY KEY, afdeling TEXT, controlevolgorde INTEGER, notitie TEXT)'


def aanvullen(pad):
    with closing(sqlite3.connect(pad)) as db, db:
        db.execute(DDL)
        db.executemany('INSERT INTO oefen_hokken VALUES(?,?,?,?)', OEFENRIJEN)


class Databankcontrole(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.map = Path(self.temp.name)
        self.bron = ROOT / 'gegevens/origineel/asserva.db'
        self.upload = self.map / 'asserva.db'
        shutil.copyfile(self.bron, self.upload)

    def test_beide_bronnen_en_exacte_identificaties(self):
        for rol, (naam, meetveld, aantal) in ROLLEN.items():
            with self.subTest(rol=rol):
                result = inspecteer(ROOT / 'gegevens/origineel' / naam, rol)
                self.assertEqual(result['aantal_metingen'], aantal)
                self.assertEqual(result['metadata']['eenheid'], 'kg' if rol == 'gewichten' else 'g')

    def test_ontbrekend_bestand_wordt_niet_aangemaakt(self):
        pad = self.map / 'ontbreekt.db'
        with self.assertRaises(FileNotFoundError):
            inspecteer(pad, 'gewichten')
        self.assertFalse(pad.exists())

    def test_verkeerde_rol(self):
        with self.assertRaisesRegex(ValueError, 'Verkeerde databank'):
            inspecteer(self.upload, 'voederopname')

    def test_onvolledige_oefening(self):
        with self.assertRaisesRegex(ValueError, 'oefen_hokken'):
            controleer_aanvulling(self.bron, self.upload, 'gewichten')
        aanvullen(self.upload)
        with closing(sqlite3.connect(self.upload)) as db, db:
            db.execute("UPDATE oefen_hokken SET afdeling='typfout' WHERE hok='1'")
        with self.assertRaisesRegex(ValueError, 'vier oefenrijen'):
            controleer_aanvulling(self.bron, self.upload, 'gewichten')

    def test_veranderde_meetwaarde_herkend_zonder_veranderd_aantal(self):
        aanvullen(self.upload)
        with closing(sqlite3.connect(self.upload)) as db, db:
            db.execute('UPDATE metingen SET VBW=999 WHERE ROW_ID=(SELECT MIN(ROW_ID) FROM metingen)')
        with self.assertRaisesRegex(ValueError, 'meetgegevens of metadata'):
            controleer_aanvulling(self.bron, self.upload, 'gewichten')

    def test_opslaan_herhalen_en_nieuwere_werkdatabase_beschermen(self):
        aanvullen(self.upload)
        doel = self.map / 'werk/asserva.db'
        bewaar_werkbestand(self.bron, self.upload, doel, 'gewichten')
        hash1 = hashlib.sha256(doel.read_bytes()).hexdigest()
        bewaar_werkbestand(self.bron, self.upload, doel, 'gewichten')
        self.assertEqual(hashlib.sha256(doel.read_bytes()).hexdigest(), hash1)
        with closing(sqlite3.connect(doel)) as db, db:
            db.execute('CREATE TABLE latere_opdracht (notitie TEXT)')
        hash2 = hashlib.sha256(doel.read_bytes()).hexdigest()
        with self.assertRaises(FileExistsError):
            bewaar_werkbestand(self.bron, self.upload, doel, 'gewichten')
        self.assertEqual(hashlib.sha256(doel.read_bytes()).hexdigest(), hash2)

    def test_csv_gelijk_aan_handmatige_invoer(self):
        with (ROOT / 'gegevens/oefeningen/oefenhokken.csv').open(encoding='utf-8', newline='') as f:
            rows = [(r['hok'],r['afdeling'],int(r['controlevolgorde']),r['notitie']) for r in csv.DictReader(f)]
        self.assertEqual(rows, OEFENRIJEN)

    def test_notebook_beide_rollen_en_hervatten(self):
        notebook = json.loads((ROOT / 'docent/notebooks/02_databanken_verkennen_en_aanvullen.ipynb').read_text(encoding='utf-8'))
        for rol, (naam, *_) in ROLLEN.items():
            with self.subTest(rol=rol):
                werk = self.map / rol
                werk.mkdir()
                subprocess.run(['git','init','-q','-b','student/test_deelnemer',str(werk)], check=True)
                shutil.copytree(ROOT / 'programmatuur', werk / 'programmatuur')
                (werk / 'gegevens/origineel').mkdir(parents=True)
                (werk / 'gegevens/werk/invoer').mkdir(parents=True)
                (werk / 'gegevens/inlevering').mkdir(parents=True)
                (werk / 'docent/notebooks').mkdir(parents=True)
                shutil.copyfile(ROOT / 'gegevens/origineel' / naam, werk / 'gegevens/origineel' / naam)
                upload = werk / 'gegevens/werk/invoer' / naam
                shutil.copyfile(ROOT / 'gegevens/origineel' / naam, upload)
                aanvullen(upload)
                config={'branch':'student/test_deelnemer','deelnemerscode':'test_deelnemer','rol':rol,'bronbestand':naam}
                (werk / 'gegevens/inlevering/01_werkplekcontrole.json').write_text(json.dumps(config),encoding='utf-8')
                old = Path.cwd()
                try:
                    os.chdir(werk / 'docent/notebooks')
                    for _ in range(2):
                        namespace={'display':lambda *args:None}
                        with redirect_stdout(io.StringIO()):
                            for cell in notebook['cells']:
                                if cell['cell_type']=='code':
                                    exec(compile(''.join(cell['source']),cell['id'],'exec'),namespace)
                    result = json.loads((werk / 'gegevens/inlevering/02_databankcontrole.json').read_text())
                    self.assertEqual(result['aantal_oefenrijen'],4)
                    self.assertEqual(result['rol'],rol)
                finally:
                    os.chdir(old)


if __name__ == '__main__':
    unittest.main(verbosity=2)
