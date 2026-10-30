# P1 lab: domain rule packs (not for yachting)

Status: lab packs seeded and measured locally. **Not** attached to the 0.2.0 release.

## Goal

Industry calque / false-friend packs installable later via `lexaudit pack install …`,
without shipping FairHelm marine content.

## Top-3 after corpus hunt

| Pack | Why | Cited public seeds |
|---|---|---|
| `saas-ui-v0` | AI/MT UI strings | [Zulip RU guide](https://zulip.readthedocs.io/en/stable/translating/russian.html), [Hermes RU review](https://github.com/NousResearch/hermes-agent/pull/41677), [localize-ru](https://www.skills.sh/i18n-agent/i18nstack/localize-ru) |
| `fintech-v0` | Payment / ledger terms | [Native Localization fintech](https://www.nativelocalization.com/industries/fintech-localization/), [Translated Right](https://www.translatedright.com/blog/fintech-app-translation-security-terminology-pitfalls-to-avoid/), [GB Translation](https://www.gb-translation.com/es/traduccion-fintech/) |
| `developer-docs-v0` | API prose coinages | [FastAPI RU prompt audit](https://github.com/fastapi/fastapi/pull/15920), [API7 translation notes](https://api7.ai/learning-center/api-101/translating-api-documentation-for-global-audiences) |

E-commerce / healthcare / legal thin packs are seeded under `packs/_lab/`
(`ecommerce-ui-v0`, `healthcare-ui-v0`, `legal-docs-v0`).

## Method used

1. Mine public style guides and i18n reviews for recurring wrong tokens.
2. Cap ~20–40 rules on `en` (and dense `de`/`ru` where useful); thin stubs elsewhere.
3. Mini fixtures: `01-clean*`, `04-defect-known`, `06-defect-open`.
4. Measure with `scripts/lab_pack_metrics.py`.

## Local metrics (2026-10-30 · expanded)

| Pack | locale | calque_words | defect score | clean max | lab_rank_ok |
|---|---|---:|---:|---:|---|
| saas-ui-v0 | en | 8 | 64.0 | 0.0 | yes |
| saas-ui-v0 | ru | 8 | 64.1 | 0.0 | yes |
| saas-ui-v0 | de | 7 | 56.1 | 0.0 | yes |
| fintech-v0 | en | 7 | 56.0 | 0.0 | yes |
| fintech-v0 | ru | 4 | 32.0 | 0.0 | yes |
| fintech-v0 | de | 4 | 32.1 | 0.0 | yes |
| developer-docs-v0 | en | 8 | 64.0 | 0.0 | yes |
| developer-docs-v0 | ru | 3 | 24.0 | 2.1 | yes |
| developer-docs-v0 | de | 4 | 32.2 | 0.2 | yes |
| ecommerce-ui-v0 | en | 6 | 48.0 | 0.0 | yes |
| ecommerce-ui-v0 | ru | 3 | 24.0 | 0.0 | yes |
| ecommerce-ui-v0 | de | 3 | 24.0 | 0.0 | yes |
| healthcare-ui-v0 | en/ru/de | see `run_lab_pack_metrics.py` | — | — | yes |
| legal-docs-v0 | en/ru/de | see `run_lab_pack_metrics.py` | — | — | yes |

Verdict: **iterate** (still fixture-backed; attach to Release only after owner go).
Lab rank + known-rule recall ≥ 0.85 bars apply via `scripts/lab_pack_metrics.py`.
0.3.0 promote checklist: `docs/p1-0.3.0-prep.md`.

## Hard rules

- No yacht / marine / survey-boat pack in the public repo.
- MIT license for packs.
- Keep under `packs/_lab/` until owner go for 0.3.0.
