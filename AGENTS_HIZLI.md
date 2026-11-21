# AGENTS_HIZLI.md: quick card for AI coding agents / Yapay zeka ajanları için hızlı kart

English first, Türkçe below. Full rules and evidence: [`AGENTS.md`](AGENTS.md) (it wins if the two ever differ). Error codes: `docs/SIK_HATALAR.md` (anchors `#rk-e-...`) and `docs/hata_imzalari.json`; general mistakes: `docs/HATALAR.md`.

## Rule 0 (mandatory) / Kural 0 (zorunlu): seeds / tohum
**EN.** Before the FIRST generation, explain the seed to the user in plain words and offer a seed trial. A seed (`tohum` in the plan) is the starting number of the randomness: the same plan with the same seed gives the same track; the same recipe with a different seed gives a different performance of it (a different melody, mood and arrangement). Nearby numbers (for example 41 and 42) do not give similar tracks, so pick numbers far apart. Propose 3 seeds with the same caption and lyrics (copy `ornekler/tohum_denemesi.json`, put the seed in each `ad`), generate them, let the user listen and choose; the seed is a creative choice, never a quality setting. Tell the cost: every seed takes the full generation time (about 0.6-0.8 x the track length, for example about 75 s for a 100 s track on a GTX 1050 Ti [measured by the authors]), the model loads once per run (about 2 minutes). Do not change the caption to get variety: only the seed changes. Details: `docs/KULLANIM.md` section "Tohum denemesi".

**TR.** İLK üretimden önce kullanıcıya tohumu düz sözlerle anlat ve tohum denemesi öner. Tohum (plandaki `tohum`) rastgeleliğin başlangıç sayısıdır: aynı plan ve aynı tohum aynı parçayı verir; aynı tarif farklı tohumla aynı şarkının başka bir yorumunu verir (farklı ezgi, hava, düzenleme). Yakın sayılar (ör. 41 ve 42) benzer parça vermez; birbirinden uzak sayılar seç. Aynı caption ve sözle 3 tohum öner (`ornekler/tohum_denemesi.json`'u kopyala, tohumu her `ad`a yaz), üret, kullanıcı dinleyip seçsin; tohum yaratıcı bir seçimdir, kalite ayarı değildir. Bedeli söyle: her tohum tam üretim süresi kadar sürer (parça süresinin yaklaşık 0,6-0,8 katı, ör. GTX 1050 Ti'de 100 sn'lik parça için yaklaşık 75 sn [yazarlar ölçtü]), model yüklemesi koşu başına bir kez (yaklaşık 2 dk). Çeşit için caption'ı değiştirme: yalnız tohum değişir. Ayrıntı: `docs/KULLANIM.md` "Tohum denemesi" bölümü.

## English: decision tree (12 steps)
1. Goal: local music generation with ACE-Step 1.5 turbo on a Windows PC with a 4 GB NVIDIA card. Anything else: tell the user and stop.
2. Quality is fixed (turbo 8 steps, int8 decoder only, fp32 compute, LM off). Never lower it to save time or memory, and never edit a plan's `adim` to anything but 8.
3. Dry run first, it writes nothing: `kur.cmd -Kuru` (install report) and `python rakkase.py denetle --plan ornekler/sozsuz_fon_ninni.json` (plan check; it needs the ACE-Step folder). Read every `HATA:` / `UYARI:` line; each carries a code such as `[RK-E-DISK]`.
4. A non-zero exit or any `HATA`: take it to the user with the code and its first step from `docs/SIK_HATALAR.md`. Do not skip a check (`--denetimsiz`) to get past it.
5. Installing is the human's step (git and uv must be installed first; `RK-E-GIT` and `RK-E-UV` say how): tell the user what `kur.cmd` will download (ACE-Step source from github.com, about 6.4 GB of models from huggingface.co/ACE-Step and /Qwen), and let the user start it. Never accept anything on the user's behalf, never type a confirmation for the human, never run a remote script piped into a shell.
6. Install: `kur.cmd` (double click, or `scripts\kur.ps1`). Safe to re-run: complete files are skipped, an interrupted download continues.
7. First success: `uret.cmd` or `python rakkase.py uret --plan ornekler/sozsuz_fon_ninni.json` (about 2 minutes of model loading plus about 0.6-0.8 x the song length on a GTX 1050 Ti [measured by the authors]). Long runs: start hidden in the background and poll; do not block.
8. Exit 0 means the run finished, nothing more: `denetle` checks plan limits (tokens, durations); it does NOT judge the music. Do not claim the music is good; the human listens.
9. `rakkase.py test` failed or did not run means the install or engine is NOT accepted. Never report success.
10. A line with a code: look it up in `docs/SIK_HATALAR.md`, give the user its first step, quote the code. Same error twice: stop, do not try a third time.
11. `ayarlar.json` paths are only what the user gave you (`ace_kok`). Never guess a path and never write a random folder there.
12. Report in the user's language, with the code, the exit code and the first 20 lines of output (or `scripts\tani.ps1`, which masks paths). No personal paths, user names, e-mail addresses or tokens: write `<ROOT>`.

**You never:** accept a model or license on the user's behalf; use a force or skip flag; lower the quality fixed values (8 steps, fp32, LM off); write a path into `ayarlar.json` that the user did not give you; download and run a remote script; run `rakkase.py test` (GPU) without the user's go-ahead and the GPU lock; change `uv.lock`; send `tani_raporu.txt` to an issue by yourself.

### Exit code -> action
| Script | Exit | Meaning | What you do | Codes |
|---|---|---|---|---|
| `kur.ps1` / `kur.cmd` | 0 | READY | Run `python rakkase.py test` (GPU, one job at a time) | - |
| `kur.ps1` | 1 | error (clone, sync, download) | Read the code, give the user its first step; re-run once after the fix | `RK-E-KLON` `RK-E-SYNC` `RK-E-INDIR` |
| `kur.ps1` | 2 | git or uv missing, or `ayarlar.json` broken | **Take it to the user** (the human installs git and uv) | `RK-E-GIT` `RK-E-UV` `RK-E-AYAR` |
| `kur.ps1` | 3 | hardware or disk not enough | **Take it to the user**; do not force it | `RK-E-OS` `RK-E-GPU` `RK-E-GPU-VRAM` `RK-E-RAM` `RK-E-DISK` |
| `kur.ps1` | 4 | stopped (stop file) | Wait for the user | - |
| `modelleri_indir.ps1` | 1 | download or checksum failed, or a bad model table | Re-run once; a checksum mismatch means a damaged file, let the script fetch it again | `RK-E-INDIR` |
| `modelleri_indir.ps1` | 3 | not enough disk | **Take it to the user** | `RK-E-DISK` |
| `modelleri_indir.ps1` | 4 | stopped (stop file); `.part` files are kept | Wait for the user | - |
| `rakkase.py uret` | 0 | OK | Tell the user where the track is; the human listens | - |
| `rakkase.py uret` | 2 | plan check ERROR or engine did not start | Fix the plan (read the message) or the install; do not use `--denetimsiz` to skip | `RK-E-PLAN` |
| `rakkase.py uret` | 3 | a track failed (finished ones are archived) | Re-run only the failed track with `--yalniz` | `RK-E-PARCA` |
| `rakkase.py uret` | 4 | RAM guard stopped the run | **Take it to the user**: close other programs; do not start a second copy | `RK-E-RAM-BEKCI` |
| `rakkase.py uret` | 5 | done, but mp3 or archive failed | Report; the wav files are in place; run `rakkase.py mp3 <folder>` after the user fixes ffmpeg | `RK-E-ARSIV` |
| `rakkase.py uret` | 6 | `ayarlar.json` missing or wrong | **Take it to the user**: the user's ACE-Step folder goes into `ace_kok` | `RK-E-AYAR-YOK` `RK-E-ACE-KOK` `RK-E-KILIT` `RK-E-VENV` `RK-E-MODEL` |
| `rakkase.py denetle` | 2 | plan check found errors | Fix the plan; read the `HATA` lines | `RK-E-PLAN` |
| `rakkase.py denetle` / `uret` / `test` | 6 | `ayarlar.json` or install missing (also checked before `denetle`) | **Take it to the user** | `RK-E-AYAR-YOK` `RK-E-ACE-KOK` `RK-E-KILIT` `RK-E-VENV` `RK-E-MODEL` |
| `rakkase.py test` | 2, 3, 4 | the 15 s generation itself failed (same meaning as `uret`) | As for `uret` | `RK-E-PLAN` `RK-E-PARCA` `RK-E-RAM-BEKCI` |
| `rakkase.py test` | 1 | FAILED (reference mismatch) | **Take it to the user**; do not change the engine to make it pass | - |
| `scripts\tani.ps1 -Cikti tani_raporu.txt` | 0 | report made (even if it found errors; without `-Cikti` it prints to the screen only) | Show the user, ask before posting it anywhere | - |
| `scripts\tani.ps1` | 6 | could not run (for example the file could not be written) | Report the first 20 lines | - |

## Türkçe: karar ağacı (12 adım)
1. Amaç: Windows bilgisayarda, 4 GB NVIDIA kartla ACE-Step 1.5 turbo ile yerel müzik üretimi. Başka bir ortamsa kullanıcıya söyle ve dur.
2. Kalite sabit (turbo 8 adım, int8 yalnız decoder, fp32 hesap, LM kapalı). Zaman ya da bellek için asla düşürme; plandaki `adim`'ı 8'den başka değere çekme.
3. Önce kuru çalıştır, hiçbir şey yazmaz: `kur.cmd -Kuru` (kurulum raporu) ve `python rakkase.py denetle --plan ornekler/sozsuz_fon_ninni.json` (plan denetimi; ACE-Step klasörü ister). Her `HATA:` / `UYARI:` satırını oku; her biri `[RK-E-DISK]` gibi bir kod taşır.
4. Sıfır olmayan çıkış ya da herhangi bir `HATA`: kodu ve `docs/SIK_HATALAR.md`'deki ilk adımı kullanıcıya götür. Geçmek için denetimi atlama (`--denetimsiz`).
5. Kurulum insanın adımıdır (önce git ve uv kurulu olmalı; `RK-E-GIT` ve `RK-E-UV` nasıl olduğunu söyler): `kur.cmd`'nin neyi indireceğini (github.com'dan ACE-Step kaynağı, huggingface.co/ACE-Step ve /Qwen'den yaklaşık 6,4 GB model) kullanıcıya söyle, başlatmayı kullanıcıya bırak. Kullanıcı adına hiçbir şeyi kabul etme, insan yerine onay yazma, uzak bir betiği kabuğa borulayıp çalıştırma.
6. Kurulum: `kur.cmd` (çift tık ya da `scripts\kur.ps1`). Tekrar çalıştırmak güvenli: tam dosya atlanır, yarım indirme sürer.
7. İlk başarı: `uret.cmd` ya da `python rakkase.py uret --plan ornekler/sozsuz_fon_ninni.json` (GTX 1050 Ti'de yaklaşık 2 dk model yükleme ve parça süresinin yaklaşık 0,6-0,8 katı [yazarlar ölçtü]). Uzun işleri gizli arka planda başlat, yoklayarak izle; bekleyerek kilitlenme.
8. Çıkış 0 yalnız koşunun bittiği demektir: `denetle` plan sınırlarını (token, süre) denetler; müziği YARGILAMAZ. "Müzik güzel" deme; dinlemek insanın işi.
9. `rakkase.py test` kaldı ya da koşmadı: kurulum ya da motor KABUL EDİLMEZ. Asla başarı bildirme.
10. Kodlu satır: `docs/SIK_HATALAR.md`'de ara, ilk adımı kullanıcıya ver, kodu yaz. Aynı hata iki kez: dur, üçüncü kez deneme.
11. `ayarlar.json` yolları yalnız kullanıcının sana verdiğidir (`ace_kok`). Yol tahmin etme, oraya rastgele klasör yazma.
12. Kullanıcının dilinde, kodla, çıkış koduyla ve çıktının ilk 20 satırıyla (ya da yolları maskeleyen `scripts\tani.ps1` ile) bildir. Kişisel yol, kullanıcı adı, e-posta, token yazma: `<ROOT>` yaz.

**Asla yapmazsın:** kullanıcı adına model ya da lisans kabul etmek; zorlama ya da atlama bayrağı kullanmak; kalite sabitlerini (8 adım, fp32, LM kapalı) düşürmek; kullanıcının vermediği yolu `ayarlar.json`'a yazmak; uzak betik indirip çalıştırmak; kullanıcının izni ve GPU kilidi olmadan `rakkase.py test` (GPU) koşmak; `uv.lock`'u değiştirmek; `tani_raporu.txt`'yi kendiliğinden issue'ya göndermek.

### Çıkış kodu -> eylem
| Betik | Çıkış | Anlam | Ne yaparsın | Kodlar |
|---|---|---|---|---|
| `kur.ps1` / `kur.cmd` | 0 | HAZIR | `python rakkase.py test` çalıştır (GPU, aynı anda tek iş) | - |
| `kur.ps1` | 1 | hata (klon, sync, indirme) | Kodu oku, ilk adımı kullanıcıya ver; düzeltme sonrası bir kez yeniden çalıştır | `RK-E-KLON` `RK-E-SYNC` `RK-E-INDIR` |
| `kur.ps1` | 2 | git ya da uv yok, ya da `ayarlar.json` bozuk | **Kullanıcıya götür** (git ve uv'yi insan kurar) | `RK-E-GIT` `RK-E-UV` `RK-E-AYAR` |
| `kur.ps1` | 3 | donanım ya da disk yetmiyor | **Kullanıcıya götür**; zorlama | `RK-E-OS` `RK-E-GPU` `RK-E-GPU-VRAM` `RK-E-RAM` `RK-E-DISK` |
| `kur.ps1` | 4 | DURDU (durdurma dosyası) | Kullanıcıyı bekle | - |
| `modelleri_indir.ps1` | 1 | indirme ya da sha256 başarısız, ya da model tablosu bozuk | Bir kez yeniden çalıştır; hash tutmuyorsa dosya bozuktur, betik yeniden indirsin | `RK-E-INDIR` |
| `modelleri_indir.ps1` | 3 | disk yetmiyor | **Kullanıcıya götür** | `RK-E-DISK` |
| `modelleri_indir.ps1` | 4 | DURDU (durdurma dosyası); `.part` dosyaları korunur | Kullanıcıyı bekle | - |
| `rakkase.py uret` | 0 | TAMAM | Parçanın yerini söyle; dinlemek insanın işi | - |
| `rakkase.py uret` | 2 | plan denetimi HATA ya da motor başlamadı | Planı (mesajı oku) ya da kurulumu düzelt; `--denetimsiz` ile atlama | `RK-E-PLAN` |
| `rakkase.py uret` | 3 | bir parça başarısız (biten arşivlenir) | Yalnız başarısız parçayı `--yalniz` ile yeniden çalıştır | `RK-E-PARCA` |
| `rakkase.py uret` | 4 | RAM bekçisi durdurdu | **Kullanıcıya götür**: başka programları kapat; ikinci kopya başlatma | `RK-E-RAM-BEKCI` |
| `rakkase.py uret` | 5 | tamam ama mp3 ya da arşiv başarısız | Bildir; wav'lar yerinde; kullanıcı ffmpeg'i düzeltince `rakkase.py mp3 <klasör>` | `RK-E-ARSIV` |
| `rakkase.py uret` | 6 | `ayarlar.json` eksik ya da yanlış | **Kullanıcıya götür**: `ace_kok`'a kullanıcının ACE-Step klasörü yazılır | `RK-E-AYAR-YOK` `RK-E-ACE-KOK` `RK-E-KILIT` `RK-E-VENV` `RK-E-MODEL` |
| `rakkase.py denetle` | 2 | plan denetimi hata buldu | Planı düzelt; `HATA` satırlarını oku | `RK-E-PLAN` |
| `rakkase.py denetle` / `uret` / `test` | 6 | `ayarlar.json` ya da kurulum eksik (`denetle`den önce de denetlenir) | **Kullanıcıya götür** | `RK-E-AYAR-YOK` `RK-E-ACE-KOK` `RK-E-KILIT` `RK-E-VENV` `RK-E-MODEL` |
| `rakkase.py test` | 2, 3, 4 | 15 sn'lik üretimin kendisi başarısız (`uret` ile aynı anlam) | `uret` gibi | `RK-E-PLAN` `RK-E-PARCA` `RK-E-RAM-BEKCI` |
| `rakkase.py test` | 1 | KALDI (referansla uyuşmadı) | **Kullanıcıya götür**; geçsin diye motoru değiştirme | - |
| `scripts\tani.ps1 -Cikti tani_raporu.txt` | 0 | rapor yazıldı (`-Cikti` yoksa yalnız ekrana yazar) | Kullanıcıya göster, bir yere yapıştırmadan önce sor | - |
| `scripts\tani.ps1` | 6 | çalışamadı (ör. dosya yazılamadı) | İlk 20 satırı bildir | - |

Status of this card / Kartın durumu: the exit codes come from the code list of meeting 9 and from the `rakkase.py` docstring; they are matched against the finished scripts by a maintainer before the release [not yet verified / henüz doğrulanmadı].
