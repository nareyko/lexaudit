# Changelog

All notable changes to this project are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- (empty — next after 0.3.0)

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
