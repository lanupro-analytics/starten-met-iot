"""Kleine rekenvoorbeelden bewaken tijdsgrenzen, eenheden en ontbrekende gegevens."""
from pathlib import Path
import sys, unittest, tempfile
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'programmatuur'))
from analyse_07 import schat_gewicht, bereken_intervallen, vat_hokken_samen, bewaar_basis, selecteer

class Rekenen(unittest.TestCase):
    def setUp(self):
        self.pop=pd.DataFrame({'dier_id':['a','b'],'hok':['1','1']})
        self.dag=pd.DataFrame([
            {'dier_id':a,'hok':'1','tijd':pd.Timestamp(t),'gewicht_kg':w}
            for a,w0,w1 in [('a',10.,12.),('b',10.,14.)]
            for t,w in [('2023-08-25 00:00',w0),('2023-08-27 00:00',w1)]])
        self.voer=pd.DataFrame([
            {'dier_id':a,'hok':'1','tijd':pd.Timestamp(t),'waarde':v}
            for a,v in [('a',1500.),('b',2000.)]
            for t in ['2023-08-25 12:00','2023-08-26 12:00']])
        self.grenzen=['2023-08-25','2023-08-27']

    def test_interpolatie_geen_extrapolatie(self):
        d=self.dag[self.dag.dier_id=='a']
        self.assertEqual(schat_gewicht(d,pd.Timestamp('2023-08-26'),48)[0],11)
        self.assertIsNone(schat_gewicht(d,pd.Timestamp('2023-08-24'),48)[0])
        self.assertIsNone(schat_gewicht(d,pd.Timestamp('2023-08-26'),24)[0])

    def test_groepen_verhouding_van_totalen(self):
        x=bereken_intervallen(self.dag,self.voer,self.pop,self.grenzen)
        h=vat_hokken_samen(x).iloc[0]
        self.assertEqual(h['dieren_bruikbaar'],2)
        self.assertAlmostEqual(h['voeder_kg'],7)
        self.assertAlmostEqual(h['groei_kg'],6)
        self.assertAlmostEqual(h['voederconversie'],7/6)
        self.assertAlmostEqual(h['groei_g_dier_dag'],1500)
        self.assertAlmostEqual(h['voeder_g_dier_dag'],1750)

    def test_grens_exclusief_en_ontbrekend_geen_nul(self):
        voer=pd.concat([self.voer,pd.DataFrame([{'dier_id':'a','hok':'1','tijd':pd.Timestamp('2023-08-27'),'waarde':99999}])])
        x=bereken_intervallen(self.dag,voer,self.pop,self.grenzen)
        self.assertEqual(x.loc[x.dier_id=='a','voeder_kg'].iloc[0],3)
        voer=self.voer.iloc[1:].copy()
        x=bereken_intervallen(self.dag,voer,self.pop,self.grenzen)
        self.assertIn('voederdagen_ontbreken',x.loc[x.dier_id=='a','reden'].iloc[0])
        self.assertEqual(vat_hokken_samen(x).iloc[0]['dieren_bruikbaar'],1)

    def test_nulgroei_en_nulbezoek(self):
        d=self.dag.copy(); d.loc[d.dier_id=='a','gewicht_kg']=10
        v=self.voer.copy(); v.loc[v.dier_id=='b','waarde']=0
        x=bereken_intervallen(d,v,self.pop,self.grenzen)
        self.assertIn('geen_positieve_groei',x.loc[x.dier_id=='a','reden'].iloc[0])
        self.assertEqual(x.loc[x.dier_id=='b','voederconversie'].iloc[0],0)

    def test_basis_bewaren_en_niet_overschrijven(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'basis'
            dier=bereken_intervallen(self.dag,self.voer,self.pop,self.grenzen)
            hok=vat_hokken_samen(dier)
            a=bewaar_basis(p,self.pop,self.dag,dier,hok,{}, {'grenzen':self.grenzen})
            b=bewaar_basis(p,self.pop,self.dag,dier,hok,{}, {'grenzen':self.grenzen})
            self.assertEqual(a,b)
            veranderd=hok.copy(); veranderd['voeder_kg']=999
            with self.assertRaises(ValueError): bewaar_basis(p,self.pop,self.dag,dier,veranderd,{}, {'grenzen':self.grenzen})
            self.assertEqual((p/'beginsituatie.json').read_text(),__import__('json').dumps(a,ensure_ascii=False,sort_keys=True,indent=2)+'\n')

    def test_selectie_eenheid_dubbel_en_hokkoppeling(self):
        rijen=[]
        for bron,rol,eenheid,waarde in [('asserva','gewichten','kg',10),('schauer','voederopname','g',0)]:
            for dier in ['a','b']:
                rijen.append({'bron':bron,'meettype':rol,'eenheid':eenheid,'record_id':bron+dier,
                    'dier_id':dier,'hok':'2' if dier=='b' and bron=='schauer' else '1',
                    'datum':'2023-08-25','tijd':'2023-08-25T12:00:00','einde':'2023-08-25T12:00:01',
                    'waarde':waarde,'foutcode':'no error','vlag':'0','herkomst':'0'})
        d=pd.DataFrame(rijen)
        g,v,p,a,u=selecteer(d)
        self.assertEqual(list(p.dier_id),['a'])
        self.assertEqual(list(u.dier_id),['b'])
        self.assertEqual(v.iloc[0].waarde,0)
        extra = d[d.dier_id.eq('a')].copy()
        extra['record_id'] += '_uitgesloten'
        extra['vlag'] = 'flagged'
        extra['waarde'] = 99999
        gg,vv,_,_,_ = selecteer(pd.concat([d,extra],ignore_index=True))
        self.assertTrue(gg.vlag.eq('0').all() and vv.vlag.eq('0').all())
        self.assertEqual(len(gg),len(g))
        self.assertEqual(len(vv),len(v))
        with self.assertRaises(ValueError): selecteer(pd.concat([d,d.iloc[[0]]]))
        d.loc[0,'eenheid']='g'
        with self.assertRaises(ValueError): selecteer(d)

    def test_grafiekassen_tonen_alle_hokken(self):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from figuren_07 import intervalfiguur
        dier=bereken_intervallen(self.dag,self.voer,self.pop,self.grenzen)
        h=vat_hokken_samen(dier)
        tweede=h.copy(); tweede['hok']='2'; tweede['voederconversie']=10
        h=pd.concat([h,tweede],ignore_index=True)
        f=intervalfiguur(h,'conversie')
        try: self.assertGreater(f.axes[0].get_ylim()[1],10)
        finally: plt.close(f)

    def test_kilogramweergave_verandert_geen_conversie(self):
        import matplotlib.pyplot as plt
        from figuren_07 import intervalfiguur
        import numpy as np
        h = vat_hokken_samen(bereken_intervallen(self.dag,self.voer,self.pop,self.grenzen))
        gram = intervalfiguur(h)
        kilo = intervalfiguur(h,kilogram=True)
        conversie = intervalfiguur(h,'conversie',kilogram=True)
        try:
            for a,b in zip(gram.axes[0].lines,kilo.axes[0].lines):
                np.testing.assert_allclose(b.get_ydata(),a.get_ydata()/1000)
            np.testing.assert_allclose(kilo.axes[0].get_ylim(),np.array(gram.axes[0].get_ylim())/1000)
            np.testing.assert_allclose(conversie.axes[0].lines[0].get_ydata(),h.voederconversie)
            self.assertEqual(kilo.axes[0].get_ylabel(),'kg per dier per dag')
        finally:
            for f in (gram,kilo,conversie): plt.close(f)

if __name__=='__main__': unittest.main(verbosity=2)
