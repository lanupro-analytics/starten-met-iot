"""Genereer de studentenversies 01–05 vanuit docent/notebooks/ naar notebooks/.

- Laat notebooks/00_start_hier.ipynb volledig ongemoeid (SHA-256-bewaakt).
- Verwijdert alle cellen met tag "oplossing" (antwoorden, oplossings-code en docent-bypasses).
- Wist alle cel-uitvoeren (outputs) en execution_count in codecellen.
- Past relatieve links ../../<map> aan naar ../<map>.
- Verwijdert de verwijzing naar bewaarde proefdocent-voorbeelduitvoer in de inleiding.
- Controleert syntax (ast.parse, bash -n), metadata en bestandsverwijzingen.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
DOCENT_DIR = ROOT / "docent" / "notebooks"
STUDENT_DIR = ROOT / "notebooks"
BEWAARCONTROLE = ROOT / "archief" / "eerste_versie" / "bewaarcontrole.json"

VOORBEELD_ZINNEN = (
    "\n\nDe voorbeelduitvoer bij de codecellen hieronder is gemaakt met `student/proefdocent`. "
    "Voer alle codecellen zelf opnieuw uit zodat jouw eigen branch en instellingen verschijnen.",
    "De voorbeelduitvoer bij de codecellen hieronder is gemaakt met `student/proefdocent`. "
    "Voer alle codecellen zelf opnieuw uit zodat jouw eigen branch en instellingen verschijnen.",
    "\nDe bewaarde uitvoer toont een voorbeeld. Tijdens je eigen uitvoering verschijnen jouw deelnemerscode en resultaten.",
    "De bewaarde uitvoer toont een voorbeeld. Tijdens je eigen uitvoering verschijnen jouw deelnemerscode en resultaten.",
)


def controleer_notebook_00() -> None:
    manifest = json.loads(BEWAARCONTROLE.read_text(encoding="utf-8"))
    for entry in manifest:
        if entry["origineel"].endswith("00_start_hier.ipynb"):
            pad = ROOT / entry["origineel"]
            actueel = hashlib.sha256(pad.read_bytes()).hexdigest()
            if actueel != entry["sha256"]:
                raise RuntimeError(
                    f"{entry['origineel']} wijkt af van de bewaarde SHA-256!"
                )
            return
    raise RuntimeError("00_start_hier.ipynb ontbreekt in bewaarcontrole.json")


def herschrijf_relatieve_paden(tekst: str) -> str:
    return re.sub(r"\.\./\.\./(?=[A-Za-z0-9_])", "../", tekst)


def opschonen_voorbeelduitvoer_zin(tekst: str) -> str:
    for zin in VOORBEELD_ZINNEN:
        tekst = tekst.replace(zin, "")
    return re.sub(r"\n{3,}", "\n\n", tekst)


def opschonen_docent_hooks_in_code(bron: str) -> str:
    bron = re.sub(
        r'\nif not re\.fullmatch\(r"student/\[a-z0-9\]\[a-z0-9_-\]\*", branch\) and "_DOCENT_BRANCH_OVERRIDE" in globals\(\):\n    branch = _DOCENT_BRANCH_OVERRIDE',
        "",
        bron,
    )
    bron = bron.replace(
        'globals().get("_DOCENT_KANDIDAAT_OVERRIDE", invoermap / bestandsnaam)',
        "invoermap / bestandsnaam",
    )
    return bron


def maak_studentenversie(docent_pad: Path, doel_pad: Path) -> dict:
    nb = nbformat.read(docent_pad, as_version=4)

    verwijderd: list[str] = []
    behouden_cellen = []
    gewiste_outputs = 0

    for cell in nb.cells:
        tags = cell.get("metadata", {}).get("tags", [])
        if "oplossing" in tags:
            verwijderd.append(str(cell.get("id") or "<zonder-id>"))
            continue

        bron = herschrijf_relatieve_paden(cell.source)
        if cell.cell_type == "markdown" and cell.get("id") == "titel":
            bron = opschonen_voorbeelduitvoer_zin(bron)
        if cell.cell_type == "code":
            bron = opschonen_docent_hooks_in_code(bron)
        cell.source = bron

        if cell.cell_type == "code":
            if cell.get("outputs"):
                gewiste_outputs += 1
            cell.outputs = []
            cell.execution_count = None
            ast.parse(cell.source)

        behouden_cellen.append(cell)

    nb.cells = behouden_cellen
    practicum_meta = nb.metadata.get("practicum")
    if not isinstance(practicum_meta, dict):
        practicum_meta = {}
    practicum_meta["versie"] = "student"
    nb.metadata["practicum"] = practicum_meta

    nbformat.validate(nb)
    doel_pad.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, doel_pad)

    controleer_studentennotebook(doel_pad)

    return {
        "bestand": doel_pad.name,
        "cellen": len(nb.cells),
        "verwijderd": verwijderd,
        "gewiste_outputs": gewiste_outputs,
    }


def controleer_studentennotebook(pad: Path) -> None:
    nb = nbformat.read(pad, as_version=4)
    nbformat.validate(nb)

    if nb.metadata.get("practicum", {}).get("versie") != "student":
        raise AssertionError(f"{pad.name}: metadata practicum.versie != 'student'")

    for cell in nb.cells:
        tags = cell.get("metadata", {}).get("tags", [])
        if "oplossing" in tags:
            raise AssertionError(f"{pad.name}: oplossing-tag nog aanwezig in {cell.id}")
        if "../../" in cell.source:
            raise AssertionError(f"{pad.name}: oud relatief pad '../../' in {cell.id}")
        if "_DOCENT_" in cell.source:
            raise AssertionError(f"{pad.name}: docent-override nog aanwezig in {cell.id}")

        if cell.cell_type == "code":
            if cell.outputs:
                raise AssertionError(f"{pad.name}: niet-lege outputs in {cell.id}")
            if cell.execution_count is not None:
                raise AssertionError(f"{pad.name}: execution_count is niet None in {cell.id}")
            ast.parse(cell.source)
        else:
            for doel in re.findall(r"\]\((\.\./[^)#]+)", cell.source):
                if not (pad.parent / doel).exists():
                    raise AssertionError(
                        f"{pad.name}: ontbrekende link '{doel}' in cel {cell.id}"
                    )
            for blok in re.findall(r"```bash\n(.*?)```", cell.source, re.S):
                subprocess.run(["bash", "-n"], input=blok, text=True, check=True)


def main() -> None:
    controleer_notebook_00()
    docent_notebooks = sorted(DOCENT_DIR.glob("0[1-5]_*.ipynb"))
    if len(docent_notebooks) != 5:
        raise RuntimeError(
            f"Verwacht 5 docentnotebooks (01-05), gevonden: {[p.name for p in docent_notebooks]}"
        )

    for docent_pad in docent_notebooks:
        doel_pad = STUDENT_DIR / docent_pad.name
        info = maak_studentenversie(docent_pad, doel_pad)
        print(
            f"OK {info['bestand']}: {info['cellen']} cellen | "
            f"{len(info['verwijderd'])} docent-/oplossingscellen verwijderd {info['verwijderd']} | "
            f"{info['gewiste_outputs']} codecellen zonder uitvoer"
        )

    controleer_notebook_00()
    print("GESLAAGD: 00_start_hier.ipynb ongewijzigd en studentenversies 01–05 geverifieerd.")


if __name__ == "__main__":
    main()
