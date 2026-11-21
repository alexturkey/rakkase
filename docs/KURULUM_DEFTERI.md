# "Rakkase" — ACE-Step 1.5 kurulum ve çalıştırma defteri (GTX 1050 Ti 4 GB, 16 GB RAM)

Amaç: bu klasördeki kurulumu hiç bilmeyen biri (insan ya da ajan), başka bir bilgisayarda sıfırdan kurup **aynı çıktıyı** (aynı tohum, aynı
ayarlar) alabilsin. Kayıt: 2026-11-02 ilk kurulum, 2026-11-05 hızlandırma/sığdırma işi. Kaynak düzeyi her satırda:
**ölçtüm** (bu makinede ölçüldü), **okudum** (belge/kod/issue; denenmedi), **tahmin** (doğrulanmadı).

Yol değişkenleri (kendi makinene göre doldur; değerler `<RAKKASE>\ayarlar.json`'da, örneği `ayarlar.ornek.json`):
- `<RAKKASE>` = bu uygulamanın kökü (`rakkase.py` giriş kapısı, `motor\`, `araclar\`, `docs\`, `ornekler\`, `testler\`)
- `<ACE_KOK>` = ACE-Step 1.5 klonu + venv + checkpoints (`ayarlar.json: ace_kok`)
- `<UV>` = uv ikilisi ve yönetilen Python/önbellek kökü (`uv.exe`, `python\`, `cache\`)
- `<KILIT_PY>` = isteğe bağlı GPU kilidi modülünün kaynak kökü (`ayarlar.json: kilit_src`; kilit altyapısı yoksa `"kilit": false`)
- Ham ölçüm logları ve csv'ler bu deponun dışında, yerel iş klasöründe kaldı (git dışı; sayıların özeti `OLCUMLER.md`).

## 1. Donanım ve işletim sistemi (ölçtüm)

| Parça | Değer |
|---|---|
| GPU | NVIDIA GeForce GTX 1050 Ti, 4 GB, Pascal sm_61 (bf16 yok, fp16 hesap 1/64 hızda, fp32 asıl hız) |
| RAM | 16 GB (16.657.056 KB görünür); diğer uygulamalarla boşta ~9,5-10,5 GB boş |
| Disk | Model ve venv: ST2000LM007 2 TB 2,5" 5400 rpm **SMR HDD** (E:); dağınık okumada 12-24 MB/s'ye düşer. C: NVMe SSD 256 GB (boş 17 GB, proje kuralı: 15 GB altına inilmez) |
| OS | Windows 10 Home 10.0.19045, Git Bash + PowerShell 5.1 |
| CUDA sürücü | nvidia-smi çalışır; torch cu128 tekerleği kendi CUDA'sını taşır (ayrı CUDA Toolkit kurulmaz) |

## 2. Sürümler ve kilitler (ölçtüm)

| Parça | Sürüm / kaynak |
|---|---|
| ACE-Step 1.5 kodu | github.com/ace-step/ACE-Step-1.5, commit `ca1e85f` ("fix(jetson): remove GPL video codecs…", #1190) |
| uv | 0.13.6 (329bf9448 2026-10-26), `<UV>\uv.exe` |
| Python | CPython 3.11.18 (uv yönetimli, `<UV>\python\cpython-3.11.18-windows-x86_64-none`) |
| torch | 2.7.1+cu128 (sm_61 destekli) |
| torchao | 0.16.0 (torch 2.7.1 ile "incompatible torch version" uyarısı verir; cpp uzantısı yüklenmez — `.to()` hızlı yolu düşer, bkz. §6.3) |
| transformers | 4.57.6 |
| accelerate | 1.12.0; diffusers 0.37.1; huggingface_hub 0.36.0; numpy 2.3.5; psutil 7.2.1; soundfile; vector_quantize_pytorch |
| Tam kilit | `<ACE_KOK>\.venv` içinden `uv pip freeze > kilit.txt` ile alınır (uv.lock paket kökünde: `uv sync` aynı sürümleri kurar) |

## 3. Model dosyaları (ölçtüm)

HF deposu `ACE-Step/Ace-Step1.5` (MIT; model kartı üretilen müziğin ticari kullanımına izin verir — okudum). Yalnız DiT yolu için gerekenler,
`<ACE_KOK>\checkpoints\` altına (`huggingface_hub.snapshot_download(repo_id="ACE-Step/Ace-Step1.5", local_dir=..., allow_patterns=[...])`,
10 satırlık bir snapshot_download çağrısı yeter; Rakkase'de ayrı betiği yok):

| Klasör | İçerik | Boyut |
|---|---|---|
| `acestep-v15-turbo/` | DiT `model.safetensors` (BF16, 677 tensör, 2,39 M×10³ param: decoder 1575 M, encoder 608 M, tokenizer 105 M, detokenizer 105 M), `config.json`, `modeling_acestep_v15_turbo.py`, `silence_latent.pt` | 4,57 GB |
| `vae/` | AutoencoderOobleck | 322 MB |
| `Qwen3-Embedding-0.6B/` | text encoder (BF16, 310 tensör) + tokenizer | 1,2 GB |
| `acestep-5Hz-lm-1.7B/` | yalnız config (LM indirilmedi, kullanılmaz) | 44 MB |

Parmak izi (sha256, 2026-11-06 ölçüldü; indirme 2026-11-02, HF commit kaydedilmemişti; kod paketi `ace-step` 1.5.0):
- `acestep-v15-turbo/model.safetensors` (4.787.825.604 bayt): `3f6e0797fad420a39bd33979eb6e840e30989e34a3794e843d23b60ec6e422d7`
- `vae/diffusion_pytorch_model.safetensors`: `da17edb604c40deaf09e9b24974e590d1ca83a374070e5d0884cfa4bed9a99b0`
Doğrulama: `sha256sum <ACE_KOK>/checkpoints/acestep-v15-turbo/model.safetensors` (~45 sn).

LM (5 Hz dil modeli, "thinking") **kapalı**: 4 GB kartta yer yok; kalite çizgimiz DiT-only.

## 4. Kurulum adımları (sırayla)

1. `git clone https://github.com/ace-step/ACE-Step-1.5 <ACE_KOK>` ve `git checkout ca1e85f`.
2. uv: `<UV>\uv.exe` indir (0.13.6, resmi sürüm). Ortam: `UV_PYTHON_INSTALL_DIR=<UV>\python`, `UV_CACHE_DIR=<UV>\cache`.
3. `cd <ACE_KOK>` → `uv python install 3.11` → `uv sync` (uv.lock'tan torch 2.7.1+cu128 dahil kurar). Not: paket `ace-step` **editable**
   (`.venv` içinde `file:///<ACE_KOK>` olarak kayıtlı).
4. Modeli indir (§3). `HF_HUB_OFFLINE=1` ile çalıştırılır (ağ yoklaması yok).
5. Uygulama: `git clone <rakkase deposu> <RAKKASE>`; `ayarlar.json` içinde `ace_kok` (ve kilit) kendi yollarına. İçerik: `rakkase.py`
   (giriş kapısı: uret/bol/test/mp3), `motor\dokum_muzik.py` (üretim motoru: akışlı yükleme + decoder yerleşik + ölçüm) ve
   `motor\calistir.py` (venv başlatıcı sarmalayıcı), `araclar\` (`kiyas_muzik.py` aynılık, `olc_lufs.py`, `bellek_izle.ps1`),
   `testler\plan_kiyas_15sn.json` + `testler\referans\` (2 Kasım referans wav), `ornekler\*.json` planlar.
6. Duman testi: §8 "Doğrulama" (`python <RAKKASE>\rakkase.py test`).

## 5. Çalıştırma

Ortak: `HF_HUB_OFFLINE=1 PYTHONIOENCODING=utf-8`; GPU işi yalnız kilitle (`--kilit`: betik modeli yükledikten sonra kilidi alır, üretim
bitince bırakır; başka makinede bayrağı verme).

Giriş kapısı (önerilen; her komut ve plan alanı örnekli: `docs/KULLANIM.md`):
```
python <RAKKASE>\rakkase.py uret --plan plan.json --cikti <klasör> [--ad <koşu adı>] [--yalniz ad1,ad2]
python <RAKKASE>\rakkase.py bol  --plan plan.json        (10 dk ön plan sınırı için koşu grupları)
python <RAKKASE>\rakkase.py test                          (15 sn kıyas parçası + referansla karşılaştırma)
python <RAKKASE>\rakkase.py mp3  <klasör>
```
`uret` arkada `<ACE_KOK>\.venv\Scripts\python.exe <RAKKASE>\motor\calistir.py --plan ... --cikti ... --ad ... [--kilit]`
çalıştırır (`HF_HUB_OFFLINE=1`). Çıktı: `<klasör>\<koşu adı>\<parça adı>.wav` (48 kHz stereo) + `.mp3` (192k)
+ `dokum.json` (aşama süreleri, RSS/VRAM, taşımalar); sonra her parça `uretimler/` arşivine (`KULLANIM.md`). Eski sade yol (`uret_muzik.py --fp32`, 2 Kasım) artık kullanılmıyor; yalnız
referans wav onunla üretildi.
Plan biçimi: `docs/KULLANIM.md` (tek yer).

Kalite çizgisi (değişmez): turbo **8 adım** (modelin kendi değeri; turbo CFG desteklemez, `guidance_scale` 1), **int8 ağırlık**
(torchao `Int8WeightOnlyConfig`, yalnız `decoder.*` Linear; paketin Tier-1 yolu), **fp32 hesap**, LM kapalı, tohum sabit.

## 6. Duvarlar ve çözümleri (kronolojik)

### 6.1 fp16 NaN (2 Kasım, F-99) → fp32 hesap (ölçtüm)
Paket Pascal'da bf16 olmadığı için fp16 yükler ve "eager" dikkat kullanır (softmax fp32'ye yükselir; issue #924/#927, commit 383c3d2).
Bizde fp16 yine NaN latent verdi (deneme 1, 2 Kasım 03:06). Çözüm: model yüklendikten sonra `dit.dtype = float32`, `model.to(float32)`,
`silence_latent` fp32 (`--fp32`). Topluluk ölçümü (okudum, PR #1352): taşan katman `encoder.lyric_encoder.layers[7].mlp.down_proj`
(çıkış ~505.000 > fp16 azami 65.504); yalnız o katmanı fp32 hesaplamak da yeter. Pascal'da fp16 hesap zaten 1/64 hızda olduğundan fp32
hesap doğru seçim; mesele yalnız **ağırlık depolaması** (bkz. 6.4).

### 6.2 Yükleme 6-11 dk ve RAM tepesi 10,6 GB (ölçtüm, 2 ve 4 Kasım)
`AutoModel.from_pretrained(dtype=fp16)`: safetensors mmap sayfaları + fp16 kopya + sonra int8 kopya + bizim fp32 kopyası üst üste.
SMR HDD'de mmap dağınık okuma 12-24 MB/s. 4 Kasım 23:45 koşusu: 6. dakikada RSS 8,2 GB hâlâ `from_pretrained` içinde; boş RAM 340 MB,
sayfa dosyası E:'de 2 GB; Claude Code'un bellek bekçisi süreci öldürdü (iki kez).
**Çözüm: akışlı yükleyici** (`dokum_muzik.py: akisli_yukle`; 2026-11-05 akşamından beri tek yol): iskelet `meta` cihazda `from_config` ile kurulur (disk okumasız; `ResidualFSQ`
ve `Qwen3RotaryEmbedding` `.item()` çağırıp kalıcı olmayan tampon kurduğu için yalnız onlar CPU'da kurulur), `model.safetensors` dosya
sırasıyla düz ardışık okunur (`readinto`, mmap yok), her tensör bf16→fp16 (paketin dönüşümüyle aynı) yerine takılır, decoder Linear'ları
paketin aynı süzgeci ve aynı `Int8WeightOnlyConfig` ile **anında** int8'e çevrilir; text encoder bf16 aslıyla aynı yöntemle yüklenir.
Ölçüm: DiT 16 sn (sıcak önbellek) / 52-55 sn (soğuk), text encoder 11 sn (paket yolu 95-101 sn), VAE 32-42 sn (paket yolu; küçük),
yükleme toplam 122-156 sn, RSS 6,4 GB (paket yolu: 6+ dk, 10,6 GB).

### 6.3 Her üretimde 63 sn DiT taşıma (ölçtüm, log 23:52)
"model.to() raised NotImplementedError (AffineQuantizedTensor on older torch). Moving parameters individually: 63 sn". İki neden:
(a) torchao 0.16 + torch 2.7.1 uyumsuzluğu `.to()` hızlı yolunu düşürür (issue #142'de torchao 0.12'ye inince 11 → 1,4 sn — okudum);
(b) asıl: RAM takası + DiT'in fp32 kopyası 4,6 GB (decoder int8 1,5 GB + **nicemlenmeyen** encoder/tokenizer/detokenizer fp32 3,1 GB)
4 GB VRAM'e sığmıyor, Windows paylaşımlı belleğe taşıyor. RAM sağlıklıyken aynı taşıma 1,1 sn (ölçtüm, 5 Kasım).
**Çözüm: decoder yerleşik modu** (motorda tek yol; eski bayrak `--decoder_yerlesik 1`): yalnız decoder (int8 + fp32 hesap) GPU'da kalıcı; encoder/tokenizer/
detokenizer CPU'da **fp16** saklanır ve yalnız `prepare_condition` (üretim başına bir kez) için GPU'ya fp16 taşınıp orada fp32 olur,
sonra fp16'ya inip CPU'ya döner (CPU'da fp32 kopya yok); text encoder CPU'da bf16, GPU'ya bf16 taşınıp orada fp32 (referans yolla birebir
aynı değerler); text encoder ve koşul modülleri GPU'dayken decoder geçici CPU'ya alınır (VRAM 4 GB). Paketin `offload_dit_to_cpu=False`
kalıcı yolu kullanılır; `_recursive_to_device` yalnız decoder'ı taşır.

### 6.4 RAM denemeleri (ölçtüm, 5 Kasım)
- yerlesik1: text encoder GPU'ya `.to(device, dtype=fp32)` ile → dönüşüm CPU'da, RSS 8,0 → 10,05 GB, bekçi durdurdu. Düzeltme: bf16 taşı,
  GPU'da fp32.
- yerlesik3: `prepare_condition`'ı CPU'da fp32 hesaplama denemesi → RSS 6,4 → 10,5 GB (fp16→fp32 dönüşüm + CPU çekirdek çalışma alanı),
  bekçi durdurdu. Düzeltme: koşul GPU'da (6.3'teki gidiş-dönüş).
- Bekçi: `dokum_muzik.py` içinde `Bekci` iş parçacığı boş RAM 30 sn boyunca < 150 MB kalırsa süreci durdurur (`os._exit(4)`; ilk sürümde 1024 MB'tı, kullanıcı kararıyla
  yalnız gerçek çökme sınırına indi); `bellek_izle.ps1` 5 sn'de
  bir RSS/boş RAM/sayfa dosyası yazar (uv trampoline + çocuk süreç aynı komut satırını taşır: en büyük bellekli olan seçilir).

### 6.5 uv başlatıcısı bozuldu: "uv trampoline failed to spawn Python child process (os error 2)" (ölçtüm)
Kök neden: proje klasörü `<ESKI_KLASOR>` → `<YENI_KLASOR>` olarak yeniden adlandırılmış. uv 0.13 trampoline'i
(`.venv\Scripts\python.exe`) çalıştıracağı Python'un **tam yolunu exe'nin içine gömer** (pyvenv.cfg'ye bakmaz; bayt düzeyinde okundu:
`<ESKI_KLASOR>\araclar\uv\python\cpython-3.11-windows-x86_64-none\python.exe`). pyvenv.cfg düzeltmek ve junction açmak bu yüzden işe
yaramadı. Aynı eski yol `Scripts\*.exe` paket komutlarında (uv script trampoline + zip) ve `HKCU\Software\Python\Astral\CPython3.11.18`
kayıt defteri girdisinde de vardı; klasik venv'lerde (pip sargıları, distlib stub + `#!<yol>` + zip) de.
Onarım (yedek önce, paketlere dokunmadan):
1. `python.exe`/`pythonw.exe`/`pyvenv.cfg` → `.yedek_20261105`; `uv venv --allow-existing --no-project --python <gerçek 3.11.18 yolu> <ACE_KOK>\.venv`
   yalnız başlatıcıları ve cfg'yi yeniden yazar (site-packages'a dokunmaz). Test: `import torch, acestep` tamam.
2. `acestep*.exe`: `uv pip install --reinstall --no-deps -e <ACE_KOK>`; diğer paket komutları: `uv pip install --reinstall --no-deps
   <paket>==<sürüm>` (önce `Scripts_exe_yedek_20261105.zip`).
3. Kayıt defteri: `reg export HKCU\Software\Python\Astral <yedek>.reg /y`, sonra `<ESKI_KLASOR>` geçen değerler yeni yola.
4. Klasik venv pip sargıları: exe içindeki `#!<ESKI_KLASOR>\...` satırı yeni yola yazılır (pip'in ürettiği biçimin aynısı); test `pip.exe --version`.
Ders: venv taşınırsa/klasör adı değişirse uv venv'lerinde başlatıcılar yeniden yazılmalı; `uv venv --relocatable` ile kurmak bunu önler (okudum).
Ayrıca: kabuk/araç katmanında `\v` dikey sekmeye dönüşebilir; Windows yolları Edit aracıyla ya da `bytes([92])` ile yazılır.

### 6.6 Claude Code bellek bekçisi
Makine sıkışınca Claude Code arka plan kabuğunu öldürür (iki koşu böyle gitti). Bağımsız/nohup süreç açmak **yasak** (kullanıcı kararı);
çözüm işin RAM'ini düşürmek (6.2-6.4). Boş RAM 1 GB altına inerse dur ve bildir.

## 7. Denenip işe yaramayanlar / reddedilenler
- CPU'da `prepare_condition` (6.4): RAM 10,5 GB. Reddedildi.
- Text encoder'ı `.to(device, dtype)` ile taşımak (6.4): CPU'da fp32 ara kopya. Reddedildi.
- Modeli meta cihazda kurarken FSQ/rotary modüllerini de meta'da bırakmak: `.item()` hatası ve `inv_freq` boş kalır. Yalnız onlar CPU'da.
- Hazır int8 durum dosyası (`--durum`, torch.save state_dict + meta iskelet + assign): akışlı yükleyici 16-55 sn olunca gerek kalmadı
  (dosya 3 GB daha yer tutardı); ölçülmedi. Kodu 2026-11-05 akşamı silindi (`git tag paket-yolu-son`).
- uv çevrimdışı yeniden kurulum (`--offline`): önbellekte paket arşivleri var ama indeks meta verisi yok, çözümleme düşüyor; ağ açık gerekir.
- int8'den aşağı (int4/GGUF) ya da adım düşürme: kalite çizgisi dışı, denenmedi. GGUF DiT için zaten yok (AdaLN; okudum, Comfy-Org tartışması).
- torchao 0.12'ye inmek: `.to()` fallback'i çözer ama bizde taşıma zaten 1,1 sn (RAM sağlıklıyken); denenmedi.

## 8. Doğrulama
1. Kurulum duman testi: `<ACE_KOK>\.venv\Scripts\python.exe -c "import torch, acestep, torchao; print(torch.cuda.is_available())"` → True.
2. Referans parça: `<RAKKASE>\testler\plan_kiyas_15sn.json` (2 Kasım aday1: caption "upbeat modern pop instrumental…", 15 sn, 120 bpm,
   C Major, 4/4, tohum 42). Eski yol çıktısı `<RAKKASE>\testler\referans\aday1_intro_neseli_15sn.wav` (int8 + fp32, LM kapalı).
3. `python <RAKKASE>\rakkase.py test` → üretir ve `araclar\kiyas_muzik.py referans.wav yeni.wav` ile karşılaştırır: max örnek farkı,
   SNR, korelasyon, log-mel farkı, LUFS/tepe. Ölçüt: korelasyon > 0,999 ve SNR > 40 dB (bit aynılığı GPU'da beklenmez). Sonuç: §9.
4. Bellek: `bellek_izle.ps1` tepe RSS; boş RAM hiç 1 GB altına inmemeli.

## 9. Ölçümler (ölçtüm; 15 sn referans parça, tohum 42)

| Koşu | Yükleme | RSS tepe | Üretim | Not |
|---|---|---|---|---|
| 2 Kasım, paket yolu (int8 + fp32 kopya, CPU+DiT offload) | 7-11,5 dk | ~9-10 GB (4 Kasım: 10,6 GB) | 137 sn (15 sn), 294 sn (20 sn), 522 sn (90 sn) | her üretimde DiT taşıma 63 sn |
| 4 Kasım 23:45, paket yolu | 6+ dk'da hâlâ yüklemede | 8,2 GB (öldürüldü) | — | bekçi |
| 5 Kasım akis1 (akışlı DiT) | 169 sn | 9,6 GB | — (bekçi, text encoder fp32) | |
| 5 Kasım yerlesik2/3 (akışlı DiT + TE, decoder yerleşik) | 122-156 sn | 6,4 GB yüklemede | — (6.4'teki iki deneme) | decoder → GPU 1,1 sn |
| 5 Kasım yerlesik4 | 105 sn | 10,4 GB (bekçi) | — | koşul modülleri toplu `.to(cuda).to(fp32)`: VRAM taştı, RAM'e kaçtı (6.7) |
| 5 Kasım yerlesik5 | 136 sn | 6,4 GB | — | Claude Code bellek temizleyicisi kapattı (6.6); kod hatası değil |
| **5 Kasım yerlesik6 (son hal, ön planda)** | **136 sn** | **9,1 GB (üretimde; yüklemede 6,4)** | **37,4 sn (15 sn)**; toplam duvar 157 sn | DiT 8×785 ms, VAE 4,9 sn, TE 3,3 sn, koşul 10+2,2 sn, taşımalar 7,4 sn; VRAM tepe 2,65 GB |
| 5 Kasım yerlesik7 (tekrar, aynı tohum) | 130 sn | 9,1 GB | 32,7 sn | determinizm kıyası aşağıda |
| 5 Kasım sarki1 (100 sn Türkçe sözlü, tohum 2026) | 133 sn | 9,1 GB | **75,3 sn (100 sn)**; toplam duvar 214 sn | DiT 8×3,07 sn = 24,5 sn, VAE 27,4 sn, TE 5,3 sn; 2 Kasım'da 90 sn parça 522 sn idi |

Aynılık (§8.3, `kiyas_muzik.py`, ölçtüm):
- yerlesik6 vs 2 Kasım aday1 (eski paket yolu, tohum 42): SNR 43,0 dB, korelasyon 0,999987, max örnek farkı 0,047, log-mel ort. fark 0,040,
  LUFS -19,3 / -19,2, tepe -0,9 dBTP. Aynı parça; fark fp32 çekirdek sırası düzeyinde.
- yerlesik6 vs yerlesik7 (aynı kod, aynı tohum, iki koşu): SNR 53,2 dB, korelasyon 0,999999, max fark 0,007. Yani GPU'da koşudan koşuya
  bile bit düzeyi aynılık yok (cuDNN/atomik toplama); 43 dB'lik eski-yeni farkı bu doğal gürültünün hemen üstünde.

### 6.7 Koşul modülleri toplu taşınınca VRAM taşması (ölçtüm, yerlesik4)
encoder+tokenizer+detokenizer'ı `m.to(cuda).to(float32)` ile taşımak GPU'da önce fp16 kopya (1,6 GB) sonra fp32 kopya (3,3 GB) tutar;
4 GB VRAM taşınca Windows sürücüsü paylaşımlı belleğe (RAM) kaçırır, RSS 6,5 → 10,4 GB. Çözüm: `gpu_fp32_gecici` — tensör tensör GPU'ya
kopyala, orada fp32 yap, CPU fp16 aslını sakla ve çağrı bitince yerine koy; encoder/tokenizer/detokenizer yalnız kendi forward'ı
süresince GPU'da (`gpu_sarili`), text encoder aynı yolla. Not: RSS üretimde yine 9,1 GB'a çıkıyor (CUDA ana bellek tamponları +
decoder'ın CPU gidiş-dönüşü; tahminim), ama boş RAM 1 GB altına inmedi ve bekçi (150 MB / 30 sn eşiği) devreye girmedi.

## 9b. Üretim tüyoları (5 Kasım gece, 1 şarkı + 6 çeşit parça; ölçtüm, dinleme kararı kullanıcının)

Sürümler/ayarlar aynı: akışlı yükleme + decoder yerleşik, turbo 8 adım, int8 decoder + fp32 hesap, LM kapalı.

| Parça | Süre | DiT adım | Üretim | Not |
|---|---|---|---|---|
| ref aday1 (enstr.) | 15 sn | 0,79 sn | 33-37 sn | koşunun ilk parçası: koşul hazırlığı 10 sn, TE 3,3 sn |
| gece şarkısı (erkek vokal, tr) | 100 sn | 3,07 sn | 75 sn | tek parça koşu |
| 1 duet (tr) | 150 sn | 4,62 sn | 121 sn | koşunun ilk parçası |
| 2 koro (tr) | 120 sn | 3,25 sn | 70,5 sn | aynı süreçte 2.: TE 0,1 sn |
| 3 halk (tr) | 130 sn | 3,81 sn | 77,9 sn | aynı süreçte 3. |
| 4 rap (tr) | 110 sn | 3,50 sn | 92,7 sn | 2. koşunun ilk parçası: TE 7,2 sn |
| 5 oryantal (enstr., `[Instrumental]`) | 120 sn | 3,19 sn | 70,4 sn | aynı süreçte 2. |
| 6 çocuk (tr) | 90 sn | 2,49 sn | 57,2 sn | aynı süreçte 3. |

Koşu toplamları (ölçtüm): koşu 1 (400 sn ses) 6 dk 53 sn, koşu 2 (320 sn ses) 6 dk 19 sn (yükleme 151 sn); 720 sn müzik 13 dk 12 sn.

- Süre ile adım süresi yaklaşık doğrusal: ~0,03 sn/adım × ses saniyesi (+ ilk parçada ısınma). Kaba kural: üretim ≈ 0,6-0,8 × ses süresi
  (sn), artı süreç başına yükleme ~120-135 sn. 10 dk'lık ön plan sınırında 400 sn ses sığdı (yükleme + 3 parça = 6 dk 53 sn ölçtüm); ama
  300 sn üstü tek parça doğrusal değil (360 sn: 45 sn/adım), bu yüzden `on_plan_ses_siniri_sn` 300 (`SINIRLAR.md`).
- Çok parça tek süreçte: `rakkase.py bol --plan` koşu gruplarını (`--yalniz ad1,ad2,...`) verir, plan bölünmez; yükleme süreç başına
  bir kez. Text encoder ilk parçada 3-5 sn, sonrakilerde 0,1 sn (ısınmış).
- Sözlü parça: plan'da `lyrics` (`[Verse 1]`, `[Chorus]`, `[Bridge]`, `[Outro]` etiketli satırlar) + `vocal_language: "tr"` yeter;
  caption İngilizce kalır (vokal türü oraya: "soft intimate male vocal", "male and female duet", "choir"). `lyrics` tam olarak
  `[Instrumental]` ise betik parçayı enstrümantal sayar (instrumental=True, dil unknown); caption'a yine `no vocals` yaz.
- Dil `tr` geçerli listede (`acestep/constants.py`); modelin Türkçe telaffuzu/söz anlaşılırlığı kulakla değerlendirilir, betik ölçmez.
- Her wav çıkınca mp3: `ffmpeg -i x.wav -c:a libmp3lame -b:a 192k x.mp3` (CPU, 1-2 sn); wav 48 kHz stereo 16 bit (100 sn ≈ 38 MB).
- Aynı tohum iki koşuda bit düzeyi aynı değil (SNR 53 dB), kulak için aynı; "aynı parça" kararı için tohum + plan yeter.
- RAM: üretimde RSS 9,1 GB'a çıkar ve orada kalır; sistemde başka ağır iş (tarayıcı sekmeleri, başka model) açıkken boş RAM 1 GB
  altına inebilir. Claude Code arka plan kabuğunu bellek sıkışınca kapatır: üretimi ön planda (tool timeout 600 s) çalıştır.
- Araç adı: kullanıcı 5 Kasım gece "Rakkase" dedi (yalnız ad; klasör/komut adı değişmedi).

## 10. Kaynaklar
- Paket: github.com/ace-step/ACE-Step-1.5 (`docs/en/GPU_COMPATIBILITY.md`: Tier 1 ≤4 GB = DiT-only, INT8, CPU+DiT offload; `docs/en/DCW.md`).
- Issue/PR: #924, #927 (pre-Ampere NaN → eager attention, commit 383c3d2); #1274 (fp32 fallback önerisi, kapandı); #1152 (PR, kapandı);
  #1352 (PR, açık: lyric encoder down_proj fp32); #142 (RAM sızıntısı, torchao 0.12 notu, commit 55717b8); #736 (yavaşlama/VRAM); #1319 (lowvram offload).
- Nicemli checkpoint kalıbı: huggingface.co/docs/diffusers/quantization/torchao; gist.github.com/sayakpaul/e1f28e86d0756d587c0b898c73822c47.
- ComfyUI/GGUF: huggingface.co/Comfy-Org/ACE-Step-1.5/discussions/1; github.com/Comfy-Org/ComfyUI/issues/12541.
- Bu depoda: `docs/OLCUMLER.md` (tüm ölçümler tek tablo), `docs/MIMARI.md` (neden böyle), `docs/SORUN_GIDERME.md` (belirti → çözüm),
  `docs/KULLANIM.md` (komutlar, plan biçimi), `docs/TARIFLER.md`, `docs/SINIRLAR.md`, `docs/HATALAR.md`, `docs/KARARLAR.md`.
- Ham kayıtlar (olcum_*.log, bellek_*.csv, koşu dokum.json'ları) yerel iş klasöründe, depo dışında; özetleri `OLCUMLER.md`.
