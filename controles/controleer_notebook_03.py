"""Controleer structuur, oplossingscellen, terminalsyntaxis en lokale verwijzingen."""
from pathlib import Path
import re
import subprocess
import tempfile
import nbformat

ROOT=Path(__file__).resolve().parents[1]
pad=ROOT/'docent/notebooks/03_eigen_server_inrichten.ipynb'
nb=nbformat.read(pad,as_version=4)
nbformat.validate(nb)
ids=[c.id for c in nb.cells]
assert len(ids)==len(set(ids))
for nr in range(1,7):
    pos=ids.index(f'vraag-{nr}')
    assert ids[pos+1:pos+3]==[f'invullen-{nr}',f'antwoord-{nr}']
    assert 'oplossing' not in nb.cells[pos+1].metadata.get('tags',[])
    assert nb.cells[pos+2].metadata.get('tags')==['oplossing']
    assert nb.cells[pos+2].source.startswith(f'**Antwoord {nr}**')
for cell in nb.cells:
    if cell.cell_type=='code':
        compile(cell.source,cell.id,'exec')
        assert not any(o.output_type=='error' for o in cell.outputs)
    else:
        assert '**Route:**' not in cell.source
        assert 'docent/notebooks/' not in cell.source
        for target in re.findall(r'\]\((\.\./[^)]+)\)',cell.source):
            assert (pad.parent/target).is_file(),target
        if '```bash' in cell.source:
            s=cell.source.strip()
            assert s.startswith('```bash') and s.endswith('```') and s.count('```')==2, f'Bash-blok niet los in {cell.id}'
blocks=[b for c in nb.cells if c.cell_type=='markdown' for b in re.findall(r'```bash\n(.*?)```',c.source,re.S)]
assert len(blocks)>=20
with tempfile.TemporaryDirectory() as tmp:
    for i,block in enumerate(blocks):
        p=Path(tmp)/f'blok-{i}.sh'; p.write_text(block,encoding='utf-8')
        subprocess.run(['bash','-n',str(p)],check=True)
print(f'GESLAAGD: {len(nb.cells)} cellen, zes vraagpatronen en {len(blocks)} terminalblokken.')
