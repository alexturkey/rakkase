# Changelog

## Unreleased

- Agent onboarding (kit KL-23): a do-this-first block at the top of `AGENTS_HIZLI.md` and `AGENTS.md` (run `scripts\tani.ps1` first, git-ignored `DURUM.md` notebook, NEVER / ASK lists, same error twice stop), a one-sentence "give this to your agent" block in `README.md` and `README.tr.md`, and a read-only DEVIATIONS section in `scripts\tani.ps1`. Quality and run behaviour unchanged.
- Share-ready panel video: after every `uret`, `<name>_panel.mp4` (1080x1080 LED spectrum with the track's audio) is made next to the track, because X, Instagram and WhatsApp do not accept audio files. One run on a 100 s track: 49 s, 8.5 MB, CPU [measured by the maintainers]. Docs: README, `docs/KULLANIM.md`, `AGENTS_HIZLI.md`.
- Seed trial: rule for AI agents to explain the seed before the first track and offer 3 seeds, `ornekler/tohum_denemesi.json`, README and `docs/KULLANIM.md` sections.

First public release preparation (no release yet).

- Public repository created from a clean history; the earlier private development history is not carried over.
- LICENSE (MIT) and NOTICE (ACE-Step 1.5 MIT, Qwen3-Embedding-0.6B Apache-2.0; nothing of them is distributed here).
- English `README.md` with `README.tr.md`, `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, `PRIVACY.md`, issue forms and PR template, CI in report-only mode for the first two weeks.
- The default producer name in the recipe archive is now `rakkase` (was an internal label).
- Quality settings unchanged: turbo 8 steps, int8 decoder only, fp32 compute, language model off.
- Example plans in `ornekler/` were neutralized for publication: a slang word and a personal first name in the lyrics were replaced with neutral words and the `not` fields lost internal notes. The measurements in `docs/OLCUMLER.md` and `docs/TARIFLER.md` were taken with the earlier wording [not re-measured].
