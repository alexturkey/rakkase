# Tarifler: iyi bir parça nasıl yazılır

Komutlar ve plan alanları `KULLANIM.md`'de; sayısal sınırlar `SINIRLAR.md`'de; kaçınılacaklar `HATALAR.md`'de. Burada çalışmış tarifler
var. Her tarif bir örnek plana bağlı: kopyala, `ad` ve `tohum`u değiştir, `rakkase.py denetle` ile bak, üret.
Dinleme kararı her zaman kullanıcının; "çalıştı" = kullanıcı beğendi ya da teknik olarak doğru çıktı (hangisi olduğu yazılı).

## Genel kalıp (her tür)

1. **Caption paragraf.** Bir prodüktör stüdyoda anlatıyormuş gibi: tür ve dönem, davul/bas, ana enstrümanlar, vokal (cinsiyet, ton,
   okuma biçimi), duygu, düzenleme ("chorus opens up with ..."), prodüksiyon ("warm analog mix"). Çelişen kelime yok; sanatçı adı yok
   (benzerlik/Content ID riski).
2. **Metas plan alanlarında**, caption'da değil: `bpm`, `ton` ("G Major"), `olcu` ("4"), `sure`.
3. **Sözler bölüm etiketli**: `[Intro]`, `[Verse 1]`, `[Pre-Chorus]`, `[Chorus]`, `[Bridge]`, `[Outro]`; etiket kısa, gerekirse tek nitelik
   (`[Verse - rap]`, `[Chorus - catchy]`). Nakarat her tekrarda yeniden yazılır. `BÜYÜK HARF` = vurgu, `(parantez)` = arka ses.
4. **Süre sözlerden hesaplanır** (`SINIRLAR.md` süre kuralı): 100 sn ≈ 2 kıta + 2 nakarat + outro (80 bpm şarkı). Denetle UYARI verirse
   ya süreyi uzat ya sözü kısalt.
5. **Ayar sırasında tohum sabit**, tek değişken değiştir; beğenilen tarif bulunca çeşit için yalnız tohum değişir (`ad`a tohumu ekle).
   **Çeşit mantığı (kullanıcı hükmü 2026-11-05):** tarif (plan JSON) çerçeveyi kurar: tür, söz, tempo, ton, vokal.
   Tohum yorumu belirler: ezgi, ses rengi, düzenleme ayrıntısı. Ölçtüm: aynı tarif, tohum 3101 ile 3102, korelasyon 0,17, SNR -1,7 dB;
   bambaşka iki şarkı. Aynı tarif ve aynı tohum ise aynı şarkı (SNR > 40 dB). Akış: tarifi yaz, birkaç tohumla çeşit üret, kullanıcı
   seçsin, seçilen tohum sabitlenir.
   Yeni tohum şöyle çekilir: `secrets.randbelow(2**32)` (paketin kendi aralığı da 0..2³²−1); yakın sayı benzer şarkı vermez.
6. Klip/karaoke gerekecekse `soz_zamani: true` (11-18 sn ek, sesi değiştirmez).

## Tarif kartları

| Tür | Örnek plan | Caption özü | bpm | Not |
|---|---|---|---|---|
| Türkçe rap (boom bap) | `ornekler/rap_claude_code_40sn.json` | paragraf: "dusty boom bap beat, punchy kick and crisp snare, deep bass, confident Turkish male rapper with tight flow, catchy chorus ..." | 92 | 40 sn: intro + 6 satır + nakarat sığar (30 sn'de nakarat sığmadı); `soz_zamani: true`. Satır 10-16 hece çalıştı. Kullanıcı beğendi, klip yapıldı |
| Rap, üç tarz (boom bap / trap / funk) | `ornekler/rap_claude_code_3_tur.json` | aynı söz, farklı davul/bas betimi ve tohum (1301-1303) | 92 / 100 / 96 | 30 sn sürümler: nakarat sıkışır (bilerek bırakıldı, denetle UYARI örneği) |
| Akustik balad | `ornekler/sozlu_balad.json` | "warm heartfelt Turkish acoustic pop ballad, soft intimate male vocal, fingerpicked acoustic guitar, gentle piano" | 80 | 100 sn = 2 kıta + 2 nakarat + outro; şarkı satırı ~1,9 ölçü |
| Koro | `ornekler/cesit_6_tarz.json` (`2_koro_daglar_120sn`) | "mixed choir, layered harmonies", geniş | 70 | satır ~2,0 ölçü |
| Duet | aynı plan (`1_duet_istasyon_150sn`) | "male and female vocals alternating then harmonizing" | 76 | 150 sn: `bol` ile kendi koşusunda |
| Halk | aynı plan (`3_halk_yayla_130sn`) | "Turkish folk female vocal, bağlama" | 92 | telaffuzu kulakla değerlendir |
| Rap (uzun) | aynı plan (`4_rap_gece_110sn`) | "Turkish rap, male MC, tight flow" | 90 | |
| Oryantal enstrümantal | aynı plan (`5_rakkase_oryantal_120sn`) | darbuka, ud, kanun; "no vocals" | 110 | |
| Çocuk şarkısı | aynı plan (`6_cocuk_kedi_90sn`) | "cheerful children's choir" | 112 | |
| Enstrümantal fon (konuşma altı) | `ornekler/sozsuz_fon_ninni.json` | "calm, unobtrusive under voice-over ... no vocals" | 66 | seviye -28..-32 LUFS (`araclar/olc_lufs.py`); uzun videoda döngüle |

## Rap ve sözlü kısa parça (2026-11-05, "Claude Code rap")

- İlk deneme virgüllü kelime listesiydi, kullanıcıya zayıf geldi; resmî rap örnekleri (`examples/text2music/example_02/03.json`) paragraf.
  İkinci tur paragraf caption ile üç tarz (boom bap / trap / funk), aynı söz ve tohum: kullanıcı boom bap'i seçti.
- 92 bpm'de rap satırı ≈ 1,15 ölçü (~3 sn), sözlü `[Intro]` ≈ 4 ölçü (~9 sn). 30 sn'de nakarat son 2 sn'ye sıkıştı; 40 sn'de nakarat
  29,8 ve 33,2. sn'de söylendi.
- Söz zamanı rapte sağlam çıktı (çöküş yok); balad ve koroda enstrümantal aralıklarda çöktü (`SINIRLAR.md`).

## Fon müziği (konuşmanın altı)

- Caption'da "no vocals", "calm", "unobtrusive under voice-over"; sözsüz plan (`lyrics` yok ya da `[Instrumental]`).
- Seviye konuşmadan 14-18 LU aşağı (-28..-32 LUFS); ölçüm `araclar/olc_lufs.py <wav>`.
- Aynı süreçte ilk parça biraz yavaş (koşul hazırlığı ~10 sn, text encoder 3-7 sn), sonrakiler ısınmış.

## Söz klibi (karaoke video) kaydı (2026-11-06, "Beynimdesin" klibi)

- Akış ve komutlar tek yerde: beceri `.claude/skills/soz-klibi/SKILL.md` (betikler `scripts/`: sahne şablonu, veri hazırlama,
  WebCodecs kayıt, hafif kalite ölçümü). Klip ajanına bu beceri brif olarak verilir.
- Kayıt YALNIZ WebCodecs yoluyla (tarayıcının kendi kodlayıcısı, kalıp: anlatim `src/bolum_50_render/render.mjs`).
- Ölçüldü (90 sn, 1080x1920, 2700 kare): ekran görüntüsü yolu ~13,5 dk (3,3 kare/sn) → WebCodecs 78 sn (36,2 kare/sn);
  kayıpsız referansa karşı VMAF 86,7 / SSIM 0,980 (x264 crf18: 84,8 / 0,976). 16 Mbps yeterli (24 Mbps fark getirmiyor).
- Kare kare ekran görüntüsü (headless screenshot) yolu kullanılmaz. Rastgele doku sabit tohumla (tekrar kayıt aynı çıkar).
- Kalite ölçümü dilimle ve en çok 2 iş parçacığıyla (`-threads 2`, `libvmaf n_threads=2`): tüm video üstünde 7 çekirdek bilgisayarı kilitledi.

## Denenip karara bağlananlar

- `shift` 3.0 (paketin turbo önerisi) vs 1.0: rap 40 sn (tohum 1301) ve balad 100 sn (tohum 2026) çiftleri `uretimler/`de
  (`..._shift3` ve 1.0 eşi). Dinlendi (2026-11-05, kullanıcı: "hepsi iyi geldi"): kulakla fark yok; varsayılan 1.0 kalır
  (söz zamanı yalnız 1.0'da güvenilir). 3.0 isteyen plan alanıyla dener (`KARARLAR.md` K13).
