# Lab packs (not released)

Experimental industry packs. Do **not** attach to GitHub Releases with 0.2.x.
See `docs/p1-0.3.0-prep.md` for promote checklist.

| Pack | Focus |
|---|---|
| `saas-ui-v0` | Product UI calques / anglicisms |
| `fintech-v0` | Payments / ledger leftovers |
| `developer-docs-v0` | API prose coinages |
| `ecommerce-ui-v0` | Checkout / cart coinages (thin) |
| `healthcare-ui-v0` | Patient UI coinages (thin) |
| `legal-docs-v0` | Contract prose coinages (thin) |

Measure / dogfood:

```bash
uv run python scripts/lab_pack_metrics.py --pack saas-ui-v0 --locale en
uv run python scripts/run_lab_pack_metrics.py
uv run lexaudit pack list --lab
uv run lexaudit pack install saas-ui-v0 --lab --dest /tmp/lexaudit-packs --force
uv run python scripts/promote_lab_pack.py saas-ui-v0   # dry-run validate
```
