# Kullanım

Komutlar, plan biçimi, arşiv. İyi parça tarifleri `TARIFLER.md`, sınır sayıları `SINIRLAR.md`, kaçınılacaklar `HATALAR.md`.

Tüm komutlar `<RAKKASE>` (bu klasör) kökünden; Python 3.x herhangi (giriş kapısı yalnız alt süreç başlatır, motor ACE-Step
venv'inde koşar; yol `ayarlar.json: ace_kok`). Ön planda çalıştır (neden: `docs/SORUN_GIDERME.md`). Süreler: `OLCUMLER.md`.

## Komutlar

| Komut | Ne yapar |
|---|---|
| `python rakkase.py uret --plan P.json [--cikti K] [--ad AD] [--yalniz a,b] [--denetimsiz]` | Önce planı denetler (HATA varsa durur), sonra plandaki parçaları (ya da yalnız `--yalniz` ile sayılanları) tek süreçte üretir; her parça `uretimler/<tarih_saat>_<ad>/` (aşağıda "Üretim arşivi"). `--ad` verilmezse `kosu_<tarih_saat>`. |
| `python rakkase.py denetle --plan P.json [--yalniz a,b]` | Yalnız plan denetimi (CPU, ~5 sn; aşağıda "Plan denetimi"). |
| `python rakkase.py bol --plan P.json` | Planı `ayarlar.json: on_plan_ses_siniri_sn` (varsayılan 300 sn ses) kadar gruplara böler, her grup için `--yalniz` satırı basar; plan dosyası değişmez. |
| `python rakkase.py test` | `testler/plan_kiyas_15sn.json`'u üretir (`cikti/test/test_<zaman>/`), `testler/referans/aday1_intro_neseli_15sn.wav` ile `araclar/kiyas_muzik.py` kıyası basar (max fark, SNR, korelasyon, log-mel, LUFS/tepe). Geçer: korelasyon > 0,999, SNR > 40 dB. |
| `python rakkase.py mp3 K` | `K` altındaki (alt klasörler dahil) her wav için yanına 192k mp3 (varsa atlar). |

Ayar `int8_onbellek` (isteğe bağlı, `ayarlar.json`): hızlı diskte (SSD) bir klasör, ör. `%LOCALAPPDATA%/rakkase/int8_onbellek`. İlk yüklemede DiT'in int8'li hali oraya yazılır (~3 GB, bir kez ~27 sn), sonraki yüklemeler 43 sn yerine ~3 sn. `null` ise kapalı. Kaynak model ya da torch/torchao sürümü değişince kendiliğinden yeniden yazılır (eskisi silinir). Doğrulama: `RAKKASE_ONBELLEK_DOGRULA=1` ile iki yol da yüklenir, bit düzeyinde karşılaştırılır (`ONBELLEK DOGRULAMA: AYNI`).

Ayar `venv` (isteğe bağlı): ACE venv'inin hızlı diskteki kopyası (ör. `%LOCALAPPDATA%/rakkase/venv`); `null` ise `<ace_kok>/.venv`. Neden ve ölçüm: `KARARLAR.md` K20. Paket güncellenince kopya yenilenir: `robocopy <ace_kok>\.venv <kopya> /MIR /MT:16`.

Çıkış kodları (`uret`): 0 tamam · 2 plan denetiminde HATA ya da motor başlamadı ·
3 bir parça başarısız (bitenler yine arşivlenir, `dokum.json` yazılı) · 4 RAM bekçisi durdurdu · 5 üretim tamam, mp3/arşiv başarısız · 6 `ayarlar.json` eksik ya da yanlış (ilk çalışmada örnekten oluşturulur; yolları düzelt). `test`: 0 GECTI, 1 KALDI.

Motor doğrudan (ölçüm/ayıklama için): `<ACE_KOK>\.venv\Scripts\python.exe motor\calistir.py --plan ... --cikti ... --ad ...
[--kilit] [--yalniz ...]` (`HF_HUB_OFFLINE=1`). Tek yol vardır (akışlı yükleme, decoder yerleşik); eski ölçüm bayrakları ve paketin
kendi yükleme yolu silindi, gerekirse `git tag paket-yolu-son`.

## Plan biçimi

```json
{
  "not": "serbest açıklama (isteğe bağlı)",
  "parcalar": [
    {
      "ad": "gece_sarkisi_100sn",
      "caption": "warm heartfelt Turkish acoustic pop ballad, soft intimate male vocal, fingerpicked acoustic guitar, gentle piano",
      "lyrics": "[Verse 1]\nGece yarısı yine sen yazarsın\n...\n\n[Chorus]\n...\n\n[Outro]\n...",
      "vocal_language": "tr",
      "sure": 100,
      "bpm": 80,
      "ton": "G Major",
      "olcu": "4",
      "tohum": 2026
    }
  ]
}
```

| Alan | Zorunlu | Anlam |
|---|---|---|
| `ad` | evet | dosya ve `--yalniz` adı; boşluksuz, sonuna süre yazmak iyi (`_100sn`) |
| `caption` | evet | İngilizce tarz/enstrüman/duygu/vokal betimi. Sınır **256 token** (bpm, ton, süre bilgisiyle birlikte; fazlası uyarısız sondan kesilir: önce bpm/ton/süre satırları, sonra caption'ın sonu, ölçüm 2026-11-05: 1083 karakterlik caption = 253 token, yani ~4,3 karakter/token). Ölçmek: ACE-Step venv'inde `checkpoints/Qwen3-Embedding-0.6B` tokenizer'ı ile `SFT_GEN_PROMPT` şablonu |
| `sure` | evet | saniye, 10-600 |
| `bpm`, `ton`, `olcu` | evet | tempo; "G Major", "C Minor"; "4" (4/4), "3" |
| `tohum` | evet | sabit sayı; aynı plan + tohum = aynı parça. Çeşit için tohumu değiştir, caption'ı değil (bkz. [Tohum denemesi](#tohum-denemesi)) |
| `lyrics` | sözlüde | `[Verse 1]`, `[Pre-Chorus]`, `[Chorus]`, `[Bridge]`, `[Outro]` etiketli satırlar; tam olarak `[Instrumental]` ise enstrümantal sayılır |
| `vocal_language` | sözlüde | ISO kodu; `tr` geçerli (`acestep/constants.py: VALID_LANGUAGES`); yoksa `unknown` |
| `instrumental` | hayır | `true` zorla enstrümantal (lyrics olsa da) |
| `adim` | hayır | 8; başka değer denetimde HATA (kalite değişmezi) |
| `shift` | hayır | zaman adımı kaydırma, varsayılan 1.0, aralık (0, 5]. Paket turbo için 3.0 önerir; bizde A/B aşamasında (`SINIRLAR.md`) |
| `gorev` / `kaynak_ses` / `cover_gucu` | hayır | `"cover"`: `kaynak_ses` (wav) ezgi, ritim, akor olarak kullanılır, süre kaynaktan; `cover_gucu` (0, 1], 8 adımın ilk int(8×g) adımı kaynakla, kalanı yalnız metinle (tını). İlk deneme: 0,625 (K22) |
| `soz_zamani` | hayır | **Sözlü parçada varsayılan açık** (2026-11-06, kullanıcı: "her üretim kelime zamanını bıraksın"); `false` kapatır, sözsüzde hiç çalışmaz. Üretimden hemen sonra ACE-Step'in kendi söz zamanı (`get_lyric_timestamp`) hesaplanır: `<ad>.soz_zamani.json` (satır LRC + token) ve arşivde `<ad>.kelimeler.json` (satır/kelime t0-t1, `supheli` işareti; `araclar/kelime_zamani.py`). Sesi değiştirmez, 11-18 sn ek. Karaoke, altyazı, klip bu dosyayı okur |

Örnekler (hepsi `TARIFLER.md` kartlarında): `ornekler/sozsuz_fon_ninni.json` (enstrümantal fon, 96 sn), `ornekler/sozlu_balad.json`
(Türkçe erkek vokal, 100 sn), `ornekler/rap_claude_code_40sn.json` (rap, söz zamanlı), `ornekler/rap_claude_code_3_tur.json` (üç tarz),
`ornekler/cesit_6_tarz.json` (duet, koro, halk, rap, oryantal enstrümantal, çocuk; 720 sn, `bol` ile 3 koşu).

## Örnek akışlar

Tek şarkı:
```
python rakkase.py uret --plan ornekler/sozlu_balad.json --ad deneme1
```
→ `uretimler/<tarih_saat>_gece_sarkisi_100sn/gece_sarkisi_100sn.mp3` (yükleme ~2 dk + üretim ~75 sn).

Çoklu plan, 10 dk sınırı:
```
python rakkase.py bol --plan ornekler/cesit_6_tarz.json
  kosu 1: --yalniz 1_duet_istasyon_150sn,2_koro_daglar_120sn
  kosu 2: --yalniz 3_halk_yayla_130sn,4_rap_gece_110sn
  kosu 3: --yalniz 5_rakkase_oryantal_120sn,6_cocuk_kedi_90sn
python rakkase.py uret --plan ornekler/cesit_6_tarz.json --ad kosu1 --yalniz 1_duet_istasyon_150sn,2_koro_daglar_120sn
...
```
Her koşu kendi `dokum.json`'unu yazar (her parçadan sonra güncellenir); parçalar `uretimler/`e.

Aynı parçadan başka aday: yalnız `tohum`u değiştir (`ad`a tohumu ekle). Caption değişince başka parça olur.

## Paylaşmaya hazır panel

X, Instagram ve WhatsApp ses dosyası kabul etmediği için `uret` her parçanın yanına `<ad>_panel.mp4` de yazar: 1080x1080, 30 kare/sn, 20 bantlı LED spektrum (eski radyo görünümü), ses kayıpsız kaynaktan AAC 320k. Video süslü değildir, parçanın gerçek spektrumudur. Ölçüm: 100 sn'lik parça için 49 sn, 8,5 MB, CPU'da [bakımcılar ölçtü, tek koşu]. Konum: `uretimler/<tarih>_<ad>/<ad>_panel.mp4` (wav ve mp3'ün yanında). Gereken: ffmpeg (PATH'te; mp3 ile aynısı), numpy, soundfile, Pillow; üçü de ACE-Step ortamında vardır [bakımcılar canlı kurulumda ölçtü], ek kurulum adımı yok. Panel CPU'da koşar, GPU istemez, pencere açmaz. Varsayılan AÇIK; kapatmak için `python rakkase.py uret --plan P.json --panel-yok` (ayar anahtarı yok, yalnız bayrak). Sonradan ya da başka bir wav için: `python rakkase.py panel <wav ya da klasör>` (klasörde panel zaten varsa atlanır). `test` panel üretmez. ffmpeg yoksa mevcut `RK-W-FFMPEG` uyarısı çıkar ve panel atlanır; `uret` sırasında panel düşerse `RK-W-PANEL` uyarısıdır ve çıkış kodu DEĞİŞMEZ (müzik ve mp3 yerinde); yalnız `rakkase.py panel` komutu başarısız olursa `RK-E-PANEL` (çıkış 5). Ayrıntı: `docs/SIK_HATALAR.md`.

## Tohum denemesi

**Tohum nedir:** plandaki `tohum`, rastgeleliğin başlangıç sayısıdır. Aynı plan + aynı tohum = aynı parça (GPU'da bit düzeyi değil; SNR > 40 dB, korelasyon > 0,999). Aynı caption ve söz farklı tohumla aynı şarkının başka bir yorumunu verir: farklı ezgi, hava, düzenleme. Yakın sayılar (41, 42) benzer parça vermez; birbirinden uzak sayılar seç (yeni tohum çekmek için `secrets.randbelow(2**32)`).

**Nasıl denenir:** aynı `caption`, `lyrics`, `sure`, `bpm`, `ton`, `olcu` ile 3 parça yaz; yalnız `tohum` (ve `ad`) değişsin. Hazır örnek: `ornekler/tohum_denemesi.json` (sözsüz, 30 sn, 3 tohum). Üret, dinle, beğeneni seç; seçilen tohum o parçanın tarifidir (`recete.json` içinde kayıtlıdır) ve sonradan aynı parça yeniden üretilebilir.

**Bedel:** her tohum tam üretim süresi kadar sürer (parça süresinin yaklaşık 0,6-0,8 katı; GTX 1050 Ti'de 100 sn'lik parça için yaklaşık 75 sn [yazarlar ölçtü, `OLCUMLER.md`]); model yüklemesi koşu başına bir kez (yaklaşık 2 dk). Üç tohum, tek parçanın yaklaşık üç katı üretim süresidir. Uzun plan için `rakkase.py bol`.

**Sınır:** tohum yaratıcı bir seçimdir, kalite ayarı değildir: turbo 8 adım ve fp32 değişmez. Çeşit için caption'ı değiştirme; o başka bir parça olur.

## Plan denetimi: `rakkase.py denetle` (2026-11-05, üretimden önce, CPU ~5 sn)

`uret` her koşudan önce kendisi çalıştırır; HATA varsa ya da denetim çalışamazsa üretim başlamaz (çıkış 2, atlamak `--denetimsiz`). Kod `araclar/denetle.py`.
| Kontrol | Düzey | Neden / kaynak |
|---|---|---|
| plan okunamıyor (JSON hatası, `parcalar` yok/boş) | HATA | |
| zorunlu alanlar (ad, caption, sure, tohum, bpm, ton, olcu) ve tipleri, `sure` 10-600, `bpm` 30-300, `olcu` 2/3/4/6, aynı `ad` iki kez, `--yalniz`'da olmayan ad | HATA | eksik metas sessizce N/A olur; aynı ad dosyaları üstüne yazar |
| `adim` ≠ 8, `shift` (0, 5] dışı, `vocal_language` paketin listesinde yok | HATA | kalite değişmezi; paket bilinmeyen dili sessizce yok sayar |
| caption + metas > 256 token (paketin kendi şablonu ve tokenizer'ı) | HATA (>240 UYARI) | fazlası sondan kesilir |
| sözler > 2048 token | HATA | `conditioning_text.py` |
| sözlü parça + caption'da "no vocals" / "instrumental track" | HATA | çelişki |
| `sure` > 300 | UYARI | 360 sn'de DiT adımı ~4 kat yavaş, VRAM taşması |
| sözler süreye sığmıyor (kaba kural) | UYARI | 30 sn rapte nakarat söylenmedi |
| satır hecesi 3-16 dışı ya da bölümde 5+ hece fark (yalnız `tr`) | UYARI | kılavuz 6-10, bizde rapte 10-16 çalıştı; model heceyi vuruşa dizer |
| çift virgül, `vocal_language` eksik, enstrümantalde vokal kelimesi (kelime sınırıyla: "trap" eşleşmez), `shift ≠ 1` + `soz_zamani` | UYARI | |

Süre kuralı ve eşiklerin kaynağı: `SINIRLAR.md` (kodla aynı; `testler/denetle_test.py` karşılaştırır). Özet: sözlü `[Intro]` ≈ 4 ölçü,
rap satırı ≈ 1,15 ölçü, şarkı satırı ≈ 2 ölçü (balad 1,9, koro 2,0; ölçüldü), bitiş payı 1 ölçü. Yeni tür ölçüldükçe güncellenir.

## Üretim arşivi: `uretimler/` (2026-11-05, kullanıcı isteği)

Her parça otomatik olarak kendi klasörüne iner: `uretimler/<YYYY-MM-DD_HH-MM-SS>_<parça_ad>/`. Zaman, wav'ın bitiş anıdır.
Klasörün içinde wav, mp3, `sozler.txt`, `plan.json` (tek parçalık, yeniden üretmek için), `recete.json`, `RECETE.md`, `kosu_dokum.json`
ve sözlü parçada `<ad>.soz_zamani.json` ile `<ad>.kelimeler.json` bulunur. Bir koşu yarıda kalsa da (çıkış 3) biten parçalar arşivlenir. Reçetede şunlar yazar:
girdi, araç ve paket sürümleri, ölçüm, sha256, üreten ve yeniden üretme komutu.
- `--cikti` verilmezse çalışma klasörü `cikti/kosular/` olur ve parça `uretimler/`e taşınır.
- `--cikti` verilirse parça orada kalır, `uretimler/`e kopyası gider. Bir projenin yanında da dursun istenirse bu kullanılır.
- Kim üretti: ortam değişkeni `RAKKASE_URETEN` (varsayılan "rakkase"). İsterseniz kendi adınızı verin, ör. `RAKKASE_URETEN=ayse`; reçeteye yazılır.
- `uretimler/` git dışıdır (kayıt, uygulama değil).
- 2026-11-05 öncesi parçalar (24 parça) elle toplandı (o bir kerelik betik repoda değil); onların reçetesindeki `toplandigi_yer`
  alanı yalnız o toplu aktarıma aittir.
