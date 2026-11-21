"""araclar/panel.py (LED spektrum paneli: wav -> mp4) yoklamasi. CPU, GPU/model yok; sentetik ses.
Her kotu girdi (bozuk/bos/yok wav, olmayan ffmpeg) kod ile bitmeli ve YARIM mp4 birakmamali; iyi girdide mp4 olculur (1080x1080, 30 fps,
h264+yuv420p, aac, sure = ses +-0,05 sn). Piksel icerigi olculmez (yazi tipi makineye gore degisir).
Calistir (kokten):  python -B -m unittest testler/test_panel.py -v    Gerekli: numpy, soundfile, Pillow, ffmpeg+ffprobe (yoksa atlanir)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL = os.path.join(KOK, "araclar", "panel.py")
FFMPEG = os.environ.get("RK_FFMPEG") or shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe") or (os.path.join(os.path.dirname(FFMPEG), "ffprobe") if FFMPEG else None)
try:
    import numpy as np
    import soundfile as sf
    import PIL  # noqa: F401
    BAGIMLI = True
except ImportError:
    BAGIMLI = False
VAR = bool(FFMPEG and BAGIMLI and FFPROBE and (shutil.which(FFPROBE) or os.path.exists(FFPROBE) or os.path.exists(FFPROBE + ".exe")))


def sentetik(yol, sure=5.0, sr=44100):
    t = np.arange(int(sure * sr)) / sr
    x = 0.3 * np.sin(2 * np.pi * 220 * t) + 0.2 * np.sin(2 * np.pi * 3520 * t) * (np.sin(2 * np.pi * 2 * t) > 0)
    sf.write(yol, np.stack([x, x * 0.8], 1).astype("float32"), sr)


def kos(args, env=None, timeout=300):
    e = dict(os.environ)
    e.update(env or {})
    return subprocess.run([sys.executable, "-X", "utf8", PANEL, *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=e, timeout=timeout)


def probe(yol):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_streams", "-show_format", "-of", "json", yol], capture_output=True, text=True, timeout=60)
    return json.loads(r.stdout)


@unittest.skipUnless(os.path.exists(PANEL), "araclar/panel.py yok")
@unittest.skipUnless(VAR, "numpy/soundfile/Pillow/ffmpeg/ffprobe yok")
class Panel(unittest.TestCase):
    def test_iyi_5sn(self):
        with tempfile.TemporaryDirectory() as t:
            w, m = os.path.join(t, "a.wav"), os.path.join(t, "a_panel.mp4")
            sentetik(w, 5.0)
            r = kos([w, m])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            p = probe(m)
            v = [s for s in p["streams"] if s["codec_type"] == "video"][0]
            a = [s for s in p["streams"] if s["codec_type"] == "audio"][0]
            self.assertEqual((v["width"], v["height"]), (1080, 1080))
            self.assertEqual(v["codec_name"], "h264")
            self.assertEqual(v["pix_fmt"], "yuv420p")
            self.assertEqual(v["r_frame_rate"], "30/1")
            self.assertEqual(a["codec_name"], "aac")
            self.assertAlmostEqual(float(p["format"]["duration"]), 5.0, delta=0.05)
            self.assertEqual(len(os.listdir(t)), 2, "gecici/artik dosya kalmamali")
            self.assertNotIn(t.lower(), json.dumps(p).lower(), "mp4 etiketlerine yol sizmamali")
            self.assertEqual({k.lower() for k in p["format"].get("tags", {})} - {"major_brand", "minor_version", "compatible_brands", "encoder"}, set())

    def test_bas_sure(self):
        with tempfile.TemporaryDirectory() as t:
            w, m = os.path.join(t, "a.wav"), os.path.join(t, "b.mp4")
            sentetik(w, 6.0)
            r = kos([w, m, "--bas", "1", "--sure", "2"])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertAlmostEqual(float(probe(m)["format"]["duration"]), 2.0, delta=0.1)

    def _kotu(self, hazirla, ad="x.wav"):
        with tempfile.TemporaryDirectory() as t:
            w, m = os.path.join(t, ad), os.path.join(t, "c_panel.mp4")
            hazirla(w)
            r = kos([w, m])
            self.assertNotEqual(r.returncode, 0, "kotu girdi kodsuz gecti: " + r.stdout + r.stderr)
            self.assertFalse(os.path.exists(m), "yarim/bos mp4 birakildi")
            self.assertEqual([f for f in os.listdir(t) if f != ad], [], "artik dosya")
            self.assertTrue((r.stdout + r.stderr).strip(), "hata mesaji bos")

    def test_bozuk_wav(self):
        self._kotu(lambda w: open(w, "wb").write(b"RIFF\x00\x00bozuk" * 10))

    def test_bos_dosya(self):
        self._kotu(lambda w: open(w, "wb").close())

    def test_sifir_saniye_wav(self):
        self._kotu(lambda w: sf.write(w, np.zeros((0, 2), "float32"), 44100))

    def test_olmayan_wav(self):
        self._kotu(lambda w: None)

    def test_ffmpeg_yok(self):
        with tempfile.TemporaryDirectory() as t:
            w, m = os.path.join(t, "a.wav"), os.path.join(t, "a_panel.mp4")
            sentetik(w, 1.0)
            r = kos([w, m], env={"RK_FFMPEG": os.path.join(t, "yok_ffmpeg.exe"), "PATH": t})
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertFalse(os.path.exists(m))
            self.assertIn("ffmpeg", (r.stdout + r.stderr).lower())

    def test_arguman_eksik_kullanim(self):
        r = kos([])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Kullanim", r.stdout + r.stderr)


@unittest.skipUnless(os.path.exists(PANEL) and VAR, "araclar/panel.py ya da bagimliliklar yok")
class PanelKomutu(unittest.TestCase):
    """rakkase.py panel <wav|klasor> ve uret --panel-yok (motor/GPU'suz kisimlar). Gecici kopya kok + ace_kok/.venv (--system-site-packages)."""

    @classmethod
    def setUpClass(cls):
        cls.t = tempfile.TemporaryDirectory()
        k = os.path.join(cls.t.name, "rk")
        os.makedirs(k)
        shutil.copy(os.path.join(KOK, "rakkase.py"), k)
        shutil.copytree(os.path.join(KOK, "araclar"), os.path.join(k, "araclar"), ignore=shutil.ignore_patterns("__pycache__"))
        ace = os.path.join(cls.t.name, "ace")
        os.makedirs(os.path.join(ace, "checkpoints", "Qwen3-Embedding-0.6B"))
        open(os.path.join(ace, "checkpoints", "Qwen3-Embedding-0.6B", "tokenizer.json"), "w").close()
        subprocess.run([sys.executable, "-m", "venv", "--without-pip", "--system-site-packages", os.path.join(ace, ".venv")], check=True, capture_output=True)
        with open(os.path.join(k, "ayarlar.json"), "w", encoding="utf-8") as f:
            json.dump({"ace_kok": ace.replace(os.sep, "/"), "kilit": False}, f)
        cls.k = k

    @classmethod
    def tearDownClass(cls):
        cls.t.cleanup()

    def rk(self, *args):
        e = dict(os.environ)
        e.pop("RK_ACE_KOK", None)
        return subprocess.run([sys.executable, "-X", "utf8", os.path.join(self.k, "rakkase.py"), *args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=e, timeout=300, cwd=self.k)

    def test_tek_wav_ve_atlama(self):
        w = os.path.join(self.k, "tek.wav")
        sentetik(w, 2.0)
        r = self.rk("panel", w)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        m = os.path.join(self.k, "tek_panel.mp4")
        self.assertTrue(os.path.exists(m))
        mt = os.path.getmtime(m)
        r = self.rk("panel", w)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(os.path.getmtime(m), mt, "var olan panel yeniden uretildi")

    def test_klasor_biri_bozuk(self):
        d = os.path.join(self.k, "klasor")
        os.makedirs(d)
        sentetik(os.path.join(d, "iyi.wav"), 1.5)
        with open(os.path.join(d, "kotu.wav"), "wb") as f:
            f.write(b"bozuk")
        r = self.rk("panel", d)
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
        self.assertIn("RK-E-PANEL", r.stdout + r.stderr)
        self.assertTrue(os.path.exists(os.path.join(d, "iyi_panel.mp4")), "iyi parca panelsiz kalmamali")
        self.assertFalse(os.path.exists(os.path.join(d, "kotu_panel.mp4")), "bozuk parca icin yarim mp4")
        self.assertEqual(sorted(os.listdir(d)), ["iyi.wav", "iyi_panel.mp4", "kotu.wav"], "artik dosya")

    def test_olmayan_yol_ve_bos_klasor(self):
        r = self.rk("panel", os.path.join(self.k, "yok.wav"))
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
        self.assertIn("RK-E-PANEL", r.stdout + r.stderr)
        bos = os.path.join(self.k, "bos")
        os.makedirs(bos)
        r = self.rk("panel", bos)
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)

    def test_ffmpeg_yok_uyari_cikis_0(self):
        w = os.path.join(self.k, "ff.wav")
        sentetik(w, 1.0)
        e = dict(os.environ, PATH=os.path.dirname(sys.executable))
        e.pop("RK_FFMPEG", None)
        r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(self.k, "rakkase.py"), "panel", w], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=e, timeout=120, cwd=self.k)
        if shutil.which("ffmpeg", path=os.path.dirname(sys.executable)):
            self.skipTest("ffmpeg python klasorunde")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("RK-W-FFMPEG", r.stdout + r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.k, "ff_panel.mp4")))

    def test_panel_yok_bayragi_tanimli(self):
        r = self.rk("uret", "-h")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("--panel-yok", r.stdout)

    def test_hata_kodlari_haritada(self):
        with open(os.path.join(KOK, "docs", "hata_imzalari.json"), encoding="utf-8") as f:
            metin = f.read()
        for kod in ("RK-E-PANEL", "RK-W-PANEL"):
            self.assertIn(kod, metin)


if __name__ == "__main__":
    unittest.main()
