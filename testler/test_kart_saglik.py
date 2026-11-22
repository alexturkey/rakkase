"""Kart kurallari, kart-bagimsiz saglik olcumu, `rakkase.py test` karar agaci ve RK-E-NAN (CPU, GPU/model/ag YOK).
Neden: referans wav yalniz GTX 1050 Ti'de bayt-yakin cikar (issue #1); baska kartta referans KALDI = "bayt uyumu kanitlanmadi", kurulum bozuk degil.
Kalite esikleri (SNR > 40 dB, korelasyon > 0,999) DEGISMEZ; bu test yalniz karar agacinin dallarini ve olcumlerin dogrulugunu yoklar.
Calistir (kokten):  python -B -m unittest testler/test_kart_saglik.py -v    Gerekli: numpy, soundfile (yoksa saglik testleri atlanir)."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "motor"))
import kart_kural  # noqa: E402

try:
    import numpy as np
    import soundfile as sf
    BAGIMLI = True
except ImportError:
    BAGIMLI = False


class KartKurali(unittest.TestCase):
    def test_referans_karti(self):
        self.assertTrue(kart_kural.referans_karti("NVIDIA GeForce GTX 1050 Ti"))
        self.assertTrue(kart_kural.referans_karti("nvidia geforce gtx 1050 ti"))
        for ad in ("NVIDIA GeForce GTX 1050", "NVIDIA GeForce GTX 1650", "NVIDIA GeForce GTX 1060 6GB", "NVIDIA GeForce RTX 3060", "", None):
            self.assertFalse(kart_kural.referans_karti(ad), ad)

    def test_vae_fp32_karta_gore(self):
        # 1050 Ti ve benzerlerinde varsayilan davranis DEGISMEZ (False); yalniz GTX 16xx True
        for ad in ("NVIDIA GeForce GTX 1650", "NVIDIA GeForce GTX 1660 Ti", "NVIDIA GeForce GTX 1650 with Max-Q Design", "NVIDIA GeForce GTX 1630"):
            self.assertTrue(kart_kural.vae_fp32_gerek(ad), ad)
        for ad in ("NVIDIA GeForce GTX 1050 Ti", "NVIDIA GeForce GTX 1060", "NVIDIA GeForce RTX 2060", "NVIDIA GeForce RTX 3050", "", None):
            self.assertFalse(kart_kural.vae_fp32_gerek(ad), ad)

    def test_vae_fp32_ayar_kazanir(self):
        self.assertTrue(kart_kural.vae_fp32_gerek("NVIDIA GeForce GTX 1050 Ti", True))
        self.assertFalse(kart_kural.vae_fp32_gerek("NVIDIA GeForce GTX 1650", False))
        self.assertTrue(kart_kural.vae_fp32_gerek("NVIDIA GeForce GTX 1650", None))

    def test_ayar_ornegi_null(self):
        with open(os.path.join(KOK, "ayarlar.ornek.json"), encoding="utf-8") as f:
            self.assertIn("vae_fp32", json.load(f))
            f.seek(0)
            self.assertIsNone(json.load(f)["vae_fp32"])

    def test_motor_yama_yalniz_kosullu(self):
        """VAE yamasi yalniz vae_fp32_gerek(...) True iken calisir (1050 Ti'de blok atlanir = bayt-ayni yol)."""
        with open(os.path.join(KOK, "motor", "dokum_muzik.py"), encoding="utf-8") as f:
            kaynak = f.read()
        i = kaynak.index("vae_fp32 = kart_kural.vae_fp32_gerek(")
        parca = kaynak[i:i + 600]
        self.assertIn("if vae_fp32:", parca)
        self.assertIn("dit._get_vae_dtype = lambda device=None: torch.float32", parca[parca.index("if vae_fp32:"):])
        self.assertEqual(kaynak.count("dit._get_vae_dtype = lambda device=None: torch.float32"), 1)


def ton(yol, sure=15.0, sr=44100, genlik=0.3, nan=False, tohum=0):
    rng = np.random.RandomState(tohum)
    t = np.arange(int(sure * sr)) / sr
    x = genlik * np.sin(2 * np.pi * 220 * t) + 0.1 * rng.randn(len(t)) * 0.05
    x = x.astype("float32")
    if nan:
        x[1000:2000] = np.nan
    sf.write(yol, np.stack([x, x], 1), sr, subtype="FLOAT")   # 32-bit float wav: NaN tasinabilir (PCM_16 NaN'i yutar)


@unittest.skipUnless(BAGIMLI, "numpy/soundfile yok")
class Saglik(unittest.TestCase):
    ARAC = os.path.join(KOK, "araclar", "saglik_muzik.py")

    def kos(self, *args):
        r = subprocess.run([sys.executable, "-X", "utf8", "-I", self.ARAC, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
        return r.returncode, r.stdout + r.stderr

    def setUp(self):
        self.t = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.t, True)

    def p(self, ad):
        return os.path.join(self.t, ad)

    def test_saglam(self):
        ton(self.p("a.wav"))
        kod, c = self.kos(self.p("a.wav"), "--beklenen-sn", "15")
        self.assertEqual(kod, 0, c)
        self.assertIn("SAGLAM", c)

    def test_nan_kod_3(self):
        ton(self.p("n.wav"), nan=True)
        kod, c = self.kos(self.p("n.wav"), "--beklenen-sn", "15")
        self.assertEqual(kod, 3, c)
        self.assertIn("NAN ", c)
        kod, c = self.kos(self.p("n.wav"), "--nan-bak")
        self.assertEqual(kod, 3, c)

    def test_nan_bak_temiz_ve_hizli(self):
        ton(self.p("a.wav"))
        kod, c = self.kos(self.p("a.wav"), "--nan-bak")
        self.assertEqual((kod, c.strip()), (0, ""), c)

    def test_sessiz_kaldi(self):
        sf.write(self.p("s.wav"), np.zeros((44100 * 15, 2), dtype="float32"), 44100)
        kod, c = self.kos(self.p("s.wav"), "--beklenen-sn", "15")
        self.assertEqual(kod, 4, c)
        self.assertIn("sessiz", c)

    def test_yarisi_sessiz_kaldi(self):
        ton(self.p("y.wav"))
        x, sr = sf.read(self.p("y.wav"), dtype="float32")
        x[: len(x) * 3 // 5] = 0
        sf.write(self.p("y.wav"), x, sr)
        kod, c = self.kos(self.p("y.wav"), "--beklenen-sn", "15")
        self.assertEqual(kod, 4, c)

    def test_sure_yanlis_kaldi(self):
        ton(self.p("k.wav"), sure=10.0)
        kod, c = self.kos(self.p("k.wav"), "--beklenen-sn", "15")
        self.assertEqual(kod, 4, c)
        self.assertIn("sure", c)

    def test_okunamayan_kod_5(self):
        with open(self.p("b.wav"), "wb") as f:
            f.write(b"bu wav degil")
        kod, c = self.kos(self.p("b.wav"))
        self.assertEqual(kod, 5, c)

    def test_iki_kosu_ayni(self):
        ton(self.p("a.wav"))
        shutil.copy(self.p("a.wav"), self.p("b.wav"))
        kod, c = self.kos(self.p("a.wav"), "--beklenen-sn", "15", "--ikinci", self.p("b.wav"))
        self.assertEqual(kod, 0, c)
        self.assertIn("tutarliligi", c)

    def test_iki_kosu_farkli_kaldi(self):
        ton(self.p("a.wav"), tohum=1)
        x, sr = sf.read(self.p("a.wav"), dtype="float32")
        gurultu = np.random.RandomState(7).randn(*x.shape).astype("float32") * 0.2
        sf.write(self.p("b.wav"), x + gurultu, sr)   # SNR ~ 9 dB: esik 40 dB'nin cok altinda
        kod, c = self.kos(self.p("a.wav"), "--beklenen-sn", "15", "--ikinci", self.p("b.wav"))
        self.assertEqual(kod, 4, c)
        self.assertIn("tutmadi", c)

    def test_iki_kosu_farkli_uzunluk_kaldi(self):
        ton(self.p("a.wav"))
        ton(self.p("b.wav"), sure=14.0)
        kod, c = self.kos(self.p("a.wav"), "--ikinci", self.p("b.wav"))
        self.assertEqual(kod, 4, c)


class FakeProc:
    def __init__(self, kod):
        self.returncode = kod


@unittest.skipUnless(BAGIMLI, "numpy/soundfile yok")
class TestKarari(unittest.TestCase):
    """rakkase.test_kos karar agaci: kiyas/uretim/saglik/NaN taklit edilir (gercek GPU yok)."""

    def setUp(self):
        self.t = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.t, True)
        k = os.path.join(self.t, "rk")
        os.makedirs(os.path.join(k, "motor"))
        os.makedirs(os.path.join(k, "araclar"))
        shutil.copy(os.path.join(KOK, "rakkase.py"), k)
        shutil.copy(os.path.join(KOK, "motor", "kart_kural.py"), os.path.join(k, "motor"))
        shutil.copy(os.path.join(KOK, "araclar", "saglik_muzik.py"), os.path.join(k, "araclar"))
        ace = os.path.join(self.t, "ace")
        os.makedirs(ace)
        with open(os.path.join(k, "ayarlar.json"), "w", encoding="utf-8") as f:
            json.dump({"ace_kok": ace, "kilit": False}, f)
        self.k = k
        ad = "rakkase_t_%d" % id(self)
        spec = importlib.util.spec_from_file_location(ad, os.path.join(k, "rakkase.py"))
        self.r = importlib.util.module_from_spec(spec)
        sys.modules[ad] = self.r
        spec.loader.exec_module(self.r)
        self.addCleanup(sys.modules.pop, ad, None)

    def kos(self, kart, kiyas=0, saglik=(0, 0), tek_kosu=False, nan=(), uret_kod=0, tum_nan=False, nan_fn=None):
        """Donus: (cikis, uret_sayisi, kiyas_sayisi). saglik: ilk ve ikinci saglik cagrisinin donus kodlari."""
        r = self.r
        sayac = {"uret": 0, "kiyas": 0, "saglik": 0}

        def uret(plan, cikti, ad, yalniz=""):
            sayac["uret"] += 1
            if uret_kod:
                return uret_kod
            klasor = os.path.join(cikti, ad)
            os.makedirs(klasor, exist_ok=True)
            sf.write(os.path.join(klasor, "x.wav"), np.zeros((100, 2), dtype="float32"), 44100)
            return 0

        def run(kom, *a, **k):
            sayac["kiyas"] += 1
            return FakeProc(kiyas)

        def saglik_f(wav, beklenen=None, ikinci=""):
            i = sayac["saglik"]; sayac["saglik"] += 1
            return saglik[min(i, len(saglik) - 1)]

        def nan_tara(yol):
            return [yol] if tum_nan else list(nan)
        nan_tara = nan_fn or nan_tara

        with mock.patch.object(r, "uret", uret), mock.patch.object(r.subprocess, "run", run), mock.patch.object(r, "saglik", saglik_f), \
                mock.patch.object(r, "nan_tara", nan_tara), mock.patch.object(r, "mp3", lambda *a, **k: None), \
                mock.patch.object(kart_kural, "kart_oku", lambda gizli=0: (kart, "6.1")), \
                mock.patch.object(r, "venv_python", lambda: sys.executable):
            try:
                kod = r.test_kos(tek_kosu)
            except SystemExit as e:
                kod = e.code
        return kod, sayac["uret"], sayac["kiyas"]

    REF = "NVIDIA GeForce GTX 1050 Ti"
    DIGER = "NVIDIA GeForce GTX 1650"

    def test_referans_karti_gecti(self):
        self.assertEqual(self.kos(self.REF, kiyas=0)[0], 0)

    def test_referans_karti_kaldi_1(self):
        kod, uret, _ = self.kos(self.REF, kiyas=1, saglik=(0, 0))
        self.assertEqual(kod, 1)
        self.assertEqual(uret, 1, "referans kartinda ikinci kosu YOK: kapi aynen")

    def test_referans_karti_kaldi_saglik_ne_derse_1(self):
        # saglik tamam olsa bile referans kartinda referans KALDI = kurulum/motor kabul edilmez (kapi gevsemez)
        self.assertEqual(self.kos(self.REF, kiyas=1, saglik=(0, 0))[0], 1)

    def test_baska_kart_referans_gecti_0(self):
        self.assertEqual(self.kos(self.DIGER, kiyas=0)[0], 0)

    def test_baska_kart_referans_kaldi_saglik_tamam_7(self):
        kod, uret, _ = self.kos(self.DIGER, kiyas=1, saglik=(0, 0))
        self.assertEqual(kod, 7)
        self.assertEqual(uret, 2, "ikinci kosu (tutarlilik) yapilmali")

    def test_baska_kart_tek_kosu_7(self):
        kod, uret, _ = self.kos(self.DIGER, kiyas=1, saglik=(0,), tek_kosu=True)
        self.assertEqual((kod, uret), (7, 1))

    def test_baska_kart_saglik_kaldi_1(self):
        kod, uret, _ = self.kos(self.DIGER, kiyas=1, saglik=(4,))
        self.assertEqual((kod, uret), (1, 1))

    def test_baska_kart_tutarsiz_kaldi_1(self):
        self.assertEqual(self.kos(self.DIGER, kiyas=1, saglik=(0, 4))[0], 1)

    def test_nan_8_her_kartta_ve_kiyas_yok(self):
        for kart in (self.REF, self.DIGER):
            kod, _, kiyas = self.kos(kart, nan=("x.wav",))
            self.assertEqual(kod, 8, kart)
            self.assertEqual(kiyas, 0, "NaN'li wav kiyaslanmaz/mp3'e gitmez")

    def test_ikinci_kosu_nan_8(self):
        sayac = {"n": 0}

        def nan_fn(yol):
            sayac["n"] += 1
            return [yol] if sayac["n"] == 2 else []
        self.assertEqual(self.kos(self.DIGER, kiyas=1, saglik=(0, 0), nan_fn=nan_fn)[0], 8)

    def test_uretim_hatasi_kodu_gecer(self):
        self.assertEqual(self.kos(self.DIGER, uret_kod=4)[0], 4)

    def test_nan_tara_gercek(self):
        """nan_tara venv python'u ile calisir (burada sys.executable): NaN'li wav'i bulur, temizi bulmaz."""
        ton(os.path.join(self.t, "temiz.wav"))
        ton(os.path.join(self.t, "nanli.wav"), nan=True)
        with mock.patch.object(self.r, "venv_python", lambda: sys.executable):
            bulunan = self.r.nan_tara(self.t)
        self.assertEqual([os.path.basename(x) for x in bulunan], ["nanli.wav"])

    def test_mp3_nanli_atlar(self):
        """mp3(atla=...) NaN'li wav'a ffmpeg calistirmaz (issue #1: ffmpeg NaN wav'da cokuyordu)."""
        for ad in ("a.wav", "b.wav"):
            ton(os.path.join(self.t, ad), sure=1.0)
        cagrilar = []
        with mock.patch.object(self.r.shutil, "which", lambda x: "ffmpeg"), \
                mock.patch.object(self.r.subprocess, "run", lambda kom, **k: cagrilar.append(kom)):
            self.r.mp3(self.t, atla=[os.path.join(self.t, "b.wav")])
        self.assertEqual(len(cagrilar), 1)
        self.assertTrue(cagrilar[0][cagrilar[0].index("-i") + 1].endswith("a.wav"))


if __name__ == "__main__":
    unittest.main()
