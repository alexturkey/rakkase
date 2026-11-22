"""Rakkase: ACE-Step 1.5 ile yerel muzik uretimi (4 GB kartta hizli yol). Tek giris kapisi.

  python rakkase.py uret  --plan plan.json [--cikti <klasor>] [--ad kosu] [--yalniz ad1,ad2]
      her parca otomatik: uretimler/<YYYY-MM-DD_HH-MM-SS>_<ad>/ (wav, mp3, sozler, recete, dokum).
      --cikti verilirse orada da kalir (kopya); verilmezse calisma klasoru cikti/kosular, parca uretimler'e tasinir.
  python rakkase.py denetle --plan plan.json [--yalniz ..] -> uretim oncesi plan denetimi (CPU, ~5 sn); uret bunu kendisi
      once calistirir, HATA varsa durur (cikis 2; atlamak: uret --denetimsiz). Ayrinti: docs/KULLANIM.md "Plan denetimi".
  python rakkase.py bol   --plan plan.json            -> on plan siniri (ayarlar.json) icin kosu gruplari (--yalniz satirlari)
  python rakkase.py test [--tek-kosu]                 -> 15 sn kiyas parcasi uretir, testler/referans ile karsilastirir. GTX 1050 Ti (referans karti):
      referans kapisi aynen (GECTI/KALDI). Baska kart: referans KALDI ise sorun cikmaz ama "bayt uyumu kanitlanmadi" (cikis 7) ve kart-bagimsiz
      saglik olcumu (NaN/inf yok, sure, seviye/sessizlik, ayni kartta ikinci kosuyla tutarlilik; --tek-kosu ikinci kosuyu atlar).
  python rakkase.py mp3   <klasor>                    -> klasordeki wav'lari 192k mp3 yapar
  python rakkase.py panel <wav|klasor>                -> LED spektrum paneli: <ad>_panel.mp4 (1080x1080, ses + panel; paylasima hazir).
      uret bunu her parca icin otomatik yapar; kapatmak: uret --panel-yok. Panel dusse de muzik teslim edilir (uyari RK-W-PANEL).

Cikis kodlari (uret): 0 tamam, 2 plan denetimi HATA / motor baslamadi ya da yuklenemedi, 3 bir parca basarisiz (bitenler yine
arsivlenir), 4 RAM bekcisi durdurdu, 5 uretim tamam ama mp3/arsiv basarisiz, 6 ayarlar.json eksik/yanlis, 8 [RK-E-NAN] uretilen wav NaN/inf (bozuk ses; mp3/panel yapilmaz).
test: 0 GECTI, 1 KALDI (referans karti ya da kart-bagimsiz saglik), 7 referans-disi kart: bayt uyumu kanitlanmadi ama saglik tamam, 8 NaN; 2/3/4/6 uret ile ayni. panel: 0 tamam, 5 [RK-E-PANEL] panel uretilemedi.
Kalite sabit (kod icinde): turbo 8 adim, int8 decoder + fp32 hesap, LM kapali, akisli yukleme, decoder yerlesik.
Her cagri modeli yukler, isi bitirir, kapanir (surekli servis yok). On planda calistir: Claude Code arka plan
kabugunu bellek sikisinca kapatiyor. Ayrinti: docs/KULLANIM.md, docs/KURULUM_DEFTERI.md.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time

KOK = os.path.dirname(os.path.abspath(__file__))
GIZLI = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW (yalniz Windows)


# Kodlar (hata() 'HATA: [KOD] ...' basar; cikis kodu docs/hata_imzalari.json): [RK-E-AYAR-YOK] [RK-E-ACE-KOK] [RK-E-KILIT] [RK-E-VENV] [RK-E-MODEL] [RK-E-PLAN] [RK-E-PARCA] [RK-E-RAM-BEKCI] [RK-E-ARSIV] [RK-E-NAN] [RK-W-REFERANS-DISI] [RK-W-FFMPEG] [RK-E-PANEL] [RK-W-PANEL]
def hata(kod, mesaj, cikis):
    """Tek bicim: 'HATA: [RK-E-XXX] mesaj'. Kod -> cikis haritasi: docs/hata_imzalari.json, cozumler: docs/SIK_HATALAR.md."""
    print(f"HATA: [{kod}] {mesaj}", flush=True)
    sys.exit(cikis)


def ayar_yukle():
    """ayarlar.json yerel ve git disi; kur.cmd (scripts/kur.ps1) yazar, elle: ayarlar.ornek.json'u ayarlar.json olarak kopyala."""
    yol = os.path.join(KOK, "ayarlar.json")
    if not os.path.exists(yol):
        hata("RK-E-AYAR-YOK", "ayarlar.json yok. Cozum: kur.cmd'yi cift tiklayin (ACE-Step'i kurar ve ayarlari yazar); ACE-Step zaten kuruluysa "
             "ayarlar.ornek.json'u ayarlar.json adiyla kopyalayip ace_kok'a ACE-Step klasorunuzu yazin / ayarlar.json is missing: run kur.cmd", 6)
    try:
        with open(yol, encoding="utf-8") as f:
            ayar = json.load(f)
    except (OSError, ValueError) as e:
        hata("RK-E-AYAR-YOK", f"ayarlar.json okunamadi ya da bozuk ({e}). Duzeltin ya da silip kur.cmd'yi yeniden calistirin / ayarlar.json unreadable", 6)
    if not os.path.isdir(os.path.expandvars(ayar.get("ace_kok", ""))):
        hata("RK-E-ACE-KOK", f"ayarlar.json ace_kok klasoru yok ({ayar.get('ace_kok')!r}). ACE-Step klasorunun yolunu yazin ya da kur.cmd'yi calistirin / ace_kok folder not found", 6)
    if ayar.get("kilit") and not os.path.isdir(ayar.get("kilit_src", "")):
        hata("RK-E-KILIT", "ayarlar.json: kilit=true ama kilit_src klasoru yok. GPU kilidi icin ozel bir modul gerekir; yoksa kilit=false yapin / kilit=true needs kilit_src", 6)
    return ayar


AYAR = ayar_yukle()


def venv_klasoru():
    """ayarlar.json 'venv' (istege bagli): ACE venv'inin hizli diskteki kopyasi; yoksa <ace_kok>/.venv. Neden: KARARLAR K20."""
    return os.path.expandvars(AYAR.get("venv") or os.path.join(AYAR["ace_kok"], ".venv"))


def venv_python():
    if os.name == "nt":
        return os.path.join(venv_klasoru(), "Scripts", "python.exe")
    return os.path.join(venv_klasoru(), "bin", "python")


def kurulum_kontrol(model=True):
    """venv ve model dosyalari yoksa uzun bir hata yerine anlasilir kod: RK-E-VENV, RK-E-MODEL (cikis 6)."""
    if not os.path.exists(venv_python()):
        hata("RK-E-VENV", f"ACE-Step Python ortami yok ({venv_python()}). Cozum: kur.cmd (uv ortamini kurar) / the Python environment is missing: run kur.cmd", 6)
    ck = os.path.join(os.path.expandvars(AYAR["ace_kok"]), "checkpoints")
    gerek = ["Qwen3-Embedding-0.6B/tokenizer.json"] + (["acestep-v15-turbo/model.safetensors", "vae/diffusion_pytorch_model.safetensors",
                                                       "Qwen3-Embedding-0.6B/model.safetensors"] if model else [])
    for g in gerek:
        if not os.path.exists(os.path.join(ck, g)):
            hata("RK-E-MODEL", f"model dosyasi eksik: {g}. Cozum: kur.cmd (indirir, sha256 dogrular, kaldigi yerden surer) / model file missing: run kur.cmd", 6)


def uret(plan, cikti, ad, yalniz=""):
    env = dict(os.environ, BETIK="dokum_muzik.py", HF_HUB_OFFLINE="1", PYTHONIOENCODING="utf-8", RAKKASE_VENV=venv_klasoru())
    kom = [venv_python(), "-B", os.path.join(KOK, "motor", "calistir.py"), "--plan", os.path.abspath(plan),
           "--cikti", os.path.abspath(cikti), "--ad", ad]
    if AYAR.get("kilit", True):
        kom.append("--kilit")
    if yalniz:
        kom += ["--yalniz", yalniz]
    print("RAKKASE", time.strftime("%H:%M:%S"), " ".join(kom[2:]), flush=True)
    r = subprocess.run(kom, env=env)  # konsol cocugu: pencere acmaz, ciktiyi miras alir
    return r.returncode


def nan_tara(yol):
    """ACE venv python'u ile wav'larda NaN/inf arar (araclar/saglik_muzik.py --nan-bak); NaN'li wav yollarini dondurur. NaN'li wav ffmpeg'i cokertir (issue #1)."""
    wavlar = [yol] if os.path.isfile(yol) else sorted(glob.glob(os.path.join(yol, "**", "*.wav"), recursive=True))
    if not wavlar:
        return []
    r = subprocess.run([venv_python(), "-B", os.path.join(KOK, "araclar", "saglik_muzik.py"), *wavlar, "--nan-bak"], creationflags=GIZLI,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return [os.path.normpath(s[4:].strip()) for s in r.stdout.splitlines() if s.startswith("NAN ")]


def saglik(wav, beklenen=None, ikinci=""):
    """Kart-bagimsiz saglik olcumu, ciktiyi ekrana basar. Donus: 0 saglam, 3 NaN, 4 baska olcu kaldi, 5 okunamadi."""
    kom = [venv_python(), "-B", os.path.join(KOK, "araclar", "saglik_muzik.py"), wav]
    if beklenen:
        kom += ["--beklenen-sn", str(beklenen)]
    if ikinci:
        kom += ["--ikinci", ikinci]
    return subprocess.run(kom, env=dict(os.environ, PYTHONIOENCODING="utf-8")).returncode


def mp3(klasor, atla=()):
    atla = {os.path.normpath(x) for x in atla}
    if not shutil.which("ffmpeg"):
        print("UYARI: [RK-W-FFMPEG] ffmpeg PATH'te yok: mp3 yapilmadi, wav dosyalari yerinde (ffmpeg kurunca: python rakkase.py mp3 <klasor>) / ffmpeg not found, no mp3", flush=True)
        return
    for w in sorted(glob.glob(os.path.join(klasor, "**", "*.wav"), recursive=True)):
        m = w[:-4] + ".mp3"
        if os.path.normpath(w) in atla:
            continue
        if not os.path.exists(m):
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", w, "-b:a", "192k", m], creationflags=GIZLI, check=True)
            print("MP3", m, flush=True)


def panel(yol, atla=()):
    """LED paneli: <ad>_panel.mp4 (wav'in yaninda). Varsa atlar. Donus: basarisiz sayisi. ACE venv python'u kullanir (numpy, soundfile, Pillow orada)."""
    if not shutil.which("ffmpeg"):
        print("UYARI: [RK-W-FFMPEG] ffmpeg PATH'te yok: panel yapilmadi (ffmpeg kurunca: python rakkase.py panel <klasor>) / ffmpeg not found, no panel", flush=True)
        return 0
    wavlar = [yol] if os.path.isfile(yol) else sorted(glob.glob(os.path.join(yol, "**", "*.wav"), recursive=True))
    atla = {os.path.normpath(x) for x in atla}
    return sum(panel_yap(w) for w in wavlar if os.path.normpath(w) not in atla)


def panel_yap(wav):
    """Tek wav icin <ad>_panel.mp4 (zaten varsa atlar). Donus: 0 tamam/atlandi, 1 basarisiz (RK-E-PANEL satiri basilir)."""
    cikti = wav[:-4] + "_panel.mp4"
    if os.path.exists(cikti):
        return 0
    r = subprocess.run([venv_python(), "-B", os.path.join(KOK, "araclar", "panel.py"), wav, cikti], creationflags=GIZLI,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    satir = (r.stdout.strip().splitlines() or [""])[-1] or (r.stderr.strip().splitlines() or [""])[-1]
    if r.returncode == 0 and os.path.exists(cikti):
        print("PANEL", cikti, flush=True)
        return 0
    print(satir if "RK-E-PANEL" in satir else f"HATA: [RK-E-PANEL] panel uretilemedi ({os.path.basename(wav)}): {satir[:200]}", flush=True)
    if os.path.exists(cikti):
        try:
            os.remove(cikti)  # yarim dosya kalmasin
        except OSError:
            pass
    return 1


def bol(plan):
    parcalar = json.load(open(plan, encoding="utf-8"))["parcalar"]
    sinir, gruplar, g, top = AYAR.get("on_plan_ses_siniri_sn", 300), [], [], 0
    for p in parcalar:
        if g and top + p["sure"] > sinir:
            gruplar.append(g); g, top = [], 0
        g.append(p["ad"]); top += p["sure"]
    if g:
        gruplar.append(g)
    return [",".join(x) for x in gruplar]


def denetle(plan, yalniz=""):
    kom = [venv_python(), "-B", os.path.join(KOK, "araclar", "denetle.py"), "--plan", os.path.abspath(plan)]
    if yalniz:
        kom += ["--yalniz", yalniz]
    ortam = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run(kom, creationflags=GIZLI, capture_output=True, env=ortam)
    cikti = r.stdout.decode("utf-8", "replace")
    try:
        sys.stdout.write(cikti)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(cikti.encode("utf-8"))
    sys.stdout.flush()
    if r.returncode not in (0, 2):
        sys.stdout.write(r.stderr.decode("utf-8", "replace")[-2000:])
    return r.returncode


def test_temizle(cikti):
    for eski in sorted(glob.glob(os.path.join(cikti, "test_2*")))[:-3]:  # son 3 test kosusu kalir (cikti/ calisma alani)
        shutil.rmtree(eski, ignore_errors=True)


def test_kos(tek_kosu=False):
    """test: 15 sn'lik referans plani. Karar agaci (kalite esikleri DEGISMEZ: SNR > 40 dB, korelasyon > 0,999):
    - wav NaN/inf: RK-E-NAN, cikis 8 (her kartta).
    - referans kiyasi GECTI: cikis 0 (referans-disi kartta bile).
    - referans karti (GTX 1050 Ti) ve KALDI: cikis 1 (kurulum/motor kabul edilmez).
    - baska kart ve referans KALDI: bayt/dalga uyumu KANITLANMADI. Kart-bagimsiz saglik (sure, seviye/sessizlik) + ayni kartta ikinci kosuyla
      tutarlilik saglamsa cikis 7 ([RK-W-REFERANS-DISI]: 'kurulum bozuk' DEGIL, 'referansla uyum kanitlanmadi'); saglik kalirsa cikis 1."""
    sys.path.insert(0, os.path.join(KOK, "motor"))
    import kart_kural  # saf Python (torch yok); yalniz test komutu ister: motor/ klasorsuz gecici kopya koklerde (testler) diger komutlar calisir
    cikti = os.path.join(KOK, "cikti", "test")
    ad = time.strftime("test_%Y%m%d_%H%M%S")
    plan = os.path.join(KOK, "testler", "plan_kiyas_15sn.json")
    kart_ad, kart_cc = kart_kural.kart_oku(GIZLI)
    ref_kart = kart_kural.referans_karti(kart_ad)
    print(f"TEST kart: {kart_ad or '(nvidia-smi okunamadi)'}, compute capability {kart_cc or '?'}; referans karti ({kart_kural.REFERANS_KART}): "
          f"{'evet' if ref_kart else 'hayir'}", flush=True)
    kod = uret(plan, cikti, ad)
    if kod:
        sys.exit(kod)
    yeni = glob.glob(os.path.join(cikti, ad, "*.wav"))[0]
    if nan_tara(yeni):
        print(f"HATA: [RK-E-NAN] test sesi NaN/inf iceriyor (kart: {kart_ad or '?'}). Kurulum bozuk sayilmaz: kart/surucu sorunu olabilir "
              "(GTX 16xx: ayarlar.json 'vae_fp32': true). Raporlayin: kart adi ve bu satir / test audio contains NaN/inf", flush=True)
        return 8
    ref = os.path.join(KOK, "testler", "referans", "aday1_intro_neseli_15sn.wav")
    r = subprocess.run([venv_python(), "-B", os.path.join(KOK, "araclar", "kiyas_muzik.py"), ref, yeni])
    mp3(os.path.join(cikti, ad))
    if r.returncode == 0:
        print("TEST GECTI: referansla uyum kanitlandi" + ("" if ref_kart else f" (kart {kart_ad or '?'} referans karti degil, yine de tuttu)"), flush=True)
        test_temizle(cikti)
        return 0
    if ref_kart:
        print("TEST KALDI: referans kartinda referansla uyum yok: kurulum/motor kabul edilmez (motoru testi gecirmek icin degistirmeyin)", flush=True)
        test_temizle(cikti)
        return 1
    sk = saglik(yeni, beklenen=15)
    if sk:
        print(f"TEST KALDI: referans-disi kart ve kart-bagimsiz saglik olcumu de kaldi (saglik cikisi {sk}): yukaridaki SAGLIK satirina bakin", flush=True)
        test_temizle(cikti)
        return 1
    tutarli = "olculmedi (--tek-kosu)"
    if not tek_kosu:
        print("TEST: ikinci kosu (ayni kart, ayni tohum): tutarlilik olculecek, ~2-3 dk", flush=True)
        ad2 = ad + "_b"
        kod2 = uret(plan, cikti, ad2)
        if kod2:
            sys.exit(kod2)
        yeni2 = glob.glob(os.path.join(cikti, ad2, "*.wav"))[0]
        if nan_tara(yeni2):
            print("HATA: [RK-E-NAN] ikinci test sesi NaN/inf iceriyor", flush=True)
            return 8
        sk2 = saglik(yeni, beklenen=15, ikinci=yeni2)
        if sk2:
            print("TEST KALDI: ayni kartta ayni tohumla iki kosu birbirini tutmadi", flush=True)
            test_temizle(cikti)
            return 1
        tutarli = "evet (SNR > 40 dB, korelasyon > 0,999)"
    print(f"UYARI: [RK-W-REFERANS-DISI] Kart {kart_ad or '?'} referans karti degil: referansla bayt/dalga uyumu KANITLANMADI. Bu 'kurulum bozuk' demek "
          f"DEGIL (farkli kartta ayni tohum farkli gurultu verebilir [tahmin]). Kart-bagimsiz saglik: SAGLAM; ayni kartta iki kosu tutarli: {tutarli}. "
          "Basari demeyin: muzigi insan dinler / reference mismatch on a non-reference card, health checks passed", flush=True)
    test_temizle(cikti)
    return 7


def main():
    ap = argparse.ArgumentParser(description="Rakkase muzik uretimi")
    alt = ap.add_subparsers(dest="komut", required=True)
    u = alt.add_parser("uret"); u.add_argument("--plan", required=True); u.add_argument("--cikti", default="")
    u.add_argument("--ad", default=time.strftime("kosu_%Y%m%d_%H%M%S")); u.add_argument("--yalniz", default="")
    u.add_argument("--denetimsiz", action="store_true", help="plan denetimini atla (onerilmez)")
    u.add_argument("--panel-yok", action="store_true", help="<ad>_panel.mp4 uretme (LED paneli)")
    d = alt.add_parser("denetle"); d.add_argument("--plan", required=True); d.add_argument("--yalniz", default="")
    b = alt.add_parser("bol"); b.add_argument("--plan", required=True)
    t = alt.add_parser("test"); t.add_argument("--tek-kosu", action="store_true", help="referans-disi kartta ikinci kosuyla tutarlilik olcumunu atla")
    m = alt.add_parser("mp3"); m.add_argument("klasor")
    pn = alt.add_parser("panel"); pn.add_argument("yol", help="wav dosyasi ya da klasor")
    a = ap.parse_args()

    if a.komut == "denetle":
        kurulum_kontrol(model=False)
        sys.exit(denetle(a.plan, a.yalniz))
    if a.komut in ("uret", "test"):
        kurulum_kontrol()
    if a.komut == "uret":
        if not a.denetimsiz:
            dk = denetle(a.plan, a.yalniz)
            if dk:
                hata("RK-E-PLAN", "URETIM BASLAMADI: " + ("plan denetiminde HATA var (yukaridaki satirlar)" if dk == 2 else f"denetim calismadi (cikis {dk})")
                     + ". Plani duzeltin; --denetimsiz ile atlamak onerilmez / plan check failed", 2)
        cikti = a.cikti or os.path.join(KOK, "cikti", "kosular")
        kod = uret(a.plan, cikti, a.ad, a.yalniz)
        kosu = os.path.join(os.path.abspath(cikti), a.ad)
        if glob.glob(os.path.join(kosu, "*.wav")):  # kod 3'te de biten parcalar arsivlenir (yarida kalan kosu kaybolmaz)
            try:
                nanli = nan_tara(kosu)
                for w in nanli:
                    print(f"HATA: [RK-E-NAN] uretilen ses NaN/inf iceriyor (bozuk): {w}. Kurulum bozuk sayilmaz: kart/surucu sorunu olabilir (GTX 16xx: "
                          "ayarlar.json 'vae_fp32': true). mp3/panel yapilmadi / generated audio contains NaN/inf", flush=True)
                if nanli and not kod:
                    kod = 8
                mp3(kosu, atla=nanli)
                if not a.panel_yok:
                    try:  # panel yan cikti: dusse muzik teslim, cikis kodu degismez
                        if panel(kosu, atla=nanli):
                            print(f"UYARI: [RK-W-PANEL] panel uretilemedi, muzik ve mp3 yerinde (elle: python rakkase.py panel {kosu})", flush=True)
                    except Exception as e:
                        print(f"UYARI: [RK-W-PANEL] panel uretilemedi ({e!r}), muzik ve mp3 yerinde", flush=True)
                sys.path.insert(0, os.path.join(KOK, "araclar"))
                import recete
                recete.yaz(a.plan, kosu, tasi=not a.cikti)  # her parca kendi klasorunde: wav, mp3, sozler, recete.json, RECETE.md
            except Exception as e:  # uretim yapildi; arsiv hatasi uretimi yok saymaz
                print(f"UYARI arsiv/mp3 basarisiz ({e!r}); wav'lar yerinde: {kosu}  (elle: python araclar/recete.py --plan .. --kosu ..)", flush=True)
                kod = kod or 5
        _KOD_AD = {2: ("RK-E-PLAN", "motor baslamadi ya da yuklenemedi"), 3: ("RK-E-PARCA", "bir parca basarisiz (biten parcalar arsivlendi; yalnizca basarisizi --yalniz ile yeniden calistirin)"),
                   4: ("RK-E-RAM-BEKCI", "bos RAM bitti, RAM bekcisi durdurdu: diger programlari kapatin, ikinci kopya baslatmayin"), 5: ("RK-E-ARSIV", "uretim tamam ama mp3/arsiv basarisiz (wav yerinde)")}
        if kod in _KOD_AD:
            print(f"HATA: [{_KOD_AD[kod][0]}] {_KOD_AD[kod][1]}", flush=True)
        sys.exit(kod)
    if a.komut == "bol":
        for i, g in enumerate(bol(a.plan), 1):
            print(f"kosu {i}: --yalniz {g}")
        return
    if a.komut == "mp3":
        mp3(a.klasor); return
    if a.komut == "panel":
        kurulum_kontrol(model=False)
        if not os.path.exists(a.yol):
            hata("RK-E-PANEL", f"yol yok: {a.yol} / path not found", 5)
        if not (os.path.isfile(a.yol) or glob.glob(os.path.join(a.yol, "**", "*.wav"), recursive=True)):
            hata("RK-E-PANEL", f"wav bulunamadi: {a.yol} / no wav found", 5)
        sys.exit(5 if panel(a.yol) else 0)
    if a.komut == "test":
        sys.exit(test_kos(a.tek_kosu))


if __name__ == "__main__":
    main()
