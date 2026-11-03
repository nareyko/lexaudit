# Draft: lexaudit 0.4.0 — honest metrics, real corpora, contextual calques

> Local draft only. Do not publish until the owner runs push / PyPI / GitHub Release.

## One-line

lexaudit 0.4 turns the synthetic story into measured tables, adds a license-clean real benchmark with annotator κ, contextual false-friend rules across seven languages, a neologism detector that finally ranks inventeds above jargon, and SARIF / baseline / RST / i18n plumbing for CI.

## Numbers (recomputed, not hand-waved)

Synthetic 42-page ablation C (see `eval/synthetic-benchmark-metrics.json`):

| Metric | 0.3 era narrative | 0.4.0 |
|---|---|---|
| Precision@3 | ~66.7% (jargon beat hapax) | **100%** |
| Known-rule recall | 26/26 | **26/26** |
| Unseen neologism recall | 0/7 | **7/7** |
| Combined word recall | ~78.8% (26/33) | **33/33** |

Real-bench (V2): stratified clean pages ×7 locales; Cohen **κ ≈ 0.85** on dual annotation.

Competitor smoke (this machine): lexaudit leads page P@3 and clean FPR; cspell recalls more OOV with heavy clean-page noise; Vale / LanguageTool skipped when absent (`docs/competitor-benchmark.md`).

## What changed for users

- `lexaudit audit --baseline` / `--write-baseline` to suppress known exceptions under `--check`
- SARIF `ruleId` like `calque.uk.ru-origin` with `startColumn` / `endColumn`
- `--glossary` CSV/YAML and `.rst` / nested i18n JSON-YAML sources
- Richer `rules/calques/*.yaml` with `positive_examples` / `negative_examples` contract tests

## License reminder

The **PyPI wheel is MIT**. The AGPL file remains policy text for a future hosted multi-tenant service that is not in this package. Corpora: `LICENSE-THIRD-PARTY.md`.

## Owner publish checklist (manual)

```bash
cd tools/lexaudit
git push origin main
gh release create v0.4.0 -F CHANGELOG.md   # after tag
# PyPI: Trusted Publisher workflow on tag, or twine — only when owner confirms
# VS Marketplace / Open VSX: separate extension bump if desired
```
