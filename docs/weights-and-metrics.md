# Scores and quality numbers

## In plain words

Two questions matter. First: how does the tool decide which page comes first? Second: how do we know it is any good? This page answers both. Terms are explained in the [glossary](glossary.md).

## How a page score is made

Each problem on a page adds points. Serious problems add more. The page with the most points is listed first.

| Problem | Points | Why |
|---|---:|---|
| Calque or invented word | 8.0 | Most important to fix |
| A needle word you track | 6.0 | You asked for it |
| Suspect, confirmed | 3.0 | Very likely wrong |
| Suspect, likely | 1.5 | Probably wrong |
| Russian Latin word in body text | 2.0 | Often a leftover English term |
| Foreign word in metadata, Title Case or English leak | 0.2 | Usually harmless, kept small |
| Weak suspect that appears once or is 3 letters or fewer | 0.1 | Noise floor |
| Template marker | 0.0 | Ignored |

Inflected forms of one bad word count once per page (for example `чеклист` and `чеклисте`), so one mistake cannot inflate the score.

Modes: `weighted` (default) or `raw` (just the number of unique suspects, for debugging, `--mode raw`). Weights can be changed under `rank_weights:` in your settings.

## How we know it works

### Needle recall

Of the tracked bad words that really occur in your texts, how many were flagged?

```text
needle_recall = (needles present AND flagged as calque or invented) / (needles present)
```

Needles that do not occur are skipped, not counted as misses. Target: 0.9 or higher.

### page@K

Of the top K pages, how many are the ones you listed as known problem pages (`gold_slugs`)?

### CLEAR regression

For every page in `gold_slugs`, the tool checks that none of the `regression_needles` remain flagged. It is a soft check and always exits 0.

```bash
uv run lexaudit eval regression --config ./lexaudit.config.yaml
uv run lexaudit eval product --config ./lexaudit.config.yaml
```

### Published benchmark

On the 42-page, 7-language test set: MAP 0.838 against 0.389 for a plain spellchecker, known-rule recall 100%, open-set recall 77.9%. Details and weak spots: [synthetic-benchmark.md](synthetic-benchmark.md).
