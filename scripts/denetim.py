"""Rakkase repo denetimi (CPU, GPU/model/ag yok). Calistir (repo kokunden):  python -I scripts/denetim.py [--kok DIZIN]

Kapilar (her biri: neden / bedel / gevseme):
  G1 gizli Unicode ve ham kontrol karakteri: gorunmez metin ajana/okura talimat tasir. Bedel: yok. Gevseme: yok.
  G2 kisisel iz: kullanici-yolu, surucu-yolu, kisisel kullanici adi, e-posta, token kaliplari. Bedel: yer tutucu (<RAKKASE>) kullanilir.
     Gevseme: yalniz scripts/denetim_izinli.txt'e yazili, gerekceli tam satir.
  G3 ikili dosya: yalniz testler/referans/*.wav (<= 8 MB); baska wav/mp3/pt/safetensors/zip repoya girmez. Gevseme: gerekceyle liste.
  G4 JSON: ornekler/, testler/ ve ayarlar.ornek.json gecerli UTF-8 JSON olmali.
  G5 Python: her .py derlenir (sozdizimi), import yapilmaz (model yuklenmez).
  G6 yerel dosya: ayarlar.json, .env, uretimler/, cikti/ izlenmez.
  G7 kalite sabiti: "fp32" ve "8 adim" ifadesi rakkase.py ve motor/dokum_muzik.py basliginda durur (sessizce silinmesin).
Cikis: 0 temiz, 1 bulgu var, 3 girdi hatali. Bulgu satiri: KAPI dosya:satir aciklama (eslesen metin YAZILMAZ: sir sizmasin).
"""
import argparse
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile

# Gorunmez/cift yonlu karakterler sayilarla verilir: bu dosya kendi kapisina takilmaz.
GIZLI = [(0x200B, 0x200F), (0x202A, 0x202E), (0x2060, 0x2064), (0x2066, 0x2069), (0xFEFF, 0xFEFF), (0xE0000, 0xE007F)]
HAM = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SIFIR = chr(0x5c)  # ters bolu
# Eski calisma adlari parca parca yazilir: bu dosya kendi (ve bekcinin) kapisina takilmasin.
IC_IZ = ["voxcpm2" + "_(?:sesl" + "endirme|ah" + "enk)", "auto" + "_dubber", "Claude" + "-Session", "tele" + "gram_mesaj", "(?<![A-Za-z])ka" + "nka(?![A-Za-z])"]
KISISEL = [
    ("kullanici-yolu", re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s<]", re.I)),
    ("surucu-yolu", re.compile(r"(?<![A-Za-z0-9])[C-Zc-z]:" + re.escape(SIFIR) + r"{1,2}(?!\s)[^\s<>]")),
    ("masaustu-yolu", re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+/(?:Desktop|Masaustu|Documents)", re.I)),
    ("kisisel-ad", re.compile("alex" + "25092025", re.I)),
    ("ic-iz", re.compile("|".join(IC_IZ), re.I)),
    ("e-posta", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("token", re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|"
                         r"-----BEGIN [A-Z ]*PRIVATE KEY-----|[Bb]earer\s+[A-Za-z0-9._-]{20,})")),
]
EPOSTA_IZINLI = re.compile(r"@(?:users\.noreply\.github\.com|example\.(?:com|org)|localhost\.invalid|yerel\.invalid)$|^noreply@", re.I)
YASAK_UZANTI = {".wav", ".mp3", ".flac", ".ogg", ".pt", ".pth", ".safetensors", ".ckpt", ".bin", ".gguf", ".onnx", ".zip", ".7z", ".mp4", ".mkv"}
YEREL = ("ayarlar.json", ".env")
YEREL_KLASOR = ("uretimler/", "cikti/", ".ajan/")
WAV_ENFAZLA = 8 * 1024 * 1024


def dosyalar(kok):
    try:
        c = subprocess.run(["git", "-C", kok, "ls-files", "-z", "--cached", "--others", "--exclude-standard"], capture_output=True, check=True)
        return sorted(x.decode("utf-8", "replace") for x in c.stdout.split(b"\0") if x)
    except Exception:
        out = []
        for d, ds, fs in os.walk(kok):
            ds[:] = [x for x in ds if x not in (".git", "__pycache__", ".venv")]
            out += [os.path.relpath(os.path.join(d, f), kok).replace(os.sep, "/") for f in fs]
        return sorted(out)


def izinliler(kok):
    yol = os.path.join(kok, "scripts", "denetim_izinli.txt")
    if not os.path.isfile(yol):
        return set()
    with open(yol, encoding="utf-8") as f:
        return {s.strip() for s in f if s.strip() and not s.startswith("#")}


def denetle(kok):
    bulgu = []
    izin = izinliler(kok)
    liste = dosyalar(kok)
    for r in liste:
        yol = os.path.join(kok, r)
        if not os.path.isfile(yol):
            continue
        ek = os.path.splitext(r)[1].lower()
        if r in YEREL or any(r.startswith(k) for k in YEREL_KLASOR):
            bulgu.append(("G6", r, 0, "yerel dosya izleniyor/ekleniyor"))
            continue
        if ek in YASAK_UZANTI:
            if not bulundu_kontrol(r, ek, yol):
                bulgu.append(("G3", r, 0, "izinsiz ikili/agirlik/ses dosyasi ya da referans wav > 8 MB"))
            continue
        ham = open(yol, "rb").read()
        if b"\0" in ham[:4096]:
            bulgu.append(("G3", r, 0, "bilinmeyen ikili dosya"))
            continue
        try:
            metin = ham.decode("utf-8")
        except UnicodeDecodeError:
            bulgu.append(("G1", r, 0, "UTF-8 degil"))
            continue
        for n, satir in enumerate(metin.split("\n"), 1):
            if any(a <= ord(ch) <= b for ch in satir for a, b in GIZLI) or HAM.search(satir):
                bulgu.append(("G1", r, n, "gorunmez Unicode ya da ham kontrol karakteri"))
            if r in ("scripts/denetim.py", "testler/denetim_test.py"):  # kasitli kotu ornekler tasir; iki dosya korumali yol (G2 atlanir, G1 atlanmaz)
                continue
            for ad, d in KISISEL:
                for m in d.finditer(satir):
                    if ad == "e-posta" and EPOSTA_IZINLI.search(m.group(0)):
                        continue
                    if f"{r}:{ad}:{n}" in izin or f"{r}:{ad}:*" in izin:
                        continue
                    bulgu.append(("G2", r, n, ad))
        if ek == ".json" and (r.startswith(("ornekler/", "testler/")) or r == "ayarlar.ornek.json"):
            try:
                json.loads(metin)
            except ValueError as e:
                bulgu.append(("G4", r, 0, f"gecersiz JSON ({e.__class__.__name__})"))
        if ek == ".py":
            with tempfile.TemporaryDirectory() as t:
                try:
                    py_compile.compile(yol, cfile=os.path.join(t, "x.pyc"), doraise=True)
                except py_compile.PyCompileError:
                    bulgu.append(("G5", r, 0, "sozdizimi hatasi"))
    for r, anahtar in (("rakkase.py", "fp32"), ("motor/dokum_muzik.py", "fp32")):
        yol = os.path.join(kok, r)
        if os.path.isfile(yol):
            bas = "".join(open(yol, encoding="utf-8", errors="replace").readlines()[:20])
            if anahtar not in bas or "8 adim" not in bas:
                bulgu.append(("G7", r, 0, "ilk 20 satirda '8 adim' ve 'fp32' kalite sabiti yok"))
    return bulgu


def bulundu_kontrol(r, ek, yol):
    return r.startswith("testler/referans/") and ek == ".wav" and os.path.getsize(yol) <= WAV_ENFAZLA


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hizli", action="store_true", help="hizli kip (varsayilan davranis; ag/model yok)")
    ap.add_argument("--kok", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    a = ap.parse_args()
    if not os.path.isdir(a.kok):
        print("HATA: kok yok", file=sys.stderr)
        return 3
    b = denetle(a.kok)
    for k, r, n, s in b:
        print(f"{k} {r}:{n} {s}")
    print(f"denetim: {len(b)} bulgu (kok: {os.path.basename(os.path.abspath(a.kok))})")
    print("SONUC: " + ("KIRMIZI" if b else "YESIL") + f" bulgu={len(b)}")
    return 1 if b else 0


if __name__ == "__main__":
    sys.exit(main())
