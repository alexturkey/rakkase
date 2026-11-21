"""Rakkase LED paneli / LED panel: wav -> paylasima hazir tek mp4 (1080x1080, 30 fps, CPU). Hata kodu / error code: [RK-E-PANEL] (cikis 5).
Kullanim: python panel.py <wav> <cikti.mp4> [--bas SN] [--sure SN]
Ses kayipsiz kaynaktan AAC 320k; video yalniz LED spektrum paneli (suslu video yok).
Gerekli: numpy, soundfile, Pillow, ffmpeg (PATH ya da RK_FFMPEG)."""
import multiprocessing, os, subprocess, sys, shutil, time
import numpy as np
import soundfile as sf
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W = H = 1080
FPS = 30
N, SEG = 20, 14                      # 20 bant, her bant 14 LED
NFFT = 4096


def hata(mesaj):
    print(f"HATA: [RK-E-PANEL] {mesaj}", flush=True)
    sys.exit(5)


def ffmpeg_yolu():
    ozel = os.environ.get("RK_FFMPEG")
    if ozel and os.path.isfile(ozel):
        return ozel
    return shutil.which("ffmpeg")


def seviyeler(x, sr, n_kare):
    """Her kare icin 20 bant seviyesi (0..1). Tum parca bir kerede, vektorel."""
    f = np.fft.rfftfreq(NFFT, 1 / sr)
    kenar = np.geomspace(40, 16000, N + 1)
    B = np.zeros((N, len(f)), np.float32)
    for k in range(N):
        m = (f >= kenar[k]) & (f < kenar[k + 1])
        if not m.any():
            m[np.searchsorted(f, kenar[k])] = True
        B[k, m] = 1 / m.sum()
    pencere = np.hanning(NFFT).astype(np.float32)
    pad = np.pad(x.astype(np.float32), (NFFT // 2, NFFT))
    merkez = (np.arange(n_kare) * sr / FPS).astype(np.int64)
    db = np.empty((n_kare, N), np.float32)
    for a in range(0, n_kare, 256):                     # bellek: 256 kare parca parca
        idx = merkez[a:a + 256, None] + np.arange(NFFT)[None, :]
        mag = np.abs(np.fft.rfft(pad[idx] * pencere, axis=1)).astype(np.float32)
        db[a:a + 256] = 20 * np.log10(mag @ B.T + 1e-9)
    # yuksek bantlar dogal olarak sonuyor: hafif egim telafisi (+4 dB/oktav degil, toplam ~16 dB)
    db += np.linspace(0, 16, N, dtype=np.float32)[None, :]
    tepe = np.percentile(db.max(axis=1), 98)            # tum parcaya gore referans: dinamik kalir
    sev = np.clip((db - (tepe - 46)) / 46, 0, 1)
    # kayan ortalama: hizli yukselir, yavas duser (LED hissi)
    cikti = np.empty_like(sev); s = np.zeros(N, np.float32)
    for i in range(n_kare):
        s = np.where(sev[i] > s, s + 0.65 * (sev[i] - s), s + 0.22 * (sev[i] - s))
        cikti[i] = s
    return cikti


def yazi_fontu(boyut):
    for ad in ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(ad, boyut)
        except OSError:
            pass
    return ImageFont.load_default()


def sahne():
    """Sabit arka plan (sonuk LED'ler), tamamen yanik LED goruntusu, parlama katmani, bant dikdortgenleri."""
    bg = Image.new("RGB", (W, H), (18, 16, 14)); d = ImageDraw.Draw(bg)
    d.rounded_rectangle([40, 150, W - 40, H - 150], 36, fill=(28, 26, 24), outline=(90, 80, 64), width=8)
    d.rounded_rectangle([90, 200, W - 90, H - 250], 12, fill=(6, 8, 6), outline=(50, 46, 40), width=4)
    x0, y0, x1, y1 = 120, 232, W - 120, H - 282
    bw = (x1 - x0) / N; sh = (y1 - y0) / SEG
    on = bg.copy(); od = ImageDraw.Draw(on)
    glow = Image.new("RGB", (W, H), (0, 0, 0)); gd = ImageDraw.Draw(glow)
    kutu = []
    for k in range(N):
        bx = int(x0 + k * bw + 7); bx2 = int(x0 + (k + 1) * bw - 7)
        kutu.append((bx, bx2))
        for s in range(SEG):
            renk = (60, 255, 90) if s < 9 else ((255, 210, 40) if s < 12 else (255, 60, 40))
            by = int(y1 - (s + 1) * sh + 4); by2 = int(y1 - s * sh - 4)
            d.rectangle([bx, by, bx2, by2], fill=tuple(int(v * 0.12) for v in renk))
            od.rectangle([bx, by, bx2, by2], fill=renk)
            gd.rectangle([bx, by, bx2, by2], fill=renk)
    f1, f2 = yazi_fontu(26), yazi_fontu(38)
    for j, t in enumerate(["60", "150", "400", "1k", "2.4k", "6k", "15k"]):
        for im in (bg, on):
            ImageDraw.Draw(im).text((x0 + j * (x1 - x0) / 6, y1 + 22), t, fill=(150, 140, 120), font=f1, anchor="mt")
    for im in (bg, on):
        ImageDraw.Draw(im).text((W // 2, H - 214), "RAKKASE", fill=(200, 180, 140), font=f2, anchor="mt")
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    glow = Image.eval(glow.crop((40, 150, W - 40, H - 150)), lambda v: v * 55 // 100)      # parlama gucu %55
    return np.asarray(bg), np.asarray(on), glow, (x0, y0, x1, y1, sh, kutu)


def tepeler(sev):
    """Tepe tutucu konumlari (tum kareler icin once hesaplanir: kareler birbirinden bagimsiz olur, paralel cizilebilir)."""
    tepe = np.zeros(N, np.float32); tut = np.zeros(N, np.int32); cikti = np.empty_like(sev)
    for i in range(len(sev)):
        yuk = sev[i] >= tepe
        tepe = np.where(yuk, sev[i], tepe)
        tut = np.where(yuk, 9, tut)                         # 9 kare tutar, sonra yavas duser
        dus = ~yuk & (tut <= 0)
        tut = np.where(~yuk & (tut > 0), tut - 1, tut)
        tepe = np.where(dus, np.maximum(sev[i], tepe - 0.012), tepe)
        cikti[i] = tepe
    return cikti


_G = {}


def hazirla():
    bg, on, glow, geo = sahne()
    _G.update(bg=Image.fromarray(bg), on=Image.fromarray(on), glow=glow, geo=geo)


def kare_ciz(sev_i, tepe_i):
    x0, y0, x1, y1, sh, kutu = _G["geo"]
    bg, on, glow = _G["bg"], _G["on"], _G["glow"]
    gy0, gy1, gx0, gx1 = 150, H - 150, 40, W - 40          # parlamanin uygulandigi pano alani
    im = bg.copy(); kucuk = np.zeros((H // 8, W // 8), np.uint8)
    for k in range(N):
        bx, bx2 = kutu[k]
        yan = int(np.rint(sev_i[k] * SEG))
        if yan > 0:
            ytop = int(y1 - yan * sh + 4); ybot = int(y1 - 4)
            kutu_k = (bx, ytop, bx2 + 1, ybot)
            im.paste(on.crop(kutu_k), kutu_k)
            kucuk[ytop // 8:ybot // 8 + 1, bx // 8:bx2 // 8 + 1] = 255
        pk = min(SEG - 1, max(0, int(tepe_i[k] * SEG)))
        if pk >= 1:
            by = int(y1 - (pk + 1) * sh + 4); by2 = int(y1 - pk * sh - 4)
            im.paste((255, 240, 200), (bx, by + int((by2 - by) * 0.35), bx2 + 1, by + int((by2 - by) * 0.6)))
    m = Image.fromarray(kucuk).filter(ImageFilter.GaussianBlur(1)).resize((W, H), Image.BILINEAR).crop((gx0, gy0, gx1, gy1))
    ek = ImageChops.multiply(glow, Image.merge("RGB", (m, m, m)))
    im.paste(ImageChops.add(im.crop((gx0, gy0, gx1, gy1)), ek), (gx0, gy0))
    return im.tobytes()


def _is(args):
    return [kare_ciz(a, b) for a, b in args]


def main():
    a = sys.argv[1:]
    bas = sure = None
    if "--bas" in a: i = a.index("--bas"); bas = float(a[i + 1]); del a[i:i + 2]
    if "--sure" in a: i = a.index("--sure"); sure = float(a[i + 1]); del a[i:i + 2]
    if len(a) != 2:
        print("Kullanim: python panel.py <wav> <cikti.mp4> [--bas SN] [--sure SN]"); sys.exit(2)
    wav, out = a
    ff = ffmpeg_yolu()
    if not ff:
        hata("ffmpeg PATH'te yok (kurun: winget install --id Gyan.FFmpeg -e) / ffmpeg not found")
    t0 = time.time()
    try:
        x, sr = sf.read(wav, always_2d=True); x = x.mean(1)
    except Exception as e:
        hata(f"wav okunamadi ({os.path.basename(wav)}: {e}) / cannot read wav")
    toplam = len(x) / sr
    if toplam < 0.2:
        hata(f"wav cok kisa ya da bos ({toplam:.2f} sn) / wav too short")
    b = bas or 0.0
    s = sure if sure else toplam - b
    s = min(s, toplam - b)
    xs = x[int(b * sr):int((b + s) * sr)]
    n_kare = int(np.ceil(s * FPS))
    sev = seviyeler(xs, sr, n_kare)
    komut = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if bas: komut += ["-ss", str(b)]
    komut += ["-i", wav]
    if sure or bas: komut += ["-t", f"{s:.3f}"]
    else: komut += ["-t", f"{toplam:.3f}"]
    komut += ["-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", out]
    p = subprocess.Popen(komut, stdin=subprocess.PIPE, creationflags=0x08000000 if os.name == "nt" else 0)
    try:
        tp = tepeler(sev)
        parca = 24                                           # kare / is parcasi
        isler = [list(zip(sev[i:i + parca], tp[i:i + parca])) for i in range(0, n_kare, parca)]
        isci = max(1, min(4, (os.cpu_count() or 2) - 1))     # makineyi kilitlememek icin bir cekirdek bos
        with multiprocessing.Pool(isci, initializer=hazirla) as havuz:
            for blok in havuz.imap(_is, isler):             # imap sirayi korur
                for fr in blok:
                    p.stdin.write(fr)
    except BrokenPipeError:
        pass
    except Exception as e:
        p.kill(); hata(f"cizim basarisiz ({e!r}) / drawing failed")
    p.stdin.close(); kod = p.wait()
    if kod != 0:
        hata(f"ffmpeg cikis kodu {kod}: panel yazilamadi / ffmpeg failed")
    print(f"{out}  {s:.1f} sn ses, {n_kare} kare, {os.path.getsize(out) / 1e6:.2f} MB, uretim {time.time() - t0:.1f} sn")


if __name__ == "__main__":
    main()
