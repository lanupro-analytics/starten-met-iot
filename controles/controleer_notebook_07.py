"""Notebookstructuur en tijdelijke studentgeneratie, zonder bestaande notebooks te wijzigen."""
from pathlib import Path
import ast,importlib.util,os,re,shutil,subprocess,tempfile
import nbformat
ROOT=Path(os.environ.get('PRACTICUM_REPO',Path(__file__).resolve().parents[1])).resolve()
pad=ROOT/'docent/notebooks/07_voederconversie_berekenen_en_visualiseren.ipynb'
nb=nbformat.read(pad,4);nbformat.validate(nb)
for i,c in enumerate(nb.cells):
    if c.cell_type=='code': ast.parse(c.source)
    else:
        if '**Vraag ' in c.source:
            assert '**Jouw antwoord' in nb.cells[i+1].source
            assert 'oplossing' in nb.cells[i+2].metadata.get('tags',[])
        for link in re.findall(r'\]\((\.\./[^)#]+)\)',c.source):
            assert (pad.parent/link).exists(),link
        if '<div ' in c.source: assert 'text-align:justify' in c.source and 'overflow-wrap:anywhere' in c.source
        assert '—' not in c.source
    assert not any(o.output_type=='error' for o in c.get('outputs',[])),c.id
spec=importlib.util.spec_from_file_location('generator',ROOT/'hulpmiddelen/maak_studentenversies.py')
gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
gen.controleer_notebook_00()
with tempfile.TemporaryDirectory(prefix='student07-') as tmp:
    p=Path(tmp);(p/'notebooks').mkdir()
    for naam in ('gegevens/gegevenswoordenboek.md','documentatie/rekenmethode_07.md'):
        (p/naam).parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/naam,p/naam)
    resultaat=gen.maak_studentenversie(pad,p/'notebooks'/pad.name)
    print(resultaat)
print('Notebook geldig, antwoordpatroon en links correct, notebook 00 behouden.')
