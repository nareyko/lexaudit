# Changelog

All notable changes to this project are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Pack field held-out corpus + metrics (`tests/fixtures/packs_field/`,
  `scripts/run_pack_field_metrics.py`, report + recall chart)
- Pack wild Wikipedia corpus + fetch/metrics scripts (`packs_wild/`,
  `fetch_wiki_pack_samples.py`, `run_pack_wild_metrics.py`)
- Field `02-clean-domain.md` fixtures (10 packs × en/de/ru)
- Bilingual `DEFAULT_TEMPLATE_CHROME` stop, identical-segment leftovers,
  length-ratio soft signal, URL/email/code strip, `bilingual_chrome_path`
- Crosslocale `ref_present` mode (default) + slug path pairing helpers
- Crosslocale A/B dogfood script + verdict report
- CX research notes + harvest script; trimmed `cx_samples/` fixtures
- Phrase calque seeds (en/de/ru); hapax wild sanity + MCP tool smoke
- VS Code `icon.png` (128×128); Cyrillic→Latin onboarding fixture
- Soft cognate demote; FP-budget + clean/wild sanity + pack density scripts
- Crosslocale `ref_ok` mode (boost when Hunspell-ok in reference locale)
- Repo hygiene check + owner publish runbook; CI density/bilingual/hygiene gates
- PyPI Trusted Publishing workflow stub (`workflow_dispatch` only)
- `docs/p1-INDEX.md` navigation for prep docs
- Bilingual `pair_paths` slug fallback (locale folder ignored; no self-pairs)

### Changed
- Package `__version__` / GitHub Action pin aligned to **0.3.0** (was stale 0.2.0)
- Docs: CLI ping/packs/`--check`; architecture crosslocale + CI gate wording
- Length-ratio leftover uses synthetic `length-ratio` token (no source-word FP)
- Pack density floors cover es/pl/sv/uk (≥12) as well as en/de/ru
- LocalAI live smoke quarantined behind `LEXAUDIT_LOCALAI_SMOKE=1`
- `.gitignore`: dumps / CX / tmp metrics / packaging artifacts stay local
- `packs/_lab/` deduped to thin `pack.yaml` stubs; calques/fixtures SSOT in `packs/<id>/`
  (~1.4 MiB twin trees removed; hygiene fails if `_lab/*/calques` reappears)
- `pack list --lab` lists stubs only (no duplicate RC+lab rows for the same id)
- Docs diagrams: SVG SSOT; raster `docs/images/*.jpg` gitignored (~1.1 MiB off tree)
- `run_lab_pack_metrics.py` resolves fixtures via `pack_content_dir` (thin `_lab` stubs)
- Mutation gate: score only `setup.cfg` `paths_to_mutate` (drop pipeline/metrics noise);
  disable `annassign`; stronger aggregate/classify/diff/template tests (kill ≥80%)

## [0.3.0] - 2026-10-30

### Added
- Ten domain rule packs promoted to `packs/` as release-candidates:
  `saas-ui-v0`, `fintech-v0`, `developer-docs-v0`, `ecommerce-ui-v0`,
  `healthcare-ui-v0`, `legal-docs-v0`, `gaming-ui-v0`, `edtech-v0`,
  `security-docs-v0`, `hr-ats-v0` (bundled in the wheel)
- Wire `enable_crosslocale` (reference-locale norm no-pair boost; default false)
  + `examples/lexaudit.config.crosslocale.yaml`
- Phrase calque match + body pass; seed rules in `rules/calques/{en,de,ru}.yaml`
- Academy bilingual pairs (`source: academy` → bodyMarkdown materialize by slug)
- VS Code extension packaging (`packages/vscode-lexaudit` 0.3.0, `.vsix` via
  `npm run package`) and MCP registry metadata (`packages/mcp-lexaudit/server.json`)
- Lab → release promote path: `scripts/promote_lab_pack.py --apply`
- Bilingual held-out / live corpora, DE UI loan extras recipe (opt-in only)

### Changed
- Densified all ten domain packs (en ≥24; de/ru ≥20; es/pl/sv/uk ≥12)
- Open-set hapax ranking: long coinage / morphology miss get likely floor weight
- `english_leak` locales expanded to `{de, es, pl, sv}`
- Docs: dual-license wording (MIT package · AGPL-3.0-or-later for hosted SaaS)

### Notes
- Package defaults stay `enable_bilingual: false` and `enable_crosslocale: false`
- Yacht / marine packs remain out of the public package
- No auto-rewrite
- Marketplace / MCP registry / PyPI upload require a separate publish go after
  local gates are green

## [0.2.0] - 2026-10-30

### Added
- `audit --check` / `--fail-on` CI exit codes, `--format sarif|json`, GitHub annotations, HTML + findings.json reports with text excerpts
- GitHub Action (`action.yml`), pre-commit hook, `workflow_dispatch` on CI
- Corpus formats: HTML, gettext `.po`, XLIFF, MkDocs, Docusaurus, VitePress trees
- `lexaudit pack list|install|verify` and `packs/core-calques-v1` artifact
- Lazy dictionary download; Python 3.10+; dual license (MIT package · AGPL for hosted SaaS — docs/licensing.md)
- Synthetic seven-locale benchmark + ablation harness

### Changed
- Ranker weights and needle recall reporting for CI summaries

## [0.1.0] - 2026-10-30

### Added
- Initial public CLI: hunspell / morph / compound / foreign / calque detectors
- Weighted page ranking, explain, expand-needle, fetch-dicts
- Core English/German/Russian calque rules
