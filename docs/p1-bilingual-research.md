# P1 bilingual research protocol

Status: lab. `enable_bilingual` remains **false** by default.

## Question

Can Latin-leak detection on paired MD files (`docs/en/{slug}.md` ↔
`docs/{locale}/{slug}.md`) reach usable precision without drowning editors in
intentional loans (`API`, `JSON`, `SEPA`, HTTP verbs)?

## Method

1. **Train** fixtures under `tests/fixtures/bilingual/train/` — used only to
   shape allowlists; not scored.
2. **Held-out** fixtures under `tests/fixtures/bilingual/heldout/` for `ru` and
   `de` targets against English sources.
3. Gold CSV `heldout/gold-leftovers.csv` labels each token as `leftover` or
   `intentional`.
4. Detector: `untranslated_latin_in_target` + `DEFAULT_INTENTIONAL_LOANS`.
5. Length ratio is logged only (soft signal, not a fail gate).
6. Metrics: `uv run python scripts/bilingual_metrics.py --json`.

## Ship bar (lab)

| Metric | Minimum |
|---|---|
| Precision | ≥ 0.75 |
| Recall | ≥ 0.60 |
| Intentional loans predicted | 0 |

Fail → iterate allowlist / min_len / pairing rules. Do not flip default config.

## Local held-out results (2026-10-30)

| Metric | Value |
|---|---:|
| Precision | 1.00 |
| Recall | 1.00 |
| F1 | 1.00 |
| Intentional FP | 0 |
| Length-ratio mean | ~1.16 |
| Lab ship bar | pass on this fixture |

Caveat: held-out texts were authored to exercise the detector. Treat the perfect
score as a **protocol ceiling**, not a production claim. Next iterate: scrape
10–20 real public EN↔RU doc pairs and re-score before enabling the flag.

## Reproduce

```bash
uv run python scripts/bilingual_metrics.py
uv run pytest -q tests/test_bilingual.py
```
