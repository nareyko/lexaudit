# Third-party corpora used by lexaudit real-bench (v0.4)

This file records licenses for stratified fixtures under
`tests/fixtures/real_bench/` and the machine-readable manifest at
`eval/corpora/manifest.json`. Raw dumps stay in `tmp/` and are not published
to git.

| Source | License | Used for | Notes |
|---|---|---|---|
| FairHelm / lexaudit original technical prose | CC0-1.0 | clean, mt, self-gec | Written for this benchmark; no copyrighted book sentences. |
| real_public FastAPI docs excerpts | MIT | clean (en/de/ru) | Upstream: fastapi/fastapi. |
| real_public Kubernetes website excerpts | CC-BY-4.0 | clean (en/de/ru) | Upstream: kubernetes/website. |
| Wikipedia REST API page summaries | CC-BY-SA-4.0 | clean (when fetched) | Attribution via URL in manifest; excerpts only. |
| grammarly/ua-gec annotated samples | CC-BY-4.0 | gec/uk | Spelling / F/Calque pairs; raw under `tmp/corpora/ua-gec/`. |
| mhagiwara/github-typo-corpus | **not used** | — | No clear MIT/Apache/BSD/CC grant in-repo (2026-11-03). Replaced with self-curated CC0 EN pairs. |

Allowed license set for committed fixtures: MIT, Apache-2.0, BSD, CC0, CC-BY, CC-BY-SA.
