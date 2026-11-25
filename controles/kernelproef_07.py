"""Voer notebook 07 uit voor beide rollen in een tijdelijke kopie, zonder server.

De fixture bootst uitsluitend het reeds geteste databaseformaat uit 06 na.
Bronbestanden en bestaande werkbestanden blijven behouden.
"""
from pathlib import Path
from contextlib import closing
import hashlib,json,os,shutil,sqlite3,subprocess,sys,tempfile
import nbformat
from nbclient import NotebookClient

ROOT=Path(os.environ.get('PRACTICUM_REPO',Path(__file__).resolve().parents[1])).resolve()
sys.path[:0]=[str(ROOT/'programmatuur'),str(ROOT/'server')]
from publiceren import lees_metingen
from meetgegevens import inhoud
from api_ophalen import analyse_overzicht


def fixture(werk):
    data=werk/'gegevens/werk'; data.mkdir(parents=True)
    db=sqlite3.connect(data/'analyse_06.db')
    db.executescript('''PRAGMA application_id=600106;
CREATE TABLE metingen(bron TEXT,record_id TEXT,meettype TEXT,dier_id TEXT,hok TEXT,datum TEXT,waarde REAL,eenheid TEXT,inhoud_json TEXT,inhoud_sha256 TEXT,PRIMARY KEY(bron,record_id));
CREATE TABLE ophalen(id INTEGER PRIMARY KEY,gecontroleerd_op TEXT,metadata_json TEXT);''')
    for rol,naam in [('gewichten','asserva.db'),('voederopname','schauer.db')]:
        bron=data/naam; shutil.copyfile(ROOT/'gegevens/origineel'/naam,bron)
        with closing(sqlite3.connect(bron)) as b,b:
            b.execute('CREATE TABLE hokken(hok TEXT PRIMARY KEY NOT NULL,gebouw TEXT,afdeling INTEGER,oppervlakte_m2 REAL)')
            b.executemany('INSERT INTO hokken VALUES(?,?,?,?)',[(str(i),'M5',1,8) for i in range(1,11)])
        with db:
            for r in lees_metingen(bron,rol,'proefdocent',None):
                tekst=inhoud(r); digest=hashlib.sha256(tekst.encode()).hexdigest()
                db.execute('INSERT INTO metingen VALUES(?,?,?,?,?,?,?,?,?,?)',
                           (r['bron'],r['record_id'],r['meettype'],r['dier_id'],r['hok'],r['bronrecord']['DATE'],r['waarde'],r['eenheid'],tekst,digest))
        print('Fixture:',rol,flush=True)
    manifest=analyse_overzicht(db)
    with db: db.execute('INSERT INTO ophalen VALUES(1,?,?)',('proef',json.dumps({'bronnen':manifest})))
    db.close(); return manifest


def main():
    uitvoer=Path(os.environ.get('UITVOER_07',ROOT/'uitvoer07')).resolve()
    uitvoer.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='iot07-') as tmp:
        werk=Path(tmp)
        for naam in ('programmatuur','server'):
            shutil.copytree(ROOT/naam,werk/naam,ignore=shutil.ignore_patterns('__pycache__'))
        subprocess.run(['git','init','-b','student/proefdocent',str(werk)],check=True,capture_output=True)
        manifest=fixture(werk)
        inlever=werk/'gegevens/inlevering';inlever.mkdir()
        voor=hashlib.sha256((werk/'gegevens/werk/analyse_06.db').read_bytes()).hexdigest()
        for rol in ('gewichten','voederopname'):
            (inlever/'01_werkplekcontrole.json').write_text(json.dumps({'deelnemerscode':'proefdocent','branch':'student/proefdocent','rol':rol}))
            (inlever/'06_apicontrole.json').write_text(json.dumps({'deelnemerscode':'proefdocent','branch':'student/proefdocent','inhoud_gelijk_aan_05':True,'herhaalde_import':{'bronnen':manifest}}))
            nb=nbformat.read(ROOT/'docent/notebooks/07_voederconversie_berekenen_en_visualiseren.ipynb',4)
            client=NotebookClient(nb,timeout=600,kernel_name='python3',resources={'metadata':{'path':str(werk)}})
            client.execute()
            nbformat.write(nb,uitvoer/f'07_uitgevoerd_{rol}.ipynb')
            verslag=json.loads((inlever/'07_analysecontrole.json').read_text())
            assert verslag['populatie']==101
            assert verslag['bruikbare_dieren_per_interval']=={'1':72,'2':98,'3':98,'4':98}
            assert abs(verslag['eigen_voederconversie']-1.263937795)<.00001
            assert hashlib.sha256((werk/'gegevens/werk/analyse_06.db').read_bytes()).hexdigest()==voor
            print('Volledig uitgevoerd en bron ongewijzigd:',rol,flush=True)
        shutil.copytree(inlever,uitvoer/'inlevering',dirs_exist_ok=True)
        # Een alternatieve periode en extra latere data mogen de vaste basis niet wijzigen.
        sys.path.insert(0,str(ROOT/'programmatuur'))
        from analyse_07 import lees_analyse,selecteer,daggewichten,bereken_intervallen,vat_hokken_samen,STANDAARD_GRENZEN
        import pandas as pd
        raw,_=lees_analyse(werk/'gegevens/werk/analyse_06.db')
        g,v,pop,_,_=selecteer(raw)
        basis=vat_hokken_samen(bereken_intervallen(daggewichten(g),v,pop,STANDAARD_GRENZEN))
        extra=raw.iloc[[0]].copy();extra['record_id']='9'*27;extra['datum']='2023-09-22'
        extra['tijd']='2023-09-22T12:00:00';extra['einde']='2023-09-22T12:00:01';extra['waarde']=999
        g2,v2,pop2,_,_=selecteer(pd.concat([raw,extra],ignore_index=True))
        later=vat_hokken_samen(bereken_intervallen(daggewichten(g2),v2,pop2,STANDAARD_GRENZEN))
        pd.testing.assert_frame_equal(basis,later)
        print('Vaste basis blijft gelijk bij extra latere records.',flush=True)

if __name__=='__main__': main()
