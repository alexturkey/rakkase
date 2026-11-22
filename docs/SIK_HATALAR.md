# Rakkase: Sık hatalar (kodlu) / Common errors (coded)

English and Turkish side by side. Every error line our scripts print looks like `HATA: [RK-E-XXX] ...` (warnings: `UYARI: [RK-W-XXX] ...`). Find the code below; each entry has the cause and ONE first step. The first steps match `docs/hata_imzalari.json`. Not in the list? See `docs/SORUN_GIDERME.md` (symptom to fix) and `docs/HATALAR.md` (general mistakes and wrong beliefs). For a bug report give the code, the exit code and the first 20 lines of output, or the file from `scripts\tani.ps1` (it masks your paths; read it before you post it).

Betiklerimizin bastığı hata satırı `HATA: [RK-E-XXX] ...` biçimindedir (uyarı: `UYARI: [RK-W-XXX] ...`). Kodu aşağıda bulun; her maddede neden ve TEK ilk adım var. İlk adımlar `docs/hata_imzalari.json` ile aynıdır. Listede yoksa `docs/SORUN_GIDERME.md` ve `docs/HATALAR.md`'ye bakın. Hata bildirirken kodu, çıkış kodunu ve çıktının ilk 20 satırını ya da `scripts\tani.ps1` dosyasını verin (yollarınızı maskeler; yapıştırmadan önce okuyun).

Labels / Etiketler: [measured/ölçtüm] we ran it, [read/okudum] taken from a document or code, [guess/tahmin] not checked. Status: the code names and first steps come from the finished scripts and `docs/hata_imzalari.json`; the causes were written from our documents and the script text, and a complete install on an empty machine has not been verified yet [not yet verified / henüz doğrulanmadı]. Exit codes are in the entries: `kur.ps1` 0 READY, 1 error, 2 input or settings needed, 3 hardware or disk not enough; `rakkase.py` 2 plan, 3 track, 4 RAM guard, 5 archive, 6 settings or install missing.

## A. Errors / Hatalar

1. <a id="rk-e-os"></a>**`RK-E-OS`** (exit/çıkış 3): Windows 10 or newer needed / Windows 10 ya da üstü gerekir
   - Cause / Neden: the scripts are Windows PowerShell 5.1 scripts [read]. / betikler Windows PowerShell 5.1 betikleridir [okudum].
   - First step / İlk adım: Use Windows 10 or 11. / Windows 10 ya da 11 kullanın.

2. <a id="rk-e-gpu"></a>**`RK-E-GPU`** (exit/çıkış 3): no usable NVIDIA card (`nvidia-smi` missing or silent) / kullanılabilir NVIDIA kart yok (`nvidia-smi` yok ya da çıktı vermiyor)
   - Cause / Neden: no NVIDIA card, or no driver [read]. / NVIDIA kart ya da sürücü yok [okudum].
   - First step / İlk adım: Install the current NVIDIA driver and run `kur.cmd` again. Rakkase needs an NVIDIA GPU with CUDA; it does not run on AMD or Intel cards. / Güncel NVIDIA sürücüsünü kurup `kur.cmd`'yi yeniden çalıştırın. Rakkase CUDA'lı NVIDIA kart ister; AMD ya da Intel kartta çalışmaz.

3. <a id="rk-e-gpu-vram"></a>**`RK-E-GPU-VRAM`** (exit/çıkış 3): less than 4 GB VRAM or compute capability below 6.1 / 4 GB'tan az VRAM ya da compute capability 6.1'in altında
   - Cause / Neden: Rakkase is sized for a 4 GB card; smaller cards were not tried [not tried]. / Rakkase 4 GB kart için boyutlandı; daha küçük kartlar denenmedi [denenmedi].
   - First step / İlk adım: Rakkase was measured on a 4 GB card. With less VRAM it does not fit. The check can be skipped with `kur.cmd -Zorla` at your own risk (not tried); we do not recommend it. A Hardware test issue helps us measure more cards. / Rakkase 4 GB kartta ölçüldü. Daha azına sığmaz. `kur.cmd -Zorla` denetimi kendi riskinizle atlar (denenmedi); önermiyoruz. Donanım testi issue'su daha çok kart ölçmemize yardım eder.

4. <a id="rk-e-ram"></a>**`RK-E-RAM`** (exit/çıkış 3): less than 12 GB RAM / 12 GB'tan az RAM
   - Cause / Neden: a run needs about 6.4 GB RAM at its peak plus the system [measured on our machine, `docs/OLCUMLER.md`]. / koşu tepe noktasında yaklaşık 6,4 GB RAM ister, sistem de yer kaplar [kendi makinemizde ölçtük, `docs/OLCUMLER.md`].
   - First step / İlk adım: Close other programs and use a computer with 16 GB RAM; below 12 GB is not supported. / Diğer programları kapatın ve 16 GB RAM'li bir bilgisayar kullanın; 12 GB altı desteklenmez.

5. <a id="rk-e-disk"></a>**`RK-E-DISK`** (exit/çıkış 3): not enough free disk space (`kur.ps1`, `modelleri_indir.ps1`) / disk boş yeri yetmiyor (`kur.ps1`, `modelleri_indir.ps1`)
   - Cause / Neden: models are about 6.4 GB in 22 files [read: `scripts/modeller.json`] plus the Python environment with torch; the whole install may need about 23 GB of disk (the check asks for about 25 GiB free) [measured: one clean install used about 23 GB]. / modeller yaklaşık 6,4 GB, 22 dosya [okudum: `scripts/modeller.json`] ve torch'lu Python ortamı; kurulumun tamamı yaklaşık 23 GB yer tuttu, denetim yaklaşık 25 GiB boş yer ister [ölçtüm: temiz bir kurulum yaklaşık 23 GB].
   - First step / İlk adım: Free disk space or install on another drive: `kur.cmd -AceKok <SURUCU>\rk\ace_step`. / Disk yeri açın ya da başka sürücüye kurun: `kur.cmd -AceKok <SURUCU>\rk\ace_step`.

6. <a id="rk-e-git"></a>**`RK-E-GIT`** (exit/çıkış 2): git is missing / git yok
   - Cause / Neden: git is not installed or not on PATH. / git kurulu değil ya da PATH'te yok.
   - First step / İlk adım: Install git (`winget install --id Git.Git -e`), open a NEW terminal and run `kur.cmd` again. / git kurun (`winget install --id Git.Git -e`), YENİ bir terminal açıp `kur.cmd`'yi yeniden çalıştırın.

7. <a id="rk-e-uv"></a>**`RK-E-UV`** (exit/çıkış 2): uv is missing (it is not installed automatically) / uv yok (kendiliğinden kurulmaz)
   - Cause / Neden: uv (the Python environment tool) is not installed or not on PATH. / uv (Python ortam aracı) kurulu değil ya da PATH'te yok.
   - First step / İlk adım: Install uv (`winget install --id=astral-sh.uv -e`, or `python -m pip install uv`) and run `kur.cmd` again; or put the path of `uv.exe` into the `RK_UV` environment variable. / uv kurun (`winget install --id=astral-sh.uv -e` ya da `python -m pip install uv`) ve `kur.cmd`'yi yeniden çalıştırın; ya da `uv.exe` yolunu `RK_UV` ortam değişkenine yazın.

8. <a id="rk-e-klon"></a>**`RK-E-KLON`** (exit/çıkış 1): ACE-Step clone failed, wrong commit, or the folder is not an ACE-Step folder / ACE-Step klonu başarısız, commit yanlış ya da klasör ACE-Step değil
   - Cause / Neden: no internet, a proxy, a half-made folder from an earlier try, or the target folder holds other files. / internet yok, vekil sunucu, önceki denemeden kalan yarım klasör ya da hedef klasörde başka dosyalar var.
   - First step / İlk adım: Check the connection and the disk; delete the half-made folder and run `kur.cmd` again, or give an empty folder with `-AceKok`. / Bağlantıyı ve diski kontrol edin; yarım klasörü silip `kur.cmd`'yi yeniden çalıştırın ya da `-AceKok` ile boş bir klasör verin.

9. <a id="rk-e-sync"></a>**`RK-E-SYNC`** (exit/çıkış 1): uv could not build the Python environment (or the plan check after install failed) / uv Python ortamını kuramadı (ya da kurulum sonrası plan denetimi başarısız)
   - Cause / Neden: an interrupted download of the Python packages (torch is large), no space, or a path problem (see `RK-W-YOL-*`). / Python paketlerinin (torch büyüktür) indirmesi kesildi, yer yok ya da yol sorunu (`RK-W-YOL-*`).
   - First step / İlk adım: Check the network and free disk space and run `kur.cmd` again: it continues where it stopped. / Ağı ve disk boş yerini kontrol edip `kur.cmd`'yi yeniden çalıştırın: kaldığı yerden sürer.

10. <a id="rk-e-indir"></a>**`RK-E-INDIR`** (exit/çıkış 1): model download or sha256 check failed (`kur.ps1`, `modelleri_indir.ps1`) / model indirme ya da sha256 doğrulaması başarısız (`kur.ps1`, `modelleri_indir.ps1`)
   - Cause / Neden: interrupted network, or a damaged file; only `huggingface.co/ACE-Step` and `huggingface.co/Qwen` are used. / ağ kesildi ya da dosya bozuk; yalnız `huggingface.co/ACE-Step` ve `huggingface.co/Qwen` kullanılır.
   - First step / İlk adım: Run `kur.cmd` again: an interrupted download continues. A file that failed the check is kept as `.sha256_uyusmadi`; delete it and run again. / `kur.cmd`'yi yeniden çalıştırın: yarım indirme kaldığı yerden sürer. Doğrulamayı geçemeyen dosya `.sha256_uyusmadi` adıyla saklanır; silip yeniden çalıştırın.

11. <a id="rk-e-ayar"></a>**`RK-E-AYAR`** (exit/çıkış 2; 1 if the file `kur.cmd` itself wrote is not valid JSON / `kur.cmd`'nin kendi yazdığı dosya JSON değilse 1): `ayarlar.json` is not valid JSON (setup left it untouched) / `ayarlar.json` bozuk (kurulum dokunmadı)
   - Cause / Neden: a typo in the file (a missing quote or comma). / dosyada yazım hatası (eksik tırnak ya da virgül).
   - First step / İlk adım: Fix the JSON or rename the file and run `kur.cmd` again. / JSON'u düzeltin ya da dosyanın adını değiştirip `kur.cmd`'yi yeniden çalıştırın.

12. <a id="rk-e-ayar-yok"></a>**`RK-E-AYAR-YOK`** (exit/çıkış 6): `ayarlar.json` is missing, unreadable or broken (`rakkase.py` reads a broken file the same way) / `ayarlar.json` yok ya da okunamıyor
   - Cause / Neden: first run on this machine, or the file was removed. / bu makinede ilk çalıştırma ya da dosya silinmiş.
   - First step / İlk adım: Double-click `kur.cmd` (it installs ACE-Step and writes the settings). If ACE-Step is already installed, copy `ayarlar.ornek.json` to `ayarlar.json` and write your ACE-Step folder into `ace_kok`. / `kur.cmd`'ye çift tıklayın (ACE-Step'i kurar ve ayarları yazar). ACE-Step zaten kuruluysa `ayarlar.ornek.json`'u `ayarlar.json` olarak kopyalayıp `ace_kok`'a ACE-Step klasörünüzü yazın.

13. <a id="rk-e-ace-kok"></a>**`RK-E-ACE-KOK`** (exit/çıkış 6): the `ace_kok` folder in `ayarlar.json` does not exist / `ayarlar.json`'daki `ace_kok` klasörü yok
   - Cause / Neden: `ace_kok` still holds the placeholder or points to a folder that is gone; `rakkase.py denetle` needs it too, for the tokenizer [measured]. / `ace_kok` yer tutucuda kalmış ya da olmayan bir klasörü gösteriyor; `denetle` de tokenizer için buna ihtiyaç duyar [ölçtüm].
   - First step / İlk adım: Write the real ACE-Step folder into `ace_kok` in `ayarlar.json`, or run `kur.cmd`. / `ayarlar.json`'daki `ace_kok`'a gerçek ACE-Step klasörünü yazın ya da `kur.cmd`'yi çalıştırın.

14. <a id="rk-e-kilit"></a>**`RK-E-KILIT`** (exit/çıkış 6): `kilit` is true but `kilit_src` is missing / `kilit` true ama `kilit_src` yok
   - Cause / Neden: the GPU lock is optional and only for people who run several GPU jobs. / GPU kilidi isteğe bağlıdır, yalnız birden çok GPU işi koşanlar içindir.
   - First step / İlk adım: Set `"kilit": false` in `ayarlar.json` (the GPU lock needs a module of your own). / `ayarlar.json`'da `"kilit": false` yapın (GPU kilidi kendi modülünüzü ister).

15. <a id="rk-e-venv"></a>**`RK-E-VENV`** (exit/çıkış 6): the ACE-Step Python environment (`.venv`) is missing / ACE-Step Python ortamı (`.venv`) yok
   - Cause / Neden: the install stopped before the uv step, or the folder was moved or renamed (uv bakes the Python path into the launchers, `docs/SORUN_GIDERME.md` 6.5) [read]. / kurulum uv adımından önce durdu ya da klasör taşındı/yeniden adlandırıldı (uv, Python yolunu başlatıcılara gömer, `docs/SORUN_GIDERME.md` 6.5) [okudum].
   - First step / İlk adım: Run `kur.cmd` (the uv step builds the environment). / `kur.cmd`'yi çalıştırın (uv adımı ortamı kurar).

16. <a id="rk-e-model"></a>**`RK-E-MODEL`** (exit/çıkış 6): a model file is missing / model dosyası eksik
   - Cause / Neden: `checkpoints` lacks `acestep-v15-turbo`, `vae` or `Qwen3-Embedding-0.6B`, or a download was cut. / `checkpoints` altında `acestep-v15-turbo`, `vae` ya da `Qwen3-Embedding-0.6B` yok ya da indirme yarım kaldı.
   - First step / İlk adım: Run `kur.cmd` (it downloads the missing files with sha256 checks and continues where it stopped). / `kur.cmd`'yi çalıştırın (eksik dosyaları sha256 doğrulamalı indirir, kaldığı yerden sürer).

17. <a id="rk-e-plan"></a>**`RK-E-PLAN`** (exit/çıkış 2): the plan check found an error, or the engine did not start / plan denetimi hata buldu ya da motor başlamadı
   - Cause / Neden: a field is missing or over a limit (caption over 256 tokens, duration outside 10 to 600 s, `adim` other than 8, lyric tags) [read: `docs/SINIRLAR.md`]. / bir alan eksik ya da sınırı aşıyor (256 token üstü caption, 10-600 sn dışı süre, 8'den farklı `adim`, söz etiketleri) [okudum: `docs/SINIRLAR.md`].
   - First step / İlk adım: Read the `HATA` lines printed above it and fix the plan (`docs/KULLANIM.md`, plan fields); do not skip the check with `--denetimsiz`. / Üstünde yazan `HATA` satırlarını okuyup planı düzeltin (`docs/KULLANIM.md`, plan alanları); `--denetimsiz` ile atlamayın.

18. <a id="rk-e-parca"></a>**`RK-E-PARCA`** (exit/çıkış 3): a track failed / bir parça başarısız
   - Cause / Neden: that track could not be generated (see `dokum.json`, field `hata`) [read]. / o parça üretilemedi (`dokum.json`, `hata` alanı) [okudum].
   - First step / İlk adım: Finished tracks are archived. Re-run only the failed one with `--yalniz <name>`. / Biten parçalar arşivlendi. Yalnız başarısız olanı `--yalniz <ad>` ile yeniden çalıştırın.

19. <a id="rk-e-ram-bekci"></a>**`RK-E-RAM-BEKCI`** (exit/çıkış 4): the RAM guard stopped the run (free RAM ran out) / RAM bekçisi koşuyu durdurdu (boş RAM bitti)
   - Cause / Neden: free RAM stayed under 150 MB for 30 seconds; the guard stops the run before the system freezes [read: `motor/dokum_muzik.py`]. / boş RAM 30 sn boyunca 150 MB altında kaldı; bekçi sistem donmadan koşuyu durdurur [okudum: `motor/dokum_muzik.py`].
   - First step / İlk adım: Close browsers and other big programs; do not start a second copy; run again. / Tarayıcı ve büyük programları kapatın; ikinci kopya başlatmayın; yeniden çalıştırın.

20. <a id="rk-e-arsiv"></a>**`RK-E-ARSIV`** (exit/çıkış 5): generation finished but the mp3/archive step failed / üretim bitti ama mp3/arşiv adımı başarısız
   - Cause / Neden: `ffmpeg` is not on PATH, or the archive folder could not be written; the wav files are in place. / `ffmpeg` PATH'te yok ya da arşiv klasörüne yazılamadı; wav dosyaları yerinde.
   - First step / İlk adım: The wav files are in place. Install ffmpeg, then `python rakkase.py mp3 <folder>`; archive by hand: `python araclar/recete.py --plan .. --kosu ..`. / wav dosyaları yerinde. ffmpeg kurup `python rakkase.py mp3 <klasör>` çalıştırın; arşiv elle: `python araclar/recete.py --plan .. --kosu ..`.

## B. Warnings / Uyarılar (the run continues / çalışma sürer)

21. <a id="rk-w-ram"></a>**`RK-W-RAM`**: less than 16 GB RAM / 16 GB'tan az RAM
   - Step / Adım: Close other programs before generating. / Üretimden önce diğer uygulamaları kapatın.

22. <a id="rk-w-disk-pay"></a>**`RK-W-DISK-PAY`**: free disk space is above the limit but the margin is thin / disk boş yeri eşiği geçti ama pay dar
   - Step / Adım: Free some more space if the install stops. / Kurulum durursa biraz daha yer açın.

23. <a id="rk-w-gpu-denenmedi"></a>**`RK-W-GPU-DENENMEDI`**: this GPU was not tried (only the GTX 1050 Ti 4 GB was verified) / bu kart denenmedi (yalnız GTX 1050 Ti 4 GB doğrulandı)
   - Step / Adım: You can continue; the result is not guaranteed. Please report your result with the Hardware test form. / Devam edebilirsiniz; sonuç garanti değil. Sonucunuzu Donanım testi formuyla bildirirseniz seviniriz.

24. <a id="rk-w-ace-surum"></a>**`RK-W-ACE-SURUM`**: your ACE-Step folder is on a different commit / ACE-Step klasörü farklı bir commit'te
   - Step / Adım: Left untouched. Rakkase was measured with the pinned commit (`ca1e85f`); if something breaks, try that commit. / Dokunulmadı. Rakkase sabit commit'le (`ca1e85f`) ölçüldü; bir şey bozulursa o commit'i deneyin.

25. <a id="rk-w-ayar-farkli"></a>**`RK-W-AYAR-FARKLI`**: `ayarlar.json` points to a different ACE-Step folder than the one just installed / `ayarlar.json` az önce kurulandan farklı bir ACE-Step klasörünü gösteriyor
   - Step / Adım: Not changed. Edit `ace_kok` in `ayarlar.json` if you want the new folder. / Değiştirilmedi. Yeni klasörü kullanmak için `ayarlar.json`'daki `ace_kok`'u düzenleyin.

26. <a id="rk-w-uvlock"></a>**`RK-W-UVLOCK`**: `uv.lock` is missing, unlocked sync / `uv.lock` yok, kilitsiz sync
   - Step / Adım: Package versions may differ from the measured ones. / Paket sürümleri ölçülenlerden farklı olabilir.

27. <a id="rk-w-ffmpeg"></a>**`RK-W-FFMPEG`**: ffmpeg is not on PATH: no mp3 / ffmpeg PATH'te yok: mp3 yapılamaz
   - Step / Adım: Install ffmpeg (`winget install --id Gyan.FFmpeg -e`); wav files are still produced. / ffmpeg kurun (`winget install --id Gyan.FFmpeg -e`); wav dosyaları yine üretilir.

28. <a id="rk-w-indir-kaynak"></a>**`RK-W-INDIR-KAYNAK`**: a file in `-ModelKlasoru` did not match its sha256 and is downloaded instead / `-ModelKlasoru`'ndaki dosya sha256 tutmadı, indirilecek
   - Step / Adım: Nothing to do; it is downloaded from the official source. / Yapacak bir şey yok; resmî kaynaktan indirilir.

29. <a id="rk-w-yol-bosluk"></a>**`RK-W-YOL-BOSLUK`**: a path contains a space / yolda boşluk var
   - Step / Adım: Prefer a short ASCII path such as `<SURUCU>\rk`; some tools break on spaces [guess]. / Kısa ASCII bir yol (örnek `<SURUCU>\rk`) önerilir; bazı araçlar boşlukta takılır [tahmin].

30. <a id="rk-w-yol-ascii"></a>**`RK-W-YOL-ASCII`**: a path contains non-ASCII characters (for example Turkish letters) / yolda ASCII dışı karakter var (ör. Türkçe harfler)
   - Step / Adım: Prefer a short ASCII path such as `<SURUCU>\rk` [guess: some tools break on these letters]. / Kısa ASCII bir yol (örnek `<SURUCU>\rk`) önerilir [tahmin: bazı araçlar bu harflerde takılır].

31. <a id="rk-w-yol-onedrive"></a>**`RK-W-YOL-ONEDRIVE`**: a path is inside OneDrive / yol OneDrive içinde
   - Step / Adım: OneDrive may lock files and upload 6 GB of models; use a folder outside OneDrive. / OneDrive dosyaları kilitleyebilir ve 6 GB modeli buluta yükler; OneDrive dışında bir klasör kullanın.

32. <a id="rk-w-yol-uzun"></a>**`RK-W-YOL-UZUN`**: a path is long / yol uzun
   - Step / Adım: Use a shorter folder such as `<SURUCU>\rk`. / Daha kısa bir klasör (örnek `<SURUCU>\rk`) kullanın.

33. <a id="rk-e-panel"></a>**`RK-E-PANEL`** (exit/çıkış 5): the panel video could not be made (`rakkase.py panel`) / panel videosu yapılamadı (`rakkase.py panel`)
   - Cause / Neden: ffmpeg is missing, the wav is missing, broken or too short, or the process stopped [read: `araclar/panel.py`]. / ffmpeg yok, wav yok, bozuk ya da çok kısa, ya da süreç düştü [okudum: `araclar/panel.py`].
   - First step / İlk adım: Install ffmpeg (`winget install --id Gyan.FFmpeg -e`) if it is missing, check that the wav is a real track, then run `python rakkase.py panel <folder>` again. The music is not affected. / ffmpeg yoksa kurun (`winget install --id Gyan.FFmpeg -e`), wav'in gerçek bir parça olduğunu kontrol edin, sonra `python rakkase.py panel <klasör>` komutunu yeniden çalıştırın. Müzik etkilenmez.

34. <a id="rk-w-panel"></a>**`RK-W-PANEL`**: the panel video failed during `uret`; the track is delivered / `uret` sırasında panel videosu düştü; parça teslim edildi
   - Step / Adım: Nothing is lost: wav and mp3 are in place and the exit code does not change. Run `python rakkase.py panel <folder>` to try again. If ffmpeg is simply missing you see `RK-W-FFMPEG` instead and the panel is skipped. / Bir şey kaybolmadı: wav ve mp3 yerinde, çıkış kodu değişmez. Yeniden denemek için `python rakkase.py panel <klasör>`. ffmpeg yoksa bunun yerine `RK-W-FFMPEG` görürsünüz ve panel atlanır.

35. <a id="rk-e-nan"></a>**`RK-E-NAN`** (exit/çıkış 8): the generated audio contains NaN/inf (corrupt sound) / üretilen ses NaN/inf içeriyor (bozuk ses)
   - Cause / Neden: an fp16 VAE decode on some cards (seen on a GTX 1650, issue #1) / bazı kartlarda fp16 VAE çözümü (GTX 1650'de görüldü, issue #1).
   - First step / İlk adım: The install is not necessarily broken: GTX 16xx cards give NaN with an fp16 VAE and the engine now keeps the VAE in fp32 on them automatically (the fix is in the code; GPU verification on a 16xx card is still pending). On another card set `"vae_fp32": true` in `ayarlar.json` and run again; if it persists, report the card name and this line (no mp3 or panel is made from a NaN wav). Cost of the fp32 VAE [measured on a GTX 1050 Ti with `vae_fp32: true`, 2026-11-23]: VRAM peak 3768 MB (2653 MB without it), reserved 4976 MB, which is more than a 4 GB card has, so Windows may spill into shared system memory [not measured]; a 15 s track took 21.2 s instead of 17.7 s (about 20 % slower). It works, but on a 4 GB card it is at the limit. / Kurulum bozuk olmak zorunda değil: GTX 16xx kartlar fp16 VAE ile NaN verir, motor bu kartlarda VAE'yi kendiliğinden fp32 yapar (düzeltme kodda; 16xx kartta GPU doğrulaması bekliyor). Başka kartta `ayarlar.json`'a `"vae_fp32": true` yazıp yeniden çalıştırın; sürerse kart adını ve bu satırı bildirin (NaN'li wav'dan mp3 ya da panel yapılmaz). fp32 VAE'nin bedeli [GTX 1050 Ti'de `vae_fp32: true` ile ölçüldü, 2026-11-23]: VRAM tepe 3768 MB (onsuz 2653 MB), ayrılan 4976 MB; bu 4 GB kartın belleğinden fazla, Windows paylaşımlı sistem belleğine taşabilir [ölçülmedi]; 15 sn parça 17,7 yerine 21,2 sn sürdü (yaklaşık %20 yavaş). Çalışır ama 4 GB kartta sınırdadır.

36. <a id="rk-w-referans-disi"></a>**`RK-W-REFERANS-DISI`** (`test` exit/çıkış 7): not the reference card: byte/waveform match with the reference is not proven / referans kartı değil: referansla bayt/dalga uyumu kanıtlanmadı
   - Cause / Neden: the reference was made on a GTX 1050 Ti; another card can draw different noise for the same seed [guess]. / referans GTX 1050 Ti'de üretildi; başka kart aynı tohumla farklı gürültü çekebilir [tahmin].
   - First step / İlk adım: This is not a failed install. The card-independent health checks passed (no NaN/inf, duration, level, two runs on this card agree). Do not report success; listen to the track yourself (`python rakkase.py uret --plan ornekler/sozsuz_fon_ninni.json`). If a health check FAILED the test exits 1 instead. / Kurulum başarısız değil. Karttan bağımsız sağlık ölçümleri geçti (NaN/inf yok, süre, seviye, bu kartta iki koşu tutarlı). Başarı demeyin; parçayı kendiniz dinleyin (`python rakkase.py uret --plan ornekler/sozsuz_fon_ninni.json`). Sağlık ölçümü KALDIYSA test bunun yerine 1 ile çıkar.
