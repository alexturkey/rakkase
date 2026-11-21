# Roadmap

Not promises: ideas that came up, in no fixed order. Anything that lowers the quality settings (turbo 8 steps, int8 decoder only, fp32 compute, language model off) is out of scope.

- Release v0.1.0 once the report-only CI has run clean on real pull requests.
- Lyric video (karaoke) recipe: nine-by-sixteen video from a generated song and its word timings (`<name>.kelimeler.json`). A private working version exists; it is not published yet because it depends on tools outside this repository.
- Translate `docs/` (Turkish now) to English, starting with `docs/KULLANIM.md` and `docs/HATALAR.md`.
- Tests on other GPUs and with other driver versions (see `CONTRIBUTING.md`, hardware test form).
- A plan check that runs without the ACE-Step tokenizer (rough token estimate), so a first-time visitor can try `denetle` before installing.
