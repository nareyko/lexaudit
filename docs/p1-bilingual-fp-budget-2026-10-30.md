# Bilingual FP budget · held-out · 2026-10-30

Track B5. Research bar: if a check’s FP rate is about **10%+** on held-out gold,
narrow or demote — do not disable globally without a reason log.

## Primary held-out (`scripts/bilingual_metrics.py`)

| Metric | Value |
|---|---|
| Precision | 1.000 |
| Recall | 1.000 |
| Intentional FP | 0 |
| Ship bar (P≥0.75 · R≥0.60) | yes |

## Anchor matrix (`--mode anchors`)

After fixing length-ratio to emit a synthetic `length-ratio` token (not a source
word like `Einstellungen`), reverse DE pairs no longer inherit false token FPs.

| Pair | P | R | Notes |
|---|---:|---:|---|
| en→de / en→ru | 1.0 | 1.0 | primary product direction |
| de→en / ru→en | 1.0 | 1.0 | |
| de→ru / ru→de | 1.0 | 1.0 | after length-ratio synthetic token fix |

## Soft signals vs gold

| Signal | Counts toward P/R? | Role |
|---|---|---|
| `bilingual-untranslated` / cyrillic | yes | core leftover |
| `bilingual-identical-segment` | yes | segment copy |
| `bilingual-length-ratio:*` | **no** (metrics skip) | ranking soft |
| `+cognate-soft` tier demote | still counted if flagged | ranking only |

## Actions taken

1. Length-ratio anchor no longer copies a source heading into predicted tokens.
2. Soft cognate demote (C3) lowers tier for shared UI Latin nouns; does not drop.
3. URL/email/code spans stripped before leftover scans (prior wave).

## Reproduce

```bash
uv run python scripts/bilingual_metrics.py
uv run python scripts/bilingual_matrix_metrics.py --mode anchors
```

Default `enable_bilingual` stays **false** until owner review + live dogfood.
