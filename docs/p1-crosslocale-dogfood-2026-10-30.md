# Crosslocale dogfood · 2026-10-30

Corpus: `tests/fixtures/packs_field/` (EN+RU trees for five packs),
audit locale `ru`, reference locale `en`.
Package default stays `enable_crosslocale: false`.

![Crosslocale A/B](images/crosslocale-ab.svg)

## Results

| Mode | words | pages | suspect | foreign | likely | xl hits |
|---|---:|---:|---:|---:|---:|---:|
| off | 134 | 17 | 23 | 78 | 61 | 0 |
| on | 134 | 17 | 23 | 78 | 84 | 23 |

Delta suspect: +0. Delta foreign: +0. Delta likely: +23.

## Verdict

KEEP DEFAULT OFF — opt-in OK: ref_present mode boosts tiers (crosslocale_hits=23, delta_likely=+23); not a default-on feature.

Opt-in recipe: `examples/lexaudit.config.crosslocale.yaml`.

## Reproduce

```bash
uv run python scripts/run_crosslocale_dogfood.py
uv run python scripts/render_field_eval_charts.py
```
