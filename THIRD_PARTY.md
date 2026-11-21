# Third-party components / Üçüncü taraf bileşenler

None of these is included in this repository; you download them yourself (see [KURULUM.md](KURULUM.md)). Details: [NOTICE](NOTICE).
Bunların hiçbiri bu depoda yok; kendiniz indirirsiniz (bkz. KURULUM.md). Ayrıntı: NOTICE.

| Component / Bileşen | Licence / Lisans | Source / Kaynak | In this repo? / Bu depoda mı? |
|---|---|---|---|
| ACE-Step 1.5 (code + turbo model weights) | MIT | https://github.com/ace-step/ACE-Step-1.5 · https://huggingface.co/ACE-Step/Ace-Step1.5 | No / Hayır |
| Qwen3-Embedding-0.6B (text encoder used by ACE-Step) | Apache-2.0 | https://huggingface.co/Qwen/Qwen3-Embedding-0.6B | No / Hayır |
| PyTorch, torchao, Transformers | their own licences / kendi lisansları | PyPI | No / Hayır |
| FFmpeg (optional, only for `rakkase.py mp3` / wav to mp3) | LGPL-2.1+ or GPL, depends on the build you install / kurduğunuz derlemeye göre | https://ffmpeg.org | No / Hayır (called from your PATH / PATH'inizden çağrılır) |

The only generated audio in this repository is the 15-second instrumental reference clip used by `python rakkase.py test` (made by this project with ACE-Step 1.5 turbo, seed 42; no voice cloning, no third-party recording).
Bu depodaki tek üretilmiş ses, `python rakkase.py test`in kullandığı 15 saniyelik sözsüz referans klibidir (bu proje ACE-Step 1.5 turbo ile üretti, tohum 42; ses klonu yok, üçüncü kişi kaydı yok).
