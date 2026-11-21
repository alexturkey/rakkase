# Install / Kurulum

English first, Türkçe below. Full story with every wall we hit: [`docs/KURULUM_DEFTERI.md`](docs/KURULUM_DEFTERI.md) (Turkish for now). Labels: [measured] we ran it on our machine, [read] taken from a document or code, not run in this exact form, [guess] not checked.

## English

Rakkase is a thin layer on top of ACE-Step 1.5. So you install ACE-Step once, then point Rakkase at it. Your folder names are yours: below `<RAKKASE>` is this repository and `<ACE_KOK>` is the ACE-Step folder.

1. **Machine.** Windows 10/11, NVIDIA GPU with 4 GB or more (tested only on a GTX 1050 Ti 4 GB [measured]), 16 GB RAM, a recent NVIDIA driver (`nvidia-smi` works). A separate CUDA Toolkit is not needed: the torch wheel carries its own CUDA [read].
2. **Tools.** Git, Python 3 (for `rakkase.py`, any 3.x [read]), and [uv](https://docs.astral.sh/uv/) (we used 0.13.6 [measured]).
3. **ACE-Step 1.5, pinned commit** [measured: this commit, `docs/KURULUM_DEFTERI.md` section 2]:
   ```
   git clone https://github.com/ace-step/ACE-Step-1.5 <ACE_KOK>
   cd <ACE_KOK>
   git checkout ca1e85f
   uv python install 3.11
   uv sync
   ```
   `uv sync` builds `<ACE_KOK>\.venv` with torch 2.7.1+cu128 from the lock file.
4. **Model files** from the official repository `ACE-Step/Ace-Step1.5` into `<ACE_KOK>\checkpoints\` (about 6.1 GB [read]): the folders `acestep-v15-turbo`, `vae`, `Qwen3-Embedding-0.6B`, and the config of `acestep-5Hz-lm-1.7B`. A `huggingface_hub.snapshot_download(repo_id="ACE-Step/Ace-Step1.5", local_dir=r"<ACE_KOK>\checkpoints", allow_patterns=[...])` call does it; the exact list and the sha256 fingerprints are in `docs/KURULUM_DEFTERI.md` section 3 [read for this exact snippet; the model files themselves were downloaded the same way on our machine]. Download only from the official repository: the engine loads model code from this folder.
5. **Tell Rakkase where ACE-Step is.** Run any command once (for example `python rakkase.py test`): it creates `ayarlar.json` from `ayarlar.ornek.json` and stops with exit code 6. Open `ayarlar.json` (it stays on your machine, git ignores it) and set `ace_kok` to your `<ACE_KOK>`. Leave `kilit` as `false` unless you have your own GPU lock module [read].
6. **Prove it.** `python rakkase.py test` generates a 15-second reference and compares it with `testler/referans/`: exit 0 means pass (correlation > 0.999 and SNR > 40 dB). About 2 minutes of model loading plus generation on our GTX 1050 Ti [measured, `docs/OLCUMLER.md`]. Then `python rakkase.py denetle --plan ornekler/sozsuz_fon_ninni.json` (CPU) and `python rakkase.py uret --plan ornekler/sozsuz_fon_ninni.json`.

Not verified: a complete install from an empty machine following only these six steps [not yet verified]. If a step fails, open a Bug report: the exit code and the first 20 lines of output (with your folder names replaced by `<RAKKASE>` and `<ACE_KOK>`).

## Türkçe

Rakkase, ACE-Step 1.5'in üzerine ince bir katmandır: önce ACE-Step'i bir kez kurarsınız, sonra Rakkase'ye onun yerini gösterirsiniz. Aşağıda `<RAKKASE>` bu depo, `<ACE_KOK>` ACE-Step klasörünüzdür (adlarını siz seçersiniz).

1. **Makine.** Windows 10/11, 4 GB ya da üstü NVIDIA kart (yalnız GTX 1050 Ti 4 GB'da denendi [ölçtüm]), 16 GB RAM, güncel NVIDIA sürücüsü (`nvidia-smi` çalışmalı). Ayrı CUDA Toolkit gerekmez: torch paketi kendi CUDA'sını taşır [okudum].
2. **Araçlar.** Git, Python 3 (`rakkase.py` için herhangi 3.x [okudum]), [uv](https://docs.astral.sh/uv/) (biz 0.13.6 kullandık [ölçtüm]).
3. **ACE-Step 1.5, sabit commit** [ölçtüm]: yukarıdaki dört komut (`git clone`, `git checkout ca1e85f`, `uv python install 3.11`, `uv sync`).
4. **Model dosyaları** resmî `ACE-Step/Ace-Step1.5` deposundan `<ACE_KOK>\checkpoints\` altına (yaklaşık 6,1 GB [okudum]); klasör listesi ve sha256 parmak izleri `docs/KURULUM_DEFTERI.md` bölüm 3'te. Yalnız resmî depodan indirin: motor model kodunu bu klasörden yükler.
5. **Rakkase'ye yeri söyleyin.** Herhangi bir komutu bir kez çalıştırın (ör. `python rakkase.py test`): `ayarlar.ornek.json`'dan `ayarlar.json` üretir ve 6 koduyla durur. `ayarlar.json`'daki `ace_kok`'u kendi `<ACE_KOK>` yolunuza yazın (dosya makinenizde kalır, git görmez). Kendi GPU kilit modülünüz yoksa `kilit` `false` kalsın.
6. **Kanıtlayın.** `python rakkase.py test`: 15 sn'lik referans üretir, `testler/referans/` ile kıyaslar; çıkış 0 = geçti. Ardından `python rakkase.py denetle --plan ornekler/sozsuz_fon_ninni.json` (CPU) ve `python rakkase.py uret --plan ornekler/sozsuz_fon_ninni.json`.

Doğrulanmadı: boş bir makinede yalnız bu altı adımla uçtan uca kurulum [henüz doğrulanmadı]. Adım takılırsa Hata bildirimi açın: çıkış kodu ve çıktının ilk 20 satırı (klasör adlarınız `<RAKKASE>` ve `<ACE_KOK>` ile değişmiş olarak).
