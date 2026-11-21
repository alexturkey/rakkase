# Sorun giderme: belirti → neden → çözüm

Kısa liste; tam öykü ve kaynaklar `KURULUM_DEFTERI.md` §6 (numaralar oradaki bölümler). Sayılar `OLCUMLER.md`, sınırlar `SINIRLAR.md`,
önlenebilir hatalar `HATALAR.md`.

| # | Belirti | Neden | Çözüm |
|---|---|---|---|
| 6.1 | Çıktı sessiz/bozuk, log'da NaN latent (fp16) | Pascal'da bf16 yok, paket fp16 yükler; `encoder.lyric_encoder.layers[7].mlp.down_proj` fp16 aralığını aşar (okudum, PR #1352) | Rakkase hesabı fp32 yapar (motor içinde sabit, bayrağı yok). |
| 6.2 | Yükleme 6-11 dk, RSS 10 GB üstü, "from_pretrained" içinde ölüyor | mmap dağınık okuma (SMR HDD) + fp16/int8/fp32 kopyaları üst üste | Rakkase motoru akışlı yükler (tek yol). Paket yoluna dönme (eski kod `git tag paket-yolu-son`). |
| 6.3 | Her parçada "Moving parameters individually: 63 sn" | DiT'in tamamı GPU'ya sığmayıp RAM'e kaçıyor; torchao `.to()` fallback'i | Rakkase motoru decoder'ı GPU'da yerleşik tutar (tek yol): taşıma ~1 sn. INFO satırı yine çıkar, zararsız. |
| 6.4 | Üretime girerken RSS 10 GB, boş RAM < 1 GB | Koşul/TE hesabı CPU'da ya da `.to(device, dtype)` CPU'da fp32 kopya | Motorun güncel hali bunu yapmaz; eski `motor/dokum_muzik.py` sürümü kullanıyorsan güncelle. |
| 6.7 | Koşul hazırlığında RSS 6,5 → 10,4 GB | Koşul modülleri toplu `.to(cuda).to(fp32)`: VRAM taştı, paylaşımlı belleğe kaçtı | Tensör tensör taşıma (`gpu_fp32_gecici`); güncel motor. |
| 6.5 | `uv trampoline failed to spawn Python child process (os error 2)` ya da `failed to canonicalize script path` | uv başlatıcısı exe içine Python'un tam yolunu gömer; klasör taşındı/yeniden adlandı | `uv venv --allow-existing --no-project --python <3.11.18 yolu> <ACE_KOK>\.venv` (paketlere dokunmaz); paket komutları `uv pip install --reinstall --no-deps <paket>==<sürüm>`; kayıt defteri `HKCU\Software\Python\Astral`. Rakkase `motor/calistir.py` bu yüzden trampoline'e değil taban Python'a dayanır. |
| 6.6 | Koşu sessizce bitti, log yarım, "stopped because the system is running low on memory" | Claude Code arka plan kabuğunu bellek baskısında kapatır | Ön planda çalıştır (Bash timeout 600 s); daha uzunu Monitor ile (605 ve 626 sn bitti). Detached/nohup yasak. Uzun plan: `rakkase.py bol`. |
| — | `BEKCI: bos RAM ... durduruluyor (çıkış 4)` | Boş RAM 30 sn boyunca < 150 MB | Başka ağır uygulamayı kapat; tekrar koş. Eşik `motor/dokum_muzik.py: Bekci`. |
| — | `unrecognized arguments: ...` ve usage başka betik adı | `BETIK` ortam değişkeni yanlış betiğe işaret ediyor (varsayılan `dokum_muzik.py`) ya da eski bayrak (`--akis`, `--fp32` silindi) | `rakkase.py` kullan; elle koşuyorsan `BETIK`'i boşalt, eski bayrakları çıkar. |
| — | `GPU kilidi` bekliyor/alınamıyor | Başka bir GPU işi kilidi tutuyor | Bitmesini bekle; `ayarlar.json: kilit=false` yalnız kilit altyapısı olmayan makinede. |
| — | Sözlü istedim, enstrümantal çıktı | `lyrics` boş ya da tam `[Instrumental]`; `instrumental: true` | Plan'a gerçek söz + `vocal_language`. Caption'da `no vocals` varsa sil. |
| — | Sözlerin bir kısmı (çoğu nakarat) söylenmemiş | Süre sözlere yetmedi; model sonu sıkıştırıyor (söz zamanında son kelimeler 0,08 sn) | `rakkase.py denetle` süre uyarısına bak; süreyi uzat ya da söz/giriş kısalt (kural `SINIRLAR.md`). `soz_zamani: true` ile kontrol et |
| — | `soz_zamani.json` `success: false`, "ara veri yok" | `save_memory_mode` açık, ara tensörler atılıyor | Ortam değişkeni ile kapat ya da bu parçada söz zamanı kullanma |
| — | mp3 yok, çıkış 5 "arşiv/mp3 başarısız" | ffmpeg PATH'te değil ya da arşiv yazılamadı | wav'lar yerinde; `ffmpeg -version`, sonra `rakkase.py mp3 <klasör>` ve `python araclar/recete.py --plan .. --kosu ..` |
| — | `URETIM BASLAMADI: plan denetiminde HATA var` | plan bozuk ya da sınır aşıldı | satırdaki HATA'yı düzelt (`SINIRLAR.md`); bilerek atlamak `--denetimsiz` |
| — | `[RK-E-AYAR-YOK]` ya da `[RK-E-ACE-KOK]` (çıkış 6) | `ayarlar.json` yok ya da `ace_kok` klasörü yok | `kur.cmd` çalıştır (ayarı yazar) ya da `ayarlar.ornek.json`'u `ayarlar.json` olarak kopyalayıp `ace_kok`'a ACE-Step klasörünü yaz; kod listesi `docs/SIK_HATALAR.md` |
| — | Çıkış 3, `HATA <parça> ...` | bir parça üretilemedi | önceki parçalar arşivlendi; `dokum.json: hata` alanı neden; o parçayı `--yalniz` ile yeniden dene |
| — | Söz zamanında satır 0 sn ya da 30 sn sürüyor | paketin hizalaması enstrümantal aralıkta çöküyor (≥5 token aynı karede) | o satırları klipte elle ya da komşu satırlardan ara değerle kullan (`SINIRLAR.md` "Söz zamanı") |
| — | Regex/desen sessizce bozuk, dosyada görünmez bayt | kabuk heredoc'u `\b`'yi geri silme baytına (0x08) çevirdi | dosyayı Write/Edit ile yaz; `grep -c $'\x08' <dosya>` |
| — | `TARGET_NOT_FOUND` güvenli silmede | Birden çok yol virgülle tek dizgi gitti | Hedefleri tek tek ver. |
| — | Kabuk içinde `\v` yol parçası kayboluyor | bash/`-c` içinde `\v` dikey sekme oluyor | Windows yollarını dosya/Edit aracıyla ya da `bytes([92])` ile yaz. |

Geri alma yolları: venv başlatıcı yedekleri `<ACE_KOK>\.venv\Scripts\*.yedek_20261105`, `Scripts_exe_yedek_20261105.zip`; kayıt defteri
`<UV>\yedek_registry_Astral_20261105.reg`. Paket kaynağına hiç dokunulmadı (tüm sarmalar `motor/dokum_muzik.py` içinde).
