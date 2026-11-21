"""Her parcaya kendi klasoru ve recetesi (kullanici istegi 2026-11-05): neyi, nasil, hangi aracla, hangi surumle; girdi, prompt, cikti.

  <kosu>/<parca_ad>/  parca.wav, parca.mp3, sozler.txt, recete.json, RECETE.md
  <RAKKASE>/uretimler/<YYYY-MM-DD_HH-MM-SS>_<parca_ad>/  ayni klasorun arsiv kopyasi (zaman = wav'in bitis ani;
  kullanici istegi 2026-11-05: tarih + saat:dk:sn, her uretim otomatik). tasi=True ise kopya degil tasima.

Kullanim:
  python recete.py --plan plan.json --kosu <cikti>/<kosu_ad> [--motor-notu "..."]
rakkase.py uret bunu kendisi cagirir. Eski kosulara geriye donuk da calisir (dokum.json + plan.json yeter).
"""
import argparse
import glob
import hashlib
import json
import os
import platform
import shutil
import subprocess
import time

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIZLI = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW (yalniz Windows)


def git(klasor, *a):
    try:
        return subprocess.run(["git", "-C", klasor, *a], capture_output=True, text=True, creationflags=GIZLI).stdout.strip()
    except Exception:
        return ""


def paket_surumleri(ace):
    sp = next(iter(glob.glob(os.path.join(ace, ".venv", "Lib", "site-packages"))
                   + glob.glob(os.path.join(ace, ".venv", "lib", "python*", "site-packages"))), "")
    s = {}
    for ad in ("torch", "torchao", "transformers", "diffusers", "safetensors", "accelerate"):
        d = glob.glob(os.path.join(sp, ad + "-*.dist-info"))
        if d:
            s[ad] = os.path.basename(d[0])[len(ad) + 1:-len(".dist-info")]
    return s


def model_bilgisi(ace):
    m = {}
    for ad in ("acestep-v15-turbo", "vae", "Qwen3-Embedding-0.6B"):
        d = os.path.join(ace, "checkpoints", ad)
        if os.path.isdir(d):
            dosyalar = sorted(glob.glob(os.path.join(d, "*.safetensors")))
            m[ad] = [dict(dosya=os.path.basename(f), bayt=os.path.getsize(f),
                          degisme=time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(f)))) for f in dosyalar]
    return m


def sha256(yol):
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def donanim():
    """Uretimi yapan makine (otomatik; eskiden sabit yaziliydi)."""
    d = dict(isletim=platform.platform(), cpu=platform.processor() or platform.machine())
    try:
        g = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True,
                           text=True, creationflags=GIZLI, timeout=10).stdout.strip().splitlines()
        d["gpu"] = g[0].strip() if g else "?"
    except Exception:
        d["gpu"] = "?"
    try:
        import psutil
        d["ram"] = f"{psutil.virtual_memory().total / 2**30:.0f} GB"
    except Exception:
        d["ram"] = "?"
    return d


def arac_bilgisi(motor_notu=""):
    ayar = json.load(open(os.path.join(KOK, "ayarlar.json"), encoding="utf-8"))
    ace = ayar["ace_kok"]
    return dict(
        arac="Rakkase (ACE-Step 1.5 hizli yol)",
        rakkase=dict(kok=KOK, commit=git(KOK, "rev-parse", "--short", "HEAD") or "commit yok",
                     kirli_agac=bool(git(KOK, "status", "--porcelain"))),  # commit'e girmemis degisiklik ya da yeni dosya (git disi klasorler haric)
        motor_notu=motor_notu or "motor: motor/dokum_muzik.py (akisli yukleme, decoder yerlesik)",
        ace_step=dict(kok=ace, repo="https://github.com/ACE-Step/ACE-Step-1.5", commit=git(ace, "rev-parse", "--short", "HEAD"),
                      model="acestep-v15-turbo (DiT), vae, Qwen3-Embedding-0.6B (metin kodlayici); LM kapali"),
        paketler=paket_surumleri(ace), modeller=model_bilgisi(ace),
        kalite=dict(adim=8, nicemleme="int8_weight_only (yalniz decoder)", hesap="fp32", lm="kapali", cfg="turbo: yok"),
        donanim=donanim())


URETIMLER = os.path.join(KOK, "uretimler")


def damga(yol):
    return time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(os.path.getmtime(yol)))


def arsivle(kaynak, ad, wav, tasi=False):
    """Parca klasorunu uretimler/<tarih_saat>_<ad>/ altina koyar; hedef varsa dokunmaz."""
    hedef = os.path.join(URETIMLER, f"{damga(wav)}_{ad}")
    if os.path.exists(hedef):
        print("UYARI arsiv zaten var, dokunulmadi:", hedef, flush=True)
        return hedef
    os.makedirs(URETIMLER, exist_ok=True)
    (shutil.move if tasi else shutil.copytree)(kaynak, hedef)
    return hedef


def yaz(plan_yol, kosu, motor_notu="", tasi=False, ureten=""):
    plan = json.load(open(plan_yol, encoding="utf-8"))
    dokum_yol = os.path.join(kosu, "dokum.json")
    dokum = json.load(open(dokum_yol, encoding="utf-8")) if os.path.exists(dokum_yol) else {}
    olcum = {p["ad"]: p for p in dokum.get("parcalar", [])}
    arac = arac_bilgisi(motor_notu)
    yazilan, hatali = [], []
    for p in plan["parcalar"]:
        try:
            h = _parca_yaz(p, plan, plan_yol, kosu, dokum, dokum_yol, olcum, arac, tasi, ureten)
        except Exception as e:  # bir parcanin hatasi otekilerin arsivini durdurmaz
            print(f"UYARI recete/arsiv {p.get('ad')}: {e!r}", flush=True)
            hatali.append(p.get("ad"))
            continue
        if h:
            yazilan.append(h)
    if hatali:
        raise RuntimeError(f"recete yazilamayan parcalar: {hatali}")
    return yazilan


def _parca_yaz(p, plan, plan_yol, kosu, dokum, dokum_yol, olcum, arac, tasi, ureten):
    ad = p["ad"]
    hedef = os.path.join(kosu, ad)
    kaynaklar = [os.path.join(kosu, ad + u) for u in (".wav", ".mp3", "_panel.mp4", ".soz_zamani.json")]
    if not any(os.path.exists(k) for k in kaynaklar) and not os.path.isdir(hedef):
        return None
    os.makedirs(hedef, exist_ok=True)
    for k in kaynaklar:
        if os.path.exists(k):
            shutil.move(k, os.path.join(hedef, os.path.basename(k)))
    wav = os.path.join(hedef, ad + ".wav")
    soz = p.get("lyrics") or "[Instrumental]"
    sz_yol = os.path.join(hedef, ad + ".soz_zamani.json")
    if os.path.exists(sz_yol):  # karaoke/altyazi icin kelime ve satir zamanlari (araclar/kelime_zamani.py)
        import kelime_zamani
        kz = kelime_zamani.kelimeler(json.load(open(sz_yol, encoding="utf-8")), p.get("lyrics"), p.get("bpm"), p.get("olcu", "4"))
        json.dump(kz, open(os.path.join(hedef, ad + ".kelimeler.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(hedef, "sozler.txt"), "w", encoding="utf-8").write(soz)
    o = olcum.get(ad, {})
    if dokum:
        shutil.copy2(dokum_yol, os.path.join(hedef, "kosu_dokum.json"))
    r = dict(
        parca=ad, uretim_zamani=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(wav))) if os.path.exists(wav) else "",
        ureten=ureten or os.environ.get("RAKKASE_URETEN", "rakkase"),
        arsiv_klasoru=os.path.join(URETIMLER, f"{damga(wav)}_{ad}") if os.path.exists(wav) else "",
        girdi=dict(caption_prompt=p["caption"], sozler=soz, dil=p.get("vocal_language", "unknown"),
                   sure_sn=p["sure"], bpm=p.get("bpm"), ton=p.get("ton"), olcu=p.get("olcu"), tohum=p["tohum"],
                   plan_dosyasi=os.path.abspath(plan_yol), plan_notu=plan.get("not", "")),
        arac=arac,
        olcum=dict(uretim_sn=o.get("uretim_sn"), dit_adim_ms=o.get("dit_adim_ms"), vram_tepe_mb=o.get("vram_tepe_mb"),
                   rss_tepe_mb=o.get("rss_tepe_mb"), shift=o.get("shift", p.get("shift", 1.0)),
                   kosu_yukleme_sn=dokum.get("yukleme_toplam_sn"), kilit_bekleme_sn=dokum.get("kilit_bekleme_sn"),
                   kosu_toplam_sn=dokum.get("toplam_sn"), dokum="kosu_dokum.json" if dokum else "yok"),
        cikti=dict(wav=os.path.basename(wav), wav_sha256=sha256(wav) if os.path.exists(wav) else "",
                   mp3=ad + ".mp3" if os.path.exists(os.path.join(hedef, ad + ".mp3")) else "",
                   soz_zamani=ad + ".soz_zamani.json" if os.path.exists(os.path.join(hedef, ad + ".soz_zamani.json")) else "",
                   kelimeler=ad + ".kelimeler.json" if os.path.exists(os.path.join(hedef, ad + ".kelimeler.json")) else ""),
        yeniden_uretmek="python rakkase.py uret --plan <bu klasor>/plan.json")
    tek_plan = {"not": f"{ad} tek parca plani (recete.py yazdi)", "parcalar": [p]}
    json.dump(tek_plan, open(os.path.join(hedef, "plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(r, open(os.path.join(hedef, "recete.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    g = r["girdi"]; a = r["arac"]; ol = r["olcum"]
    md = [f"# {ad}", "", f"Üretim: {r['uretim_zamani']} · üreten {r['ureten']} · Rakkase {a['rakkase']['commit']} · ACE-Step {a['ace_step']['commit']}",
          "", "## Girdi", f"- Tarif (caption, İngilizce prompt): {g['caption_prompt']}",
          f"- Dil {g['dil']} · süre {g['sure_sn']} sn · bpm {g['bpm']} · ton {g['ton']} · ölçü {g['olcu']}/4 · tohum {g['tohum']}",
          f"- Sözler: `sozler.txt`", f"- Plan: `{g['plan_dosyasi']}`",
          "", "## Araç", f"- {a['arac']}; {a['motor_notu']}",
          f"- Kalite: {a['kalite']['adim']} adım, {a['kalite']['nicemleme']}, {a['kalite']['hesap']} hesap, LM {a['kalite']['lm']}",
          f"- Paketler: " + ", ".join(f"{k} {v}" for k, v in a["paketler"].items()),
          f"- Donanım: {a['donanim']['gpu']}, {a['donanim']['ram']} RAM, {a['donanim']['cpu']}",
          "", "## Ölçüm (ölçüldü)", f"- Üretim {ol['uretim_sn']} sn · DiT adımı {ol['dit_adim_ms']} ms · VRAM tepe {ol['vram_tepe_mb']} MB · RAM tepe {ol['rss_tepe_mb']} MB",
          f"- Koşu: yükleme {ol['kosu_yukleme_sn']} sn, GPU kilidi bekleme {ol['kilit_bekleme_sn']} sn, toplam {ol['kosu_toplam_sn']} sn (koşudaki bütün parçalar)",
          "", "## Çıktı", f"- `{r['cikti']['wav']}` sha256 {r['cikti']['wav_sha256'][:16]}…, `{r['cikti']['mp3']}`",
          "", "## Yeniden üretmek", f"`{r['yeniden_uretmek']}`", ""]
    open(os.path.join(hedef, "RECETE.md"), "w", encoding="utf-8").write("\n".join(md))
    if os.path.exists(wav):
        ars = arsivle(hedef, ad, wav, tasi)
        print("ARSIV", ars, flush=True)
    print("RECETE", hedef, flush=True)
    return hedef


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True); ap.add_argument("--kosu", required=True); ap.add_argument("--motor-notu", default="")
    ap.add_argument("--ureten", default="")
    a = ap.parse_args()
    yaz(a.plan, a.kosu, a.motor_notu, ureten=a.ureten)
