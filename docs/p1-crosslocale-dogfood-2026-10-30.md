# Crosslocale dogfood · 2026-10-30

Corpus: `tests/fixtures/packs_field/` (EN+RU trees for five packs), audit locale `ru`,
reference locale `en`. Package default stays `enable_crosslocale: false`.

![Crosslocale A/B](images/crosslocale-ab.svg)

## Results

| Mode | words | pages | suspect | foreign | calque |
|---|---:|---:|---:|---:|---:|
| off | 134 | 17 | 23 | 78 | 6 |
| on | 134 | 17 | 23 | 78 | 6 |

Delta suspect: **+0**. Delta foreign: **+0**.

## Verdict

KEEP DEFAULT OFF — no meaningful status delta on this corpus; flag stays available for consumers with aligned EN reference docs.

Opt-in recipe: `examples/lexaudit.config.crosslocale.yaml`.

## Reproduce

```bash
uv run python scripts/run_crosslocale_dogfood.py
uv run python scripts/render_field_eval_charts.py
```
