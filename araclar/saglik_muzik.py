"""Kart-bagimsiz saglik olcumu (bayt/referans uyumu DEGIL): bir wav'in muzik gibi gorunup gorunmedigine bakar.
EN: card-independent health check of a wav (finite samples, duration, level, silence) and optional same-card two-run consistency.
Neden / why: referans wav yalniz 1050 Ti'de bayt-yakin cikar; baska kartta referansla kiyas KALIR ama kurulum saglam olabilir (issue #1).
Bu arac yalniz "ses bozuk mu" der; muzigin guzel olup olmadigini YARGILAMAZ (insan dinler).
Kullanim / usage (venv python): saglik_muzik.py a.wav [b.wav ...] [--beklenen-sn 15] [--tolerans-sn 0.5] [--nan-bak] [--ikinci iki.wav]
  --nan-bak   yalniz NaN/inf bakar (hizli; uret sonrasi)
  --ikinci    ayni kartta ayni tohumla ikinci kosu: birinci wav ile kiyas (SNR > 40 dB ve korelasyon > 0.999; ayni esikler kiyas_muzik.py)
Cikis / exit: 0 saglam, 3 NaN/inf (RK-E-NAN), 4 baska saglik olcusu kaldi, 5 okunamadi."""
import argparse
import os
import sys

import numpy as np
import soundfile as sf

ESIK_SNR, ESIK_KOR = 40.0, 0.999   # kiyas_muzik.py ile ayni
SESSIZ_DB = -60.0                  # tum parcanin RMS'i bunun altindaysa "sessiz"
SESSIZ_PENCERE_DB = -70.0          # 0,5 sn pencere bunun altindaysa sessiz pencere
SESSIZ_ORAN_MAX = 0.5              # pencerelerin yarisindan fazlasi sessizse kaldi


def oku(yol):
    x, sr = sf.read(yol, dtype="float32")
    return (x if x.ndim == 1 else x.mean(axis=1)), sr, x


def olc(yol):
    """Dict: sonlu_mu, sure_sn, rms_db, tepe, sessiz_oran. Sonlu degilse oteki olculer None."""
    x, sr, ham = oku(yol)
    sonlu = bool(np.isfinite(ham).all())
    ozet = dict(yol=yol, sr=sr, sonlu=sonlu, sure_sn=len(x) / sr, rms_db=None, tepe=None, sessiz_oran=None)
    if not sonlu or len(x) == 0:
        return ozet
    ozet["tepe"] = float(np.abs(ham).max())
    ozet["rms_db"] = float(10 * np.log10(float(np.mean(x.astype("float64") ** 2)) + 1e-20))
    p = max(int(0.5 * sr), 1)
    n = len(x) // p
    if n:
        kareler = x[: n * p].reshape(n, p).astype("float64")
        db = 10 * np.log10(np.mean(kareler ** 2, axis=1) + 1e-20)
        ozet["sessiz_oran"] = float(np.mean(db < SESSIZ_PENCERE_DB))
    return ozet


def kiyas(a, b):
    xa, sra, _ = oku(a)
    xb, srb, _ = oku(b)
    if sra != srb or len(xa) != len(xb):
        return None, None
    d = xa - xb
    guc = float(np.mean(xa.astype("float64") ** 2)) + 1e-12
    snr = 10 * np.log10(guc / (float(np.mean(d.astype("float64") ** 2)) + 1e-12))
    kor = float(np.corrcoef(xa, xb)[0, 1])
    return float(snr), kor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wav", nargs="+")
    ap.add_argument("--beklenen-sn", type=float, default=None)
    ap.add_argument("--tolerans-sn", type=float, default=0.5)
    ap.add_argument("--nan-bak", action="store_true")
    ap.add_argument("--ikinci", default="")
    a = ap.parse_args()
    kod = 0
    for yol in a.wav:
        try:
            o = olc(yol)
        except Exception as e:  # okunamayan/bozuk dosya
            print(f"SAGLIK {os.path.basename(yol)}: okunamadi ({e!r})", flush=True)
            return 5
        if not o["sonlu"]:
            print(f"NAN {yol}", flush=True)
            print(f"SAGLIK {os.path.basename(yol)}: KALDI NaN/inf var (RK-E-NAN)", flush=True)
            kod = 3
            continue
        if a.nan_bak:
            continue
        kusur = []
        if a.beklenen_sn is not None and abs(o["sure_sn"] - a.beklenen_sn) > a.tolerans_sn:
            kusur.append(f"sure {o['sure_sn']:.2f} sn (beklenen {a.beklenen_sn} +-{a.tolerans_sn})")
        if o["rms_db"] is None or o["rms_db"] < SESSIZ_DB:
            kusur.append(f"neredeyse sessiz (RMS {o['rms_db']} dB)")
        if o["sessiz_oran"] is not None and o["sessiz_oran"] > SESSIZ_ORAN_MAX:
            kusur.append(f"pencerelerin %{o['sessiz_oran'] * 100:.0f}'i sessiz")
        if a.ikinci:
            snr, kor = kiyas(yol, a.ikinci)
            if snr is None:
                kusur.append("ikinci kosu farkli uzunluk/ornekleme")
            else:
                print(f"SAGLIK iki kosu tutarliligi: SNR {snr:.1f} dB, korelasyon {kor:.6f} (esik SNR > {ESIK_SNR}, kor > {ESIK_KOR})", flush=True)
                if not (snr > ESIK_SNR and kor > ESIK_KOR):
                    kusur.append("ayni kartta ayni tohumla iki kosu birbirini tutmadi")
        print(f"SAGLIK {os.path.basename(yol)}: {o['sure_sn']:.2f} sn, RMS {o['rms_db']:.1f} dB, tepe {o['tepe']:.3f}, sessiz pencere "
              f"%{(o['sessiz_oran'] or 0) * 100:.0f} | {'KALDI: ' + '; '.join(kusur) if kusur else 'SAGLAM (sonlu, sure, seviye)'}", flush=True)
        if kusur and kod != 3:
            kod = 4
    return kod


if __name__ == "__main__":
    sys.exit(main())
