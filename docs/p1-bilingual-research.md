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

6. Crowdin-synced GitHub mirrors under `tests/fixtures/bilingual/live_crowdin/`:
   - Jellyfin Web + Immich i18n (Crowdin API needs a token; mirrors used instead)
   - Owner checklist: `docs/p1-owner-review-bilingual.md`

7. Gold CSVs label each token as `leftover` or `intentional`.

8. Detector: `untranslated_latin_in_target` + `DEFAULT_INTENTIONAL_LOANS`
   + function-word stop + skip kebab slugs with ≥2 hyphens.

9. Metrics: `uv run python scripts/bilingual_metrics.py --json`.

## Ship bar (lab)

| Metric | Minimum |
|---|---|
| Precision | ≥ 0.75 |
| Recall | ≥ 0.60 |
| Intentional loans predicted | 0 |

Fail → iterate allowlist / min_len / pairing rules. Do not flip default config.

## Local results (2026-10-30)

### Synthetic held-out (legacy EN→* aggregate)

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

### Crowdin-via-GitHub (Jellyfin + Immich · 2026-10-30)

| Metric | Value |
|---|---:|
| Precision | 1.00 |
| Recall | 1.00 |
| F1 | 1.00 |
| Intentional FP | 0 |
| Lab ship bar | pass (DE loans basename-scoped) |

## Language-pair matrix (2026-10-30)

All **6 directed pairs** among `{en, de, ru}`:

| Anchor | Pairs |
|---|---|
| with English | en→de, en→ru, de→en, ru→en |
| with German | de→en, de→ru, en→de, ru→de |
| with Russian | ru→en, ru→de, en→ru, de→ru |

Detectors:

- **latin-overlap** — shared Latin tokens in source∩target (EN/DE → *, and DE→EN on dedicated pages)
- **cyrillic-overlap** — shared Cyrillic tokens (RU → EN/DE)

Latin matching uses `\p{Latin}` (umlauts: `Überweisungen`).  
`scripts/bilingual_matrix_metrics.py` scores P/R only when gold rows exist for that `(source, target)`; otherwise reports unsupervised alarm counts.

### Held-out matrix (gold for all 6 pairs · ship_all=True)

| pair | detector | P | R | F1 | alarms | ship |
|---|---|---:|---:|---:|---:|---|
| en→de | latin-overlap | 1.00 | 1.00 | 1.00 | 18 | yes |
| en→ru | latin-overlap | 1.00 | 1.00 | 1.00 | 12 | yes |
| de→en | latin-overlap | 1.00 | 1.00 | 1.00 | 18 | yes |
| de→ru | latin-overlap | 1.00 | 1.00 | 1.00 | 12 | yes |
| ru→en | cyrillic-overlap | 1.00 | 1.00 | 1.00 | 5 | yes |
| ru→de | cyrillic-overlap | 1.00 | 1.00 | 1.00 | 5 | yes |

Notes on held-out construction:

- EN/DE/RU `payments.md` / `settings.md` carry planted Latin + Cyrillic leftovers for cross directions.
- DE→EN gold is scoped to `german-leak.md` (clean DE source ↔ EN with `Überweisungen` / `Auszahlungen`). Raw latin-overlap on fluent EN pages would FP every shared English word present in leaky DE — do **not** score DE→EN on those paths without a dedicated gold basename.
- de→en `alarms=18` includes unscored pages; P/R uses gold paths only.

### Other corpora (EN→* gold only; reverse unsupervised)

| corpus | en→de | en→ru | de→en alarms | de→ru alarms | ru→en | ru→de |
|---|---|---|---:|---:|---:|---:|
| real_public | P/R 1.0 | P/R 1.0 | 15 | 15 | 0 | 0 |
| community | P/R 1.0 | P/R 1.0 | 43 | 40 | 0 | 0 |
| live_weblate | P/R 1.0 | P/R 1.0 | 34 | 32 | 0 | 0 |
| live_crowdin | P/R 1.0 | P/R 1.0 | 5 | 5 | 0 | 0 |

Research takeaways:

1. EN→RU / EN→DE / DE→RU — latin-overlap is the working production shape; DE→RU reuses the same leftover vocabulary as EN→RU when DE still contains English UI loans.
2. RU→EN / RU→DE — need cyrillic-overlap; public corpora here have 0 Cyrillic leftovers in EN/DE targets (expected for these samples). Held-out proves the detector; live validation needs a Cyrillic-leak harvest next.
3. DE→EN — latin-overlap is only safe with a clean DE source + gold-scoped EN leaks (`german-leak.md`). Do not enable broadly on mixed DE UI dumps without basename gold or a German-lexicon gate.
4. Unsupervised de→* alarm counts on community/Weblate mirror EN leftover density (same Latin tokens), not new defects.

Caveats:

- Perfect synthetic score remains a protocol ceiling.
- Real-public leftover recall is driven by the seeded overlay; official
  FastAPI/k8s translations are mostly clean after brand allowlist + prose
  scrub (anchors/URLs/fences).
- Community fixtures reconstruct documented defects; they are not live scrapes
  of production apps. Treat P/R as a pattern lock, then validate on fresh PRs.
- Live Weblate sample is time-boxed and curated into MD wrappers.
- Crowdin REST API returned 401 without a token; this pass uses public GitHub
  mirrors of Crowdin-synced trees instead.
- DE UI loans (`dashboard`, `toast`, `store`, `download`, `upload`, …) stay out
  of DEFAULT — see `docs/p1-de-loan-policy.md`.
- `enable_bilingual` stays false until owner signs
  `docs/p1-owner-review-bilingual.md`.

## Reproduce

```bash
# Legacy EN→* held-out
uv run python scripts/bilingual_metrics.py

# Full en/de/ru directed matrix (6 pairs)
uv run python scripts/bilingual_matrix_metrics.py \
  --label heldout --out tmp/bilingual-matrix/heldout.json

uv run python scripts/bilingual_metrics.py \
  --fixtures tests/fixtures/bilingual/real_public \
  --gold tests/fixtures/bilingual/real_public/gold-leftovers.csv \
  --extra-loans tests/fixtures/bilingual/real_public/intentional-extra.txt \
  --label real_public
uv run python scripts/bilingual_matrix_metrics.py \
  --fixtures tests/fixtures/bilingual/real_public \
  --gold tests/fixtures/bilingual/real_public/gold-leftovers.csv \
  --extra-loans tests/fixtures/bilingual/real_public/intentional-extra.txt \
  --label real_public --out tmp/bilingual-matrix/real_public.json

uv run python scripts/bilingual_metrics.py \
  --fixtures tests/fixtures/bilingual/community \
  --gold tests/fixtures/bilingual/community/gold-leftovers.csv \
  --label community
uv run python scripts/bilingual_matrix_metrics.py \
  --fixtures tests/fixtures/bilingual/community \
  --gold tests/fixtures/bilingual/community/gold-leftovers.csv \
  --label community --out tmp/bilingual-matrix/community.json

uv run python scripts/bilingual_metrics.py \
  --fixtures tests/fixtures/bilingual/live_weblate \
  --gold tests/fixtures/bilingual/live_weblate/gold-leftovers.csv \
  --extra-loans tests/fixtures/bilingual/live_weblate/intentional-extra-de.txt \
  --extra-loans-locales de \
  --extra-loans-basenames galette-dashboard.md,goosemod-toast.md,dicio-toast.md \
  --label live_weblate
uv run python scripts/bilingual_matrix_metrics.py \
  --fixtures tests/fixtures/bilingual/live_weblate \
  --gold tests/fixtures/bilingual/live_weblate/gold-leftovers.csv \
  --extra-loans tests/fixtures/bilingual/live_weblate/intentional-extra-de.txt \
  --extra-loans-locales de \
  --extra-loans-basenames galette-dashboard.md,goosemod-toast.md,dicio-toast.md \
  --label live_weblate --out tmp/bilingual-matrix/live_weblate.json

uv run python scripts/bilingual_metrics.py \
  --fixtures tests/fixtures/bilingual/live_crowdin \
  --gold tests/fixtures/bilingual/live_crowdin/gold-leftovers.csv \
  --extra-loans tests/fixtures/bilingual/live_crowdin/intentional-extra-de.txt \
  --extra-loans-locales de \
  --extra-loans-basenames jellyfin-dashboard.md,jellyfin-download.md,immich-transfer.md \
  --label live_crowdin
uv run python scripts/bilingual_matrix_metrics.py \
  --fixtures tests/fixtures/bilingual/live_crowdin \
  --gold tests/fixtures/bilingual/live_crowdin/gold-leftovers.csv \
  --extra-loans tests/fixtures/bilingual/live_crowdin/intentional-extra-de.txt \
  --extra-loans-locales de \
  --extra-loans-basenames jellyfin-dashboard.md,jellyfin-download.md,immich-transfer.md \
  --label live_crowdin --out tmp/bilingual-matrix/live_crowdin.json

uv run pytest -q tests/test_bilingual.py
```
