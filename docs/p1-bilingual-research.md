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

4. Community imperfect under `tests/fixtures/bilingual/community/`:
   - Reconstructed leftovers from public i18n issues/PRs (Excalidraw,
     Ever-teams, Zulip guide, Homebox)
   - See `community/SOURCES.md`

5. Live Weblate sample under `tests/fixtures/bilingual/live_weblate/`:
   - Time-boxed pull from hosted.weblate.org public units API (2026-10-30)
   - DE UI loans scoped via `--extra-loans-locales de` + basenames
   - Policy: `docs/p1-de-loan-policy.md`

6. Gold CSVs label each token as `leftover` or `intentional`.

7. Detector: `untranslated_latin_in_target` + `DEFAULT_INTENTIONAL_LOANS`
   + function-word stop + skip kebab slugs with ≥2 hyphens.

8. Metrics: `uv run python scripts/bilingual_metrics.py --json`.

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

### Community imperfect (cited public leftover patterns)

| Metric | Value |
|---|---:|
| Precision | 1.00 |
| Recall | 1.00 |
| F1 | 1.00 |
| Intentional FP | 0 |
| Lab ship bar | pass (regression lock on planted leftovers) |

### Live Weblate (hosted.weblate.org · 2026-10-30)

| Metric | Value |
|---|---:|
| Precision | 1.00 |
| Recall | 1.00 |
| F1 | 1.00 |
| Intentional FP | 0 |
| Lab ship bar | pass (with DE loan basename scope) |

Caveats:

- Perfect synthetic score remains a protocol ceiling.
- Real-public leftover recall is driven by the seeded overlay; official
  FastAPI/k8s translations are mostly clean after brand allowlist + prose
  scrub (anchors/URLs/fences).
- Community fixtures reconstruct documented defects; they are not live scrapes
  of production apps. Treat P/R as a pattern lock, then validate on fresh PRs.
- Live Weblate sample is time-boxed and curated into MD wrappers; Crowdin bulk
  sample deferred (no auth token this pass).
- DE UI loans (`dashboard`, `toast`, `store`, …) stay out of DEFAULT — see
  `docs/p1-de-loan-policy.md`.
- `enable_bilingual` stays false until owner review of DE loan list + optional
  Crowdin sample.

## Reproduce

```bash
uv run python scripts/bilingual_metrics.py
uv run python scripts/bilingual_metrics.py \
  --fixtures tests/fixtures/bilingual/real_public \
  --gold tests/fixtures/bilingual/real_public/gold-leftovers.csv \
  --extra-loans tests/fixtures/bilingual/real_public/intentional-extra.txt \
  --label real_public
uv run python scripts/bilingual_metrics.py \
  --fixtures tests/fixtures/bilingual/community \
  --gold tests/fixtures/bilingual/community/gold-leftovers.csv \
  --label community
uv run python scripts/bilingual_metrics.py \
  --fixtures tests/fixtures/bilingual/live_weblate \
  --gold tests/fixtures/bilingual/live_weblate/gold-leftovers.csv \
  --extra-loans tests/fixtures/bilingual/live_weblate/intentional-extra-de.txt \
  --extra-loans-locales de \
  --extra-loans-basenames galette-dashboard.md,goosemod-toast.md,dicio-toast.md \
  --label live_weblate
uv run pytest -q tests/test_bilingual.py
```
