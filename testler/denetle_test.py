"""CPU testleri (GPU ve model yuklemez; tokenizer ~5 sn). Calistir:
  <ACE venv python> -m unittest testler/denetle_test.py -v      (rakkase kokunden)

Kapsam: (1) docs/SINIRLAR.md "Denetim esikleri" tablosu = araclar/denetle.py sabitleri (belge ile kod ayrisirsa kirilir);
(2) bozuk plan kasalari HATA verir, saglam olanlar vermez; (3) desenler kelime sinirli ("trap" rap sayilmaz);
(4) rakkase.py denetle cikis kodlari (bozuk JSON, bos parca listesi, olmayan --yalniz); (5) kiyas_muzik.py esigi cikis koduyla uygular.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "araclar"))
import denetle  # noqa: E402

TOK = None


def tok():
    global TOK
    if TOK is None:
        TOK = denetle.tokenizer()
    return TOK


def saglam(**degis):
    p = dict(ad="deneme_30sn", caption="warm acoustic pop ballad with soft male vocal, fingerpicked guitar and gentle piano",
             lyrics="[Verse 1]\nGece yine sessiz kaldı sokaklar\nBir şarkı tuttum dilimde\n\n[Chorus]\nKal benimle bu gece\nKal benimle",
             vocal_language="tr", sure=60, bpm=80, ton="G Major", olcu="4", tohum=7)
    p.update(degis)
    for k in [k for k, v in degis.items() if v is SIL]:
        p.pop(k)
    return p


SIL = object()


def hatalar(p, adlar=None):
    bulgu, _ = denetle.denetle(p, tok(), adlar or [p.get("ad") if isinstance(p, dict) else None], denetle.gecerli_diller())
    return [m for d, m in bulgu if d == "HATA"], [m for d, m in bulgu if d == "UYARI"]


class BelgeKodAyni(unittest.TestCase):
    def test_sinirlar_tablosu_kodla_ayni(self):
        with open(os.path.join(KOK, "docs", "SINIRLAR.md"), encoding="utf-8") as f:
            metin = f.read()
        satirlar = re.findall(r"^\| `([A-Z_]+)` \| ([0-9.]+) \|", metin, re.M)
        self.assertGreaterEqual(len(satirlar), 10, "SINIRLAR.md tablosu okunamadi")
        for ad, deger in satirlar:
            self.assertTrue(hasattr(denetle, ad), f"SINIRLAR.md'de {ad} var, denetle.py'de yok")
            self.assertAlmostEqual(float(getattr(denetle, ad)), float(deger), msg=f"{ad}: belge {deger}, kod {getattr(denetle, ad)}")


class PlanKasalari(unittest.TestCase):
    def test_saglam_plan_hatasiz(self):
        h, _ = hatalar(saglam())
        self.assertEqual(h, [])

    def test_bozuk_alanlar_hata(self):
        kasalar = {
            "eksik tohum": saglam(tohum=SIL),
            "olcu sayi": saglam(olcu=4),
            "olcu 5": saglam(olcu="5"),
            "ton sayi": saglam(ton=1),
            "sure yazi": saglam(sure="60"),
            "sure 5": saglam(sure=5),
            "tohum ondalik": saglam(tohum=1.5),
            "bpm bool": saglam(bpm=True),
            "adim 7": saglam(adim=7),
            "shift 0": saglam(shift=0),
            "dil yok": saglam(vocal_language="xx"),
            "dil liste": saglam(vocal_language=["tr"]),
            "ad bolu": saglam(ad="a/b"),
            "sozlu ama no vocals": saglam(caption="calm piano, no vocals"),
            "caption 256 ustu": saglam(caption="warm cinematic orchestral pop with soaring strings " * 30),
        }
        for ad, p in kasalar.items():
            with self.subTest(ad):
                h, _ = hatalar(p)
                self.assertTrue(h, f"{ad}: HATA bekleniyordu")

    def test_ayni_ad_hata(self):
        h, _ = hatalar(saglam(), adlar=["deneme_30sn", "deneme_30sn"])
        self.assertTrue(any("ayni 'ad'" in m for m in h))

    def test_parca_nesne_degil(self):
        h, _ = hatalar("yazi")
        self.assertTrue(h)

    def test_adim_8_ve_shift_3_gecer(self):
        h, u = hatalar(saglam(adim=8, shift=3.0))
        self.assertEqual(h, [])
        h, u = hatalar(saglam(shift=3.0, soz_zamani=True))
        self.assertTrue(any("shift" in m for m in u))

    def test_sure_yetmezse_uyari(self):
        uzun = "\n".join(["[Verse 1]"] + ["Bir satır daha yazdım buraya"] * 20)
        _, u = hatalar(saglam(lyrics=uzun, sure=30))
        self.assertTrue(any("sn istiyor" in m for m in u))


class Desenler(unittest.TestCase):
    def test_trap_vokal_sayilmaz(self):
        self.assertIsNone(denetle.VOKAL_DESEN.search("dark trap beat, therapy for the night"))
        self.assertIsNotNone(denetle.VOKAL_DESEN.search("male rap vocals"))
        self.assertIsNone(denetle.RAP_DESEN.search("trap beat, wrapped in reverb"))

    def test_enstrumantal_deseni(self):
        self.assertIsNotNone(denetle.ENSTRUMANTAL_DESEN.search("instrumental track, warm piano"))
        self.assertIsNone(denetle.ENSTRUMANTAL_DESEN.search("pop song with an instrumental break before the last chorus"))

    def test_rap_katsayisi_kelime_sinirli(self):
        p = saglam(caption="dark trap beat with sung vocal hooks")
        rap = saglam(caption="boom bap rap with tight flow")
        bol = denetle.bolumler(p["lyrics"])
        self.assertGreater(denetle.gereken_sure(p, bol), denetle.gereken_sure(rap, bol))


class Komutlar(unittest.TestCase):
    def kos(self, *a):
        r = subprocess.run([sys.executable, os.path.join(KOK, "rakkase.py"), *a], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        return r.returncode, r.stdout + r.stderr

    def plan_dosyasi(self, icerik):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        f.write(icerik); f.close()
        self.addCleanup(os.remove, f.name)
        return f.name

    def test_bozuk_json(self):
        kod, cikti = self.kos("denetle", "--plan", self.plan_dosyasi("{bozuk"))
        self.assertEqual(kod, 2, cikti)

    def test_bos_parcalar(self):
        kod, cikti = self.kos("denetle", "--plan", self.plan_dosyasi('{"parcalar": []}'))
        self.assertEqual(kod, 2, cikti)

    def test_olmayan_yalniz(self):
        kod, cikti = self.kos("denetle", "--plan", self.plan_dosyasi(json.dumps({"parcalar": [saglam()]})), "--yalniz", "yok")
        self.assertEqual(kod, 2, cikti)

    def test_uret_bozuk_planda_baslamaz(self):
        kod, cikti = self.kos("uret", "--plan", self.plan_dosyasi('{"parcalar": [{"ad": "x"}]}'))
        self.assertEqual(kod, 2, cikti)
        self.assertIn("URETIM BASLAMADI", cikti)

    def test_ornek_planlar_hatasiz(self):
        for ad in sorted(os.listdir(os.path.join(KOK, "ornekler"))):
            with self.subTest(ad):
                kod, cikti = self.kos("denetle", "--plan", os.path.join(KOK, "ornekler", ad))
                self.assertEqual(kod, 0, cikti)


class Kiyas(unittest.TestCase):
    def test_esik_cikis_kodu(self):
        import numpy as np
        import soundfile as sf
        ref = os.path.join(KOK, "testler", "referans", "aday1_intro_neseli_15sn.wav")
        x, sr = sf.read(ref, dtype="float32")
        gurultulu = os.path.join(tempfile.mkdtemp(), "gurultulu.wav")
        sf.write(gurultulu, x + np.random.default_rng(0).normal(0, 0.05, x.shape).astype("float32"), sr)
        self.addCleanup(lambda: (os.remove(gurultulu), os.rmdir(os.path.dirname(gurultulu))))
        betik = os.path.join(KOK, "araclar", "kiyas_muzik.py")
        self.assertEqual(subprocess.run([sys.executable, betik, ref, ref], capture_output=True).returncode, 0)
        self.assertEqual(subprocess.run([sys.executable, betik, ref, gurultulu], capture_output=True).returncode, 1)


class Recete(unittest.TestCase):
    def test_arsiv_ve_soz_zamani(self):
        """Gecici kosu + gecici arsiv (gercek uretimler/'e yazmaz): wav'i olan parca arsivlenir, olmayan atlanir."""
        import shutil
        import numpy as np
        import soundfile as sf
        import recete
        t = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, t, True)
        eski = recete.URETIMLER
        recete.URETIMLER = os.path.join(t, "arsiv")
        self.addCleanup(setattr, recete, "URETIMLER", eski)
        kosu = os.path.join(t, "kosu"); os.makedirs(kosu)
        p1 = saglam(ad="a", soz_zamani=True)
        plan = os.path.join(t, "plan.json")
        with open(plan, "w", encoding="utf-8") as f:
            json.dump({"parcalar": [p1, saglam(ad="b")]}, f)
        sf.write(os.path.join(kosu, "a.wav"), np.zeros(4800, "float32"), 48000)
        with open(os.path.join(kosu, "a.soz_zamani.json"), "w") as f:
            json.dump({"success": True}, f)
        with open(os.path.join(kosu, "dokum.json"), "w") as f:
            json.dump({"parcalar": [{"ad": "a", "uretim_sn": 1.0}], "yukleme_toplam_sn": 120.0, "toplam_sn": 121.0}, f)
        yazilan = recete.yaz(plan, kosu, tasi=True)
        self.assertEqual([os.path.basename(y) for y in yazilan], ["a"])
        arsiv = os.listdir(recete.URETIMLER)
        self.assertEqual(len(arsiv), 1)
        icerik = set(os.listdir(os.path.join(recete.URETIMLER, arsiv[0])))
        self.assertTrue({"a.wav", "a.soz_zamani.json", "a.kelimeler.json", "plan.json", "recete.json", "RECETE.md", "kosu_dokum.json"} <= icerik)


class KelimeZamani(unittest.TestCase):
    def test_token_kelime_satir(self):
        import kelime_zamani
        tok = [dict(text=x, start=a, end=a + 0.3) for x, a in
               [("[Verse]", 0.0), ("\n", 0.1), ("Gece", 1.0), (" yine", 1.5), (" sessiz", 2.0), ("\n", 2.4),
                ("Kal", 3.0), (" benimle", 3.5), ("\n", 4.0), ("Son", 5.0), (" satir", 5.6)]]
        d = kelime_zamani.kelimeler({"success": True, "token_timestamps": tok}, "[Verse]\nGece yine sessiz\nKal benimle\nSon satir", 120, "4")
        self.assertTrue(d["success"])
        self.assertEqual(d["uyusmayan_kelime"], 0)
        self.assertEqual([s["metin"] for s in d["satirlar"]], ["Gece yine sessiz", "Kal benimle", "Son satir"])
        self.assertEqual(d["satirlar"][1]["kelimeler"][1]["k"], "benimle")
        self.assertTrue(d["satirlar"][0]["supheli"] and d["satirlar"][-1]["supheli"])  # ilk/son satir hep supheli

    def test_basarisiz_soz_zamani(self):
        import kelime_zamani
        self.assertFalse(kelime_zamani.kelimeler({"success": False, "error": "x"}, "a")["success"])


if __name__ == "__main__":
    unittest.main()
