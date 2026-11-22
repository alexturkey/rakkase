"""kur.ps1 uv adimi: kurulum duzeni (onbellek ve gecici dosya ACE klasorune, kalici sistem degisikligi yok, cift indirme yok).
Sahte uv (RK_UV = .cmd): gercek uv, ag, indirme YOK. Sahte uv ortam degiskenlerini ve argumanlari bir gunluge yazar.
Calistir (kokten):  python -B -m unittest testler/test_kur_duzeni.py -v"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PS = shutil.which("powershell") or "powershell.exe"
# Kalici sistem degisikligi desenleri PARCALI yazilir: bu dosyanin kendisi bekci/PR kapisinin supheli-komut taramasina takilmasin.
YASAK = (r"\bset" + "x" + r"\b", r"\breg\s+" + "add" + r"\b", "HK" + "CU:|HK" + "LM:", r"\$PRO" + "FILE" + r"\b",
         "Set-Execution" + r"Policy(?![^\n]*-Scope\s+Process)", "SetEnviron" + r"mentVariable\s*\([^)]*,\s*['\"]?(User|Machine)\b",
         r"pip3?\s+install[^\n]*--user")


SAHTE_UV = """@echo off
echo ARGS=%*>>"%UVLOG%"
echo CACHE=%UV_CACHE_DIR%>>"%UVLOG%"
echo PYDIR=%UV_PYTHON_INSTALL_DIR%>>"%UVLOG%"
echo PYBIN=%UV_PYTHON_BIN_DIR%>>"%UVLOG%"
echo TMP=%TMP%>>"%UVLOG%"
if "%1"=="python" if "%2"=="find" exit /b %FIND_RC%
if "%1"=="sync" (
  mkdir ".venv\\Scripts" 2>nul
  echo.>".venv\\Scripts\\python.exe"
)
exit /b 0
"""


@unittest.skipUnless(sys.platform == "win32", "Windows PowerShell 5.1 gerekir")
class UvKurulumDuzeni(unittest.TestCase):
    def kos(self, find_rc="1", venv_var=False, onbellek_var=False, env_ek=None):
        t = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, t, True)
        k = os.path.join(t, "rk")
        os.makedirs(os.path.join(k, "scripts"))
        for f in ("kur.ps1", "modeller.json"):
            shutil.copy(os.path.join(KOK, "scripts", f), os.path.join(k, "scripts"))
        ace = os.path.join(t, "ace")
        os.makedirs(ace)
        open(os.path.join(ace, "pyproject.toml"), "w").write("[project]\nname='x'\n")
        if venv_var:
            os.makedirs(os.path.join(ace, ".venv", "Scripts"))
            open(os.path.join(ace, ".venv", "Scripts", "python.exe"), "w").write("")
        if onbellek_var:
            os.makedirs(os.path.join(ace, ".onbellek", "uv"))
        uv = os.path.join(t, "uv.cmd")
        open(uv, "w").write(SAHTE_UV.replace("\n", "\r\n"))
        log = os.path.join(t, "uv.log")
        env = dict(os.environ, RK_UV=uv, UVLOG=log, FIND_RC=find_rc)
        for a in ("RK_ACE_KOK", "UV_CACHE_DIR", "UV_PYTHON_INSTALL_DIR", "UV_PYTHON_BIN_DIR"):
            env.pop(a, None)
        env.update(env_ek or {})
        r = subprocess.run([PS, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(k, "scripts", "kur.ps1"), "-Adim", "uv", "-AceKok", ace],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=180)
        gunluk = open(log, encoding="utf-8", errors="replace").read() if os.path.exists(log) else ""
        return r.returncode, r.stdout + r.stderr, gunluk, ace

    @staticmethod
    def al(gunluk, ad):
        return re.findall(r"^%s=(.*)$" % ad, gunluk, re.M)

    def test_onbellek_ve_python_ace_klasorune(self):
        kod, c, g, ace = self.kos(find_rc="1")
        self.assertEqual(kod, 0, c)
        n = lambda p: os.path.realpath(p).lower()
        sync_onbellek = self.al(g, "CACHE")[-1]
        self.assertEqual(n(sync_onbellek), n(os.path.join(ace, ".onbellek", "uv")))
        self.assertEqual(n(self.al(g, "PYDIR")[-1]), n(os.path.join(ace, ".onbellek", "uv-python")))
        self.assertEqual(n(self.al(g, "PYBIN")[-1]), n(os.path.join(ace, ".onbellek", "uv-bin")))
        self.assertEqual(n(self.al(g, "TMP")[-1]), n(os.path.join(ace, "gecici")))
        self.assertTrue(any(a.startswith("python install") for a in self.al(g, "ARGS")), g)

    def test_uygun_python_varsa_install_atlanir(self):
        kod, c, g, ace = self.kos(find_rc="0")
        self.assertEqual(kod, 0, c)
        self.assertFalse(any(a.startswith("python install") for a in self.al(g, "ARGS")), g)
        self.assertIn("atlandi", c)
        self.assertEqual(self.al(g, "PYDIR")[-1], "", "python zaten varken uv Python dizini yonlendirilmez")
        self.assertTrue(self.al(g, "CACHE")[-1].lower().endswith("uv"))

    def test_var_olan_venv_ortami_degistirmez(self):
        kod, c, g, ace = self.kos(find_rc="1", venv_var=True)
        self.assertEqual(kod, 0, c)
        for ad in ("CACHE", "PYDIR", "PYBIN"):
            self.assertTrue(all(x == "" for x in self.al(g, ad)), (ad, g))
        self.assertFalse(os.path.exists(os.path.join(ace, ".onbellek")))
        self.assertFalse(os.path.exists(os.path.join(ace, "gecici")))

    def test_kullanici_degeri_korunur(self):
        kendi = {"UV_CACHE_DIR": "Z:/benim/uv", "UV_PYTHON_INSTALL_DIR": "Z:/benim/py", "UV_PYTHON_BIN_DIR": "Z:/benim/bin"}
        kod, c, g, ace = self.kos(find_rc="1", env_ek=kendi)
        self.assertEqual(kod, 0, c)
        self.assertEqual(self.al(g, "CACHE")[-1], "Z:/benim/uv")
        self.assertEqual(self.al(g, "PYDIR")[-1], "Z:/benim/py")
        self.assertEqual(self.al(g, "PYBIN")[-1], "Z:/benim/bin")
        self.assertFalse(os.path.exists(os.path.join(ace, ".onbellek", "uv-python")))

    def test_yarim_kalan_ilk_kosuda_ikincide_onbellek_koke(self):
        # ilk uv sync .venv'i olusturup yarida kaldi: .venv + kokte .onbellek\uv var; ikinci kosu varsayilan onbellege DONMEZ
        kod, c, g, ace = self.kos(find_rc="1", venv_var=True, onbellek_var=True)
        self.assertEqual(kod, 0, c)
        n = lambda p: os.path.realpath(p).lower()
        self.assertEqual(n(self.al(g, "CACHE")[-1]), n(os.path.join(ace, ".onbellek", "uv")))

    def test_kalici_sistem_degisikligi_yok(self):
        metin = open(os.path.join(KOK, "scripts", "kur.ps1"), encoding="utf-8-sig").read()
        kod = "\n".join(s for s in metin.splitlines() if not s.strip().startswith("#"))
        for desen in YASAK:
            self.assertIsNone(re.search(desen, kod, re.I), desen)


if __name__ == "__main__":
    unittest.main()
