"""Controleer notebookstructuur, codeblokken en studentgeneratie zonder bronwijzigingen."""
from pathlib import Path
import ast, importlib.util, re, subprocess, sys, tempfile
import nbformat

ROOT=Path(__file__).resolve().parents[1]
pad=ROOT/'docent/notebooks/06_gegevens_opvragen_via_een_api.ipynb'
nb=nbformat.read(pad,4); nbformat.validate(nb)
blokken=0
for cell in nb.cells:
    if cell.cell_type=='code':
        ast.parse(cell.source)
    else:
        for blok in re.findall(r'```bash\n(.*?)```',cell.source,re.S):
            assert cell.source.strip().startswith('```bash') and cell.source.strip().endswith('```')
            assert cell.source.count('```')==2, cell.id
            subprocess.run(['bash','-n'],input=blok,text=True,check=True)
            blokken+=1
        for doel in re.findall(r'\]\((\.\./[^)#]+)\)',cell.source):
            assert (pad.parent/doel).exists(), (cell.id,doel)
        if '<div ' in cell.source:
            assert 'text-align:justify' in cell.source and 'overflow-wrap:anywhere' in cell.source,cell.id
        if '**Vraag ' in cell.source:
            i=nb.cells.index(cell)
            assert '**Jouw antwoord' in nb.cells[i+1].source
            assert 'oplossing' in nb.cells[i+2].metadata.get('tags',[])

spec=importlib.util.spec_from_file_location('generator',ROOT/'hulpmiddelen/maak_studentenversies.py')
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
gen.controleer_notebook_00()
with tempfile.TemporaryDirectory() as tmp:
    basis=Path(tmp); (basis/'notebooks').mkdir()
    for naam in ('afbeeldingen','gegevens','documentatie'):
        (basis/naam).symlink_to(ROOT/naam,target_is_directory=True)
    resultaat=gen.maak_studentenversie(pad,basis/'notebooks'/pad.name)
    print('Studentgeneratie gecontroleerd:',resultaat)
print(f'Notebook valide, {len(nb.cells)} cellen, {blokken} Bash-blokken gecontroleerd. Notebook 00 behouden.')
