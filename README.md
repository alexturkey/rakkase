# Rakkase

<p align="center"><img src="docs/gorsel/banner.jpg" alt="Rakkase" width="100%"></p>

English · [Türkçe](README.tr.md)

Translations follow this English README; if they differ, the English text is authoritative, especially the license text. The detailed documents in [`docs/`](docs/) are in Turkish for now.

> Local music generation with ACE-Step 1.5 (turbo) on a 4 GB graphics card: you write a plan file, Rakkase checks it, generates the track, and archives it together with its recipe.

Rakkase is a thin, careful wrapper around [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) that makes the turbo model fit and run on a GTX 1050 Ti (4 GB VRAM) with 16 GB RAM: int8 decoder, fp32 computation, language model off, streaming load. Quality is not traded for fit: 8 diffusion steps (the model's own value) and fp32 are fixed. It makes vocal tracks (Turkish included) and instrumentals, 10 to 600 seconds (comfortable up to about 300 seconds).

**What we measured, and where:** one machine only (GTX 1050 Ti 4 GB, 16 GB RAM, Windows 10, 2026-11-05) [measured by the authors, `docs/OLCUMLER.md`]: model load about 2 minutes once per process; a 15 s track about 35-48 s, a 100 s song about 63-75 s, a 150 s duet 121 s; about 6.4 GB RAM peak. The numbers were measured on 2026-11-05 with the earlier engine text and were not re-measured since [not re-measured]. Other cards and less than 4 GB were not tried; a faster card will most likely work but that is a guess [guess].

> **Using an AI coding agent (Codex, Claude Code, Gemini, Cursor)?** Give it this one sentence: "Read `AGENTS_HIZLI.md` to the end, run `scripts\tani.ps1` first, keep your progress in `DURUM.md`, and ask me before you delete or move anything, change system Python or PATH, or lower a quality setting." The agent will diagnose this PC, write a checklist and ask you at every decision.

**Installing with an AI coding agent (Claude Code, Codex, Gemini CLI, Copilot, Cursor...)? Start from [`AGENTS.md`](AGENTS.md)** (quick card: [`AGENTS_HIZLI.md`](AGENTS_HIZLI.md)). You install git, uv and Python once; the agent runs the rest after you say yes.

**Before you start:**
- Windows 10/11 and an **NVIDIA GPU with 4 GB or more** (tested only on a GTX 1050 Ti; no NVIDIA card, macOS or Linux: this does not run yet).
- About **25 GiB free disk** (models 6.4 GB; the whole install is about 23 GB).
- You install **git, uv and Python 3** yourself (`winget install --id Git.Git -e`, `winget install --id=astral-sh.uv -e`, `winget install --id Python.Python.3.12 -e`), then open a new terminal; the Microsoft Store "python" alias is not Python.

## Quick start (start here)

1. **Check your machine:** Windows 10/11 [measured: Windows 10], an NVIDIA GPU with 4 GB or more [tested only on a GTX 1050 Ti], 16 GB RAM, free disk for about 6.4 GB of models (22 files) [read: `scripts/modeller.json`] plus the Python environment with torch; the whole install may need about 23 GB of disk (the check asks for about 25 GiB free) [measured: one clean install used about 23 GB on a 1050 Ti machine, models copied from a local source, so the download time was not measured]. Install **git** and **uv** first (they are not installed for you): `winget install --id Git.Git -e` and `winget install --id=astral-sh.uv -e`, then open a new terminal. ffmpeg is optional (without it you get wav files but no mp3): `winget install --id Gyan.FFmpeg -e`.
2. **Download and extract** this repository (green **Code** button, **Download ZIP**) into a SHORT folder without spaces or non-English letters, for example a folder named `rk` at the top of a drive. Windows may show a SmartScreen warning for a file downloaded from the internet: read `scripts\kur.ps1` first (it is a plain text script), then decide. Do not run it as administrator (it is not needed).
3. **Double-click `kur.cmd`.** It checks git, uv, driver, disk and VRAM, installs [ACE-Step 1.5](https://github.com/ACE-Step/ACE-Step-1.5) at the tested commit, downloads the model files (about 6.4 GB, only from `huggingface.co/ACE-Step` and `huggingface.co/Qwen`, checked with sha256), and writes `ayarlar.json` for you. Time depends on your connection and disk [not measured]. A half-finished run continues where it stopped: just run it again. To see the plan first, run `kur.cmd -Kuru` in a terminal: it prints a report of what it would do and writes nothing, no file, no folder, no network [measured by the maintainers on a copy folder]. If you already have an ACE-Step folder, `kur.cmd` finds it and does not install it again.
4. **Double-click `uret.cmd`:** it generates the safest example (`ornekler/sozsuz_fon_ninni.json`, no lyrics); to make your own, drag a `plan.json` onto `uret.cmd`. The track lands in `uretimler/<date_time>_<name>/` as wav + mp3 with a recipe file. About 2 minutes of model loading plus 0.6-0.8 x the song length on our GTX 1050 Ti [measured by the authors, `docs/OLCUMLER.md`]; the default example (96 s) takes roughly 3 minutes [derived from those numbers, not run as is].
5. **Prove your install (GPU):** `python rakkase.py test` generates a 15 s reference and compares it with the committed reference wav (pass: correlation > 0.999 and SNR > 40 dB; exit 0 = pass, 1 = fail).

If something fails the script prints `HATA: [RK-E-...]`: look the code up in [`docs/SIK_HATALAR.md`](docs/SIK_HATALAR.md) (one first step per code). For a bug report run `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\tani.ps1 -Cikti tani_raporu.txt` (it masks your paths and user name; still read the file before you post it). Manual install without the scripts: [`KURULUM.md`](KURULUM.md).

Status: one complete install into a clean folder with a fresh uv environment ran to HAZIR in 32 min 6 s (uv downloads 13 min 50 s, package install 3 min 34 s, models about 14 min), then `rakkase.py test` passed on the GPU (SNR 44.1 dB, correlation 0.999988, 539 s, VRAM peak 2653 MB, RAM peak 7688 MB) [measured: maintainers, 2026-11-22, models copied from a local copy, so the HuggingFace download itself and a truly empty machine (no git/uv) are not yet verified]; if you get stuck, please open a bug report, it helps us fix the steps. No GPU or no ACE-Step yet? Then nothing runs for you in five minutes: read the documents, send plans or translation fixes (see `CONTRIBUTING.md`), and come back after step 3.

```
python rakkase.py denetle --plan P.json   # plan check, CPU, a few seconds, does not load the model
python rakkase.py uret    --plan P.json   # checks first, then generates and archives
python rakkase.py bol     --plan P.json   # splits a long plan into runs of about 300 s each
python rakkase.py test                    # compare against the reference after an engine change
python rakkase.py mp3     <folder>        # mp3 192k next to every wav
```

## Disk layout and removal
Everything Rakkase installs lives in one root folder, `<ACE_KOK>` (default `<repo>\ace_step`; change it with `kur.cmd -AceKok <folder>`, for example to a roomier drive). Nothing is written to the system PATH, the user profile or the registry. `ayarlar.json` (your settings) stays next to `rakkase.py`.

| Folder under `<ACE_KOK>` | What is in it | Size |
|---|---|---|
| `checkpoints` | model files (22 files from `huggingface.co/ACE-Step` and `/Qwen`, sha256-checked) | about 6.4 GB [read: `scripts/modeller.json`] |
| `.venv` | the Python environment (uv, torch 2.7.1+cu128) | most of the rest of the about 23 GB [measured: one clean install, total] |
| `.onbellek\uv` | uv download cache | part of the same total [not measured separately] |
| `.onbellek\uv-python`, `.onbellek\uv-bin` | uv's own Python 3.11 and its launcher shortcuts; created only if no suitable Python 3.11 was found | part of the same total [not measured separately] |
| `gecici` | temporary files of the install | small [not measured] |

For the install script's own process only, `UV_CACHE_DIR`, `TMP` and `TEMP` point into this root (and `UV_PYTHON_INSTALL_DIR` and `UV_PYTHON_BIN_DIR` too when uv has to install its own Python; if a `.venv` already exists nothing is changed; a value you set yourself for any of the `UV_` variables is left alone and used; `TMP` and `TEMP` always go to the root), so uv does not fill the user profile or the system drive. Hugging Face and torch caches are not used (Rakkase has its own pinned downloader).

**Already downloaded the model?** Give the folder to `kur.cmd` with `-AceKok`; a complete file with the right sha256 is skipped, not downloaded again. An interrupted download continues from its `.part` file.

**Removal:** close Rakkase, then delete the Rakkase folder and the `<ACE_KOK>` folder (by default these are the same folder, because `<ACE_KOK>` is inside the repository folder). That is the whole uninstall. Not ours to remove: pip or uv caches that existed before the install, and git, uv or Python installed with `winget` (use `pip cache purge`, `uv cache clean` or Windows "Apps" yourself). Your tracks are in `uretimler/`: copy them out before deleting.

## Example plans

| File | What | Notes |
|---|---|---|
| `ornekler/sozsuz_fon_ninni.json` | 96 s instrumental lullaby (guitar, cello, clarinet) | no lyrics: the safest first try |
| `ornekler/rap_claude_code_40sn.json` | 40 s Turkish rap, original lyrics | one track, fast; "Claude" in the name is a product name used in the sample lyrics |
| `ornekler/sozlu_balad.json` | 100 s Turkish ballad, original lyrics | vocal, one track |
| `ornekler/cesit_6_tarz.json` | six styles (duet, choir, folk, rap, oriental, children) | about 10 minutes of audio: a later try |

A plan is JSON: `caption` (English style description, 256-token limit), `lyrics` with `[Verse]`/`[Chorus]` tags, `sure` (seconds), `bpm`, `ton`, `olcu`, `tohum` (same plan + same seed = same track). Every field is explained in [`docs/KULLANIM.md`](docs/KULLANIM.md), the limits in [`docs/SINIRLAR.md`](docs/SINIRLAR.md), recipes that worked in [`docs/TARIFLER.md`](docs/TARIFLER.md).

## Seeds (try three)
A seed (`tohum` in the plan) is the starting number of the randomness. The same plan with the same seed gives the same track; the same recipe with a different seed gives a different performance of it, so one idea can become several songs. Nearby numbers (41 and 42) do not give similar results: pick numbers far apart. Try three seeds with `ornekler/tohum_denemesi.json`, listen and keep the one you like. Every seed takes the full generation time (about 0.6-0.8 x the track length) and the seed is a creative choice, not a quality setting. Details: [`docs/KULLANIM.md`](docs/KULLANIM.md) ("Tohum denemesi"). AI agents are told to explain this to you before the first track.

## A panel video you can share
X, Instagram and WhatsApp do not accept a plain audio file. So after every `uret`, Rakkase also makes `<name>_panel.mp4` next to the track: a 1080x1080 video of an old-radio style LED spectrum that moves with the music, with the lossless-source audio inside (AAC 320k). On a 100 s track it took 49 s and 8.5 MB on the CPU [measured by the maintainers, one run; not on other machines]. The panel shows the real spectrum of the track; it does not change the music. It needs ffmpeg (the same one the mp3 uses; numpy, soundfile and Pillow are already in the ACE-Step environment). Without ffmpeg the track and the mp3 are still made and the panel is skipped with a warning; if the panel fails during `uret` you only get a warning and the exit code does not change. Turn it off with `--panel-yok`, make it later with `python rakkase.py panel <wav or folder>`. More: [`docs/KULLANIM.md`](docs/KULLANIM.md) ("Paylaşmaya hazır panel"). The same copyright note applies to what you share: no artist names, no other people's lyrics.

[![Rakkase LED panel frame: click to play the 20 second example](docs/gorsel/ornek_panel.png)](docs/gorsel/ornek_panel.mp4)

Click the picture to play a 20 second example (a Turkish folk-style excerpt made with Rakkase itself; sung by the model, no voice cloning).

## When something goes wrong
Start with [`docs/SORUN_GIDERME.md`](docs/SORUN_GIDERME.md) (what you see, what to do) and [`docs/HATALAR.md`](docs/HATALAR.md) (15 common mistakes, 7 common wrong beliefs). `rakkase.py uret` exit codes: 0 done, 2 plan check error or engine did not start, 3 a track failed, 4 RAM guard stopped it, 5 done but archive failed, 6 `ayarlar.json` missing or wrong.

## Folders

| Where | What |
|---|---|
| `rakkase.py` | the single front door (uret, denetle, bol, test, mp3) |
| `motor/` | generation engine (ACE-Step wrappers, measurement) and venv launcher |
| `araclar/` | plan check, recipe archive, wav comparison, loudness, memory monitor |
| `ornekler/` | example plans (each is described in `docs/TARIFLER.md`) |
| `testler/` | comparison plan, reference wav (our own ACE-Step output), CPU test |
| `docs/` | documents (Turkish for now) |
| `ayarlar.json` | your local paths (not in git; copy of `ayarlar.ornek.json`) |

## Contributing, support, security
[`CONTRIBUTING.md`](CONTRIBUTING.md) (first pull request in 5 steps), [`AGENTS.md`](AGENTS.md) (for AI coding agents), [`SUPPORT.md`](SUPPORT.md) (goals, not guarantees), [`SECURITY.md`](SECURITY.md) (report vulnerabilities privately through GitHub's "Report a vulnerability"; do not open public issues), [`PRIVACY.md`](PRIVACY.md) (no telemetry), [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## License and attribution

- Rakkase code and documents: MIT, see [`LICENSE`](LICENSE). Third-party notices: [`NOTICE`](NOTICE).
- ACE-Step 1.5 code: MIT (https://github.com/ace-step/ACE-Step-1.5). Model weights: MIT; the model card says the generated music can be used commercially (https://huggingface.co/ACE-Step/Ace-Step1.5; this is the developers' statement, not an independent guarantee).
- Text encoder Qwen3-Embedding-0.6B: Apache-2.0 (https://huggingface.co/Qwen/Qwen3-Embedding-0.6B).
- No weights are in this repository; they are downloaded from the official source during install. For generated music, similarity to existing styles and the use of protected material are your responsibility (as in the ACE-Step README): do not use artist names or other people's lyrics in plans. Details: `docs/HATALAR.md` (wrong belief Y7: music rights).
