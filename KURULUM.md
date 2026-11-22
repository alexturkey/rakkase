# Install / Kurulum

English first, Türkçe below. Full story with every wall we hit: [`docs/KURULUM_DEFTERI.md`](docs/KURULUM_DEFTERI.md) (Turkish for now). Labels: [measured] we ran it on our machine, [read] taken from a document or code, not run in this exact form, [guess] not checked.

## English

**Two ways.** (A) the easy way: double-click `kur.cmd`. (B) by hand, below, for advanced users or when the script stops and you want to see each step.

**A. `kur.cmd` (recommended).** Extract the repository into a short folder without spaces (for example a folder named `rk` at the top of a drive). Double-click `kur.cmd`; to see a report first, run `kur.cmd -Kuru` in a terminal. Install git, uv and Python 3 first (`winget install --id Git.Git -e`, `winget install --id=astral-sh.uv -e`, `winget install --id Python.Python.3.12 -e`; they are not installed for you; `python` must work in a new terminal: the Microsoft Store "python" alias is not Python). You need an NVIDIA GPU (4 GB or more) and about 25 GiB free disk. It checks git, uv, driver, disk and VRAM, installs ACE-Step 1.5 at the tested commit, downloads the model files (about 6.4 GB, from `huggingface.co/ACE-Step` and `huggingface.co/Qwen`, with sha256 checks) and writes `ayarlar.json` with your `ace_kok`. Run it again after an interruption: it continues. **Already have an ACE-Step folder?** `kur.cmd` detects it and does not install it again; if it does not, put your folder into `ace_kok` in `ayarlar.json` by hand (step B5). An error prints `HATA: [RK-E-...]`: see `docs/SIK_HATALAR.md`. Windows may warn about a file downloaded from the internet: read `scripts\kur.ps1` first; do not run it as administrator. Status of the scripts: [not yet verified end to end on an empty machine].

**B. By hand.**

Rakkase is a thin layer on top of ACE-Step 1.5. So you install ACE-Step once, then point Rakkase at it. Your folder names are yours: below `<RAKKASE>` is this repository and `<ACE_KOK>` is the ACE-Step folder.

1. **Machine.** Windows 10/11, NVIDIA GPU with 4 GB or more (tested only on a GTX 1050 Ti 4 GB [measured]), 16 GB RAM, a recent NVIDIA driver (`nvidia-smi` works). A separate CUDA Toolkit is not needed: the torch wheel carries its own CUDA [read].
2. **Tools.** Git, Python 3 (for `rakkase.py`, any 3.x [read]), and [uv](https://docs.astral.sh/uv/) (we used 0.13.6 [measured]).
3. **ACE-Step 1.5, pinned commit** [measured: this commit, `docs/KURULUM_DEFTERI.md` section 2]:
   ```
   git clone https://github.com/ACE-Step/ACE-Step-1.5 <ACE_KOK>
   cd <ACE_KOK>
   git checkout ca1e85f
   uv python install 3.11
   uv sync
   ```
   `uv sync` builds `<ACE_KOK>\.venv` with torch 2.7.1+cu128 from the lock file.
4. **Model files** from the official repository `ACE-Step/Ace-Step1.5` into `<ACE_KOK>\checkpoints\` (about 6.4 GB [read: `scripts/modeller.json`]): the folders `acestep-v15-turbo`, `vae`, `Qwen3-Embedding-0.6B`, and the config of `acestep-5Hz-lm-1.7B`. A `huggingface_hub.snapshot_download(repo_id="ACE-Step/Ace-Step1.5", local_dir=r"<ACE_KOK>\checkpoints", allow_patterns=[...])` call does it; the exact list and the sha256 fingerprints are in `docs/KURULUM_DEFTERI.md` section 3 [read for this exact snippet; the model files themselves were downloaded the same way on our machine]. Download only from the official repository: the engine loads model code from this folder.
5. **Tell Rakkase where ACE-Step is.** Copy `ayarlar.ornek.json` to `ayarlar.json` yourself (Rakkase does NOT create it: without the file every command stops with exit code 6, `RK-E-AYAR-YOK`; with the placeholder text still in `ace_kok` it stops with `RK-E-ACE-KOK`). Open `ayarlar.json` (it stays on your machine, git ignores it) and set `ace_kok` to your `<ACE_KOK>`. `kur.cmd` writes this file for you, so this step is only for the manual way. Leave `kilit` as `false` unless you have your own GPU lock module [read].
6. **Prove it.** `python rakkase.py test` generates a 15-second reference and compares it with `testler/referans/`: exit 0 means pass (correlation > 0.999 and SNR > 40 dB). About 2 minutes of model loading plus generation on our GTX 1050 Ti [measured, `docs/OLCUMLER.md`]. Then `python rakkase.py denetle --plan ornekler/sozsuz_fon_ninni.json` (CPU) and `python rakkase.py uret --plan ornekler/sozsuz_fon_ninni.json`.

Measured: one clean-folder install ran to HAZIR in 32 min 6 s (uv downloads 13 min 50 s, package install 3 min 34 s, models about 14 min) and the GPU test passed [measured: maintainers, models copied from a local copy]. Not verified: the HuggingFace download itself and a machine without git/uv [not yet verified]. If a step fails, open a Bug report: the exit code and the first 20 lines of output (with your folder names replaced by `<RAKKASE>` and `<ACE_KOK>`).

## Türkçe

**İki yol.** (A) kolay yol: `kur.cmd`'ye çift tıklayın. (B) elle (aşağıda), ileri düzey ya da betik durunca her adımı görmek isterseniz.

**A. `kur.cmd` (önerilen).** Depoyu boşluksuz kısa bir klasöre açın (ör. bir sürücünün en üstünde `rk` adlı klasör). `kur.cmd`'ye çift tıklayın; önce rapor görmek için terminalde `kur.cmd -Kuru`. Önce git, uv ve Python 3'ü kurun (`winget install --id Git.Git -e`, `winget install --id=astral-sh.uv -e`, `winget install --id Python.Python.3.12 -e`; sizin için kurulmaz; yeni terminalde `python` çalışmalı: Microsoft Store "python" takma adı Python değildir). 4 GB ya da üstü NVIDIA kart ve yaklaşık 25 GiB boş disk gerekir. git, uv, sürücü, disk ve VRAM'i denetler, ACE-Step 1.5'i denediğimiz commit'te kurar, model dosyalarını indirir (yaklaşık 6,4 GB, `huggingface.co/ACE-Step` ve `huggingface.co/Qwen`'den, sha256 denetimiyle) ve `ace_kok`'unuzla `ayarlar.json`'u yazar. Kesilirse yeniden çalıştırın: kaldığı yerden sürer. **ACE-Step klasörünüz zaten var mı?** `kur.cmd` bulur, yeniden kurmaz; bulamazsa klasörünüzü `ayarlar.json`'daki `ace_kok`'a elle yazın (B5). Hata `HATA: [RK-E-...]` basar: `docs/SIK_HATALAR.md`. İnternetten inen dosya için Windows uyarı verebilir: önce `scripts\kur.ps1`'i okuyun; yönetici olarak çalıştırmayın. Betiklerin durumu: [boş makinede uçtan uca henüz doğrulanmadı].

**B. Elle.**

Rakkase, ACE-Step 1.5'in üzerine ince bir katmandır: önce ACE-Step'i bir kez kurarsınız, sonra Rakkase'ye onun yerini gösterirsiniz. Aşağıda `<RAKKASE>` bu depo, `<ACE_KOK>` ACE-Step klasörünüzdür (adlarını siz seçersiniz).

1. **Makine.** Windows 10/11, 4 GB ya da üstü NVIDIA kart (yalnız GTX 1050 Ti 4 GB'da denendi [ölçtüm]), 16 GB RAM, güncel NVIDIA sürücüsü (`nvidia-smi` çalışmalı). Ayrı CUDA Toolkit gerekmez: torch paketi kendi CUDA'sını taşır [okudum].
2. **Araçlar.** Git, Python 3 (`rakkase.py` için herhangi 3.x [okudum]), [uv](https://docs.astral.sh/uv/) (biz 0.13.6 kullandık [ölçtüm]).
3. **ACE-Step 1.5, sabit commit** [ölçtüm]: yukarıdaki dört komut (`git clone`, `git checkout ca1e85f`, `uv python install 3.11`, `uv sync`).
4. **Model dosyaları** resmî `ACE-Step/Ace-Step1.5` deposundan `<ACE_KOK>\checkpoints\` altına (yaklaşık 6,4 GB [okudum: `scripts/modeller.json`]); klasör listesi ve sha256 parmak izleri `docs/KURULUM_DEFTERI.md` bölüm 3'te. Yalnız resmî depodan indirin: motor model kodunu bu klasörden yükler.
5. **Rakkase'ye yeri söyleyin.** `ayarlar.ornek.json`'u kendiniz `ayarlar.json` olarak kopyalayın (Rakkase onu KENDİLİĞİNDEN üretmez: dosya yoksa her komut 6 koduyla durur, `RK-E-AYAR-YOK`; `ace_kok`'ta yer tutucu metin kalmışsa `RK-E-ACE-KOK`). `ayarlar.json`'daki `ace_kok`'u kendi `<ACE_KOK>` yolunuza yazın (dosya makinenizde kalır, git görmez). `kur.cmd` bu dosyayı sizin için yazar; bu adım yalnız elle kurulum içindir. Kendi GPU kilit modülünüz yoksa `kilit` `false` kalsın.
6. **Kanıtlayın.** `python rakkase.py test`: 15 sn'lik referans üretir, `testler/referans/` ile kıyaslar; çıkış 0 = geçti. Ardından `python rakkase.py denetle --plan ornekler/sozsuz_fon_ninni.json` (CPU) ve `python rakkase.py uret --plan ornekler/sozsuz_fon_ninni.json`.

Ölçüldü: temiz klasörde tam kurulum 32 dk 6 sn’de (uv paket indirme 13 dk 50 sn, paket kurulumu 3 dk 34 sn, modeller yaklaşık 14 dk) HAZIR oldu, GPU testi geçti [ölçtüm: bakımcılar, modeller yerel kopyadan]. Doğrulanmadı: HuggingFace indirmesinin kendisi ve git/uv’siz makine [henüz doğrulanmadı]. Adım takılırsa Hata bildirimi açın: çıkış kodu ve çıktının ilk 20 satırı (klasör adlarınız `<RAKKASE>` ve `<ACE_KOK>` ile değişmiş olarak).
