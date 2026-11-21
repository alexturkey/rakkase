# Sık yapılan 15 hata ve doğru bilinen 7 yanlış

Plan yazmadan, motora dokunmadan ve sonuç yorumlamadan önce bir kez oku. Her madde: **belirti → neden → önleme → kim yakalar → kaynak**.
Kaynak etiketi: *ölçtük* (bu makinede), *okuduk* (resmî belge/kod), *yayıncıya göre*, *tahmin*. Kısaltmalar: T = ACE-Step
`docs/en/Tutorial.md`, I = `docs/en/INFERENCE.md`, G = `docs/en/GPU_COMPATIBILITY.md`. Sınır sayıları tek yerde: `SINIRLAR.md`.

## A. Plan ve prompt (üretimden önce)

**1. Caption'ı kelime listesi yazmak.** Belirti: tarz "sıradan", ritim zayıf. Neden: resmî örnekler paragraf; model betimi bir prodüktör
anlatımı gibi okur. Önleme: paragraf yaz (tür, davul, bas, vokal nasıl okuyor, nakarat, düzenleme). Kim: insan (`TARIFLER.md`).
Kaynak: ölçtük (rap v1 kullanıcıya zayıf geldi, v2 paragraf), okuduk (T, `examples/text2music`).

**2. Çelişen kelimeler.** Belirti: "çamur" tarz, bozuk bölüm. Neden: "relaxed" + "energetic", "violin" caption'da ama sözde
`[Guitar Solo]`. Önleme: caption ↔ söz etiketleri aynı hikâye; çelişkiyi zamana yay ("starts with strings, builds into rock"). Kim: insan;
denetle yalnız "no vocals + söz" çelişkisini yakalar. Kaynak: okuduk (T:387-391, T:464-480).

**3. BPM/ton/ölçüyü caption'a yazmak.** Belirti: tempo tutmuyor. Neden: bunların ayrı alanı var (metas). Önleme: `bpm`, `ton`, `olcu` plan
alanlarında; caption'da yalnız tür/duygu/enstrüman/tını. Kim: denetle alanların varlığını ve biçimini zorunlu kılar; caption'a bpm/ton yazılmasını yakalamaz, o insan işi. Kaynak: okuduk (T:700).

**4. Caption'ı karakterle ölçmek.** Belirti: bpm/ton tutmuyor, caption'ın sonu yok sayılmış gibi. Neden: sınır 256 **token**, metas dahil,
kesme sondan ve sessiz. Önleme: `rakkase.py denetle` (token sayar). Kim: denetle HATA. Kaynak: okuduk (`conditioning_text.py`), ölçtük.

**5. Süreyi sözlere göre seçmemek.** Belirti: "sözlerin bir kısmı söylenmemiş" (çoğu nakarat). Neden: model sözleri atmaz, sona sıkıştırır,
`success: true` döner. Önleme: denetle süre UYARISI; `soz_zamani: true` ile doğrula. Kim: denetle UYARI. Kaynak: ölçtük (30 sn rap:
nakarat son 2 sn'de, kelime başına 0,08 sn; 40 sn'de sığdı).

**6. Etiketi uzatmak, satır hecesini dağıtmak.** Belirti: etiket metni şarkı gibi söyleniyor; ritim tökezliyor. Neden: `[Chorus - anthemic
- stacked - epic ...]`; 6 heceden sonra 14 hece. Önleme: etiket kısa (`[Chorus - catchy]`); bölümde satırlar ±2 hece; kılavuz 6-10 hece,
bizde rapte 10-16 çalıştı. Kim: denetle UYARI (yalnız `tr`). Kaynak: okuduk (T:446-458, T:511-525), ölçtük.

**7. Sözlü istedim, enstrümantal çıktı (ya da tersi).** Neden: `lyrics` boş/tam `[Instrumental]`, `instrumental: true`, caption'da
"no vocals". Önleme: gerçek söz + `vocal_language: tr`; enstrümantalde caption'a `no vocals`. Kim: denetle (çelişki HATA, eksik dil UYARI).
Kaynak: okuduk (I:340, I:349), ölçtük.

**8. İki şeyi aynı anda değiştirmek.** Belirti: neyin işe yaradığı bilinmiyor. Neden: hem caption hem tohum değişti (aynı tohum iki farklı
tarifte de kullanıldı). Önleme: ayarlarken tohum sabit, bir değişken; çeşit için yalnız tohum değişir. Kim: insan. Kaynak: okuduk
(T:873, T:918-920), ölçtük (tohum 9103 iki tarifte).

## B. Çalıştırma

**9. Uzun koşuyu arka plana atmak.** Belirti: koşu sessizce bitti, log yarım, "system is running low on memory". Neden: Claude Code arka plan
kabuğunu bellek baskısında kapatır (RSS üretimde ~9 GB). Önleme: ön planda (Bash 600 sn), daha uzunu Monitor ile; nohup/detached yasak;
plan `rakkase.py bol` ile bölünür. Kim: kural (`CLAUDE.md`). Kaynak: ölçtük (iki koşu kayboldu; 605 ve 626 sn Monitor ile bitti).

**10. 300 sn üstü tek parça.** Belirti: adım 45 sn (beklenen ~11), sistem kasıyor. Neden: VRAM 4096 MB'ı aşıp paylaşımlı belleğe taşıyor.
Önleme: ≤ 300 sn parçalar. Kim: denetle UYARI. Kaynak: ölçtük (360 sn), yayıncıya göre (G:9 tier-1 sınırı LM'siz 6 dk).

**11. GPU işini kilitsiz ya da üst üste koşmak.** Belirti: VRAM taşar, iki iş de yavaşlar ya da çöker. Neden: aynı kartta başka bir model (ses, çeviri vb.) ve
Rakkase. Önleme: `ayarlar.json: kilit=true`; motor kilidi model yüklemeden önce alır, bekleme süresi `dokum.json: kilit_bekleme_sn`.
Kim: motor. Kaynak: ölçtük, karar (`KARARLAR.md`).

**12. Kabuğa Windows yolu ya da regex'i ters bölüyle yazmak.** Belirti: `\v` yol parçası kayboluyor; `\b` gerçek geri silme baytına
(0x08) dönüşüp desen sessizce bozuluyor. Neden: bash `-c`/heredoc ve Python normal dizgisi kaçış uygular. Önleme: dosyaya Write/Edit
aracıyla yaz, ham dizgi `r"..."`; şüphede `grep -c $'\x08'`. Kim: insan/ajan. Kaynak: ölçtük (2026-11-05, `denetle.py`).

## C. Motor ve kurulum (4 GB Pascal)

**13. fp16 hesap.** Belirti: sözlü parçada sessiz/bozuk çıktı, NaN latent. Neden: Pascal'da bf16 yok, paket fp16'ya düşer;
`lyric_encoder.layers[7].mlp.down_proj` ~505 000 > 65 504. Önleme: hesap fp32 (motor içinde sabit, bayrağı yok). Kim: motor. Kaynak:
ölçtük, okuduk (issue #1243, #1260; PR #1352).

**14. Paketin kendi yükleme ve boşaltma yolu.** Belirti: yükleme 6-11 dk, RSS 10,6 GB; her parçada 63 sn "Moving parameters
individually". Neden: mmap dağınık okuma (HDD) + fp16/int8/fp32 kopyaları; nicemlenmiş modelde `.to()` başarısız, tensör tensör taşıma.
Önleme: Rakkase motoru (akışlı yükleme + decoder yerleşik); eski yol `git tag paket-yolu-son`. Kim: motor. Kaynak: ölçtük
(`KURULUM_DEFTERI.md` §6.2-6.3), yayıncıya göre aynı sorun başkalarında (discussion #1293, issue #1338, #1341).

**15. Venv klasörünü taşımak/yeniden adlandırmak.** Belirti: `uv trampoline failed to spawn Python child process`. Neden: uv başlatıcı exe'si
taban Python'un tam yolunu içine gömer. Önleme: `motor/calistir.py` taban Python'a dayanır; taşıdıysan `uv venv --allow-existing`.
Kim: `calistir.py`. Kaynak: ölçtük (`KURULUM_DEFTERI.md` §6.5).

## Doğru bilinen 7 yanlış

| # | Yanlış | Doğrusu | Kaynak |
|---|---|---|---|
| Y1 | "Aynı tohum = bit düzeyinde aynı ses." | Aynı parça, bit değil: GPU'da SNR 44-59 dB. Paket sürümü değişince de sapar. Kıyas SNR > 40 dB ve korelasyonla. | ölçtük; okuduk (T:881-895, issue #1345) |
| Y2 | "Caption sınırı 512 karakter." | Kesme 256 token'da, metas dahil; önce bpm/ton/süre gider, uyarı çıkmaz. 512 karakter API belgesinin önerisi. | okuduk (`conditioning_text.py`, I:338) |
| Y3 | "`success: true` ise bütün sözler söylendi." | Model fazlasını sona sıkıştırır; yalnız söz zamanı gösterir. | ölçtük |
| Y4 | "Turbo'da adım ya da guidance artırmak kaliteyi yükseltir." | Turbo guidance'ı damıtmaya gömmüştür (1.0'a zorlanır); önerilen 8 adım. Bizde 8 sabit. | okuduk (I:359-364) |
| Y5 | "Üretim süresi ses süresiyle doğrusal." | ~300 sn'ye kadar yaklaşık (≈ 0,5-0,8 ×); üstünde 4 GB'ta VRAM taşar, 4 kat yavaşlar. | ölçtük |
| Y6 | "bpm/ton/süre emirdir; söz zamanı her yerde doğrudur." | Metas rehberdir (118-122 bpm çıkabilir); söz zamanı DTW ile zorlanır, enstrümantal aralıkta çöker, `probability` hep 0. | okuduk (T:660-690, `dit_alignment.py`), ölçtük |
| Y7 | "Kod ve model MIT, öyleyse çıktı her kullanımda risksiz." | MIT yazılımı/ağırlığı kapsar; model kartı ticari kullanımı serbest der (geliştirici beyanı), ama üslup benzerliği/korumalı malzeme riski kullanıcıdadır; resmî soru başlıkları (#1256, #1364, #1358) cevapsız. | okuduk (LICENSE, HF model kartı, README:297) |

Yeni bir hata ikinci kez görülürse buraya madde olur (15'i aşarsa en az görüleni `SORUN_GIDERME.md`'ye iner). Hata bir araçla
yakalanabiliyorsa önce araca (denetle, motor), sonra buraya "Kim yakalar" ile.
