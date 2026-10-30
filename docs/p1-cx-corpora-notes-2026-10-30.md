# Content Translation (CX) corpora · local research notes · 2026-10-30

Track A3 from `p1-next-wave-plan-2026-10-30.md`. **Do not commit dumps.**

## What CX dumps are

Wikimedia publishes parallel corpora from Content Translation (human-edited
segments only in dumps). Formats: TMX and JSON. Docs:
[Published translations](https://www.mediawiki.org/wiki/Content_translation/Published_translations).

Index: <https://dumps.wikimedia.org/other/contenttranslation/>  
Snapshot used for planning: `20261016/`.

## Useful pair files (download to `dumps/` only)

| File | ~size | Use for lexaudit |
|---|---:|---|
| `cx-corpora.ru2en.text.json.gz` | ~10 MiB | Cyrillic leftovers into EN; EN chrome in RU→EN |
| `cx-corpora._2ru.text.json.gz` | ~13 MiB | All sources → RU (Latin leftovers in RU) |
| `cx-corpora.en2ru.text.json.gz` | ~131 MiB | Too large for casual laptop harvest — skip |

Example download (stays gitignored):

```bash
mkdir -p dumps
curl -L -o dumps/cx-corpora.ru2en.text.json.gz \
  https://dumps.wikimedia.org/other/contenttranslation/20261016/cx-corpora.ru2en.text.json.gz
# harvest leftovers into fixtures with scripts/harvest_cx_leftover_samples.py
# never git-add dumps/ or *.tmx.gz
```

## What to keep in git

- Short attributed fixture snippets under `tests/fixtures/bilingual/` (hand-trimmed).
- This note + sample **ids** list produced by the harvest script.
- Wikipedia REST summaries in `packs_wild/` (already CC BY-SA, slug-named).

## What never enters git

- Full CX JSON/TMX dumps (`dumps/`, `cx-corpora.*`, `*.tmx`, `*.tmx.gz`).
- Long verbatim Wikipedia article bodies.
- Host-private FairHelm bilingual trees (use local config only).

## License reminder

Wikipedia / CX text is typically CC BY-SA. Keep source URL or dump id + short
extracts. Prefer reconstruct + attribute over long quotes.
