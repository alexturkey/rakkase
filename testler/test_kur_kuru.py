"""scripts/kur.ps1 -Kuru ve kontrol0 sahte ortam matrisi (Windows PowerShell 5.1; ag, indirme, kurulum YOK).
Her dal: kasitli kotu ortam -> beklenen HATA kodu ve cikis kodu; iyi ortam -> 0. -Kuru hicbir dosya olusturmaz/degistirmez.
Calistir (kokten):  python -B -m unittest testler/test_kur_kuru.py -v"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PS = shutil.which("powershell") or "powershell.exe"
IYI = "ram=16;bos_ram=8;disk=60;gpu=NVIDIA GeForce GTX 1050 Ti;vram=4096;cc=6.1"  # git/uv anahtari YOKSA gercek PATH/RK_UV kullanilir; anahtar VARSA (deger ne olursa) yok sayilir


def agac(d):
    s = {}
    for r, _, fs in os.walk(d):
        for f in fs:
            p = os.path.join(r, f)
            s[os.path.relpath(p, d)] = (os.path.getsize(p), os.path.getmtime(p))
    return s


BOM_BAYT = bytes([0xEF, 0xBB, 0xBF])


@unittest.skipUnless(sys.platform == "win32", "Windows PowerShell 5.1 gerekir")
class KurKuru(unittest.TestCase):
    def kos(self, sahte, bayrak=("-Kuru",), ayar=None, hazirla=None, ace_ac=True, kok_ad="rk"):
        with tempfile.TemporaryDirectory() as t:
            k = os.path.join(t, kok_ad)
            os.makedirs(os.path.join(k, "scripts"))
            for f in ("kur.ps1", "modeller.json"):
                shutil.copy(os.path.join(KOK, "scripts", f), os.path.join(k, "scripts"))
            ace = os.path.join(t, "ace")
            if ace_ac is not None:
                os.makedirs(ace)
            if ayar is not None:
                with open(os.path.join(k, "ayarlar.json"), "wb") as f:
                    f.write(ayar if isinstance(ayar, bytes) else ayar.encode("utf-8"))
            if hazirla:
                hazirla(k, ace)
            once = agac(t)
            env = dict(os.environ)
            env.pop("RK_ACE_KOK", None)
            env["RK_KURU_SAHTE"] = sahte
            env["RK_UV"] = sys.executable  # uv yerine var olan bir dosya: yalniz Test-Path (kuru kosuda calistirilmaz)
            r = subprocess.run([PS, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(k, "scripts", "kur.ps1"),
                                "-AceKok", ace, *bayrak], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)
            self.assertEqual(once, agac(t), "-Kuru dosya olusturdu/degistirdi")
            return r.returncode, r.stdout + r.stderr

    def test_iyi_ortam(self):
        kod, c = self.kos(IYI)
        self.assertEqual(kod, 0, c)
        self.assertIn("KURU TAMAM", c)
        self.assertNotIn("HATA:", c)

    def test_tek_tek_hatalar(self):
        # (sahte ortam degisimi, beklenen kod, beklenen cikis)
        for degis, kod_beklenen, cikis in (
            ("ram=8", "RK-E-RAM", 3), ("disk=10", "RK-E-DISK", 3), ("gpu=yok", "RK-E-GPU", 3),
            ("vram=3000", "RK-E-GPU-VRAM", 3), ("cc=5.2", "RK-E-GPU-VRAM", 3), ("git=yok", "RK-E-GIT", 2), ("uv=yok", "RK-E-UV", 2),
        ):
            with self.subTest(degis=degis):
                d = dict(kv.split("=", 1) for kv in IYI.split(";"))
                d.update([degis.split("=", 1)])
                kod, c = self.kos(";".join(f"{a}={b}" for a, b in d.items()))
                self.assertEqual(kod, cikis, c)
                self.assertIn(f"HATA: [{kod_beklenen}]", c)

    def test_hepsi_bir_arada_tek_liste(self):
        kod, c = self.kos("ram=8;disk=10;gpu=yok;vram=3000;git=yok;uv=yok")
        self.assertEqual(kod, 3, c)
        for k in ("RK-E-RAM", "RK-E-DISK", "RK-E-GPU", "RK-E-GIT", "RK-E-UV"):
            self.assertIn(f"[{k}]", c)

    def test_ram_12_ile_16_arasi_uyari(self):
        d = IYI.replace("ram=16", "ram=14")
        kod, c = self.kos(d)
        self.assertEqual(kod, 0, c)
        self.assertIn("RK-W-RAM", c)

    def test_baska_gpu_uyari(self):
        kod, c = self.kos(IYI.replace("NVIDIA GeForce GTX 1050 Ti", "NVIDIA GeForce RTX 3060"))
        self.assertEqual(kod, 0, c)
        if "GPU: NVIDIA GeForce RTX 3060" not in c:
            self.skipTest("bu makinede nvidia-smi var: sahte GPU adi yalniz nvidia-smi yokken uygulanir (kur.ps1 test kancasi siniri)")
        self.assertIn("RK-W-GPU-DENENMEDI", c)

    def test_bozuk_ayar_cikis_2_ve_dokunmaz(self):
        kod, c = self.kos(IYI, ayar=b"{bozuk")
        self.assertEqual(kod, 2, c)
        self.assertIn("RK-E-AYAR", c)

    def test_ayar_bom_ve_turkce_gecerli(self):
        kod, c = self.kos(IYI, ayar=b"\xef\xbb\xbf" + json.dumps({"not": "\u0130\u015f\u011f\u00fc"}).encode("utf-8"))
        self.assertEqual(kod, 0, c)

    def test_dolu_ama_ace_degil(self):
        def h(k, ace):
            open(os.path.join(ace, "baska.txt"), "w").close()
        kod, c = self.kos(IYI, hazirla=h)
        self.assertEqual(kod, 1, c)
        self.assertIn("RK-E-KLON", c)

    def test_yol_uyarilari(self):
        kod, c = self.kos(IYI, kok_ad="bosluklu T\u00fcrk\u00e7e OneDrive yol")
        self.assertEqual(kod, 0, c)
        for k in ("RK-W-YOL-BOSLUK", "RK-W-YOL-ASCII", "RK-W-YOL-ONEDRIVE"):
            self.assertIn(k, c)

    def test_sahte_kuru_disinda_yok_sayilir(self):
        # -Kuru verilmeden sahte olcum kullanilmaz; yalniz okuyan 'kontrol0' adimi (hicbir sey yazmaz/indirmez)
        kod, c = self.kos("ram=1;disk=1;gpu=yok;git=yok;uv=yok", bayrak=("-Adim", "kontrol0"))
        self.assertNotIn("SAHTE OLCUM", c)

    def test_hata_kodlari_haritada(self):
        # kur.ps1'in basabildigi her RK- kodu docs/hata_imzalari.json'da tanimli olmali (tek harita)
        with open(os.path.join(KOK, "docs", "hata_imzalari.json"), encoding="utf-8") as f:
            harita = json.load(f)
        metin = json.dumps(harita)
        with open(os.path.join(KOK, "scripts", "kur.ps1"), encoding="utf-8") as f:
            kur = f.read()
        import re
        kodlar = set(re.findall(r"RK-[EW]-[A-Z0-9-]+", kur))
        eksik = [k for k in sorted(kodlar) if k not in metin]
        self.assertEqual(eksik, [], f"hata_imzalari.json'da yok: {eksik}")


def _yer_var():
    """-Adim ayar da donanim/disk kapisindan gecer (kontrol0 her zaman kosar): gercek GPU ve >= 25 GiB bos disk gerekir."""
    if not shutil.which("nvidia-smi"):
        return None
    for taban in (os.environ.get("RK_TEST_TMP"), "E:/t/rk_denetci", tempfile.gettempdir()):
        if taban and os.path.isdir(taban) and shutil.disk_usage(taban).free > 25 * 1024 ** 3:
            return taban
    return None


@unittest.skipUnless(_yer_var(), "gercek NVIDIA GPU ve >= 25 GiB bos disk yok (kontrol0 sahte olcumle calismaz)")
class KurAyar(unittest.TestCase):
    """kur.ps1 -Adim ayar: var olan ayarlar.json'u EZMEME, yer tutucuyu doldurma, bozuk dosyaya dokunmama."""

    def kos(self, ayar, ace_ad="ace"):
        with tempfile.TemporaryDirectory(dir=_yer_var()) as t:
            k = os.path.join(t, "rk")
            os.makedirs(os.path.join(k, "scripts"))
            for f in ("kur.ps1", "modeller.json"):
                shutil.copy(os.path.join(KOK, "scripts", f), os.path.join(k, "scripts"))
            yol = os.path.join(k, "ayarlar.json")
            if ayar is not None:
                with open(yol, "wb") as f:
                    f.write(ayar if isinstance(ayar, bytes) else json.dumps(ayar).encode("utf-8"))
            ace = os.path.join(t, ace_ad)
            env = dict(os.environ)
            env["RK_UV"] = sys.executable
            env.pop("RK_ACE_KOK", None)
            r = subprocess.run([PS, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(k, "scripts", "kur.ps1"),
                                "-Adim", "ayar", "-AceKok", ace], capture_output=True, text=True, encoding="utf-8", errors="replace",
                               env=env, timeout=120)
            ham = open(yol, "rb").read() if os.path.exists(yol) else None
            return r.returncode, r.stdout + r.stderr, ham, ace

    def test_yok_ise_yazar_kisisel_alan_yok(self):
        kod, c, ham, ace = self.kos(None)
        self.assertEqual(kod, 0, c)
        d = json.loads(ham.decode("utf-8"))
        self.assertEqual(d["ace_kok"], ace.replace(os.sep, "/"))
        self.assertIs(d["kilit"], False)
        self.assertEqual(d["kilit_src"], "")
        self.assertFalse(ham.startswith(b"\xef\xbb\xbf"), "BOM yazilmamali")

    def test_yer_tutucu_doldurulur_digerleri_korunur(self):
        kod, c, ham, ace = self.kos({"ace_kok": "<ACE_KOK: buraya>", "venv": "X:/benim/venv", "not": "\u0130\u015f"})
        self.assertEqual(kod, 0, c)
        d = json.loads(ham.decode("utf-8"))
        self.assertEqual(d["ace_kok"], ace.replace(os.sep, "/"))
        self.assertEqual(d["venv"], "X:/benim/venv")
        self.assertEqual(d["not"], "\u0130\u015f")

    def test_farkli_ace_kok_ezilmez(self):
        kod, c, ham, ace = self.kos({"ace_kok": "Z:/baska/ace", "kilit": True, "kilit_src": "Q:/benim/src"})
        self.assertEqual(kod, 0, c)
        self.assertIn("RK-W-AYAR-FARKLI", c)
        d = json.loads(ham.decode("utf-8"))
        self.assertEqual(d["ace_kok"], "Z:/baska/ace")
        self.assertIs(d["kilit"], True)
        self.assertEqual(d["kilit_src"], "Q:/benim/src")

    def test_ayni_ace_kok_zaten_dogru(self):
        with tempfile.TemporaryDirectory(dir=_yer_var()) as t:
            ace = os.path.join(t, "ace").replace(os.sep, "/")
        kod, c, ham, _ = self.kos({"ace_kok": ace})  # farkli gecici klasor: FARKLI uyarisi beklenir (yol ayni degil)
        self.assertEqual(kod, 0, c)

    def test_bozuk_json_cikis_2_dokunulmaz(self):
        kod, c, ham, _ = self.kos(b"{bozuk")
        self.assertEqual(kod, 2, c)
        self.assertEqual(ham, b"{bozuk")

    def test_bom_li_dosya_okunur(self):
        kod, c, ham, ace = self.kos(BOM_BAYT + json.dumps({"ace_kok": "", "not": "\u00e7"}).encode("utf-8"))
        self.assertEqual(kod, 0, c)
        d = json.loads(ham.decode("utf-8"))
        self.assertEqual(d["not"], "\u00e7")
        self.assertEqual(d["ace_kok"], ace.replace(os.sep, "/"))


if __name__ == "__main__":
    unittest.main()
