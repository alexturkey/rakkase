"""scripts/modelleri_indir.ps1 guvenlik yoklamasi (Windows PowerShell 5.1, sahte yerel sunucu, ag ve model yok).
Her kotu girdi KIRMIZI (cikis 1 + HATA satiri), iyi girdi yesil. Calistir (kokten):  python -B -m unittest testler/test_indirici_guvenlik.py -v
Sunucu yalniz 127.0.0.1; RK_URL_TABAN test kancasi indiriciye 'https://huggingface.co' yerine bunu verir.
Kopya klasor: indirici kendi kopyasindan calisir, depoya yazmaz."""
import hashlib
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PS = shutil.which("powershell") or "powershell.exe"
REV = "a" * 40
ICERIK = b"rakkase-test-" * 100  # 1300 bayt
SHA = hashlib.sha256(ICERIK).hexdigest()


class Sunucu(http.server.BaseHTTPRequestHandler):
    sayac = {"istek": 0}

    def log_message(self, *a):
        pass

    def do_GET(self):
        Sunucu.sayac["istek"] += 1
        yol = self.path
        ara = yol.split("/resolve/" + REV + "/", 1)[-1]
        if ara.startswith("yonlen_dis"):
            self.send_response(302); self.send_header("Location", "https://evil.example.invalid/x"); self.end_headers(); return
        if ara.startswith("yonlen_http"):
            self.send_response(302); self.send_header("Location", "http://huggingface.co.example.invalid/x"); self.end_headers(); return
        if ara.startswith("yonlen_icerde"):
            self.send_response(302); self.send_header("Location", yol.replace("yonlen_icerde", "iyi")); self.end_headers(); return
        if ara.startswith("dongu"):
            self.send_response(302); self.send_header("Location", yol); self.end_headers(); return
        govde = ICERIK
        if ara.startswith("yanlis"):
            govde = b"x" * len(ICERIK)
        if ara.startswith("fazla"):
            govde = ICERIK + b"Z" * (30 * 1024 * 1024)  # beklenenden cok veri
        if ara.startswith("kesik"):
            self.send_response(200); self.send_header("Content-Length", str(len(ICERIK))); self.end_headers()
            self.wfile.write(ICERIK[:500]); self.wfile.flush(); self.close_connection = True; return
        r = self.headers.get("Range")
        if r and ara.startswith("iyi"):
            bas = int(r.split("=")[1].split("-")[0])
            self.send_response(206); self.send_header("Content-Length", str(len(govde) - bas))
            self.send_header("Content-Range", f"bytes {bas}-{len(govde)-1}/{len(govde)}"); self.end_headers()
            self.wfile.write(govde[bas:]); return
        self.send_response(200); self.send_header("Content-Length", str(len(govde))); self.end_headers()
        try:
            self.wfile.write(govde)
        except OSError:
            pass


def girdi(hedef, sha=SHA, boyut=len(ICERIK), url=None):
    return {"hedef": hedef, "url": url or f"https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/{REV}/{hedef}",
            "sha256": sha, "boyut": boyut, "git_blob_sha1": "0" * 40}


@unittest.skipUnless(sys.platform == "win32", "Windows PowerShell 5.1 gerekir")
class Indirici(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Sunucu)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def kos(self, dosyalar, hazirla=None, bayrak=(), taban=True, revizyon=REV):
        with tempfile.TemporaryDirectory() as t:
            os.makedirs(os.path.join(t, "scripts"))
            shutil.copy(os.path.join(KOK, "scripts", "modelleri_indir.ps1"), os.path.join(t, "scripts"))
            tablo = {"surum": 1, "repo": "x", "revizyon": revizyon,
                     "izinli_konaklar": ["huggingface.co"], "izinli_konak_son_ekleri": [".hf.co"], "dosyalar": dosyalar}
            with open(os.path.join(t, "scripts", "modeller.json"), "w", encoding="utf-8") as f:
                json.dump(tablo, f)
            hedef = os.path.join(t, "ckpt")
            os.makedirs(hedef)
            if hazirla:
                hazirla(hedef)
            env = dict(os.environ)
            if taban:
                env["RK_URL_TABAN"] = f"http://127.0.0.1:{self.port}"
            r = subprocess.run([PS, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(t, "scripts", "modelleri_indir.ps1"),
                                "-Hedef", hedef, *bayrak], capture_output=True, text=True, env=env, timeout=120)
            icerik = {}
            for d, _, fs in os.walk(hedef):
                for f in fs:
                    icerik[os.path.relpath(os.path.join(d, f), hedef).replace(os.sep, "/")] = os.path.getsize(os.path.join(d, f))
            return r.returncode, r.stdout + r.stderr, icerik

    def test_iyi_indirir_ve_dogrular(self):
        kod, cikti, ic = self.kos([girdi("iyi/a.bin")])
        self.assertEqual(kod, 0, cikti)
        self.assertEqual(ic, {"iyi/a.bin": len(ICERIK)})

    def test_zaten_var_atlar(self):
        def h(hedef):
            os.makedirs(os.path.join(hedef, "iyi")); open(os.path.join(hedef, "iyi", "a.bin"), "wb").write(ICERIK)
        n = Sunucu.sayac["istek"]
        kod, cikti, _ = self.kos([girdi("iyi/a.bin")], h)
        self.assertEqual(kod, 0, cikti)
        self.assertEqual(Sunucu.sayac["istek"], n, "var ve sha tutuyorsa ag istegi atilmamali")

    def test_izinli_olmayan_yonlendirme(self):
        kod, cikti, ic = self.kos([girdi("yonlen_dis/a.bin")])
        self.assertEqual(kod, 1, cikti)
        self.assertIn("izinli olmayan", cikti)
        self.assertEqual(ic, {})

    def test_http_yonlendirme_reddedilir(self):
        kod, cikti, ic = self.kos([girdi("yonlen_http/a.bin")])
        self.assertEqual(kod, 1, cikti)
        self.assertEqual(ic, {})

    def test_yonlendirme_dongusu(self):
        kod, cikti, ic = self.kos([girdi("dongu/a.bin")])
        self.assertEqual(kod, 1, cikti)
        self.assertIn("yonlendirme", cikti)

    def test_yanlis_sha_yerine_konmaz(self):
        kod, cikti, ic = self.kos([girdi("yanlis/a.bin")])
        self.assertEqual(kod, 1, cikti)
        self.assertNotIn("yanlis/a.bin", ic, "hash tutmayan dosya hedef adiyla durmamali")
        self.assertIn("sha256 tutmadi", cikti)

    def test_kesik_govde_part_korunur(self):
        kod, cikti, ic = self.kos([girdi("kesik/a.bin")])
        self.assertEqual(kod, 1, cikti)
        self.assertNotIn("kesik/a.bin", ic)
        self.assertIn("kesik/a.bin.part", ic)

    def test_range_200_donerse_bastan(self):
        # sunucu 'oyuncu/' icin Range'i yok sayar (200): .part'in ustune EKLENMEMELI, dosya dogru cikmali
        def h(hedef):
            os.makedirs(os.path.join(hedef, "oyuncu"))
            open(os.path.join(hedef, "oyuncu", "a.bin.part"), "wb").write(b"Q" * 400)
        kod, cikti, ic = self.kos([girdi("oyuncu/a.bin")], h)
        self.assertEqual(kod, 0, cikti)
        self.assertEqual(ic.get("oyuncu/a.bin"), len(ICERIK))

    def test_range_206_surer(self):
        def h(hedef):
            os.makedirs(os.path.join(hedef, "iyi"))
            open(os.path.join(hedef, "iyi", "a.bin.part"), "wb").write(ICERIK[:400])
        kod, cikti, ic = self.kos([girdi("iyi/a.bin")], h)
        self.assertEqual(kod, 0, cikti)
        self.assertEqual(ic.get("iyi/a.bin"), len(ICERIK))

    def test_fazla_veri_durdurulur(self):
        # beklenenden cok veri akitan sunucu diski doldurmamali: .part beklenen boyutun cok uzerine cikmamali
        kod, cikti, ic = self.kos([girdi("fazla/a.bin")])
        self.assertEqual(kod, 1, cikti)
        buyuk = [k for k, v in ic.items() if v > 10 * len(ICERIK)]
        self.assertEqual(buyuk, [], f"sinirsiz veri yazildi: {ic}")

    def test_yol_gecisi_tablosu(self):
        for kotu in ("../kacak.bin", "a/../../kacak.bin", "/mutlak.bin", "C:/kacak.bin", "a/b:ads.bin", "a\\..\\b.bin",
                     "//sunucu/pay/x.bin", "iyi/.gizli.bin", "NUL", "iyi/CON.txt", "iyi/a.bin."):
            with self.subTest(kotu=kotu):
                kod, cikti, ic = self.kos([girdi(kotu, url=f"https://huggingface.co/x/resolve/{REV}/iyi/a.bin")])
                self.assertEqual(kod, 1, f"{kotu!r} reddedilmedi: {cikti}")
                self.assertEqual(ic, {}, f"{kotu!r} dosya yazdi")

    def test_url_main_reddedilir(self):
        kod, cikti, _ = self.kos([girdi("iyi/a.bin", url="https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/main/iyi/a.bin")])
        self.assertEqual(kod, 1, cikti)
        self.assertIn("main", cikti)

    def test_tablo_bozuk(self):
        for dosyalar in ([], [{"hedef": "iyi/a.bin"}], [girdi("iyi/a.bin", sha="zz")], [girdi("iyi/a.bin", sha=SHA.upper())]):
            with self.subTest(dosyalar=str(dosyalar)[:40]):
                kod, cikti, ic = self.kos(dosyalar)
                self.assertEqual(kod, 1, cikti)
                self.assertEqual(ic, {})

    def test_kuru_yazmaz_ag_kullanmaz(self):
        n = Sunucu.sayac["istek"]
        kod, cikti, ic = self.kos([girdi("iyi/a.bin")], bayrak=("-Kuru",))
        self.assertEqual(kod, 0, cikti)
        self.assertEqual(ic, {})
        self.assertEqual(Sunucu.sayac["istek"], n)

    def test_hedef_disina_yazmaz_ve_yer_tutucu_bos_hedef(self):
        with tempfile.TemporaryDirectory() as t:
            r = subprocess.run([PS, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(KOK, "scripts", "modelleri_indir.ps1")],
                               capture_output=True, text=True, timeout=60, cwd=t)
            self.assertEqual(r.returncode, 1)
            self.assertIn("RK-E-INDIR", r.stdout)

    def test_test_kancasi_yoksa_gercek_konak_disi_yok(self):
        # RK_URL_TABAN verilmeden sahte sunucuya gidilmez: 127.0.0.1 izinli degildir (varsayilan ag yolu kapali)
        kod, cikti, ic = self.kos([girdi("iyi/a.bin", url=f"http://127.0.0.1:{self.port}/resolve/{REV}/iyi/a.bin")], taban=False)
        self.assertEqual(kod, 1, cikti)
        self.assertEqual(ic, {})


if __name__ == "__main__":
    unittest.main()
