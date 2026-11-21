# Mimari: neden böyle

ACE-Step 1.5 turbo DiT'inin (`AceStepConditionGenerationModel`) parçaları ve 4 GB VRAM / 16 GB RAM'e sığdırma kararları.
Sayılar `OLCUMLER.md`'de; duvarların öyküsü `KURULUM_DEFTERI.md` §6.

## Model ve boyutlar (ölçtüm, `param_envanteri`)
| Parça | Param | Rol | Rakkase'de nerede |
|---|---|---|---|
| decoder | 1575 M (hepsi Linear) | difüzyon (8 Euler adımı, üretimin tamamı) | GPU'da kalıcı, int8 ağırlık (1,5 GB), fp32 hesap |
| encoder | 608 M | caption/söz/timbre koşulu (`prepare_condition`, parça başına 1 kez) | CPU fp16; yalnız kendi çağrısında GPU fp32 (2,4 GB) |
| tokenizer / detokenizer | 105 M + 105 M | LM ipucu üretimi (aynı `prepare_condition` içinde) | CPU fp16; kendi çağrısında GPU fp32 |
| text encoder Qwen3-Embedding-0.6B | ~600 M | caption/söz gömme | CPU bf16; çağrısında GPU fp32 |
| VAE (Oobleck) | 322 MB | latent → ses | paket yolu: üretimde GPU, sonra CPU |

Paketin kendi yolu (Tier-1): her şeyi fp16 yükler, decoder'ı int8 yapar, modelin tamamını üretim başına GPU'ya taşır. Bizde fp16 hesap
NaN verdiğinden (F-99) model fp32'ye çevrildi; o zaman DiT fp32 + int8 = 4,6 GB → 4 GB VRAM'e sığmaz, Windows sürücüsü paylaşımlı
belleğe (RAM) kaçırır: 63 sn/parça taşıma, RSS 10,6 GB.

## 1. Akışlı yükleyici (`dokum_muzik.py: akisli_yukle`)
Sorun: `from_pretrained(dtype=fp16)` safetensors'ı mmap ile dağınık okur (SMR HDD'de 12-24 MB/s), fp16 kopya + int8 kopya + fp32 kopya
üst üste: 6-11 dk ve 10,6 GB.
Çözüm: iskelet `meta` cihazda `from_config` ile (disk okumasız; `.item()` çağıran `ResidualFSQ` ve kalıcı olmayan tampon kuran
`Qwen3RotaryEmbedding` CPU'da), dosya **sırayla** `readinto` ile okunur (mmap yok), her tensör dosyadaki bf16'dan hedef dtype'a çevrilip
`_parameters/_buffers`'a takılır, decoder Linear'ları paketin aynı süzgeci ve aynı `Int8WeightOnlyConfig` ile **o anda** int8 olur
(fp16 kopya hiç oluşmaz). Anahtar seti `state_dict().keys()` ile dosyayla birebir doğrulanır. Text encoder aynı yolla bf16 (dosyadaki
aslı). Sonuç: DiT 16-55 sn, TE 11 sn, RSS 6,4 GB.
Okuyucu iş parçacığı (2026-11-05 gece): disk okuması ayrı iş parçacığında, dönüştürme/int8 ana iş parçacığında üst üste biner; aradaki kuyruk `KUYRUK_MB` (256 MB) bütçeli, RAM tepesi değişmez. DiT 47-54 → 43 sn, TE 13-15 → 11 sn. Tüketici hata verirse okuyucu durdurulur, dosya ondan sonra kapanır.
int8 önbellek (`dit_yukle`, ayar `int8_onbellek`): akışlı yükleyicinin ürettiği durum (decoder int8, kalan fp16) bir kez `torch.save` ile hızlı diske yazılır; sonra meta iskelet + `load_state_dict(assign=True)` ile `torch.load(weights_only=True)`'dan kurulur (2,9-3,9 sn). Anahtar: kaynak boyu+tarihi, torch ve torchao sürümü. Ağırlıklar bit düzeyinde aynı (677 tensör, ölçtüm). Aynılık: paketle aynı dönüşüm (bf16→fp16→fp32 decoder dışı; decoder int8 aynı config).

## 2. Decoder yerleşik (`dokum_muzik.py`: `decoder_tasi`, `pc_gpu`, `ctx_yerlesik`)
Sorun: üretimde yalnız decoder çalışır (8 adım); encoder/tokenizer/detokenizer parça başına bir kez. Hepsini birlikte taşımak VRAM'i
taşırır.
Çözüm: paketin `offload_dit_to_cpu=False` kalıcı yolu kullanılır ama `_recursive_to_device` sarılır: yalnız `decoder` + üst düzey
parametreler (`null_condition_emb`) GPU'ya gider ve orada kalır (0,6-1,1 sn). Koşul modülleri ve text encoder CPU'da düşük hassasiyette
(fp16/bf16) saklanır; **hesap hep GPU'da fp32** (CPU'da fp32 hesap denemesi RAM'i 10,5 GB'a çıkardı). 2026-11-05 gecesinden beri
decoder koşul hazırlığında da GPU'dan inmez: koşul modülleri katman katman gelir (§3).

## 3. Katman katman GPU fp32 (`katmanli_gpu`, `gpu_sarili`; eski yol `gpu_fp32_gecici`)
2026-11-05 gece: encoder, tokenizer, detokenizer ve text encoder altındaki her modül yalnız kendi doğrudan parametrelerini kendi
forward'u süresince GPU'ya alır (ön kanca), bitince CPU aslı geri (son kanca). Tepe VRAM = decoder + tek katman, decoder GPU'da kalır;
taşıma parça başına 7,4 → 2,4-3,6 sn. Parametresi kendi forward'u dışında kullanılan bir modül cihaz hatası verirse o modül için
aşağıdaki eski yola dönülür (decoder geçici CPU'ya). Aynı fp32 çekirdekler: eski yolla SNR 52,7-58,8 dB.

Eski yol (yedek):
Sorun: `modul.to(cuda).to(float32)` GPU'da önce fp16 kopya (1,6 GB) sonra fp32 kopya (3,3 GB) tutar; taşınca RAM'e kaçar (RSS 10,4 GB).
`.to(device, dtype)` tek adımda ise dönüşümü CPU'da yapar (RSS +2,3 GB).
Çözüm: her parametre/tampon tek tek GPU'ya kopyalanır ve orada fp32 olur (geçici yük 1 tensör); CPU'daki fp16/bf16 aslı saklanır,
çağrı bitince `p.data` eski tensöre döndürülür (yeniden dönüşüm yok, değer kaybı yok). Encoder, tokenizer, detokenizer forward'ları
sarılı: her biri yalnız kendi çağrısı süresince GPU'da; text encoder `_load_model_context("text_encoder")` sarmasıyla aynı.
Sayısal sonuç referans yolla aynı çekirdekler (fp32 GPU), fark yalnız çekirdek sırası (SNR 43-53 dB).

## 4. Bekçi ve ölçüm
`Bekci` iş parçacığı RSS/boş RAM örnekler; yalnız gerçek çökme sınırında (boş RAM < 150 MB, 30 sn) durdurur (kullanıcı kararı: sayfa
dosyasına taşma kabul). `dokum.json`: aşama süreleri, taşımalar, DiT adım süresi (forward hook), VRAM tepe, RSS. `araclar/bellek_izle.ps1`
dışarıdan 5 sn'de bir RSS/boş RAM/sayfa dosyası yazar (`calistir.py` adlı en büyük python süreci).

## 5. Bilinçli olarak yapılmayanlar
- (Kaldırıldı 2026-11-05 gece: hazır int8 durum dosyası artık var, `int8_onbellek`; 43 sn HDD okumasına karşı hızlı diskte 3 sn.)
- VAE büyük parça (256/512): ölçtüm, daha yavaş (33,8 / 29,8 sn) ve VRAM paylaşımlı belleğe taştı; örtüşme 64 → 16 seçildi.
- Arka planda önden okuma iş parçacığı (yükleme başında): import'la diski boğdu, yükleme 159 sn; yerine tam zamanında `isit()`.
- SDPA dikkat (eager yerine): ölçtüm, DiT 22,82 → 22,74 sn, fark yok; paketin Pascal kararı (eager) kaldı.
- Text encoder gömmelerini önbelleklemek (ComfyUI kalıbı): TE 11 sn yükleme + 0,1-7 sn hesap; kazanç küçük, karmaşıklık büyük.
- torchao 0.12'ye inmek (`.to()` fallback): taşıma zaten 1 sn.
- Encoder'ı da int8 yapmak: referans yoldan sapma (encoder fp32), kanıtsız; kalite çizgisi yalnız decoder int8.
- Kalıcı servis/ısınmış süreç: proje kuralı (sürekli açık model yok); yükleme 135 sn kabul edildi.

## 5b. Söz zamanı motorun içinden (`plan: soz_zamani`, 2026-11-05)
- Şarkıda kelime sesten (CTC/Whisper) yakalanmaz: alttaki müzik ve modelin "söylemiş gibi" telaffuzu (kullanıcı). Zaman, sözü üreten
  DiT'in sözlere bakan cross-attention'ından alınır: paketin hazır `get_lyric_timestamp` (`lyric_timestamp.py`, `dit_alignment.py`:
  dikkat matrisi + tek yönlü hizalama), son adım gürültü seviyesinde decoder'ın bir ek geçişi.
- Konuşma sentezinde de kullanılan fikir (motor dikkati + tek yönlü yol); konuşmadaki ses enerjisiyle kenar oturtma burada yok
  (müzik altında sessizlik yok).
- Ara veriler (pred_latents, encoder_hidden_states, context_latents, lyric_token_idss) yalnız üretim sırasında var; bu yüzden hazır
  parçaya sonradan uygulanmaz, `soz_zamani: true` ile aynı tohumdan yeniden üretilir (aynı parça, SNR 59 dB). `save_memory_mode`
  açıksa ara veri tutulmaz ve json'da hata yazar.
- Token → kelime toplama motorda değil, kullanan tarafta (örnek: `uretimler/2026-11-05_claude_code_rap_klip/veri.py`).

## 6. Dosya haritası
`rakkase.py` (alt süreç başlatır, mp3, bol, test) → `motor/calistir.py` (ACE-Step venv'inin site-packages'ını taban Python'a tanıtır,
`BETIK`'i çalıştırır; uv trampoline'e bağımlı değil) → `motor/dokum_muzik.py` (paket `AceStepHandler`'ını sarar: `_load_*`
zamanlayıcıları, `AutoModel.from_pretrained` yerine `akisli_yukle`, `_recursive_to_device` ve `_load_model_context` sarmaları,
`prepare_condition`/encoder/tokenizer/detokenizer sarmaları, `uret()` döngüsü, `dokum.json`).
