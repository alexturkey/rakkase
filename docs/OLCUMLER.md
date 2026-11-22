# Ölçümler

Makine: GTX 1050 Ti 4 GB (Pascal), 16 GB RAM, model ve venv SMR HDD (ikinci disk). Kaynak etiketi: **ölçtüm** (bu makine, log/csv/dokum.json),
**okudum** (belge/issue), **tahmin**. Ham kayıtlar (log, csv, dokum.json) yerel iş klasöründe ve
`uretimler/*/kosu_dokum.json`'da (git dışı). Hepsi ölçtüm, aksi yazılmadıkça.

## 1. Yükleme (süreç başına bir kez)

| Adım | Paket yolu (2-4 Kasım) | Rakkase (5 Kasım, yerlesik6/7, sarki1, kosu1/2) |
|---|---|---|
| import acestep | ~25 sn | 25-27 sn |
| DiT (4,57 GB bf16 → fp16 + decoder int8) | 6-11 dk (mmap, HDD) | 51-55 sn soğuk / 16 sn sıcak önbellek |
| VAE (322 MB) | 32-42 sn | 31-40 sn (paket yolu) |
| Text encoder Qwen3-0.6B | 95-101 sn | 11-12 sn |
| Toplam | 7-11,5 dk | 130-151 sn |
| RSS yükleme sonu | 9-10,6 GB | 6,35-6,4 GB |
| Boş RAM en düşük (yüklemede) | 340 MB (öldürüldü) | 4,4-4,5 GB |

## 2. Üretim (parça başına)

| Parça | Süre | Mod | Üretim | DiT adım | VAE | TE | Not |
|---|---|---|---|---|---|---|---|
| aday1 (enstr.) 2 Kasım | 15 sn | paket yolu | 137 sn | — | — | 15 sn embed | DiT taşıma 63 sn/parça |
| 20 sn / 90 sn, 2 Kasım | 20 / 90 | paket yolu | 294 / 522 sn | | | | |
| ref aday1, yerlesik6 | 15 | Rakkase | **37,4 sn** | 0,79 sn | 4,9 sn | 3,3 sn | koşul 10 + 2,2 sn; taşımalar 7,4 sn |
| ref aday1, yerlesik7 | 15 | Rakkase | 32,7 sn | 0,80 sn | 4,8 sn | 3,2 sn | tekrar koşu |
| gece şarkısı (tr, erkek) | 100 | Rakkase | **75,3 sn** | 3,07 sn | 27,4 sn | 5,3 sn | toplam duvar 214 sn |
| 1 duet (tr) | 150 | Rakkase | 121,0 sn | 4,62 sn | | 4,1 sn | kosu1 ilk parça |
| 2 koro (tr) | 120 | Rakkase | 70,5 sn | 3,25 sn | | 0,1 sn | |
| 3 halk (tr) | 130 | Rakkase | 77,9 sn | 3,81 sn | | 0,1 sn | |
| 4 rap (tr) | 110 | Rakkase | 92,7 sn | 3,50 sn | | 7,2 sn | kosu2 ilk parça |
| 5 oryantal (enstr.) | 120 | Rakkase | 70,4 sn | 3,19 sn | | 0,1 sn | `[Instrumental]` |
| 6 çocuk (tr) | 90 | Rakkase | 57,2 sn | 2,49 sn | | 0,1 sn | |
| the_last_view_of_earth (enstr.) | 360 | Rakkase, Monitor | 498,1 sn | **45,05 sn** | | | VRAM tepe 4716 MB (paylaşımlı belleğe taşma), RAM tepe 11,3 GB, koşu 626,6 sn; kurala göre ~11 sn/adım beklenirdi (~4 kat) |
| claude_code_rap v1 ×2 (tr) | 30 | Rakkase | 25,6 sn | 0,82 sn | 7,7 sn | 0,1 sn | VRAM 2657 MB; koşu 274,6 sn |
| claude_code_rap v2 ×3 (tr) | 30 | Rakkase | 38,1 / 25,7 / 25,4 sn | 1,04 / 0,83 / 0,83 sn | ~8 sn | 3,2 / 0,1 sn | koşu 211,7 sn |
| v2 boom bap + `soz_zamani` | 30 | Rakkase | +18,1 sn söz zamanı | | | | koşu 197,4 sn; VRAM taşmadı |

Not (ölçüm): ~300 sn üstünde DiT adımı doğrusal büyümüyor (360 sn'de 4 kat); uzun parça Monitor ile 600 sn sınırını aşarak bitti.

Koşu toplamları: kosu1 (400 sn ses, 3 parça) 6 dk 53 sn; kosu2 (320 sn, 3 parça) 6 dk 19 sn; 720 sn müzik 13 dk 12 sn.
Kural (ölçümden): ~300 sn'ye kadar üretim ≈ 0,5-0,8 × ses süresi; DiT adımı ≈ 0,03 sn × ses saniyesi; yükleme ~120-135 sn sabit.

### Söz süresi (motorun söz zamanından, `soz_zamani: true`)

| Parça | bpm | Süre | Giriş satırı | 6 rap satırı | Nakarat |
|---|---|---|---|---|---|
| rap v2 boom bap t1301 | 92 | 30 sn | 0-9,0 sn | 9,44-27,44 sn (satır 2,3-4,1 sn, ort. 3,0 = 1,15 ölçü) | 28,0-29,9: 8 kelime 2 sn'ye sıkışık, kullanıcı duymadı |
| rap v3 boom bap t1301 | 92 | 40 sn | 0-8,7 sn | 9,52-29,6 sn | 29,76 ve 33,2'de başladı, son satır boşluğu doldurdu (6,7 sn) |

| balad "gece şarkısı" t2026 | 80 | 100 sn | | şarkı satırı, sağlam satırlarda ort. 1,9 ölçü (10/18 satır sağlam) | 1. kıta 0-30 sn tek satıra yığıldı (hizalama çöküşü) |
| koro "dağlar" | 70 | 120 sn | | şarkı satırı, sağlam satırlarda ort. 2,0 ölçü (9/18 satır sağlam) | 56,6 ve 71,0 sn'de 24-32 token aynı karede |

Kural (`araclar/denetle.py`, `SINIRLAR.md`) bu dört ölçümden: rap 1,15, şarkı 2,0 ölçü/satır. "Sağlam satır": aynı karede < 5 token,
token başına ≥ 0,15 sn, 0,6-3,5 ölçü arası; ilk ve son satır hesaba katılmaz (Rakkase ajanı yöntemi, 2026-11-05).
Söz zamanı hesabı 11-18 sn ek (rap 30 sn: 18,1; balad 100 sn: ~11; koro 120 sn: ~11).

### 2026-11-05 akşam geliştirme turu (motor sadeleşti, ölçtüm)

| Ölçü | Önce | Sonra | Not |
|---|---|---|---|
| `rakkase.py test` (ref'e) | SNR 44,0 dB, korelasyon 0,999987 | SNR 41,0 dB, korelasyon 0,999987 | eşik > 40 / > 0,999: geçti |
| Eski kod çıktısı ↔ yeni kod çıktısı | — | SNR 48,3 dB, korelasyon 0,999999 | aynı ses (GPU çekirdek sırası düzeyinde fark) |
| Yükleme (15 sn test koşusu) | ~130-135 sn | 126,0 sn (kilit beklemesi ayrı: 0 sn) | ölü yollar kalktı; ayrıca ölçümden kilit beklemesi ayrıldı |
| RSS tepe | 9,1 GB | 9,08 GB | aynı |
| shift 3.0, rap 40 sn t1301 | (1.0: arşivde) | üretim 52,2 sn, DiT adımı 1,28 sn | ilk parça (ısınma dahil) |
| shift 3.0, balad 100 sn t2026 | (1.0: 100,9 sn, söz zamanı dahil) | üretim 62,6 sn, DiT adımı 2,85 sn | aynı süreçte 2. parça; kalite kararı kulakla |

### 2026-11-05 gece GPU hız turu (aynı makine, aynı tohum, ölçtüm)
| Ölçü | Tur başı | Gece sonu | Ne değişti |
|---|---|---|---|
| Süreç toplamı, 15 sn parça (yükleme + üretim) | ~158 sn (126 + 32,6) | **49,6-89 sn** (ılık 32 + 17,4; ilk soğuk 69,8 + 19,6) | hepsi |
| Süreç toplamı, 100 sn "gece şarkısı" t2026 | 214 sn (üretim 75,3) | **84,7 sn** (yükleme 32,6 + üretim 51,9) | hepsi |
| Yükleme | 105-126 sn | 32-70 sn (import ılık 14 / soğuk 31 sn) | aşağıdaki dört satır |
| DiT yükleme | 47-54 sn | 2,7-3,9 sn | okuyucu iş parçacığı (43 sn) + int8 önbellek C:'de (K18, K19) |
| VAE yükleme | 31-33 sn | 1,3-4,6 sn | tam zamanında ısıtma `isit` (K16) |
| Text encoder yükleme | 13-15 sn | 3-15 sn | okuyucu iş parçacığı; dosya önbellekteyse 3 sn |
| Import | 10-31 sn (E: HDD) | 14 sn ılık (C: NVMe venv) | K20 |
| VAE çözme, 100 sn | 26,6 sn (40 çağrı) | 17,6 sn (27 çağrı) | örtüşme 64 → 16 (K15) |
| Taşıma / parça | 6,8-7,4 sn | 2,4-3,6 sn | katman katman GPU, decoder inmez (K17) |
| DiT 8 adım, 15 sn | 6,1-6,3 sn | 4,9 sn | venv C:'de (çekirdek DLL'leri hızlı diskten, tahminim) |
| DiT 8 adım, 100 sn | 22,7 sn | 23,2 sn | değişmedi: hesap sınırı (~1,37/2,1 TFLOPS) |
| RSS tepe | 7,6 GB | 7,0-7,1 GB | önbellekten kurulum |
| VRAM tepe | 2,65 GB | 2,65 GB | aynı |
| Kalite: `rakkase.py test` | SNR 44,4 dB | SNR 42,1-45,0 dB (10 koşu, hepsi geçti) | eşik 40 dB |
| Kalite: 100 sn eski ↔ yeni | — | SNR 61,6 dB, korelasyon 1,000000 | sabahki arşiv çıktısına karşı |
| int8 önbellek ↔ akışlı yükleme | — | 677 tensör bit düzeyinde aynı | `RAKKASE_ONBELLEK_DOGRULA=1` |
Reddedilen (ölçtüm): VAE chunk 256/512 (33,8/29,8 sn, VRAM taştı); arka planda önden okuma (yükleme 159 sn); SDPA dikkat (22,82 → 22,74 sn,
fark yok). Not: E:'de ölçüm sırasında başka disk işi (boyut taraması) koşarsa import 50-65 sn'ye çıkıyor; o koşular tabloya alınmadı.

## 3. Bellek

| Ölçü | Paket yolu | Rakkase |
|---|---|---|
| RSS yükleme tepe | 10,6 GB (4 Kasım) | 6,4 GB |
| RSS üretim tepe | ~10 GB | 9,1 GB (koşul modülleri GPU'dayken; sonra orada kalır) |
| VRAM tepe / ayrılmış | taşıyor (4,6 GB fp32 DiT → paylaşımlı belleğe) | 2,65 GB / 3,35-3,38 GB |
| Decoder CPU→GPU | 63 sn (RAM takaslı) | 0,6-1,1 sn |
| Sayfa dosyası | 2 GB | 1,1-1,4 GB |

Başarısız denemelerin RSS'i (neden `SORUN_GIDERME.md`): akis1 9,6 GB; yerlesik1 10,05 GB; yerlesik3 10,5 GB; yerlesik4 10,4 GB.

## 4. Aynılık (`araclar/kiyas_muzik.py`)

| Kıyas | max fark | SNR | korelasyon | log-mel | LUFS | tepe |
|---|---|---|---|---|---|---|
| yerlesik6 vs 2 Kasım aday1 (paket yolu, tohum 42) | 0,047 | 43,0 dB | 0,999987 | 0,040 | -19,3 / -19,2 | -0,9 dBTP |
| yerlesik6 vs yerlesik7 (aynı kod, aynı tohum) | 0,007 | 53,2 dB | 0,999999 | 0,038 | -19,3 / -19,3 | -0,9 dBTP |
| `rakkase.py test`, `soz_zamani` eklemesinden sonra (2026-11-05 20:13) | 0,056 | 44,0 dB | 0,999987 | 0,039 | -19,3 / -19,2 | -0,9 dBTP |
| `rakkase.py test`, cover alanı eklemesinden sonra (2026-11-07 22:48) | 0,046 | 43,1 dB | 0,999988 | 0,040 | -19,3 / -19,2 | -0,9 dBTP |
| rap v2 boom bap t1301: ilk üretim vs `soz_zamani: true` yeniden üretim | 0,013 | 59,1 dB | 0,999999 | 0,021 | -15,5 / -15,5 | -1,0 dBTP |

Yorum: GPU'da iki koşu bile bit düzeyi aynı değil (cuDNN/atomik toplama); eski-yeni fark bu doğal gürültünün hemen üstünde, aynı parça.
Test ölçütü bu yüzden korelasyon > 0,999 ve SNR > 40 dB.

## 5. Karşılaştırma (okudum, denenmedi)
- ACE-Step `docs/en/GPU_COMPATIBILITY.md`: Tier 1 (≤4 GB) = DiT-only + INT8 + CPU offload; süre verilmiyor.
- Issue #142: torchao 0.16 + torch 2.7 `.to()` fallback 11 sn, torchao 0.12 ile 1,4 sn (Linux). Bizde RAM sağlıklıyken 1 sn, değiştirilmedi.

## 6. Temiz klasörde kurulum ve ilk GPU testi (2026-11-22, ölçtüm)
Aynı makine (GTX 1050 Ti 4 GB, 16 GB RAM, Windows 10). Kurulum `scripts/kur.ps1` ile boş bir klasöre, taze uv ortamıyla yapıldı; modeller yerel bir kopyadan alındı (HuggingFace indirmesi bu ölçüme dahil değil).

| Ölçüm | Değer | Not |
|---|---|---|
| `kur.ps1` toplam süre | 32 dk 6 sn (uv paket indirme 13 dk 50 sn, 125 paket kurulumu 3 dk 34 sn, modeller yaklaşık 14 dk), çıkış kodu 0, HAZIR | modeller yerel kopyadan; internetten indirme süresi ölçülmedi |
| Kurulumun disk tüketimi | yaklaşık 23 GB (boş E: 823 GB -> 800 GB) | `df` GB yuvarlaması, birkaç yüz MB sapabilir; denetim eşiği bu yüzden ~25 GiB |
| `rakkase.py test` sonucu | GEÇTİ | referans karşılaştırması |
| SNR / korelasyon | 44,1 dB / 0,999988 | eşik: SNR > 40 dB, korelasyon > 0,999 |
| Toplam süre | 539 sn | soğuk ilk yükleme dahil (ilk koşu, önbellek yok) |
| VRAM tepe | 2653 MiB | 15 sn'lik test parçası; uzun parçada artabilir |
| RAM (RSS) tepe | 7688 MB | |

Kaynak: ana oturumun kurulum günlüğü ve test çıktı klasörü (yerel iş klasörü, repoda değil). Denenmedi: HuggingFace'ten gerçek indirme, git/uv'siz boş makine, başka GPU.

## 7. vae_fp32 yolu ve varsayılan yol kıyası (2026-11-23, ölçtüm, GTX 1050 Ti, 15 sn referans, tohum 42)

| Koşu | Sonuç | VRAM tepe / ayrılan | Üretim |
|---|---|---|---|
| Yeni kod, varsayılan (`vae_fp32` null → false) | TEST GECTI, çıkış 0 | 2653 / 3178 MB | 17,7 sn |
| Eski kod (4f8e2d0) | GECTI, çıkış 0 | - | 17,3 sn |
| Eski ↔ yeni kıyası | SNR 56,8 dB, korelasyon 0,999999, uzunluk eşit (SHA256 farklı: GPU'da bayt aynılık garanti değil) | - | - |
| Yeni kod, `vae_fp32: true` | TEST GECTI, sağlık SAGLAM (RMS -22 dB, sessiz %0) | 3768 / 4976 MB (4096 MB fiziksel kartı aşar; paylaşımlı belleğe taşma olası, ölçülmedi) | 21,2 sn |
