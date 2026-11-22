"""Rakkase motoru: ACE-Step 1.5 turbo'yu 4 GB VRAM / 16 GB RAM'e sigdirip plan.json'daki parcalari uretir ve olcer.
Paket kaynagina yazilmaz; tum degisiklikler bu dosyadaki sarmalardir (neden: docs/MIMARI.md).

Kalite (degismez): turbo 8 adim, decoder Linear'lari int8 (torchao), hesap fp32 (Pascal'da fp16 NaN), LM kapali.
Tek yol: akisli yukleme (DiT ve text encoder ardisik okuma, aninda int8) + decoder yerlesik (yalniz decoder GPU'da kalici,
kosul modulleri tensor tensor GPU'ya). Paketin kendi yukleme yolu ve eski olcum bayraklari 2026-11-05'te silindi: git tag
paket-yolu-son (4 GB'da 7-11 dk yukleme, 10,6 GB RAM: docs/OLCUMLER.md).
Olcum: asama sureleri, tasimalar, DiT adimi, VAE, VRAM/RSS tepe; bos RAM bekcisi (150 MB alti 30 sn -> cikis 4).
Cikti: <cikti>/<ad>/<parca>.wav, sozlu parcada <parca>.soz_zamani.json (soz_zamani: false ile kapanir), dokum.json (her parcadan sonra yeniden yazilir).
Cikis kodlari: 0 tamam, 2 baslatma/yukleme basarisiz, 3 bir parca basarisiz (oncekiler ve dokum.json yazili kalir), 4 bekci.
Her cikis yolunda GPU kilidi birakilir ve surec os._exit ile kapanir (paketin arka plan is parcaciklari sureci acik tutar).
Kullanim: python rakkase.py uret --plan plan.json  (rakkase.py -> calistir.py -> bu dosya)
"""
import argparse
import glob
import json
import os
import shutil
import sys
import threading
import time
import traceback
from contextlib import ExitStack, contextmanager

_AYAR = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ayarlar.json"), encoding="utf-8"))
ACE = os.environ.get("RAKKASE_ACE", _AYAR["ace_kok"])
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kart_kural  # noqa: E402  saf Python: kart adina gore kurallar (VAE fp32 yamasi)
sys.path.insert(0, ACE)

T0 = time.time()
ASAMALAR = []  # (ad, sure_sn, rss_once_mb, rss_sonra_mb)
KILIT = ExitStack()  # GPU kilidi; her cikis yolunda __main__ kapatir
CIKTI = {"klasor": ""}  # bekci cikarken _tmp_ ara klasorlerini temizlemek icin


def rss_mb():
    import psutil
    return psutil.Process().memory_info().rss / 2**20


def bos_ram_mb():
    import psutil
    return psutil.virtual_memory().available / 2**20


def asama(ad, fn):
    r0, t = rss_mb(), time.time()
    sonuc = fn()
    ASAMALAR.append((ad, round(time.time() - t, 2), round(r0), round(rss_mb())))
    print(f"ASAMA {ad}: {time.time() - t:.1f} sn  RSS {r0:.0f} -> {rss_mb():.0f} MB  bos RAM {bos_ram_mb():.0f} MB", flush=True)
    return sonuc


class Bekci(threading.Thread):
    """RSS/bos RAM ornekleyici. Kullanici karari 2026-11-05 01:04: uretimi durdurmasin; yalniz gercek cokme sinirinda
    (bos RAM < 150 MB ve bu 30 sn surerse) durdurur. Sayfa dosyasina tasma kabul (yavas olsun, bitsin)."""

    def __init__(self, esik_mb=150, aralik=1.0, sure_sn=30):
        super().__init__(daemon=True)
        self.esik, self.aralik, self.sure, self.tepe_rss, self.min_bos, self.dur = esik_mb, aralik, sure_sn, 0.0, 1e9, False

    def run(self):
        dusuk_baslangic = None
        while not self.dur:
            r, b = rss_mb(), bos_ram_mb()
            self.tepe_rss, self.min_bos = max(self.tepe_rss, r), min(self.min_bos, b)
            if b < self.esik:
                dusuk_baslangic = dusuk_baslangic or time.time()
                if time.time() - dusuk_baslangic >= self.sure:
                    print(f"BEKCI: bos RAM {b:.0f} MB < {self.esik} MB, {self.sure} sn surdu, durduruluyor (RSS {r:.0f} MB)", flush=True)
                    if CIKTI["klasor"]:
                        for t in glob.glob(os.path.join(CIKTI["klasor"], "_tmp_*")):
                            shutil.rmtree(t, ignore_errors=True)
                    KILIT.close()
                    sys.stdout.flush()
                    os._exit(4)
            else:
                dusuk_baslangic = None
            time.sleep(self.aralik)


KUYRUK_MB = 256  # akisli yuklemede okuyucu ile donusturucu arasindaki tampon siniri (RAM tepesi korunur)


def isit(yol, blok_mb=16):
    """Dosyayi buyuk bloklarla ARDISIK okuyup isletim sisteminin dosya onbellegine koyar (veri RSS'e girmez). Neden (olcum
    2026-11-05 gece): paket VAE'yi mmap ile dagnik okuyor; DiT yuklemesinin bellek baskisi VAE dosyasini onbellekten atiyor ve
    337 MB 31-33 sn suruyor (HDD ~11 MB/s); onbellekteyken from_pretrained 0,4 sn. Yukleyiciden hemen once cagrilir: diskte
    baska okuyucu yokken (surec basinda ayri iplikle onden okuma import'la disk icin yarisip 20 -> 56 sn yavaslatti, reddedildi)."""
    t, n, tampon = time.time(), 0, bytearray(blok_mb * 2**20)
    with open(yol, "rb", buffering=0) as f:
        while True:
            k = f.readinto(tampon)
            if not k:
                break
            n += k
    print(f"ISITMA {os.path.basename(os.path.dirname(yol))}: {n / 2**20:.0f} MB, {time.time() - t:.1f} sn", flush=True)


def param_envanteri(ad, modul):
    """Parametreleri (tensor turu, dtype) -> MB olarak toplar; torchao AQT icin gercek int8 veri boyutu."""
    import torch
    top = {}
    for p in modul.parameters():
        impl = getattr(p, "tensor_impl", None)
        if impl is not None:
            nb = sum(getattr(impl, a).numel() * getattr(impl, a).element_size()
                     for a in ("int_data", "scale", "zero_point") if getattr(impl, a, None) is not None)
            anahtar = "AQT/int8"
        else:
            nb = p.numel() * p.element_size()
            anahtar = f"{type(p).__name__}/{str(p.dtype).replace('torch.', '')}"
        top[anahtar] = top.get(anahtar, 0) + nb
    top = {k: round(v / 2**20) for k, v in top.items()}
    print(f"ENVANTER {ad}: {top} (toplam {sum(top.values())} MB)", flush=True)
    return top


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--cikti", required=True)
    ap.add_argument("--ad", required=True, help="kosu adi; cikti/<ad>/ altina yazar")
    ap.add_argument("--yalniz", default="", help="virgulle parca adlari: yalniz bunlar uretilir (10 dk on plan siniri icin kosulara bolme)")
    ap.add_argument("--kilit", action="store_true", help="GPU kilidini model yuklemeden ONCE al, surec sonunda birak")
    args = ap.parse_args()

    with open(args.plan, encoding="utf-8") as f:
        plan = json.load(f)
    cikti = os.path.join(os.path.abspath(args.cikti), args.ad)
    os.makedirs(cikti, exist_ok=True)
    CIKTI["klasor"] = cikti
    os.chdir(ACE)
    bekci = Bekci()
    bekci.start()
    kilit = KILIT
    kilit_bekleme_sn = 0.0
    if args.kilit:
        # yukleme de GPU kullanir (decoder, text encoder, VAE): kilit yuklemeden once alinir (2026-11-05 F2, A1.2)
        sys.path.insert(0, _AYAR["kilit_src"])
        from bolum_00_omurga.runtime.kaynak_kilidi import kaynak_kullan
        sahip = "".join(c for c in os.environ.get("RAKKASE_URETEN", "rakkase").lower() if c.isalnum() or c in "_-")[:32]
        bekle = int(_AYAR.get("kilit_bekle_sn", 3600))
        print(f"GPU kilidi bekleniyor (sahip ajan:{sahip or 'rakkase'}, en cok {bekle} sn)...", flush=True)
        t_k = time.time()
        kilit.enter_context(kaynak_kullan(["gpu"], "ajan:" + (sahip or "rakkase"), "rakkase_" + args.ad, bekle_saniye=bekle))
        kilit_bekleme_sn = round(time.time() - t_k, 1)
        print("GPU kilidi alindi", time.strftime("%H:%M:%S"), flush=True)

    import torch
    print(f"baslangic RSS {rss_mb():.0f} MB bos RAM {bos_ram_mb():.0f} MB", flush=True)
    asama("import_acestep", lambda: __import__("acestep.handler"))
    from acestep.handler import AceStepHandler
    from acestep.llm_inference import LLMHandler
    from acestep.inference import GenerationConfig, GenerationParams, generate_music
    import transformers

    # --- yukleyici asamalarini sar (sinif duzeyinde, paket dosyasina yazilmaz)
    for isim in [n for n in dir(AceStepHandler) if n.startswith(("_load_", "_apply_dit_quant"))]:
        orig = getattr(AceStepHandler, isim)
        if not callable(orig) or isim == "_load_model_context":
            continue

        def sarili(self, *a, _o=orig, _n=isim, **k):
            if _n == "_load_vae_model":
                isit(os.path.join(ACE, "checkpoints", "vae", "diffusion_pytorch_model.safetensors"))
            if _n == "_load_text_encoder_and_tokenizer":
                # yukleyici text encoder'i CPU'da _get_vae_dtype('cpu') = fp32'ye cevirir (2,3 GB); bf16 kalsin
                gvd = self._get_vae_dtype
                self._get_vae_dtype = lambda device=None: torch.bfloat16 if device == "cpu" else gvd(device)
                try:
                    return asama(_n, lambda: _o(self, *a, **k))
                finally:
                    del self._get_vae_dtype
            return asama(_n, lambda: _o(self, *a, **k))

        setattr(AceStepHandler, isim, sarili)
    fp_orig = transformers.AutoModel.from_pretrained.__func__

    def meta_iskelet(cfg, attn):
        """DiT iskeleti meta cihazda (bellek/disk yok). ResidualFSQ (tokenizer/detokenizer) init'te .item() cagirir ve kalici
        olmayan tamponlar kurar; yalniz o modul CPU'da kurulur (kucuk)."""
        import vector_quantize_pytorch.residual_fsq as rf
        from transformers.models.qwen3.modeling_qwen3 import Qwen3RotaryEmbedding  # inv_freq kalici olmayan tampon
        siniflar = (rf.ResidualFSQ, Qwen3RotaryEmbedding)
        eski = {s: s.__init__ for s in siniflar}

        def cpu_init_yap(orig):
            def cpu_init(self, *a, **kk):
                with torch.device("cpu"):
                    orig(self, *a, **kk)
            return cpu_init

        for s in siniflar:
            s.__init__ = cpu_init_yap(eski[s])
        try:
            with torch.device("meta"):
                return transformers.AutoModel.from_config(cfg, trust_remote_code=True, attn_implementation=attn)
        finally:
            for s in siniflar:
                s.__init__ = eski[s]

    def meta_kontrol(model):
        kalan = [n for n, t in list(model.named_parameters()) + list(model.named_buffers()) if t.device.type == "meta"]
        if kalan:
            raise RuntimeError(f"meta kalan tensorler: {kalan[:5]}")

    def akisli_yukle(yol, nicemle=True, hedef_dtype=None, **k):
        """Akisli yukleme: iskelet meta'da (disk okumasiz), safetensors dosya sirasiyla duz ardisik okunur (mmap yok),
        her tensor hedef dtype'a (DiT: bf16 -> fp16, paketin dtype=fp16 yuklemesiyle ayni donusum; text encoder: bf16 asli)
        yerine takilir; nicemle=True ise decoder Linear'lari paketin suzgeciyle (decoder.*, tokenizer/detokenizer haric)
        aninda torchao Int8WeightOnlyConfig ile int8'e cevrilir. Tam fp16/fp32 kopya hic olusmaz: tepe RAM ~ son model.
        Nicemleme tensor basina bagimsiz oldugundan sonuc paket yoluyla ayni."""
        import gc
        import struct
        from transformers import AutoConfig
        from torchao.quantization import Int8WeightOnlyConfig, quantize_
        from torchao.quantization.quant_api import _is_linear
        cfg = AutoConfig.from_pretrained(yol, trust_remote_code=True)
        attn = k.get("attn_implementation") or "sdpa"  # DiT: yukleyici 'eager' verir (Pascal); text encoder: paketin varsayilani sdpa
        model = meta_iskelet(cfg, attn)
        hedef_dtype = hedef_dtype or k.get("dtype", torch.float16)
        dosya = os.path.join(yol, "model.safetensors")
        f = open(dosya, "rb", buffering=0)
        try:
            return _akis_govde(f, model, nicemle, hedef_dtype, attn, struct, gc, Int8WeightOnlyConfig, quantize_, _is_linear)
        finally:
            f.close()

    def _akis_govde(f, model, nicemle, hedef_dtype, attn, struct, gc, Int8WeightOnlyConfig, quantize_, _is_linear):
        n = struct.unpack("<Q", f.read(8))[0]
        baslik = json.loads(f.read(n))
        baslik.pop("__metadata__", None)
        taban = 8 + n
        sirali = sorted(baslik.items(), key=lambda kv: kv[1]["data_offsets"][0])
        model_anahtarlar = set(model.state_dict().keys())  # kalici olmayan tamponlar (inv_freq, FSQ) dosyada yok, CPU'da kuruldu
        dosya_anahtarlar = set(baslik)
        if model_anahtarlar != dosya_anahtarlar:
            raise RuntimeError(f"anahtar uyumsuz: modelde fazla {sorted(model_anahtarlar - dosya_anahtarlar)[:5]} "
                               f"dosyada fazla {sorted(dosya_anahtarlar - model_anahtarlar)[:5]}")
        dt_map = {"BF16": torch.bfloat16, "F16": torch.float16, "F32": torch.float32}
        qcfg = Int8WeightOnlyConfig()
        linear_bekleyen = {}  # fqn -> kalan parametre adlari
        for fqn, m in model.named_modules():
            if nicemle and isinstance(m, torch.nn.Linear) and fqn.split(".")[0] == "decoder" and \
                    not any(p in ("tokenizer", "detokenizer") for p in fqn.split(".")):
                linear_bekleyen[fqn] = {n_ for n_, _ in m.named_parameters(recurse=False)}
        sayac = [0, 0]  # okunan bayt, int8'e cevrilen Linear
        # Okuyucu is parcacigi (2026-11-05 gece): disk okumasi (GIL'siz) ile donusum/int8 nicemleme (CPU) ust uste biner.
        # Kuyruk bayt butcesiyle sinirli (KUYRUK_MB): RAM tepesi degismez. Ayni tensorler, ayni sira, ayni islem: cikti ayni.
        import queue
        import threading
        kuyruk, butce, hata, dur = queue.Queue(), threading.BoundedSemaphore(KUYRUK_MB), [], threading.Event()

        def okuyucu():
            try:
                beklenen = taban
                for ad_, bilgi_ in sirali:
                    b0_, b1_ = bilgi_["data_offsets"]
                    mb = max(1, min(KUYRUK_MB, (b1_ - b0_ + 2**20 - 1) >> 20))  # yukari yuvarla
                    for _ in range(mb):
                        while not butce.acquire(timeout=0.5):
                            if dur.is_set():
                                return
                    if dur.is_set():
                        return
                    if taban + b0_ != beklenen:
                        f.seek(taban + b0_)
                    tampon_ = bytearray(b1_ - b0_)
                    f.readinto(tampon_)
                    beklenen = taban + b1_
                    kuyruk.put((ad_, bilgi_, tampon_, mb))
            except BaseException as e:  # ana dongu hatayi gorur
                hata.append(e)
            finally:
                kuyruk.put(None)
        th = threading.Thread(target=okuyucu, daemon=True, name="akis_okuyucu")
        th.start()
        try:
            _akis_tuket(kuyruk, butce, model, dt_map, hedef_dtype, linear_bekleyen, quantize_, qcfg, _is_linear, sayac)
        finally:
            dur.set()
            while th.is_alive():  # okuyucu bekliyorsa cozulsun; dosya bundan sonra kapanir
                try:
                    kuyruk.get(timeout=0.1)
                except queue.Empty:
                    pass
            th.join()
        okunan, nicem = sayac
        if hata:
            raise hata[0]
        gc.collect()
        print(f"AKIS: {okunan / 2**20:.0f} MB okundu, {len(sirali)} tensor, {nicem} Linear int8, RSS {rss_mb():.0f} MB", flush=True)
        if linear_bekleyen:
            raise RuntimeError(f"nicemlenmemis Linear kaldi: {list(linear_bekleyen)[:5]}")
        meta_kontrol(model)
        model.config._attn_implementation = attn
        return model

    def _akis_tuket(kuyruk, butce, model, dt_map, hedef_dtype, linear_bekleyen, quantize_, qcfg, _is_linear, sayac):
        """Kuyruktan tensorleri alir, hedef dtype'a cevirip yerine takar, Linear tamamlaninca int8'e cevirir."""
        while True:
            oge = kuyruk.get()
            if oge is None:
                break
            ad, bilgi, tampon, mb = oge
            del oge
            b0, b1 = bilgi["data_offsets"]
            t = torch.frombuffer(tampon, dtype=dt_map[bilgi["dtype"]]).reshape(bilgi["shape"]).to(hedef_dtype)
            del tampon
            for _ in range(mb):
                butce.release()
            modul_adi, _, p_adi = ad.rpartition(".")
            modul = model.get_submodule(modul_adi) if modul_adi else model
            if p_adi in modul._parameters:
                modul._parameters[p_adi] = torch.nn.Parameter(t, requires_grad=False)
            else:
                modul._buffers[p_adi] = t
            sayac[0] += b1 - b0
            if modul_adi in linear_bekleyen:
                linear_bekleyen[modul_adi].discard(p_adi)
                if not linear_bekleyen[modul_adi]:
                    quantize_(modul, qcfg, filter_fn=_is_linear)  # paketle ayni config, ayni _is_linear
                    sayac[1] += 1
                    del linear_bekleyen[modul_adi]

    def duz(t):
        """tensor alt sinifini (torchao AffineQuantizedTensor) ic tensorlerine acar: bit karsilastirmasi icin."""
        if hasattr(t, "__tensor_flatten__"):
            adlar, _ = t.__tensor_flatten__()
            return [x for n in adlar for x in duz(getattr(t, n))]
        return [t]

    def ayni_mi(m1, m2):
        s1, s2 = m1.state_dict(), m2.state_dict()
        if s1.keys() != s2.keys():
            return False, "anahtarlar farkli"
        for ad in s1:
            a_, b_ = duz(s1[ad]), duz(s2[ad])
            if len(a_) != len(b_) or any(x.dtype != y.dtype or x.shape != y.shape or not torch.equal(x, y) for x, y in zip(a_, b_)):
                return False, ad
        return True, f"{len(s1)} tensor bit duzeyinde ayni"

    def dit_yukle(yol, **k):
        """int8 onbellek (2026-11-05 gece, ayarlar.json 'int8_onbellek' klasoru; yoksa kapali): akisli yukleyicinin urettigi
        durum (decoder int8, kalan fp16) bir kez torch.save ile hizli diske yazilir; sonraki yuklemeler 4,5 GB HDD okuma +
        CPU nicemleme yerine bu dosyayi okur. Anahtar: kaynak dosya boyu+tarihi, torch ve torchao surumu, bicim surumu.
        Agirliklar ayni (RAKKASE_ONBELLEK_DOGRULA=1: iki yol da yuklenip bit duzeyinde karsilastirilir)."""
        klasor = _AYAR.get("int8_onbellek")
        if not klasor:
            return akisli_yukle(yol, **k)
        import torchao
        kaynak = os.path.join(yol, "model.safetensors")
        st = os.stat(kaynak)
        anahtar = f"dit_int8_v1_{st.st_size}_{st.st_mtime_ns}_t{torch.__version__}_ao{torchao.__version__}".replace("+", "_")
        dosya = os.path.join(os.path.expandvars(klasor), anahtar + ".pt")
        if os.path.exists(dosya):
            t = time.time()
            cfg = transformers.AutoConfig.from_pretrained(yol, trust_remote_code=True)
            attn = k.get("attn_implementation") or "sdpa"
            model = meta_iskelet(cfg, attn)
            sd = torch.load(dosya, map_location="cpu", weights_only=True)  # guvenli yukleme (torchao tensorleri izinli listede)
            model.load_state_dict(sd, strict=True, assign=True)
            del sd
            meta_kontrol(model)
            model.config._attn_implementation = attn
            print(f"ONBELLEK int8 okundu: {os.path.getsize(dosya) / 2**20:.0f} MB, {time.time() - t:.1f} sn", flush=True)
            if os.environ.get("RAKKASE_ONBELLEK_DOGRULA") == "1":
                taze = akisli_yukle(yol, **k)
                ok, neden = ayni_mi(model, taze)
                print(f"ONBELLEK DOGRULAMA: {'AYNI' if ok else 'FARKLI'} ({neden})", flush=True)
                del taze
                if not ok:
                    raise RuntimeError("int8 onbellek akisli yukleme ile ayni degil")
            return model
        model = akisli_yukle(yol, **k)
        try:
            os.makedirs(os.path.dirname(dosya), exist_ok=True)
            for eski in glob.glob(os.path.join(os.path.dirname(dosya), "dit_int8_v*.pt")):
                os.remove(eski)  # eski anahtarli onbellek (yalniz bu motorun kendi dosyasi)
            t = time.time()
            gecici = dosya + ".yaziliyor"
            torch.save(model.state_dict(), gecici)
            os.replace(gecici, dosya)
            print(f"ONBELLEK int8 yazildi: {os.path.getsize(dosya) / 2**20:.0f} MB, {time.time() - t:.1f} sn", flush=True)
        except Exception as e:  # onbellek yazilamazsa uretim surer
            print(f"UYARI int8 onbellek yazilamadi: {e}", flush=True)
            if os.path.exists(dosya + ".yaziliyor"):
                os.remove(dosya + ".yaziliyor")
        return model

    def fp_sarili(cls, yol, *a, **k):
        if "acestep-v15-turbo" in str(yol):
            return asama("DiT akisli (meta iskelet + ardisik okuma + aninda int8)", lambda: dit_yukle(yol, **k))
        if "Qwen3-Embedding" in str(yol):
            # text encoder: bf16 asli, ardisik okuma; fp32 ara kopya yok (paket yolu: from_pretrained fp32 2,3 GB + mmap)
            return asama("text encoder akisli (meta iskelet + ardisik okuma, bf16)",
                         lambda: akisli_yukle(yol, nicemle=False, hedef_dtype=torch.bfloat16, **k))
        return fp_orig(cls, yol, *a, **k)

    transformers.AutoModel.from_pretrained = classmethod(fp_sarili)

    tasimalar = []
    rtd_orig = AceStepHandler._recursive_to_device

    def rtd_sarili(self, model, device, dtype=None):
        etiket = "model" if model is getattr(self, "model", None) else "vae" if model is getattr(self, "vae", None) \
            else "text_encoder" if model is getattr(self, "text_encoder", None) else type(model).__name__
        t = time.time()
        r = rtd_orig(self, model, device, dtype)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        tasimalar.append((etiket, str(device), round(time.time() - t, 2)))
        print(f"TASIMA {etiket} -> {device}: {time.time() - t:.1f} sn", flush=True)
        return r

    AceStepHandler._recursive_to_device = rtd_sarili

    # --- yukleme
    dit = AceStepHandler()
    msg, ok = asama("initialize_service(toplam)", lambda: dit.initialize_service(
        project_root=ACE, config_path="acestep-v15-turbo", device="cuda",
        offload_to_cpu=True, offload_dit_to_cpu=True,
        quantization=None))  # akisli yukleyici decoder'i zaten int8 yukler
    if not ok:
        print("baslatma basarisiz:", msg, flush=True)
        return 2

    def fp32_kopya():
        """Hesap fp32 (kalite degismezi; Pascal'da fp16 NaN). Yalniz decoder (int8 AQT dis turu + 1,5 M norm/bias) ve ust duzey
        parametreler fp32; encoder/tokenizer/detokenizer fp16 saklanir, prepare_condition sirasinda gecici fp32 (RAM 3,3 -> 1,6 GB).
        Text encoder CPU'da bf16 (dosyadaki asli), GPU'ya giderken fp32 olur."""
        dit.dtype = torch.float32
        dit.model.decoder.to(torch.float32)
        for ad, p in list(dit.model._parameters.items()):
            if p is not None:
                dit.model._parameters[ad] = torch.nn.Parameter(p.data.to(torch.float32), requires_grad=False)
        dit.silence_latent = dit.silence_latent.to(torch.float32)
        if getattr(dit, "text_encoder", None) is not None:
            dit.text_encoder = dit.text_encoder.to(torch.bfloat16)
    asama("fp32_kopya(model+text_encoder)", fp32_kopya)
    # GTX 16xx: paket VAE'yi Pascal oncesi kartlarda GPU'da fp16 yapar ve bu kartlarda NaN verir (issue #1: ilk NaN vae.decoder.block.1.res_unit1.conv1,
    # DiT ve text encoder temiz). VAE'yi GPU'da da fp32 tut: kalite sabitleri (8 adim, fp32 hesap) ayni, yalniz VAE hassasiyeti ARTAR.
    # 1050 Ti ve diger kartlarda blok calismaz: varsayilan yol degismez (1050 Ti olcumu 2026-11-23: eski/yeni kod kiyasi SNR 56,8 dB, korelasyon 0,999999; GPU'da bayt aynilik garanti degil). Elle: ayarlar.json "vae_fp32": true/false (null = karta gore).
    vae_fp32 = kart_kural.vae_fp32_gerek(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "", _AYAR.get("vae_fp32"))
    if vae_fp32:
        dit._get_vae_dtype = lambda device=None: torch.float32
        print("VAE fp32 (GPU): GTX 16xx ya da ayarlar.json vae_fp32; NaN onlemi (issue #1)", flush=True)
    env = {ad: param_envanteri(ad, m) for ad, m in (("model", dit.model), ("vae", dit.vae), ("text_encoder", dit.text_encoder))}
    yukleme_sn = round(time.time() - T0 - kilit_bekleme_sn, 1)  # kilit beklemesi haric
    print(f"yukleme bitti: {yukleme_sn:.1f} sn, RSS {rss_mb():.0f} MB, tepe {bekci.tepe_rss:.0f} MB", flush=True)
    llm = LLMHandler()

    # --- decoder yerlesik yol
    model = dit.model
    rtd_ic = dit._recursive_to_device  # sarili surum (zaman olcer)

    def decoder_tasi(device):
        """Yalniz decoder + null_condition_emb; encoder/tokenizer/detokenizer CPU'da kalir."""
        rtd_ic(model.decoder, device, torch.float32)
        for ad, p in list(model._parameters.items()):  # ust duzey parametreler (null_condition_emb)
            if p is not None and p.device.type != torch.device(device).type:
                model._parameters[ad] = torch.nn.Parameter(p.data.to(device), requires_grad=False)

    rtd_once = dit._recursive_to_device

    def rtd_yerlesik(m, device, dtype=None):
        if m is model:
            return decoder_tasi(device)
        return rtd_once(m, device, dtype)

    dit._recursive_to_device = rtd_yerlesik
    dit.offload_dit_to_cpu = False  # paketin kalici yolu: ilk parcada decoder GPU'ya, sonra kalir

    pc_orig = model.prepare_condition

    def gpu_fp32_gecici(modul):
        """Modulun parametre ve tamponlarini TEK TEK GPU'ya tasiyip orada fp32 yapar (kayan noktali olanlar);
        CPU asillari (fp16/bf16) saklanir, geri alma islevi onlari yerine koyar. Neden tek tek: m.to(cuda).to(fp32)
        tum modulu once fp16 (1,6 GB) sonra fp32 (3,3 GB) olarak GPU'da ustuste tutuyor; 4 GB VRAM tasinca Windows
        paylasimli bellege (RAM) kaciriyor -> yerlesik4'te RSS 6,5 -> 10,4 GB (bekci). Tek tek: gecici yuk 1 tensor."""
        asil = []
        for t_ in list(modul.parameters()) + list(modul.buffers()):
            asil.append((t_, t_.data))
            g = t_.data.to(dit.device)
            t_.data = g.to(torch.float32) if g.is_floating_point() else g

        def geri():
            for t_, d in asil:
                t_.data = d
            torch.cuda.empty_cache()
        return geri

    def katmanli_gpu(kok):
        """Katman katman GPU fp32 (2026-11-05 gece): kokun altindaki her modul YALNIZ KENDI dogrudan parametre/tamponlarini
        kendi forward'u suresince GPU'ya alir (on kanca), bitince CPU asillari geri (son kanca). Tepe VRAM = decoder + tek katman,
        bu yuzden decoder kosul hazirligi ve text encoder sirasinda GPU'dan inmez (eskiden parca basi ~5 sn gidis-donus).
        Ayni cekirdekler, ayni fp32 hesap: cikti degismez (rakkase.py test ile dogrulanir)."""
        bekleyen = {}

        def on(m, _a):
            asil = []
            for t_ in list(m._parameters.values()) + list(m._buffers.values()):
                if t_ is None or t_.device.type == "cuda":
                    continue
                asil.append((t_, t_.data))
                g = t_.data.to(dit.device, non_blocking=True)
                t_.data = g.to(torch.float32) if g.is_floating_point() else g
            bekleyen.setdefault(id(m), []).append(asil)  # bos da olsa: ic ice cagrida son() dogru kaydi alir

        def son(m, _a, _o):
            liste = bekleyen.get(id(m))
            if liste:
                for t_, d in liste.pop():
                    t_.data = d

        for m in kok.modules():
            if any(True for _ in m.parameters(recurse=False)) or any(True for _ in m.buffers(recurse=False)):
                m.register_forward_pre_hook(on)
                m.register_forward_hook(son)

        def hepsini_geri():
            for liste in bekleyen.values():
                while liste:
                    for t_, d in liste.pop():
                        t_.data = d
        return hepsini_geri

    def gpu_sarili(modul, ad):
        """modulun forward'u: katman katman GPU fp32; ilk cagrida hata olursa (parametresi kendi forward'u disinda kullanilan
        modul) eski yola doner: butun modul cagri suresince GPU'da, decoder gecici CPU'da."""
        f_orig = modul.forward
        geri_hepsi = katmanli_gpu(modul)
        GERI[ad] = geri_hepsi
        durum = {"katmanli": True}

        def f(*a, **k):
            t = time.time()
            if durum["katmanli"]:
                try:
                    return f_orig(*a, **k)
                except RuntimeError as e:
                    if isinstance(e, torch.cuda.OutOfMemoryError) or "device" not in str(e):
                        raise  # yalniz cihaz uyusmazligi eski yola dondurur; OOM ve baska hata yukari
                    geri_hepsi()
                    durum["katmanli"] = False
                    print(f"UYARI {ad}: katmanli GPU olmadi ({str(e)[:120]}), eski yola donuldu", flush=True)
                finally:
                    geri_hepsi(); torch.cuda.empty_cache(); torch.cuda.synchronize()
                    print(f"KOSUL {ad} katmanli GPU fp32: {time.time() - t:.1f} sn, RSS {rss_mb():.0f} MB", flush=True)
            dec_gpu = next(model.decoder.parameters()).device.type == "cuda"
            if dec_gpu:
                decoder_tasi("cpu")
            geri = gpu_fp32_gecici(modul)
            try:
                return f_orig(*a, **k)
            finally:
                geri()
                if dec_gpu:
                    decoder_tasi(dit.device)
                torch.cuda.synchronize()
                print(f"KOSUL {ad} GPU fp32 gidis-donus: {time.time() - t:.1f} sn, RSS {rss_mb():.0f} MB", flush=True)
        modul.forward = f

    # prepare_condition icinde sirayla encoder (608 M -> 2,4 GB fp32), tokenizer (105 M), detokenizer (105 M) cagrilir;
    # her biri yalniz kendi cagrisi sirasinda GPU'da olur (encoder tek basina 2,4 GB; ucu birden 3,3 GB + gecici fp16 1,6 GB sigmaz).
    GERI = {}
    gpu_sarili(model.encoder, "encoder")
    gpu_sarili(model.tokenizer, "tokenizer")
    gpu_sarili(model.detokenizer, "detokenizer")
    gpu_sarili(dit.text_encoder, "text_encoder")

    def pc_gpu(*a, **k):
        """prepare_condition GPU'da, referans yolla ayni cekirdekler: kosul modulleri gpu_sarili ile katman katman gelip gider,
        decoder GPU'da kalir (CPU'da fp32 kopya yok; CPU'da hesap denemesi RAM'i 10,5 GB'a cikardi)."""
        t = time.time()
        out = pc_orig(*a, **k)
        torch.cuda.synchronize()
        print(f"KOSUL prepare_condition toplam: {time.time() - t:.1f} sn, RSS {rss_mb():.0f} MB", flush=True)
        return out

    model.prepare_condition = pc_gpu

    ctx_once = dit._load_model_context

    @contextmanager
    def ctx_yerlesik(model_name):
        if model_name == "text_encoder":
            # text encoder forward'u gpu_sarili ile katman katman GPU fp32 (asagida); decoder GPU'da kalir. Paketin kendi
            # tasimasi (.to(device, dtype): CPU'da 2,3 GB fp32 kopya) atlanir. Paket embed_tokens'i forward disinda da cagirir:
            # kancalar onu da karsilar; hata yolunda GPU'da kalan katman olmasin diye cikista hepsi geri.
            try:
                yield
            finally:
                GERI["text_encoder"]()
            return
        with ctx_once(model_name):
            yield

    dit._load_model_context = ctx_yerlesik

    # --- uretim kancalari
    adim = {"n": 0, "sn": 0.0}

    def on_kanca(m, i):
        torch.cuda.synchronize(); adim["t"] = time.time()

    def son_kanca(m, i, o):
        torch.cuda.synchronize(); adim["n"] += 1; adim["sn"] += time.time() - adim["t"]

    dit.model.decoder.register_forward_pre_hook(on_kanca)
    dit.model.decoder.register_forward_hook(son_kanca)
    sayac = {"text_encoder": [0, 0.0], "vae_decode": [0, 0.0]}

    def sar(obj, ad, anahtar):
        o = getattr(obj, ad)

        def f(*a, **k):
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            t = time.time(); r = o(*a, **k)
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            sayac[anahtar][0] += 1; sayac[anahtar][1] += time.time() - t
            return r
        setattr(obj, ad, f)

    sar(dit.text_encoder, "forward", "text_encoder")
    sar(dit.vae, "decode", "vae_decode")
    # VAE cozme ortusmesi (latent kare, 2026-11-05 gece olcumu): paket 4 GB kartta 128'lik pencereyi 64 -> 32 ortusmeyle kullanir,
    # isin yarisi atilir. 16 (decoder alici alani ~9 kare): 100 sn'de VAE 26,6 -> 17,7 sn, ayni surecte 16 ile 8 arasi fark -61,6 dB,
    # eski ciktiya SNR 58,8 dB (GPU gurultu tabani); VRAM ayni. Pencereyi buyutmek (256/512) VRAM tasirip yavaslatti (33,8 / 29,8 sn).
    VAE_ORTUSME = 16
    vae_ayar = {"ortusme": VAE_ORTUSME}
    td_orig = dit.tiled_decode

    def td_sarili(latents, chunk_size=None, overlap=64, offload_wav_to_cpu=None):
        return td_orig(latents, chunk_size=chunk_size, overlap=vae_ayar["ortusme"] or overlap, offload_wav_to_cpu=offload_wav_to_cpu)
    dit.tiled_decode = td_sarili

    sonuclar = []

    def dokum_yaz(hata=None):
        """Her parcadan sonra (ve hatada) yeniden yazilir: yarida kalan kosuda biten parcalarin olcumu kaybolmaz."""
        ozet = dict(ad=args.ad, asamalar=ASAMALAR, envanter_mb=env, kilit_bekleme_sn=kilit_bekleme_sn, yukleme_toplam_sn=yukleme_sn,
                    parcalar=sonuclar, vae_fp32=vae_fp32, rss_tepe_mb=round(bekci.tepe_rss), min_bos_ram_mb=round(bekci.min_bos),
                    toplam_sn=round(time.time() - T0, 1), hata=hata)
        with open(os.path.join(cikti, "dokum.json"), "w", encoding="utf-8") as f:
            json.dump(ozet, f, ensure_ascii=False, indent=1)

    def parca_uret(p):
        adim["n"], adim["sn"] = 0, 0.0
        for v in sayac.values():
            v[0], v[1] = 0, 0.0
        tasimalar.clear()
        torch.cuda.reset_peak_memory_stats()
        t1 = time.time()
        sozlu = (bool(p.get("lyrics")) and p["lyrics"].strip().lower() != "[instrumental]"
                 and not p.get("instrumental", False))  # plan'da gercek soz varsa sozlu sarki (2026-11-05)
        params = GenerationParams(caption=p["caption"], lyrics=p.get("lyrics") or "[Instrumental]", instrumental=not sozlu,
                                  vocal_language=p.get("vocal_language", "unknown") if sozlu else "unknown", duration=p["sure"],
                                  bpm=p.get("bpm"), keyscale=p.get("ton", ""), timesignature=p.get("olcu", "4"),
                                  seed=p["tohum"], inference_steps=p.get("adim", 8), shift=float(p.get("shift", 1.0)),
                                  thinking=False, use_cot_metas=False, use_cot_caption=False, use_cot_language=False)
        if p.get("gorev", "text2music") == "cover":  # 2026-11-07: ezgiyi biz yazariz (MIDI referans) -> paketin Cover gorevi;
            # plan alanlari: kaynak_ses (wav), cover_gucu (0-1: 8 adimin ilk int(8*g) adimi kaynak kodlarla, kalani yalniz metinle).
            # Sure kaynaktan gelir (paket). Alan yoksa eski text2music yolu bit duzeyinde ayni (bu satirlar calismaz).
            params.task_type = "cover"
            params.src_audio = p["kaynak_ses"]
            params.audio_cover_strength = float(p.get("cover_gucu", 1.0))
        conf = GenerationConfig(batch_size=1, use_random_seed=False, audio_format="wav")
        tmp = os.path.join(cikti, "_tmp_" + p["ad"])
        os.makedirs(tmp, exist_ok=True)
        try:
            res = generate_music(dit, llm, params, conf, save_dir=tmp)
            sure = time.time() - t1
            if not res.success:
                raise RuntimeError(f"generate_music: {res.error}")
            hedef = os.path.join(cikti, p["ad"] + ".wav")
            shutil.move(res.audios[0]["path"], hedef)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)  # hata yolunda da ara klasor kalmaz
        if sozlu and p.get("soz_zamani", True):  # varsayilan acik (kullanici 2026-11-06: her sozlu uretim kelime zamanini birakir); ACE-Step'in kendi soz zamani (DiT cross-attention), uretimden sonra; sesi degistirmez
            t_sz = time.time(); ek = res.extra_outputs or {}
            try:
                if ek.get("pred_latents") is None:
                    raise RuntimeError("ara veri yok (save_memory_mode?)")
                if params.shift != 1.0:
                    print("UYARI: shift != 1; paketin soz zamani son adimi t=1/adim varsayar, hizalama kayabilir", flush=True)
                sz = dit.get_lyric_timestamp(
                    pred_latent=ek["pred_latents"][:1], encoder_hidden_states=ek["encoder_hidden_states"][:1],
                    encoder_attention_mask=ek["encoder_attention_mask"][:1], context_latents=ek["context_latents"][:1],
                    lyric_token_ids=ek["lyric_token_idss"][:1], total_duration_seconds=float(p["sure"]),
                    vocal_language=params.vocal_language, inference_steps=int(params.inference_steps), seed=42)  # paketin arayuzuyle ayni (lrc_utils.py: seed=42)

                def _d(x):
                    return x if isinstance(x, (str, int, float, bool, type(None))) else (
                        [_d(i) for i in x] if isinstance(x, (list, tuple)) else (
                            {k: _d(v) for k, v in x.items()} if isinstance(x, dict) else _d(vars(x))))
                sz = _d(sz)
            except Exception as e:
                sz = {"success": False, "error": repr(e)}
            sz["hesap_sn"] = round(time.time() - t_sz, 2)
            with open(os.path.join(cikti, p["ad"] + ".soz_zamani.json"), "w", encoding="utf-8") as f:
                json.dump(sz, f, ensure_ascii=False, indent=1)
            print("SOZ_ZAMANI", p["ad"], sz.get("success"), sz.get("error"), sz["hesap_sn"], flush=True)
        return dict(ad=p["ad"], sure_sn=p["sure"], tohum=p["tohum"], shift=params.shift, vae_ortusme=vae_ayar["ortusme"], uretim_sn=round(sure, 1),
                    dit_adim=adim["n"], dit_adim_toplam_sn=round(adim["sn"], 2),
                    dit_adim_ms=round(1000 * adim["sn"] / max(1, adim["n"]), 1),
                    text_encoder=dict(cagri=sayac["text_encoder"][0], sn=round(sayac["text_encoder"][1], 2)),
                    vae_decode=dict(cagri=sayac["vae_decode"][0], sn=round(sayac["vae_decode"][1], 2)),
                    tasimalar=list(tasimalar), tasima_toplam_sn=round(sum(t[2] for t in tasimalar), 2),
                    vram_tepe_mb=round(torch.cuda.max_memory_allocated() / 2**20),
                    vram_reserved_mb=round(torch.cuda.max_memory_reserved() / 2**20),
                    rss_mb=round(rss_mb()), rss_tepe_mb=round(bekci.tepe_rss), dosya=hedef)

    secili = {a.strip() for a in args.yalniz.split(",") if a.strip()}
    kod = 0
    dokum_yaz()
    try:
        for p in plan["parcalar"]:
            if secili and p["ad"] not in secili:
                continue
            try:
                kayit = parca_uret(p)
            except Exception as e:
                print("HATA", p["ad"], repr(e), flush=True)
                dokum_yaz(hata=f"{p['ad']}: {e!r}")
                kod = 3
                break
            print("PARCA", json.dumps(kayit, ensure_ascii=False), flush=True)
            sonuclar.append(kayit)
            dokum_yaz()
    finally:
        kilit.close()
        if args.kilit:
            print("GPU kilidi birakildi", time.strftime("%H:%M:%S"), flush=True)
        bekci.dur = True
    print("DOKUM", os.path.join(cikti, "dokum.json"), f"toplam {time.time() - T0:.1f} sn RSS tepe {bekci.tepe_rss:.0f} MB", flush=True)
    return kod


if __name__ == "__main__":
    try:
        kod = main()
    except SystemExit as e:  # argparse vb.
        kod = e.code if isinstance(e.code, int) else 2
    except BaseException:  # yukleme hatasi: iz yazilir, kilit birakilir, surec asili kalmaz
        traceback.print_exc()
        kod = 2
    finally:
        KILIT.close()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(kod or 0)  # ACE-Step arka plan is parcaciklari sureci acik tutuyor (2026-11-02 kaydi)
