"""Contracttests met een echte HTTP-server en tijdelijke SQLite-bestanden."""
from pathlib import Path
import json, os, sqlite3, sys, tempfile, threading, time, unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'server'), str(ROOT/'programmatuur')]
import requests
import uvicorn
from toegang_api import controlewaarde
from meetgegevens import open_opslag, verwerk, canoniek
from webdienst import maak_app
from api_ophalen import werk_analyse_bij, APP_ID


def bericht(n, rol='gewichten'):
    gewicht = rol == 'gewichten'
    rid = str(10**26 + n)
    raw = {'ROW_ID':rid, 'EID':'dier1', 'PEN':'1', 'DATE':'2023-08-24',
           'TIMESTAMPstart':'20230824120000' if gewicht else '2023-08-24 12:00:00',
           'TIMESTAMPstop':'20230824120100' if gewicht else '2023-08-24 12:01:00',
           'VBW' if gewicht else 'VFI':10.0}
    return {'schema_versie':1,'deelnemer':'proef','bron':'asserva' if gewicht else 'schauer',
            'meettype':rol,'record_id':rid,'dier_id':'dier1','hok':'1',
            'tijd':{'start':'2023-08-24T12:00:00','einde':'2023-08-24T12:01:00'},
            'tijdzone':'onbevestigd; vermoedelijk Europe/Brussels',
            'meetveld':'VBW' if gewicht else 'VFI','waarde':10.0,'eenheid':'kg' if gewicht else 'g',
            'hokmetadata':{'hok':'1','gebouw':'M5','afdeling':1,'oppervlakte_m2':8.0},'bronrecord':raw}


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pad = Path(cls.tmp.name)/'verzameld.db'
        cls.db = open_opslag(cls.pad)
        for n, rol in [(1,'gewichten'),(2,'gewichten'),(3,'voederopname')]:
            b=bericht(n,rol)
            assert verwerk(cls.db,canoniek(b),f'practicum/proef/metingen/{rol}','proef',rol)=='nieuw'
        cls.db.commit()
        cls.wachtwoord='alleen-een-lokaal-testwachtwoord'
        app=maak_app(cls.pad,controlewaarde(cls.wachtwoord))
        cls.server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=18766,log_level='error'))
        cls.thread=threading.Thread(target=cls.server.run,daemon=True); cls.thread.start()
        for _ in range(100):
            if cls.server.started: break
            time.sleep(.05)
        if not cls.server.started: raise RuntimeError('Testserver niet gestart')
        cls.url='http://127.0.0.1:18766'

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit=True; cls.thread.join(5); cls.db.close(); cls.tmp.cleanup()

    def get(self,pad,**params):
        return requests.get(self.url+pad,params=params,auth=('eigenaar',self.wachtwoord),timeout=10)

    def test_auth_en_documentatie(self):
        for pad in ['/gezondheid','/metadata','/metingen','/openapi.json']:
            self.assertEqual(requests.get(self.url+pad,timeout=5).status_code,401)
        self.assertEqual(self.get('/gezondheid').json()['status'],'bereikbaar')
        self.assertIn('/metingen',self.get('/openapi.json').json()['paths'])
        self.assertEqual(requests.post(self.url+'/metingen',timeout=5).status_code,405)
        self.assertEqual(requests.get(self.url+'/metadata',auth=('eigenaar','verkeerd'),timeout=5).status_code,401)

    def test_filter_fouten_en_leeg(self):
        self.assertEqual(self.get('/metingen',meettype='gewichten',hok='1').json()['aantal'],2)
        for params in [{'meettype':'fout'},{'limiet':0},{'vanaf':'gisteren'}, {'vanaf':'2023-08-25','tot':'2023-08-24'}, {'hoik':'1'}]:
            self.assertEqual(self.get('/metingen',**params).status_code,422)
        for params in [{'hok':'999'}, {'hok':"1' OR 1=1 --"}, {'tot':'2023-08-24'}]:
            r=self.get('/metingen',**params); self.assertEqual(r.status_code,200); self.assertEqual(r.json()['metingen'],[])

    def test_paginering_en_identiteit(self):
        meta=self.get('/metadata').json(); grens=meta['grens']
        ids=[]; na=0
        while True:
            page=self.get('/metingen',grens=grens,na=na,limiet=1).json()
            ids.extend((b['bron'],b['record_id']) for b in page['metingen'])
            if page['volgende_na'] is None: break
            self.assertGreater(page['volgende_na'],na); na=page['volgende_na']
        self.assertEqual(len(ids),3); self.assertEqual(len(set(ids)),3)
        self.assertTrue(all(isinstance(rid,str) and len(rid)==27 for _,rid in ids))
        self.assertEqual(meta['bronnen']['asserva']['aantal'],2)

    def test_import_herhaling_rollback_en_bronbescherming(self):
        def ophalen(pad, parameters=None):
            r=self.get(pad,**(parameters or {})); r.raise_for_status(); return r.json()
        pad=Path(self.tmp.name)/'analyse.db'
        eerste=werk_analyse_bij(ophalen,pad,lambda x:None)
        tweede=werk_analyse_bij(ophalen,pad,lambda x:None)
        self.assertEqual(eerste['nieuw'],3); self.assertEqual(tweede['nieuw'],0)
        self.assertEqual(tweede['ongewijzigd'],3)
        with self.assertRaises(ValueError): werk_analyse_bij(ophalen,self.pad)
        def kapot(pad,parameters=None):
            result=ophalen(pad,parameters)
            if pad=='/metadata': result['bronnen']['asserva']['sha256']='0'*64
            return result
        with self.assertRaises(ValueError): werk_analyse_bij(kapot,pad)
        with sqlite3.connect(pad) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM metingen').fetchone()[0],3)
        leeg=Path(self.tmp.name)/'teruggedraaid.db'
        with self.assertRaises(ValueError): werk_analyse_bij(kapot,leeg)
        with sqlite3.connect(leeg) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM metingen').fetchone()[0],0)

    def test_z_toevoeging_tijdens_paginering(self):
        grens=self.get('/metadata').json()['grens']
        b=bericht(99)
        with self.db:
            verwerk(self.db,canoniek(b),'practicum/proef/metingen/gewichten','proef','gewichten')
        try:
            oude=self.get('/metingen',grens=grens).json()
            nieuwe=self.get('/metingen').json()
            self.assertEqual(oude['aantal'],3)
            self.assertEqual(nieuwe['aantal'],4)
        finally:
            with self.db: self.db.execute('DELETE FROM metingen WHERE record_id=?',(b['record_id'],))


if __name__=='__main__': unittest.main(verbosity=2)
