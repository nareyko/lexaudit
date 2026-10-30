# Changelog

All notable changes to this project are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-10-30

### Added
- `audit --check` / `--fail-on` CI exit codes, `--format sarif|json`, GitHub annotations, HTML + findings.json reports with text excerpts
- GitHub Action (`action.yml`), pre-commit hook, `workflow_dispatch` on CI
- Corpus formats: HTML, gettext `.po`, XLIFF, MkDocs, Docusaurus, VitePress trees
- `lexaudit pack list|install|verify` and `packs/core-calques-v1` artifact
- Lazy dictionary download; Python 3.10+; MIT license (hosted AGPL note in docs/licensing.md)
- Docs: backend hunspell vs spylls metrics; P1 lab notes (MCP, bilingual, domain packs)

### Changed
- Docs language: texts/passages as the primary unit; ranking tables say "texts"

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
