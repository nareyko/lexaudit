# Changelog

All notable changes to this project are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- Docs: dual-license wording (MIT package · AGPL-3.0-or-later for hosted SaaS) in
  README, CONTRIBUTING, `docs/licensing.md`, architecture, docs index
- Densified lab packs `ecommerce-ui-v0`, `healthcare-ui-v0`, `legal-docs-v0`,
  `gaming-ui-v0`, `edtech-v0`, `security-docs-v0`, `hr-ats-v0` (en ≥24 domain
  rules; de/ru ≥20; es/pl/sv/uk ≥12) with UK `override_ok` for Latin leftovers
- Open-set hapax ranking: long coinage / morphology miss get likely floor weight
- `english_leak` locales expanded to `{de, es, pl, sv}`

### Added (P1 lab only — not on PyPI yet)
- Wire `enable_crosslocale` (reference-locale norm no-pair boost; default false)
- Phrase calque match + body pass; seed rules in `rules/calques/{en,de,ru}.yaml`
- Academy bilingual pairs (`source: academy` → bodyMarkdown materialize by slug)
- FairHelm root `lexaudit.config.bilingual.yaml` + `scripts/fairhelm_bilingual_dogfood.sh`
  (package / main config stay `enable_bilingual: false`)

- Lab domain packs `saas-ui-v0`, `fintech-v0`, `developer-docs-v0` under `packs/_lab/` + `scripts/lab_pack_metrics.py`
- Bilingual held-out protocol, gold CSV, allowlist, `scripts/bilingual_metrics.py`
- VS Code shell-out extension stub + MCP/VS Code dogfood doc
- Real-public bilingual corpus (FastAPI + Kubernetes excerpts + seeded overlay),
  `scripts/build_real_public_corpus.py`, extra-loans file for official pages
- Expanded lab pack rules + RU/DE fixtures; kebab-slug skip in bilingual detector
- Community imperfect bilingual corpus (Excalidraw / Ever-teams / Zulip / Homebox
  reconstructions) + English function-word stop list
- Thin lab pack `ecommerce-ui-v0`
- Live Weblate leftover sample + DE loan policy doc; metrics
  `--extra-loans-locales` / `--extra-loans-basenames`
- `scripts/fetch_weblate_leftover_sample.py` (optional refresh)
- Crowdin-via-GitHub leftover sample (Jellyfin + Immich); owner-review checklist
- Example opt-in config `examples/lexaudit.config.bilingual.yaml`
- Lab packs `healthcare-ui-v0`, `legal-docs-v0`; known-rule recall in
  `lab_pack_metrics.py`; `run_lab_pack_metrics.py`; `docs/p1-0.3.0-prep.md`
- `lexaudit pack list|install --lab`; `scripts/promote_lab_pack.py` dry-run
- `scripts/fairhelm_soft_dogfood.sh` host soft audit helper

## [0.2.0] - 2026-10-30

### Added
- `audit --check` / `--fail-on` CI exit codes, `--format sarif|json`, GitHub annotations, HTML + findings.json reports with text excerpts
- GitHub Action (`action.yml`), pre-commit hook, `workflow_dispatch` on CI
- Corpus formats: HTML, gettext `.po`, XLIFF, MkDocs, Docusaurus, VitePress trees
- `lexaudit pack list|install|verify` and `packs/core-calques-v1` artifact
- Lazy dictionary download; Python 3.10+; dual license (MIT package · AGPL for hosted SaaS — docs/licensing.md)
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
