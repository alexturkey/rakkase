"""scripts/denetim.py kapilarinin negatif yoklamasi (CPU, model yok): her kapi kasitli kotu girdide KIRMIZI, temiz girdide yesil.
Calistir (kokten):  python -B -m unittest testler/denetim_test.py -v"""
import os
import subprocess
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DENETIM = os.path.join(KOK, "scripts", "denetim.py")
SURUCU = "C" + ":" + chr(92)  # kaynak dosya kendi kapisina takilmasin


def kos(dosyalar):
    with tempfile.TemporaryDirectory() as t:
        for ad, veri in dosyalar.items():
            yol = os.path.join(t, ad)
            os.makedirs(os.path.dirname(yol), exist_ok=True)
            with open(yol, "wb") as f:
                f.write(veri if isinstance(veri, bytes) else veri.encode("utf-8"))
        r = subprocess.run([sys.executable, "-I", DENETIM, "--kok", t], capture_output=True, text=True)
        return r.returncode, r.stdout


class Denetim(unittest.TestCase):
    def kirmizi(self, dosyalar, kapi):
        kod, cikti = kos(dosyalar)
        self.assertEqual(kod, 1, cikti)
        self.assertIn(kapi, cikti)

    def test_temiz(self):
        kod, cikti = kos({"README.md": "Rakkase. noreply@github.com\n", "k.py": "x = 1\n", "ornekler/p.json": "{}"})
        self.assertEqual(kod, 0, cikti)

    def test_g1_cift_yonlu(self):
        self.kirmizi({"a.md": "x\u202ey\n"}, "G1")

    def test_g1_ham_kontrol(self):
        self.kirmizi({"a.md": b"x\x01y\n"}, "G1")

    def test_g2_yol_ad_posta_token(self):
        self.kirmizi({"a.md": SURUCU + "Users" + chr(92) + "biri\n"}, "G2")
        self.kirmizi({"a.md": SURUCU + "proje\n"}, "G2")
        self.kirmizi({"a.md": "bana yaz: biri@ornek.net\n"}, "G2")
        self.kirmizi({"a.md": "ghp_" + "A" * 30 + "\n"}, "G2")
        self.kirmizi({"a.md": "naber kanka\n"}, "G2")

    def test_g2_cikti_eslesen_metni_yazmaz(self):
        _, cikti = kos({"a.md": "ghp_" + "Z" * 30 + "\n"})
        self.assertNotIn("ZZZZ", cikti)

    def test_g3_ikili(self):
        self.kirmizi({"a.mp3": b"ID3"}, "G3")
        self.kirmizi({"model.safetensors": b"x"}, "G3")
        self.kirmizi({"testler/referans/b.wav": b"R" * (9 * 1024 * 1024)}, "G3")
        kod, cikti = kos({"testler/referans/b.wav": b"RIFF" * 10})
        self.assertEqual(kod, 0, cikti)

    def test_g3_gorsel(self):
        kod, cikti = kos({"docs/gorsel/b.jpg": b"\xff\xd8\xff" + b"x" * 100})
        self.assertEqual(kod, 0, cikti)
        self.kirmizi({"docs/gorsel/b.jpg": b"\xff\xd8\xff" + b"x" * (3 * 1024 * 1024)}, "G")
        self.kirmizi({"baska/b.jpg": b"\xff\xd8\xff" + b"x" * 100}, "G")
        self.kirmizi({"docs/gorsel/b.exe": b"MZ"}, "G3")

    def test_g4_json(self):
        self.kirmizi({"ornekler/p.json": "{bozuk"}, "G4")

    def test_g5_python(self):
        self.kirmizi({"k.py": "def (:\n"}, "G5")

    def test_g6_yerel(self):
        self.kirmizi({"ayarlar.json": "{}"}, "G6")
        self.kirmizi({"uretimler/x/a.txt": "x"}, "G6")

    def test_g7_kalite_sabiti(self):
        self.kirmizi({"rakkase.py": '"""x"""\n'}, "G7")
        kod, cikti = kos({"rakkase.py": '"""turbo 8 adim, fp32"""\n'})
        self.assertEqual(kod, 0, cikti)


if __name__ == "__main__":
    unittest.main()
