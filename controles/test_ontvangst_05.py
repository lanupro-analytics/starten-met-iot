"""Validatie en idempotente opslag, zonder netwerk of bestaande werkbestanden."""
from pathlib import Path
from contextlib import closing
import copy,json,os,shutil,sqlite3,sys,tempfile,unittest
ROOT=Path(os.environ.get('PRACTICUM_REPO',Path(__file__).resolve().parents[1]))
sys.path[:0]=[str(ROOT/'programmatuur'),str(ROOT/'server'),str(Path(__file__).parent)]
from publiceren import lees_metingen
from meetgegevens import valideer,open_opslag,verwerk,canoniek,overzicht,selectie_manifest,nu


class Opslag(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.map=Path(self.tmp.name)
        self.db=open_opslag(self.map/'verzameld.db'); self.addCleanup(self.db.close)
        with self.db:
            self.db.execute("INSERT INTO verbindingen(deelnemer,rol,toestand,bijgewerkt_op) VALUES('proef','gewichten','gereed',?)",(nu(),))
        self.berichten={}
        for rol,naam in [('gewichten','asserva.db'),('voederopname','schauer.db')]:
            pad=self.map/naam; shutil.copyfile(ROOT/'gegevens/origineel'/naam,pad)
            with closing(sqlite3.connect(pad)) as db,db:
                db.execute('CREATE TABLE hokken(hok TEXT PRIMARY KEY NOT NULL, gebouw TEXT, afdeling INTEGER, oppervlakte_m2 REAL)')
                db.executemany('INSERT INTO hokken VALUES(?,?,?,?)',[(str(i),'M5',1,8.0) for i in range(1,11)])
            self.berichten[rol]=next(lees_metingen(pad,rol,'proef',1))
    def test_beide_rollen_en_exacte_identificatie(self):
        for rol,b in self.berichten.items():
            v=valideer(canoniek(b).encode(),f'practicum/proef/metingen/{rol}','proef',rol)
            self.assertEqual(v['record_id'],b['bronrecord']['ROW_ID'])
    def test_ongeldig_verstoort_opslag_niet(self):
        b=self.berichten['gewichten']; topic='practicum/proef/metingen/gewichten'
        fouten=[b'geen json',b'{"a":1,"a":2}',b'[]',b'{"waarde":NaN}']
        for sleutel,waarde in [('eenheid','g'),('record_id',123),('deelnemer','ander'),('schema_versie',True),('waarde',True),('tijd',{})]:
            f=copy.deepcopy(b); f[sleutel]=waarde; fouten.append(json.dumps(f).encode())
        with self.db:
            for payload in fouten: self.assertEqual(verwerk(self.db,payload,topic,'proef','gewichten'),'ongeldig')
            self.assertEqual(verwerk(self.db,canoniek(b),topic,'proef','gewichten'),'nieuw')
        self.assertEqual(overzicht(self.map/'verzameld.db')['bronnen']['asserva']['aantal'],1)
    def test_herhalen_conflict_en_manifest(self):
        b=self.berichten['gewichten']; topic='practicum/proef/metingen/gewichten'
        with self.db:
            self.assertEqual(verwerk(self.db,canoniek(b),topic,'proef','gewichten'),'nieuw')
            self.assertEqual(verwerk(self.db,canoniek(b),topic,'proef','gewichten'),'dubbel')
            f=copy.deepcopy(b); f['waarde']=999; f['bronrecord']['VBW']=999
            self.assertEqual(verwerk(self.db,canoniek(f),topic,'proef','gewichten'),'conflict')
            f=copy.deepcopy(b); f['deelnemer']='ander'
            self.assertEqual(verwerk(self.db,canoniek(f),'practicum/ander/metingen/gewichten','ander','gewichten'),'dubbel')
        self.assertEqual(overzicht(self.map/'verzameld.db')['bronnen'],selectie_manifest([b]))
    def test_null_is_geen_nul(self):
        b=copy.deepcopy(self.berichten['gewichten']); topic='practicum/proef/metingen/gewichten'
        for waarde in [0,None]:
            b['waarde']=waarde; b['bronrecord']['VBW']=waarde
            self.assertEqual(valideer(canoniek(b),topic,'proef','gewichten')['waarde'],waarde)
    def test_verkeerd_topic_en_grote_payload(self):
        b=self.berichten['gewichten']
        with self.assertRaises(ValueError): valideer(canoniek(b),'practicum/proef/controle/json','proef','gewichten')
        with self.assertRaises(ValueError): valideer(b' '*60001,'practicum/proef/metingen/gewichten','proef','gewichten')

if __name__=='__main__': unittest.main(verbosity=2)
