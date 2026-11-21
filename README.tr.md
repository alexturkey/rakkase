# Rakkase

[English](README.md) · Türkçe

Çeviri İngilizce README'yi izler; fark olursa İngilizce metin esastır, özellikle lisans metni. [`docs/`](docs/) altındaki ayrıntılı belgeler şimdilik Türkçedir.

> ACE-Step 1.5 (turbo) ile 4 GB'lık ekran kartında yerel müzik üretimi: plan dosyasını yazarsınız, Rakkase denetler, parçayı üretir ve reçetesiyle birlikte arşivler.

Rakkase, [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5)'in turbo modelini 4 GB VRAM'li GTX 1050 Ti'de 16 GB RAM ile sığdırıp hızlı çalıştıran ince ve dikkatli bir sarmalayıcıdır: int8 decoder, fp32 hesap, dil modeli kapalı, akışlı yükleme. Sığsın diye kaliteden ödün verilmez: 8 difüzyon adımı (modelin kendi değeri) ve fp32 sabittir. Sözlü (Türkçe dahil) ve enstrümantal parça üretir; 10 ile 600 sn arası (rahat bölge yaklaşık 300 sn'ye kadar).

**Neyi nerede ölçtük:** yalnız tek makinede (GTX 1050 Ti 4 GB, 16 GB RAM, Windows 10, 2026-11-05) [yazarlar ölçtü, `docs/OLCUMLER.md`]: model yükleme süreç başına bir kez yaklaşık 2 dk; 15 sn'lik parça yaklaşık 35-48 sn, 100 sn'lik şarkı yaklaşık 63-75 sn, 150 sn'lik düet 121 sn; RAM tepesi yaklaşık 6,4 GB. Sayılar 2026-11-05'te önceki motor metniyle ölçüldü, sonra yeniden ölçülmedi [yeniden ölçülmedi]. Başka kartlar ve 4 GB altı denenmedi; daha güçlü kartta büyük olasılıkla çalışır ama bu tahmindir [tahmin].

## Hızlı başlangıç (Quick start)

1. **Ne gerekir:** Windows 10/11 [ölçtüm: Windows 10], 4 GB ya da üstü NVIDIA kart [yalnız GTX 1050 Ti'de denendi], 16 GB RAM, yaklaşık 6,1 GB model için boş disk [okudum: `docs/KURULUM_DEFTERI.md` bölüm 3] ve torch'lu Python ortamı için yer (boyutu ölçülmedi), giriş kapısı için Python, ACE-Step ortamını kurmak için [uv](https://docs.astral.sh/uv/).
2. **ACE-Step 1.5'i bir kez kurun** (sabit commit, model indirme, ayar dosyası): [`KURULUM.md`](KURULUM.md) (kısa), [`docs/KURULUM_DEFTERI.md`](docs/KURULUM_DEFTERI.md) (tam, karşılaştığımız her duvarla).
3. **Planı CPU'da denetleyin** (GPU yok, model yüklenmez; tokenizer için ACE-Step klasörü gerekir):
   ```
   python rakkase.py denetle --plan ornekler/sozsuz_fon_ninni.json
   ```
4. **Üretin:**
   ```
   python rakkase.py uret --plan ornekler/sozsuz_fon_ninni.json
   ```
   Parça `uretimler/<tarih_saat>_<ad>/` altına wav + mp3, sözler ve reçete dosyasıyla düşer.
5. **Kurulumunuzu kanıtlayın:** `python rakkase.py test` 15 sn'lik bir referans üretir ve depodaki referans wav ile kıyaslar (geçer: korelasyon > 0,999 ve SNR > 40 dB; çıkış 0 = geçti, 1 = kaldı). GPU ister.

Durum: yazarların makinesinde (GTX 1050 Ti 4 GB) günlük kullanımda: 81 üretim koşusu, her biri tarifiyle arşivli [ölçtük]. Henüz yapmadığımız tek şey, yalnız bu depoyla boş bir makineye sıfırdan kurulum; takılırsanız hata bildirimi açın, adımları düzeltmemize yarar. GPU'nuz ya da ACE-Step kurulumunuz yoksa beş dakikada hiçbir şey çalışmaz: belgeleri okuyun, plan ya da çeviri düzeltmesi gönderin (`CONTRIBUTING.md`), 2. adımdan sonra dönün.

```
python rakkase.py denetle --plan P.json   # plan denetimi, CPU, birkaç sn, modeli yüklemez
python rakkase.py uret    --plan P.json   # önce denetler, sonra üretir ve arşivler
python rakkase.py bol     --plan P.json   # uzun planı yaklaşık 300 sn'lik koşulara böler
python rakkase.py test                    # motor değişince referansla kıyas
python rakkase.py mp3     <klasör>        # her wav'ın yanına mp3 192k
```

## Örnek planlar

| Dosya | Ne | Not |
|---|---|---|
| `ornekler/sozsuz_fon_ninni.json` | 96 sn enstrümantal ninni (gitar, çello, klarnet) | sözsüz: ilk deneme için en güvenlisi |
| `ornekler/rap_claude_code_40sn.json` | 40 sn Türkçe rap, özgün söz | tek parça, kısa; addaki "Claude" örnek sözlerde geçen bir ürün adıdır |
| `ornekler/sozlu_balad.json` | 100 sn Türkçe balad, özgün söz | sözlü, tek parça |
| `ornekler/cesit_6_tarz.json` | altı tarz (düet, koro, halk, rap, oryantal, çocuk) | yaklaşık 10 dk ses: sonraya |

Plan bir JSON'dur: `caption` (İngilizce tarz tarifi, 256 token sınırı), `[Verse]`/`[Chorus]` etiketli `lyrics`, `sure` (sn), `bpm`, `ton`, `olcu`, `tohum` (aynı plan + aynı tohum = aynı parça). Her alan [`docs/KULLANIM.md`](docs/KULLANIM.md)'de, sınırlar [`docs/SINIRLAR.md`](docs/SINIRLAR.md)'de, işe yarayan tarifler [`docs/TARIFLER.md`](docs/TARIFLER.md)'de.

## Bir şey ters giderse
Önce [`docs/SORUN_GIDERME.md`](docs/SORUN_GIDERME.md) (ne görürsünüz, ne yapılır) ve [`docs/HATALAR.md`](docs/HATALAR.md) (15 sık hata, 7 yanlış inanç). `rakkase.py uret` çıkış kodları: 0 tamam, 2 plan denetiminde hata ya da motor başlamadı, 3 bir parça başarısız, 4 RAM bekçisi durdurdu, 5 üretim tamam ama arşiv başarısız, 6 `ayarlar.json` eksik ya da yanlış.

## Klasörler

| Yer | İçerik |
|---|---|
| `rakkase.py` | tek giriş kapısı (uret, denetle, bol, test, mp3) |
| `motor/` | üretim motoru (ACE-Step sarmaları, ölçüm) ve venv başlatıcı |
| `araclar/` | plan denetimi, reçete arşivi, wav kıyası, ses seviyesi, bellek izleyici |
| `ornekler/` | örnek planlar (her biri `docs/TARIFLER.md`'de anlatılır) |
| `testler/` | kıyas planı, referans wav (kendi ACE-Step çıktımız), CPU testi |
| `docs/` | belgeler (şimdilik Türkçe) |
| `ayarlar.json` | yerel yollarınız (git dışı; `ayarlar.ornek.json`'dan kopya) |

## Katkı, destek, güvenlik
[`CONTRIBUTING.md`](CONTRIBUTING.md) (ilk PR 5 adımda), [`AGENTS.md`](AGENTS.md) (yapay zeka ajanları için), [`SUPPORT.md`](SUPPORT.md) (hedef, garanti değil), [`SECURITY.md`](SECURITY.md) (açıkları GitHub'ın "Report a vulnerability" bağlantısıyla gizli bildirin; herkese açık issue açmayın), [`PRIVACY.md`](PRIVACY.md) (telemetri yok), [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Lisans ve atıf

- Rakkase kodu ve belgeleri: MIT, bkz. [`LICENSE`](LICENSE). Üçüncü taraf bildirimleri: [`NOTICE`](NOTICE).
- ACE-Step 1.5 kodu: MIT (https://github.com/ace-step/ACE-Step-1.5). Model ağırlıkları: MIT; model kartı üretilen müziğin ticari kullanılabileceğini söyler (https://huggingface.co/ACE-Step/Ace-Step1.5; geliştirici beyanıdır, bağımsız garanti değil).
- Metin kodlayıcı Qwen3-Embedding-0.6B: Apache-2.0 (https://huggingface.co/Qwen/Qwen3-Embedding-0.6B).
- Ağırlıklar bu depoda yok; kurulumda resmî kaynaktan indirilir. Üretilen müzikte üslup benzerliği ve korumalı malzeme kullanımının sorumluluğu sizdedir (ACE-Step README'sindeki gibi): planlarda sanatçı adı ve başkasının sözü kullanmayın. Ayrıntı: `docs/HATALAR.md` (yanlış Y7: müzik hakları).
