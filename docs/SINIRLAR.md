# Sınırlar: plan yazmadan önce bilinecek sayılar

Her sayının yanında: nereden geldiği (ölçtük / okuduk / tahmin) ve aşınca ne olduğu. `araclar/denetle.py` bu sayıları kullanır;
`testler/denetle_test.py` aşağıdaki "Denetim eşikleri" tablosunu kodla karşılaştırır, ikisi ayrışırsa test kırılır.
Bir sayı değişirse önce ölçüm (`OLCUMLER.md`), sonra kod, sonra bu tablo; üçü aynı commit'te.

## Denetim eşikleri (kodla birebir; test bu tabloyu okur)

| Anahtar | Değer | Birim | Aşınca | Kaynak |
|---|---|---|---|---|
| `CAPTION_SINIR` | 256 | token | HATA: fazlası sondan kesilir, önce bpm/ton/süre satırları gider, sonra caption sonu | okuduk: `acestep/.../conditioning_text.py` (truncation=True); ölçtük: 1083 karakter = 253 token (~4,3 karakter/token) |
| `CAPTION_UYARI` | 240 | token | UYARI: sınıra az kaldı | bizim pay |
| `SOZ_SINIR` | 2048 | token | HATA: sözlerin sonu kesilir | okuduk: aynı dosya, söz kodlayıcı |
| `SOZ_UYARI` | 1800 | token | UYARI | bizim pay |
| `SURE_UYARI` | 300 | sn | UYARI: DiT adımı ~4 kat yavaşlar, VRAM paylaşımlı belleğe taşar | ölçtük: 360 sn parça 45 sn/adım, VRAM 4716 MB (`OLCUMLER.md`) |
| `GIRIS_OLCU` | 4.0 | ölçü | süre hesabı: sözlü `[Intro]` | ölçtük: 92 bpm rapte 8,7-9 sn |
| `RAP_SATIR_OLCU` | 1.15 | ölçü/satır | süre hesabı: rap satırı | ölçtük: 92 bpm, 30 sn'de nakarat sıkıştı (0,08 sn/kelime), 40 sn'de sığdı |
| `SARKI_SATIR_OLCU` | 2.0 | ölçü/satır | süre hesabı: şarkı satırı | ölçtük: sağlam satırlarda balad (80 bpm) ort. 1,9, koro (70 bpm) ort. 2,0 (iki örnek) |
| `BITIS_PAYI_OLCU` | 1.0 | ölçü | süre hesabı: son pay | bizim pay |
| `KALITE_ADIM` | 8 | adım | HATA: kalite değişmezi | turbo modelin kendi değeri (`CLAUDE.md`) |

Süre kuralı: `gereken sn = (GIRIS + satır × katsayı + BITIS_PAYI) × (60 / bpm × olcu)`; `[Instrumental]`, `break`, `solo`, `interlude`
bölümleri 4 ölçü. Yalnız UYARI verir: kaba kuraldır, tür ve tempoyla değişir. Kesin kontrol `soz_zamani: true` (satır başına zaman).

## Kartlar

**Caption: 256 token, karakter değil.** Paketin API belgesindeki "512 karakter" ayrı bir öneridir; asıl kesme tokenizer'da 256 token'da,
bpm/ton/ölçü/süre satırları da bu sayıya dahildir ve en sonda durdukları için **ilk onlar** kesilir. Uyarı çıkmaz. Denetle sayar.

**Sözler: 2048 token.** Biçim `# Languages\n<dil>\n\n# Lyric\n<sözler><|endoftext|>`. 100 sn'lik Türkçe şarkı ≈ 210 token: sınır uzakta,
ama süre sınırı çok önce gelir (aşağıda).

**Süre: 10-600 sn, rahat bölge ≤ 300 sn.** 4 GB kartta 300 sn üstü doğrusal büyümez (360 sn: adım 45 sn, beklenen ~11). Yayıncıya göre
model 30-60 sn ve 2-4 dk'da en kararlı; 4 dk üstü yapı kayabilir. Uzun iş: parçalara böl.

**Bir süreç ≈ 300 sn ses** (`ayarlar.json: on_plan_ses_siniri_sn`). Yükleme ~2 dk + üretim ≈ 0,5-0,8 × ses süresi. Bash ön plan sınırı
600 sn; daha uzunu Monitor ile. Çoklu plan: `rakkase.py bol`.

**Sözler süreye sığmalı.** Model fazlasını atmaz, sona sıkıştırır ve `success: true` döner (30 sn rap: nakarat son 2 sn'de). Denetle
kaba hesabı UYARI verir; `soz_zamani: true` gerçek zamanı gösterir.

**Söz zamanı her yerde güvenilir değil.** Paketin hizalaması (DTW) ilk token'ı 0'a, sonuncuyu bitişe zorlar: enstrümantal aralıklarda
aynı kareye ≥5 token yığılır ya da tek satır 30 sn'ye yayılır (balad ve koroda ölçtük; rapte görülmedi). `probability` alanı hep 0
(paket koda gömmüş). Klipte kullanmadan önce: aynı kareye ≥ 5 token düşen, token başına < 0,15 sn kalan ya da 0,6-3,5 ölçü dışında kalan satır şüpheli; ilk ve son satır her zaman şüpheli (yöntem ve ölçüm: `OLCUMLER.md` Söz süresi).

**Tohum: aynı plan + tohum = aynı parça, bit düzeyinde değil.** GPU'da iki koşu SNR 44-59 dB, korelasyon > 0,99998. Test eşiği SNR > 40 dB,
korelasyon > 0,999.

**`shift`: varsayılan 1.0.** Paketin INFERENCE.md'si turbo için 3.0 önerir, Tutorial.md turbo'nun 1, 2 ve 3'te damıtıldığını söyler (iki
belge çelişkili). Bizde A/B dinlendi (2026-11-05): kulakla fark yok, varsayılan 1.0 kalır (K13). `shift ≠ 1` iken
`soz_zamani` kayabilir (paket son adımı t = 1/adım varsayar). Aralık (0, 5].

**Bellek (16 GB RAM, 4 GB VRAM).** RSS tepe ~9,1 GB, VRAM tepe ~2,7 GB (30 sn) / ~3,3 GB (100-150 sn). Motor bekçisi boş RAM 30 sn boyunca
150 MB altında kalırsa çıkış 4 ile durur; ama sen 1 GB altında dur (başka ağır uygulamayı kapat). Paket yolu (motorsuz) 10,6 GB RSS'e çıkar.

**Diller.** `vocal_language` paketin `VALID_LANGUAGES` listesinden (`tr` var). Türkçe telaffuz kalitesi için resmî ölçü yok: kulakla.
Hece denetimi yalnız `tr`'de (Türkçe sesli harf sayar).
