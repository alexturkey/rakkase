"""Kart kurallari (saf Python, torch yok): hangi kart referans karti, hangi kartta VAE fp32 zorunlu.
EN: pure helpers, no torch. Reference card = GTX 1050 Ti 4 GB (the card the test reference was made on); GTX 16xx need the VAE in fp32 on the GPU.
Neden / why: GTX 16xx NaN ses verir (VAE fp16, issue #1); referans wav yalniz uretildigi kartta bayt-yakin cikar
(CUDA rastgele sayi uretecinin ayni tohumla farkli kartta ayni gurultuyu verecegi beklenmez [tahmin, issue #1]).
Kullanan / used by: rakkase.py (test kapisi), motor/dokum_muzik.py (VAE yamasi)."""
import re
import subprocess

REFERANS_KART = "GTX 1050 Ti"


def referans_karti(ad):
    """1050 Ti (referansin uretildigi kart) mi? Ad nvidia-smi'den: 'NVIDIA GeForce GTX 1050 Ti'."""
    return REFERANS_KART.lower() in (ad or "").lower()


def vae_fp32_gerek(ad, ayar_degeri=None):
    """VAE GPU'da fp32 olsun mu. ayarlar.json 'vae_fp32': true/false ise o kazanir (elle zorlama); yoksa (null) ad GTX 16xx ise True.
    1050 Ti ve digerleri icin False: varsayilan davranis (ve bayt cikti) DEGISMEZ."""
    if ayar_degeri is not None:
        return bool(ayar_degeri)
    return re.search(r"\bGTX 16\d\d", ad or "") is not None


def kart_oku(gizli=0):
    """(ad, compute_cap) nvidia-smi'den; okunamazsa ('', ''). Eski suruculerde compute_cap alani olmayabilir: cc ''."""
    for alanlar in ("name,compute_cap", "name"):
        try:
            r = subprocess.run(["nvidia-smi", f"--query-gpu={alanlar}", "--format=csv,noheader,nounits"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=30, creationflags=gizli)
        except (OSError, subprocess.SubprocessError):
            return "", ""
        satir = (r.stdout.strip().splitlines() or [""])[0]
        if r.returncode == 0 and satir:
            parca = [p.strip() for p in satir.split(",")]
            return parca[0], (parca[1] if len(parca) > 1 else "")
    return "", ""
