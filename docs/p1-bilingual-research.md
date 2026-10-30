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

V1 locales: `{en, de, pl, ru, es, sv, uk}` → **42 directed pairs** (`--mode all`).

| Focus | Coverage |
|---|---|
| with English | en↔ each of de/pl/ru/es/sv/uk |
| with German | de↔ each of en/pl/ru/es/sv/uk |
| with Russian | ru↔ each of en/de/pl/es/sv/uk |
| others among themselves | es/pl/sv/uk mutual (unsupervised on held-out unless gold added) |

Modes: `all` (42) · `anchors` (en/de/ru = 6) · `anchors_x_others` (30).

Detectors:

- **latin-overlap** — shared Latin tokens (EN/DE/ES/PL/SV → *)
- **cyrillic-overlap** — when source is `ru` or `uk` (into Latin or other Cyrillic)

Latin matching uses `\p{Latin}` (umlauts).  
P/R scored only when gold exists for `(source, target)`; else unsupervised alarms.

### Held-out V1 matrix (26 scored / 16 unsupervised · ship_all=True)

Scored anchors × others (all P=R=F1=1.00 unless noted):

| source→ | de | pl | ru | es | sv | uk |
|---|---|---|---|---|---|---|
| **en** | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| **de** | — | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| **ru** | 1.0 | 1.0 | — | 1.0 | 1.0 | 1.0 |
| **uk** | 1.0 | 1.0 | unsup | 1.0 | 1.0 | — |
| **es/pl/sv→ru** | — | — | 1.0 | — | — | — |

Also scored: `de→en` (gold on `german-leak.md` only), `ru→en`, `uk→en`.  
Unsupervised (alarms only): most `es/pl/sv ↔ {en,de,es,pl,sv,uk}` without gold — typically 11–15 latin alarms from shared English UI leftovers.

Notes:

- Held-out adds `es/`, `pl/`, `sv/`, `uk/` with planted EN leftovers + Cyrillic RU leaks.
- DE→EN still requires clean DE source + gold basename (`german-leak.md`).
- `uk→ru` left unsupervised (both Cyrillic; shared planted Russian forms would need separate gold policy).

### Other corpora

| corpus | scored pairs | notes |
|---|---|---|
| real_public | en→de/ru P/R 1.0 | FastAPI + k8s; no es/pl/sv/uk trees |
| community | en→de/ru P/R 1.0 | reconstructed leftovers |
| live_weblate | en→de/ru P/R 1.0 | hosted.weblate EN/DE/RU sample |
| live_crowdin | en→de/ru P/R 1.0 | Jellyfin/Immich GitHub mirrors |
| **live_v1_others** (2026-10-30 harvest) | **en→es/pl/sv/uk P/R 1.0 · ship_all** | Weblate es/pl/sv/uk leftovers |

### Live V1 others harvest (es/pl/sv/uk · 2026-10-30)

| pair | P | R | F1 | ship |
|---|---:|---:|---:|---|
| en→es | 1.00 | 1.00 | 1.00 | yes |
| en→pl | 1.00 | 1.00 | 1.00 | yes |
| en→sv | 1.00 | 1.00 | 1.00 | yes |
| en→uk | 1.00 | 1.00 | 1.00 | yes |

Sources: soapbox / dicio / taiga / muos / godot units via Weblate API (200-row time-boxed pull).  
Jellyfin/Immich GitHub `es/pl/sv/uk` mirrors mostly translate `Dashboard`/`Download` (e.g. ES `Panel de control`), so they were weak leftover sources this pass — Weblate UI loans worked better.

Research takeaways:

1. EN→{de,pl,ru,es,sv,uk} latin-overlap holds on held-out and on live_v1_others harvest.
2. DE→{pl,ru,es,sv,uk} same on held-out; DE→EN only with dedicated clean-DE gold pages.
3. RU/UK→Latin targets need cyrillic-overlap; held-out proves it; live Cyrillic→Latin harvest still thin (follow-up).
4. Cross-other pairs (es↔pl, …) without gold stay unsupervised.
5. Prefer Weblate leftover queries over fully localized product mirrors when hunting EN loans in ES/PL/SV/UK.

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

# Full V1 directed matrix (42 pairs among en/de/pl/ru/es/sv/uk)
uv run python scripts/bilingual_matrix_metrics.py \
  --mode all --label heldout-v1 --out tmp/bilingual-matrix/heldout-v1.json
# Anchors only (en/de/ru = 6) or anchors×others (30):
#   --mode anchors | --mode anchors_x_others

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

uv run python scripts/bilingual_matrix_metrics.py \
  --fixtures tests/fixtures/bilingual/live_v1_others \
  --gold tests/fixtures/bilingual/live_v1_others/gold-leftovers.csv \
  --mode all --label live_v1_others \
  --out tmp/bilingual-matrix/live_v1_others.json

uv run pytest -q tests/test_bilingual.py
```
