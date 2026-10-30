# P1 lab: domain rule packs (not for yachting)

Status: **10** packs densified and promoted to `packs/` as **release-candidate**
for 0.3.0 (local; not on PyPI yet). See `docs/p1-0.3.0-prep.md` and
`docs/p1-owner-publish-runbook-2026-10-30.md`.

## Goal

Industry calque / false-friend packs installable later via `lexaudit pack install …`,
without shipping marine / yacht content.

## Inventory (10)

| Pack | Why | Cited public seeds |
|---|---|---|
| `saas-ui-v0` | AI/MT UI strings | [Zulip RU](https://zulip.readthedocs.io/en/stable/translating/russian.html), [Hermes](https://github.com/NousResearch/hermes-agent/pull/41677), [localize-ru](https://www.skills.sh/i18n-agent/i18nstack/localize-ru) |
| `fintech-v0` | Payment / ledger | [Native Localization](https://www.nativelocalization.com/industries/fintech-localization/), [Translated Right](https://www.translatedright.com/blog/fintech-app-translation-security-terminology-pitfalls-to-avoid/) |
| `developer-docs-v0` | API prose | [FastAPI](https://github.com/fastapi/fastapi/pull/15920), [API7](https://api7.ai/learning-center/api-101/translating-api-documentation-for-global-audiences) |
| `ecommerce-ui-v0` | Checkout / cart | densified · RC in 0.3.0 |
| `healthcare-ui-v0` | Patient UI | densified · RC in 0.3.0 |
| `legal-docs-v0` | Contract prose | densified · RC in 0.3.0 |
| `gaming-ui-v0` | Game HUD / loot | [Allcorrect guide](https://allcorrectgames.com/wp-content/uploads/2023/10/Localization_guide_2_allcorrect.pdf), [GameDeveloper](https://www.gamedeveloper.com/business/localising-your-game-how-to-make-it-not-suck), [IGDA](https://igda.org/news-archive/high-quality-localization-help-loc-help-you/), [Loc'd](https://locdandloaded.net/2021/05/31/style-guide/) |
| `edtech-v0` | LMS / SCORM | [SCORMBuilder](https://scormbuilder.ai/blog/translate-scorm-course/), [Translated](https://translated.com/resources/e-learning-translation-interactivity-localization-guide), [Anan](https://anantranslations.com/scorm-xapi-translation-guide/), [Vozo](https://www.vozo.ai/blogs/e-learning-translation/elearning-courseware-translation-guide) |
| `security-docs-v0` | Pen-test / security | [Smartling](https://www.smartling.com/questions/security-terminology-translation-consistency), [CIOL](https://www.ciol.org.uk/net-security), [UA terms paper](https://doi.org/10.30525/978-9934-26-548-8-26) |
| `hr-ats-v0` | ATS / recruiting | [CVUniform](https://www.cvuniform.com/blog/risks-of-automatically-translating-candidate-experience?lang=en), [iSmartRecruit](https://www.ismartrecruit.com/blogs/multilingual-recruitment-best-practices), [TreeGarden](https://treegarden.io/blog/multilingual-ats-software/) |

## Method used

1. Mine public style guides and i18n reviews for recurring wrong tokens.
2. Cap ~20–40 rules on `en`; `de`/`ru` ≥12 (often ≥24); `es`/`pl`/`sv`/`uk` ≥12.
3. Mini fixtures: `01-clean*`, `04-defect-known`, `06-defect-open`.
4. Measure with `scripts/lab_pack_metrics.py` / `run_lab_pack_metrics.py`.

## Why these four new themes

| Theme | Gap vs existing six |
|---|---|
| Gaming | Distinct UI nouns (loot, matchmake, respawn) not covered by SaaS |
| EdTech | LMS/SCORM/xAPI tracking copy — high MT breakage, not API docs |
| Security | Ordinary English as terms of art (`exploit`, `sandbox`) — opposite of fintech |
| HR/ATS | Candidate-facing + pipeline verbs — compliance-adjacent, not legal contracts |

Rejected for now (overlap or yacht-adjacent): travel/hospitality (thin demand signal),
gov/civic (overlaps legal), media-streaming (overlaps SaaS), marine/yacht (**never**).

## Local metrics

```bash
uv run python scripts/run_lab_pack_metrics.py
# 2026-10-30: 10 packs × en/de/es/pl/ru/sv/uk → failed=0
```

0.3.0 promote checklist: `docs/p1-0.3.0-prep.md`.

## Hard rules

- No yacht / marine / survey-boat pack in the public repo (hard rule).
- MIT license for packs.
- Keep under `packs/_lab/` until owner go for promote.
