"""scripts/tani.ps1 DEVIATIONS section (kit KL-23): names of RK_* variables only, never values; writes nothing. No network, no GPU.
Run (from the root): python -B -m unittest testler/test_tani_sapma.py -v"""
import os
import shutil
import subprocess
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PS = shutil.which("powershell") or "powershell.exe"
TANI = os.path.join(KOK, "scripts", "tani.ps1")


def kos(env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    p = subprocess.run([PS, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", TANI], capture_output=True, env=env, timeout=180)
    return p.returncode, p.stdout.decode("utf-8", "replace")


class Sapma(unittest.TestCase):
    def test_bolum_var_ad_gorunur_deger_gizli(self):
        deger = "gizli" + "Deger" + "12345"
        kod, c = kos({"RK_TEST_EZME": deger})
        self.assertEqual(kod, 0, c[-300:])
        self.assertIn("deviations / sapma", c)
        self.assertIn("RK_TEST_EZME", c)
        self.assertNotIn(deger, c)

    def test_ps1_yalniz_ascii(self):
        with open(TANI, "rb") as f:
            self.assertTrue(all(b < 128 for b in f.read()), "Windows PowerShell 5.1 icin tani.ps1 ASCII kalmali")


if __name__ == "__main__":
    unittest.main()
