from pathlib import Path
import hashlib,json,sqlite3,sys,tempfile,unittest,gzip
from contextlib import closing
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'programmatuur'))
from aanvulling_08 import voeg_toe,snapshot,lees_basis

class Aanvullen(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/'werk.db'
        self.schema={'ROW_ID':'TEXT','DATE':'TEXT','VBW':'REAL'}
        self.controle={'rol':'gewichten','bron_sha256':'abc','schema':self.schema}
        with closing(sqlite3.connect(self.p)) as db,db:
            db.executescript('CREATE TABLE metingen(ROW_ID TEXT PRIMARY KEY,DATE TEXT,VBW REAL);CREATE TABLE metadata(eigenschap TEXT,waarde TEXT);')
            db.executemany('INSERT INTO metadata VALUES(?,?)',[('rol','gewichten'),('bron_sha256','abc')])
            db.execute('INSERT INTO metingen VALUES(?,?,?)',('1','2023-08-25',7))
    def tearDown(self):self.tmp.cleanup()
    def test_toevoegen_herhalen(self):
        r=[{'ROW_ID':'2','DATE':'2023-09-21','VBW':15}]
        self.assertEqual(voeg_toe(self.p,r,self.controle)['nieuw'],1)
        self.assertEqual(voeg_toe(self.p,r,self.controle)['nieuw'],0)
        with closing(sqlite3.connect(self.p)) as db,db:self.assertEqual(db.execute('SELECT VBW FROM metingen WHERE ROW_ID="1"').fetchone()[0],7)
    def test_conflict_draait_hele_import_terug(self):
        r=[{'ROW_ID':'2','DATE':'2023-09-21','VBW':15},{'ROW_ID':'1','DATE':'2023-09-21','VBW':99}]
        with self.assertRaises(ValueError):voeg_toe(self.p,r,self.controle)
        with closing(sqlite3.connect(self.p)) as db,db:self.assertEqual(db.execute('SELECT COUNT(*) FROM metingen').fetchone()[0],1)
    def test_verkeerde_rol_en_datum(self):
        with self.assertRaises(ValueError):voeg_toe(self.p,[],dict(self.controle,rol='voederopname'))
        with self.assertRaises(ValueError):voeg_toe(self.p,[{'ROW_ID':'3','DATE':'2023-08-25','VBW':8}],self.controle)
    def test_snapshot_kan_teruggelezen(self):
        doel=Path(self.tmp.name)/'snapshot.db.gz'
        info=snapshot(self.p,doel)
        self.assertEqual(info['sha256'],hashlib.sha256(doel.read_bytes()).hexdigest())
        herstel=Path(self.tmp.name)/'herstel.db';herstel.write_bytes(gzip.decompress(doel.read_bytes()))
        with closing(sqlite3.connect(herstel)) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM metingen').fetchone()[0],1)

if __name__=='__main__':unittest.main(verbosity=2)
