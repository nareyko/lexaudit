# Field eval · bilingual FP · crosslocale dogfood (2026-10-30)

Local research track before Marketplace/PyPI noise. Detection only.

## Goals

1. Pack field proof — held-out corpus not equal to pack `04-defect-known`;
   measure recall on seeded public-style defects + false-positive rate on clean pages.

2. Bilingual FP hygiene — skip template chrome / nav crumbs / brand shells that
   inflate leftover counts without being untranslated prose.

3. Crosslocale A/B — same corpus with `enable_crosslocale` off vs on; verdict
   keep-off-default + when to opt in.

4. Reports + graphs — committed markdown + SVG under `docs/images/`.

5. Public tree hygiene — tighten `.gitignore` for build artifacts.

## Out of scope

- PyPI / Marketplace / push
- Bilingual package default-on
- Auto-rewrite / yacht packs
- Embedding network calls

## Method (packs)

| Stratum | Path pattern | Expectation |
|---|---|---|
| Clean | `tests/fixtures/packs_field/<pack>/{en,de,ru}/01-clean.md` | defect score ≤ clean; no pack calque hits preferred |
| Seeded defect | `…/04-defect-seeded.md` | ≥5 pack patterns planted; known-rule recall ≥ 0.7 |
| Gold | `tests/fixtures/packs_field/gold.csv` | pack,locale,path,label,token |

Sources are **reconstructed** public-style UI/docs prose (not verbatim copyrighted
pages). See `tests/fixtures/packs_field/SOURCES.md`.

## Method (bilingual)

Add `DEFAULT_TEMPLATE_CHROME` stop (nav/template Latin shells). Keep kebab skip.
Regression: held-out leftover recall must not collapse; chrome FP on synthetic
nav page must drop.

## Method (crosslocale)

Script audits field EN+RU trees twice; compares suspect tiers / page scores.
Verdict recorded in `docs/p1-crosslocale-dogfood-2026-10-30.md`.

## Success bar

| Gate | Bar |
|---|---|
| Pack field | mean seeded recall ≥ 0.70; clean calque hits = 0 macro |
| Bilingual chrome | synthetic chrome leftovers ≤ 1 after fix |
| Crosslocale | written verdict; default stays false |
| Gates | ruff / mypy / pytest / lab metrics green |
