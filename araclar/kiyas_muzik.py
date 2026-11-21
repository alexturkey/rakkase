"""Iki (ya da daha cok) WAV'in ayniligi: ornek bazinda max fark, SNR, korelasyon, LUFS/tepe (ffmpeg loudnorm), log-mel spektrum farki.
Kullanim: <python> kiyas_muzik.py referans.wav yeni1.wav [yeni2.wav ...]   (ilk dosya referans)
Kaynak duzeyi: olcum. Tohum sabitken 'tohum duzeyi aynilik' olcutu: max fark ~1e-5..1e-3, SNR > 40 dB, korelasyon > 0,999."""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

GIZLI = 0x08000000


def lufs(yol):
    p = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", yol, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=GIZLI)
    j = json.loads(re.findall(r"\{[^{}]*\}", p.stderr)[-1])
    return float(j["input_i"]), float(j["input_tp"])


def logmel(x, sr, n_fft=2048, hop=512, n_mel=64):
    pen = np.hanning(n_fft)
    n = 1 + (len(x) - n_fft) // hop
    frames = np.lib.stride_tricks.as_strided(x, shape=(n, n_fft), strides=(x.strides[0] * hop, x.strides[0]))
    spec = np.abs(np.fft.rfft(frames * pen, axis=1)) ** 2
    f = np.linspace(0, sr / 2, spec.shape[1])
    mel_f = 2595 * np.log10(1 + f / 700)
    kenar = np.linspace(mel_f.min(), mel_f.max(), n_mel + 2)
    fb = np.zeros((n_mel, spec.shape[1]))
    for i in range(n_mel):
        lo, mid, hi = kenar[i:i + 3]
        fb[i] = np.clip(np.minimum((mel_f - lo) / (mid - lo + 1e-9), (hi - mel_f) / (hi - mid + 1e-9)), 0, None)
    return np.log10(spec @ fb.T + 1e-10)


ESIK_SNR, ESIK_KOR = 40.0, 0.999  # rakkase.py test esigi (CLAUDE.md "Test zorunlulugu")


def main():
    ref = sys.argv[1]
    r, sr = sf.read(ref, dtype="float32")
    r = r if r.ndim == 1 else r.mean(axis=1)
    rl, rt = lufs(ref)
    print(f"referans {os.path.basename(ref)}: {len(r) / sr:.2f} sn, {sr} Hz, LUFS {rl:.1f}, tepe {rt:.1f} dBTP")
    kaldi = 0
    for y in sys.argv[2:]:
        x, sr2 = sf.read(y, dtype="float32")
        if sr2 != sr:
            print(f"{os.path.basename(y)}: ornekleme hizi farkli ({sr2} != {sr}), kiyaslanmadi | KALDI")
            kaldi += 1
            continue
        x = x if x.ndim == 1 else x.mean(axis=1)
        n = min(len(x), len(r))
        d = x[:n] - r[:n]
        guc = float(np.mean(r[:n] ** 2)) + 1e-12
        snr = 10 * np.log10(guc / (float(np.mean(d ** 2)) + 1e-12))
        kor = float(np.corrcoef(x[:n], r[:n])[0, 1])
        lm = float(np.mean(np.abs(logmel(x[:n], sr) - logmel(r[:n], sr))))
        xl, xt = lufs(y)
        print(f"{os.path.basename(y)}: {len(x) / sr:.2f} sn | max fark {np.abs(d).max():.2e} | SNR {snr:.1f} dB | korelasyon {kor:.6f} | "
              f"log-mel ort. fark {lm:.4f} | LUFS {xl:.1f} (ref {rl:.1f}) | tepe {xt:.1f} dBTP | uzunluk esit {len(x) == len(r)}")
        gecti = snr > ESIK_SNR and kor > ESIK_KOR and len(x) == len(r)
        kaldi += not gecti
        print(f"  {'GECTI' if gecti else 'KALDI'} (esik SNR > {ESIK_SNR} dB, korelasyon > {ESIK_KOR}, uzunluk esit)")
    return 1 if kaldi else 0


if __name__ == "__main__":
    sys.exit(main())
