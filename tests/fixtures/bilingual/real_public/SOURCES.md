# Real-public bilingual corpus sources

Lab fixtures only. Short prose excerpts (code fences / anchors / URLs stripped).
Licenses remain with upstream projects; excerpts are for detector research.

| Slug | Upstream | License | Retrieved |
|---|---|---|---|
| `fastapi-*` | [fastapi/fastapi](https://github.com/fastapi/fastapi) `docs/{en,ru,de}/docs/…` | MIT | 2026-10-30 |
| `k8s-pods` | [kubernetes/website](https://github.com/kubernetes/website) `content/{en,ru,de}/docs/concepts/workloads/pods/_index.md` | CC BY 4.0 | 2026-10-30 |
| `k8s-overview` | kubernetes/website overview `_index.md` (EN+RU; DE description stub skipped when thin) | CC BY 4.0 | 2026-10-30 |
| `seeded-leak` | Synthetic overlay on payment/UI phrasing (not upstream text) | MIT (this repo) | 2026-10-30 |

Rebuild from a staging download:

```bash
# populate /tmp/lexaudit-corpus as in docs/p1-bilingual-research.md
uv run python scripts/build_real_public_corpus.py --staging /tmp/lexaudit-corpus
```
