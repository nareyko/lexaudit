# Changelog

All notable changes to this project are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-30

First public release.

### Added
- Vocabulary audit for 7 languages: English, German, Spanish, Polish, Russian, Swedish, Ukrainian.
- Ranked page queue (`queue.md`), CSV and JSON reports with a JSON Schema contract.
- Commands: `init`, `doctor`, `fetch-dicts`, `audit`, `explain`, `rank`, `expand-needle`, `label`, `eval`, `diff`, `ping`.
- Calque and false-friend rule packs for all 7 languages.
- `fetch-dicts`: downloads spelling dictionaries into the user cache, no admin rights needed.
- Built-in pure-Python spelling checker (`spylls`) used when the system `hunspell` program is absent.
- Standard Markdown support (`audit --path`).
- 42-page, 7-language benchmark (MAP 0.838, open-set recall 77.9%).
- Diagrams generated from code (`scripts/render_diagrams.py`).
- Quality gates: ruff, mypy strict, pytest with 80% branch coverage, Hypothesis fuzzing, golden regression, CRAP gate, mutation gate (80%).

### Limits
- Phrase-level calques built from valid words are not detected without the optional `label` step.
- About 22% of unseen invented words are missed in the benchmark.
