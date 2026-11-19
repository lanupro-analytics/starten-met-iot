"""Voorkom ongeldige serveradressen en onbedoeld vervangen van certificaten."""
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
from certificaat_maken import controleer_invoer, maak_certificaat

class Instellingen(unittest.TestCase):
    def test_invoer(self):
        self.assertEqual(controleer_invoer('203.0.113.7', 'jan_janssens'), ('203.0.113.7', 'jan_janssens'))
        for adres, code in [('x;touch /tmp/x','jan'),('203.0.113.7','../jan'),('::1','jan')]:
            with self.assertRaises(ValueError): controleer_invoer(adres, code)

    def test_herhalen_zonder_vervanging(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'tls'
            maak_certificaat(root,'127.0.0.1','proef')
            before={p.name:p.read_bytes() for p in root.iterdir()}
            maak_certificaat(root,'127.0.0.1','proef')
            self.assertEqual(before,{p.name:p.read_bytes() for p in root.iterdir()})
            with self.assertRaises(FileExistsError): maak_certificaat(root,'127.0.0.2','proef')
            self.assertEqual(before,{p.name:p.read_bytes() for p in root.iterdir()})

if __name__=='__main__': unittest.main(verbosity=2)
