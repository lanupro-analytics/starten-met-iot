"""Voer de codecellen uit in tijdelijke Git-repositories, zonder cloudresources."""
from pathlib import Path
import contextlib
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "docent/notebooks/01_werkomgeving_inrichten.ipynb"


class Werkplekcontrole(unittest.TestCase):
    def setUp(self):
        self.nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "student/proefdocent", str(self.root)], check=True)
        (self.root / "docent/notebooks").mkdir(parents=True)
        (self.root / "README.md").write_text("Werkplek", encoding="utf-8")

    def run_cells(self, folder=None):
        previous = Path.cwd()
        os.chdir(folder or self.root)
        namespace = {}
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                for cell in self.nb["cells"]:
                    if cell["cell_type"] == "code":
                        exec(compile("".join(cell["source"]), cell["id"], "exec"), namespace)
        finally:
            os.chdir(previous)
        return namespace

    def test_uitvoering_vanuit_notebookmap(self):
        self.run_cells(self.root / "docent/notebooks")
        result = json.loads((self.root / "gegevens/inlevering/01_werkplekcontrole.json").read_text())
        self.assertEqual(result["deelnemerscode"], "proefdocent")
        self.assertEqual(result["branch"], "student/proefdocent")
        self.assertEqual(result["rol"], "gewichten")

    def test_herhaalde_uitvoering_behoudt_bestaande_notitie(self):
        self.run_cells()
        note = self.root / "gegevens/werk/werknotitie.txt"
        note.write_text("Zelf aangevulde observatie", encoding="utf-8")
        self.run_cells()
        self.assertEqual(note.read_text(encoding="utf-8"), "Zelf aangevulde observatie")

    def test_main_wordt_geblokkeerd_voor_bestandsschrijven(self):
        subprocess.run(["git", "symbolic-ref", "HEAD", "refs/heads/main"], cwd=self.root, check=True)
        with self.assertRaisesRegex(RuntimeError, "student/"):
            self.run_cells()
        self.assertFalse((self.root / "gegevens").exists())

    def test_andere_branch_wordt_ook_geblokkeerd(self):
        subprocess.run(["git", "symbolic-ref", "HEAD", "refs/heads/codex/controle"], cwd=self.root, check=True)
        with self.assertRaisesRegex(RuntimeError, "student/"):
            self.run_cells()
        self.assertFalse((self.root / "gegevens").exists())

    def test_ongeldige_rol_wordt_afgevangen(self):
        cell = next(c for c in self.nb["cells"] if c["id"] == "rol-instellen")
        cell["source"] = "".join(cell["source"]).replace('rol = "gewichten"', 'rol = "onbekend"').splitlines(keepends=True)
        with self.assertRaisesRegex(ValueError, "gewichten.*voederopname"):
            self.run_cells()

    def test_notebook00_is_bytegelijk_bewaard(self):
        manifest = json.loads((ROOT / "archief/eerste_versie/bewaarcontrole.json").read_text(encoding="utf-8"))
        for entry in manifest:
            if entry["origineel"].endswith("00_start_hier.ipynb"):
                self.assertEqual(hashlib.sha256((ROOT / entry["origineel"]).read_bytes()).hexdigest(), entry["sha256"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
