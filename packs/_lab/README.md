# Lab packs (not released)

Experimental industry packs. Do **not** attach to GitHub Releases with 0.2.x.

| Pack | Focus |
|---|---|
| `saas-ui-v0` | Product UI calques / anglicisms |
| `fintech-v0` | Payments / ledger leftovers |
| `developer-docs-v0` | API prose coinages |

Measure with:

```bash
uv run python scripts/lab_pack_metrics.py --pack saas-ui-v0 --locale en
```
