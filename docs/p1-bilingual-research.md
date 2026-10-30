# P1 bilingual research protocol

Status: lab. `enable_bilingual` remains false by default.

## Question

Can Latin-leak detection on paired MD files (`docs/en/{slug}.md` ↔
`docs/{locale}/{slug}.md`) reach usable precision without drowning editors in
intentional loans (`API`, `JSON`, `SEPA`, HTTP verbs)?

## Method

1. Train fixtures under `tests/fixtures/bilingual/train/` — used only to
   shape allowlists; not scored.

2. Synthetic held-out under `tests/fixtures/bilingual/heldout/` for `ru` and
   `de` (protocol ceiling).

3. Real-public under `tests/fixtures/bilingual/real_public/`:
   - FastAPI MIT docs EN↔RU/DE (6 tutorial/feature slugs)
   - Kubernetes website CC BY pods (+ overview EN/RU)
   - `seeded-leak.md` overlay for leftover recall (documented synthetic)
   - Prose-only excerpts via `scripts/build_real_public_corpus.py`
   - Extra loans file (official pages only; not merged into DEFAULT)

4. Gold CSVs label each token as `leftover` or `intentional`.

5. Detector: `untranslated_latin_in_target` + `DEFAULT_INTENTIONAL_LOANS`
   (+ skip kebab slugs with ≥2 hyphens).

6. Metrics: `uv run python scripts/bilingual_metrics.py --json`.

## Ship bar (lab)

| Metric | Minimum |
|---|---|
| Precision | ≥ 0.75 |
| Recall | ≥ 0.60 |
| Intentional loans predicted | 0 |

Fail → iterate allowlist / min_len / pairing rules. Do not flip default config.

## Local results (2026-10-30)

### Synthetic held-out

| Metric | Value |
|---|---:|
| Precision | 1.00 |
| Recall | 1.00 |
| F1 | 1.00 |
| Intentional FP | 0 |
| Lab ship bar | pass (protocol ceiling) |

### Real-public (FastAPI + k8s + seeded overlay)

| Metric | Value |
|---|---:|
| Precision | 1.00 |
| Recall | 1.00 |
| F1 | 1.00 |
| Intentional FP | 0 |
| Official-page alarms (after extra loans) | 0 |
| Lab ship bar | pass on this corpus |

Caveats:

- Perfect synthetic score remains a protocol ceiling.
- Real-public leftover recall is driven by the seeded overlay; official
  FastAPI/k8s translations are mostly clean after brand allowlist + prose
  scrub (anchors/URLs/fences).
- German tech docs keep many English loans (`parameter`, `request`, …) — those
  live in `intentional-extra.txt`, not in DEFAULT (so held-out leftovers
  like `query` / `parameters` still fire).
- Next iterate before default-on: more imperfect community translations (not
  only polished official trees) and a human pass on DE loan policy.

## Reproduce

```bash
uv run python scripts/bilingual_metrics.py
uv run python scripts/bilingual_metrics.py \
  --fixtures tests/fixtures/bilingual/real_public \
  --gold tests/fixtures/bilingual/real_public/gold-leftovers.csv \
  --extra-loans tests/fixtures/bilingual/real_public/intentional-extra.txt \
  --label real_public
uv run pytest -q tests/test_bilingual.py
```
