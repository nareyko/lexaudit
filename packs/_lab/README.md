# Lab packs (not released)

Experimental industry packs. Do **not** attach to GitHub Releases with 0.2.x.
See `docs/p1-0.3.0-prep.md` for promote checklist. Inventory: **10** packs.

| Pack | Focus | 0.3.0 proposal |
|---|---|---|
| `saas-ui-v0` | Product UI calques / anglicisms | promote |
| `fintech-v0` | Payments / ledger leftovers | promote |
| `developer-docs-v0` | API prose coinages | promote |
| `ecommerce-ui-v0` | Checkout / cart coinages | promote |
| `healthcare-ui-v0` | Patient UI coinages | promote |
| `legal-docs-v0` | Contract prose coinages | promote |
| `gaming-ui-v0` | Game HUD / loot coinages | keep lab (harvest) |
| `edtech-v0` | LMS / SCORM coinages | keep lab (harvest) |
| `security-docs-v0` | Security / pen-test prose | keep lab (harvest) |
| `hr-ats-v0` | ATS / recruiting coinages | keep lab (harvest) |

Measure / dogfood:

```bash
uv run python scripts/lab_pack_metrics.py --pack saas-ui-v0 --locale en
uv run python scripts/run_lab_pack_metrics.py
uv run lexaudit pack list --lab
uv run lexaudit pack install saas-ui-v0 --lab --dest /tmp/lexaudit-packs --force
uv run python scripts/promote_lab_pack.py saas-ui-v0   # dry-run validate
```
