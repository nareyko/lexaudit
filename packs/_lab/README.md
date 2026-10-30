# Lab packs (not released)

Experimental industry packs. Do **not** attach to GitHub Releases with 0.2.x.

| Pack | Focus |
|---|---|
| `saas-ui-v0` | Product UI calques / anglicisms |
| `fintech-v0` | Payments / ledger leftovers |
| `developer-docs-v0` | API prose coinages |
| `ecommerce-ui-v0` | Checkout / cart coinages (thin) |

Measure with:

```bash
uv run python scripts/lab_pack_metrics.py --pack saas-ui-v0 --locale en
uv run python scripts/lab_pack_metrics.py --pack ecommerce-ui-v0 --locale ru
```
