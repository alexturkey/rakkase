# Rakkase

English · [Türkçe](README.tr.md)

Translations follow this English README; if they differ, the English text is authoritative, especially the license text. The detailed documents in [`docs/`](docs/) are in Turkish for now.

> Local music generation with ACE-Step 1.5 (turbo) on a 4 GB graphics card: you write a plan file, Rakkase checks it, generates the track, and archives it together with its recipe.

Rakkase is a thin, careful wrapper around [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) that makes the turbo model fit and run on a GTX 1050 Ti (4 GB VRAM) with 16 GB RAM: int8 decoder, fp32 computation, language model off, streaming load. Quality is not traded for fit: 8 diffusion steps (the model's own value) and fp32 are fixed. It makes vocal tracks (Turkish included) and instrumentals, 10 to 600 seconds (comfortable up to about 300 seconds).

**What we measured, and where:** one machine only (GTX 1050 Ti 4 GB, 16 GB RAM, Windows 10, 2026-11-05) [measured by the authors, `docs/OLCUMLER.md`]: model load about 2 minutes once per process; a 15 s track about 35-48 s, a 100 s song about 63-75 s, a 150 s duet 121 s; about 6.4 GB RAM peak. The numbers were measured on 2026-11-05 with the earlier engine text and were not re-measured since [not re-measured]. Other cards and less than 4 GB were not tried; a faster card will most likely work but that is a guess [guess].

## Quick start (start here)

1. **What you need:** Windows 10/11 [measured: Windows 10], an NVIDIA GPU with 4 GB or more [tested only on GTX 1050 Ti], 16 GB RAM, free disk for about 6.1 GB of models [read: `docs/KURULUM_DEFTERI.md` section 3] plus the Python environment with torch (size not measured), Python for the front door, and [uv](https://docs.astral.sh/uv/) to build the ACE-Step environment.
2. **Install ACE-Step 1.5 once** (pinned commit, model download, settings file): see [`KURULUM.md`](KURULUM.md) (short) and [`docs/KURULUM_DEFTERI.md`](docs/KURULUM_DEFTERI.md) (full, with every wall we hit).
3. **Check a plan on the CPU** (no GPU, no model load; it does need the ACE-Step folder for the tokenizer):
   ```
   python rakkase.py denetle --plan ornekler/sozsuz_fon_ninni.json
   ```
4. **Generate:**
   ```
   python rakkase.py uret --plan ornekler/sozsuz_fon_ninni.json
   ```
   The track lands in `uretimler/<date_time>_<name>/` as wav + mp3 with lyrics and a recipe file.
5. **Prove your install:** `python rakkase.py test` generates a 15 s reference and compares it with the committed reference wav (pass: correlation > 0.999 and SNR > 40 dB; exit 0 = pass, 1 = fail). It needs the GPU.

Status: the install path is documented but a clean-machine install from this repository alone has not been run end to end [not yet verified]; if you get stuck, please open a bug report, it helps us fix the steps. No GPU or no ACE-Step yet? Then nothing runs for you in five minutes: read the documents, send plans or translation fixes (see `CONTRIBUTING.md`), and come back after step 2.

```
python rakkase.py denetle --plan P.json   # plan check, CPU, a few seconds, does not load the model
python rakkase.py uret    --plan P.json   # checks first, then generates and archives
python rakkase.py bol     --plan P.json   # splits a long plan into runs of about 300 s each
python rakkase.py test                    # compare against the reference after an engine change
python rakkase.py mp3     <folder>        # mp3 192k next to every wav
```

## Example plans

| File | What | Notes |
|---|---|---|
| `ornekler/sozsuz_fon_ninni.json` | 96 s instrumental lullaby (guitar, cello, clarinet) | no lyrics: the safest first try |
| `ornekler/rap_claude_code_40sn.json` | 40 s Turkish rap, original lyrics | one track, fast; "Claude" in the name is a product name used in the sample lyrics |
| `ornekler/sozlu_balad.json` | 100 s Turkish ballad, original lyrics | vocal, one track |
| `ornekler/cesit_6_tarz.json` | six styles (duet, choir, folk, rap, oriental, children) | about 10 minutes of audio: a later try |

A plan is JSON: `caption` (English style description, 256-token limit), `lyrics` with `[Verse]`/`[Chorus]` tags, `sure` (seconds), `bpm`, `ton`, `olcu`, `tohum` (same plan + same seed = same track). Every field is explained in [`docs/KULLANIM.md`](docs/KULLANIM.md), the limits in [`docs/SINIRLAR.md`](docs/SINIRLAR.md), recipes that worked in [`docs/TARIFLER.md`](docs/TARIFLER.md).

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
