"""kur.ps1 -Kuru: hazir komut onerileri (winget git/uv, en bos surucu icin -AceKok) ve HAZIR satirinin venv python tam yolu.
Ag, indirme, kurulum YOK; -Kuru hicbir dosya yazmaz (sahte olcum RK_KURU_SAHTE). Betik komutu KENDISI calistirmaz, yalniz basar.
Calistir (kokten):  python -B -m unittest testler/test_kur_oneri.py -v"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PS = shutil.which("powershell") or "powershell.exe"
IYI = "ram=16;bos_ram=8;disk=60;gpu=NVIDIA GeForce GTX 1050 Ti;vram=4096;cc=6.1"
BS = "\\"


@unittest.skipUnless(sys.platform == "win32", "Windows PowerShell 5.1 gerekir")
class KurOneri(unittest.TestCase):
    def kos(self, sahte):
        with tempfile.TemporaryDirectory() as t:
            k = os.path.join(t, "rk")
            os.makedirs(os.path.join(k, "scripts"))
            for f in ("kur.ps1", "modeller.json"):
                shutil.copy(os.path.join(KOK, "scripts", f), os.path.join(k, "scripts"))
            ace = os.path.join(t, "ace")
            os.makedirs(ace)
            env = dict(os.environ, RK_KURU_SAHTE=sahte, RK_UV=sys.executable)
            env.pop("RK_ACE_KOK", None)
            r = subprocess.run([PS, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(k, "scripts", "kur.ps1"), "-Kuru", "-AceKok", ace],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)
            return r.returncode, r.stdout + r.stderr, ace

    def test_git_uv_yok_hazir_winget_satiri(self):
        kod, c, _ = self.kos(IYI + ";git=yok;uv=yok")
        self.assertEqual(kod, 2, c)
        self.assertIn("HAZIR KOMUT", c)
        self.assertIn("  winget install --id Git.Git -e", c)
        self.assertIn("  winget install --id=astral-sh.uv -e", c)

    def test_yalniz_uv_yok_yalniz_uv_satiri(self):
        kod, c, _ = self.kos(IYI + ";uv=yok")
        self.assertEqual(kod, 2, c)
        self.assertIn("  winget install --id=astral-sh.uv -e", c)
        self.assertNotIn("  winget install --id Git.Git -e", c)

    def test_iyi_ortamda_oneri_yok(self):
        kod, c, _ = self.kos(IYI)
        self.assertEqual(kod, 0, c)
        self.assertNotIn("HAZIR KOMUT", c)

    def test_disk_yetmez_en_bos_surucu_onerilir(self):
        # X: en bos, Y: ikinci; kurulum surucusu (gecici klasorun surucusu) elenir. Kesin yol onerisi: <S>:\rk\ace_step
        kod, c, _ = self.kos(IYI.replace("disk=60", "disk=10") + ";suruculer=X:500,Y:40")
        self.assertEqual(kod, 3, c)
        self.assertIn("[RK-E-DISK]", c)
        self.assertIn("kur.cmd -AceKok X:" + BS + "rk" + BS + "ace_step", c)
        self.assertNotIn("-AceKok Y:", c)

    def test_disk_yetmez_hicbir_surucu_yeterli_degil_oneri_yok(self):
        kod, c, _ = self.kos(IYI.replace("disk=60", "disk=10") + ";suruculer=X:12,Y:20")
        self.assertEqual(kod, 3, c)
        self.assertNotIn("-AceKok X:", c)
        self.assertNotIn("-AceKok Y:", c)

    def test_disk_yeterliyse_surucu_onerisi_yok(self):
        kod, c, _ = self.kos(IYI + ";suruculer=X:500")
        self.assertEqual(kod, 0, c)
        self.assertNotIn("-AceKok X:", c)

    def test_hazir_satiri_venv_python_tam_yolu(self):
        kod, c, ace = self.kos(IYI)
        self.assertEqual(kod, 0, c)
        py = os.path.join(os.path.realpath(ace), ".venv", "Scripts", "python.exe")   # betik uzun yolu basar (8.3 kisa ad degil)
        self.assertIn('"' + py + '" -X utf8 rakkase.py test', c)
        self.assertIn('"' + py + '" -X utf8 rakkase.py uret --plan', c)
        self.assertIn("sistem Python gerekmez", c)
        self.assertIn("cikis 7", c)


if __name__ == "__main__":
    unittest.main()
