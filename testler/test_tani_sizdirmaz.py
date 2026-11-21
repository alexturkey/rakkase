"""scripts/tani.ps1 sizdirmazlik yoklamasi (Windows PowerShell 5.1, ag yok). Sahte kullanici/makine adi + sahte sirlar; ham halleri
hicbir cikti bicimde (metin, -Json, -KartSatiri, -Cikti dosyasi; UTF-8/UTF-16/ANSI/JSON-kacisli) gecmemeli. Gercek kullanici adi da.
Suzgec 'kaba desen'dir (tani.ps1 basligi): bu test bilinen siniflari kilitler, 'mutlak gizlilik' iddiasi degildir.
Calistir (kokten):  python -B -m unittest testler/test_tani_sizdirmaz.py -v"""
import getpass
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PS = shutil.which("powershell") or "powershell.exe"
AD = "Test Kullan" + chr(0x131) + "c" + chr(0x131) + " " + chr(0xC7)       # Test Kullanıcı Ç
MAKINE = "TESTMAKINE-07"
POSTA = "test.kullanici" + chr(64) + "ornek.net"
SIRLAR = ["ghp_" + ("A1b2C3d4" * 5)[:36], "hf_" + "Zy9Xw8Vu" * 4, "sk-" + "Qq1Ww2Ee" * 4, "Bearer " + "abcDEF123456" * 3]
DIGER = "musteri" + "_proje_gizli"
BS = chr(92)


def log_metni():
    s = []
    s.append("Traceback ... File " + '"C:' + BS + "Users" + BS + AD + BS + "Desktop" + BS + "rk" + BS + "x.py" + '"')
    s.append("path2 C:/" + "Us" + "ers/" + AD + "/Desktop/rk/y.py")
    s.append('json "C:' + BS * 2 + "Users" + BS * 2 + AD + BS * 2 + 'x" and ' + "u-escaped: Test Kullan" + BS + "u0131c" + BS + "u0131 " + BS + "u00c7")
    s.append("short TESTKU~1 and home %USERPROFILE%" + BS + "rk")
    s.append("mail " + POSTA + " host " + MAKINE)
    s.append("tokens: " + " ; ".join(SIRLAR))
    s.append("drive D:" + BS + DIGER + BS + "a.wav and unc " + BS * 2 + "sunucu" + BS + "pay" + BS + DIGER)
    s.append("HATA: [RK-E-DISK] bos yer yetmiyor")
    return "\n".join(s) + "\n"


def tehlikeli():
    ham = [AD, MAKINE, POSTA, DIGER, "TESTKU~1", "Test Kullan" + chr(0x131) + "c", "Test Kullan" + BS + "u0131c" + BS + "u0131", "u0131c" + BS + "u0131 "]
    ham += SIRLAR[:3] + ["A1b2C3d4A1b2", "Zy9Xw8VuZy9X", "Qq1Ww2EeQq1W", "abcDEF123456abcDEF"]
    ham += [getpass.getuser(), "ALEX25" + "~1"]
    return [h for h in ham if len(h) >= 5]


@unittest.skipUnless(sys.platform == "win32", "Windows PowerShell 5.1 gerekir")
class Tani(unittest.TestCase):
    def kos(self, ek=(), log_bayt=None):
        with tempfile.TemporaryDirectory(dir=("E:/t/rk_denetci" if os.path.isdir("E:/t/rk_denetci") else None)) as t:
            k = os.path.join(t, "rk")
            os.makedirs(os.path.join(k, "scripts")); os.makedirs(os.path.join(k, "docs"))
            for f in ("tani.ps1", "kur.ps1", "modeller.json"):
                shutil.copy(os.path.join(KOK, "scripts", f), os.path.join(k, "scripts"))
            shutil.copy(os.path.join(KOK, "docs", "hata_imzalari.json"), os.path.join(k, "docs"))
            shutil.copy(os.path.join(KOK, "rakkase.py"), k)
            logy = os.path.join(t, "log.txt")
            with open(logy, "wb") as f:
                f.write(log_bayt)
            cikti = os.path.join(t, "rapor.txt")
            env = dict(os.environ)
            env.update(USERNAME=AD, COMPUTERNAME=MAKINE, USERPROFILE="C:" + BS + "Users" + BS + AD, USERDOMAIN=MAKINE)
            r = subprocess.run([PS, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(k, "scripts", "tani.ps1"),
                                "-Log", logy, "-Cikti", cikti, *ek], capture_output=True, env=env, timeout=180)
            dosya = open(cikti, "rb").read() if os.path.exists(cikti) else b""
            return r.returncode, r.stdout + r.stderr + b"\n----\n" + dosya

    def kontrol(self, kod, ham_bayt):
        self.assertEqual(kod, 0, ham_bayt[:600])
        # her olasi kodlamada ara: UTF-8, UTF-16LE, UTF-16BE, cp1254
        govde = ham_bayt
        metinler = [govde.decode("utf-8", "replace"), govde.decode("utf-16-le", "replace"), govde.decode("cp1254", "replace")]
        bulunan = []
        for h in tehlikeli():
            for m in metinler:
                if h.lower() in m.lower():
                    bulunan.append(h)
        # UTF-16 / UTF-8 bayt dizisi olarak da
        for h in tehlikeli():
            for enc in ("utf-8", "utf-16-le", "utf-16-be", "cp1254"):
                try:
                    if h.lower().encode(enc) in govde.lower():
                        bulunan.append(h)
                except UnicodeEncodeError:
                    pass
        self.assertEqual(sorted(set(bulunan)), [], "sizinti: " + repr(sorted(set(bulunan))))
        return govde

    def test_utf8_log(self):
        kod, c = self.kos(log_bayt=log_metni().encode("utf-8"))
        self.kontrol(kod, c)

    def test_utf16_log(self):
        kod, c = self.kos(log_bayt=b"\xff\xfe" + log_metni().encode("utf-16-le"))
        self.kontrol(kod, c)

    def test_ansi_log(self):
        kod, c = self.kos(log_bayt=log_metni().encode("cp1254", "replace"))
        self.kontrol(kod, c)

    def test_json_bicimi(self):
        kod, c = self.kos(ek=("-Json",), log_bayt=log_metni().encode("utf-8"))
        self.kontrol(kod, c)

    def test_kart_satiri(self):
        kod, c = self.kos(ek=("-KartSatiri",), log_bayt=log_metni().encode("utf-8"))
        self.kontrol(kod, c)

    def test_hata_kodu_eslesir(self):
        kod, c = self.kos(log_bayt=log_metni().encode("utf-8"))
        self.assertIn(b"RK-E-DISK", c)

    def test_ag_yok_kendiliginden_gondermez(self):
        # betikte ag cagrisi (Invoke-WebRequest, WebClient, HttpWebRequest, Invoke-RestMethod, curl) bulunmamali
        icerik = open(os.path.join(KOK, "scripts", "tani.ps1"), encoding="utf-8").read().lower()
        for yasak in ("invoke-webrequest", "invoke-restmethod", "webclient", "httpwebrequest", "start-bitstransfer", "curl ", "iwr "):
            code_satirlari = [l for l in icerik.split("\n") if not l.lstrip().startswith("#") and yasak in l]
            self.assertEqual(code_satirlari, [], yasak)


if __name__ == "__main__":
    unittest.main()
