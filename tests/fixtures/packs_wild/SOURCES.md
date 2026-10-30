# Pack wild corpus (Wikipedia)

Short summaries via Wikipedia REST page/summary.
License: CC BY-SA 4.0 — Wikipedia contributors.
Refresh: `uv run python scripts/fetch_wiki_pack_samples.py`
Do not commit full dumps, CX corpora, or title-named duplicates here.
Keep slug filenames (`wiki-{slug}.md`) only; prune stale on refresh.

## Files

- `tests/fixtures/packs_wild/developer-docs-v0/de/wiki-api.md`
- `tests/fixtures/packs_wild/developer-docs-v0/de/wiki-openapi.md`
- `tests/fixtures/packs_wild/developer-docs-v0/en/wiki-api.md`
- `tests/fixtures/packs_wild/developer-docs-v0/en/wiki-openapi.md`
- `tests/fixtures/packs_wild/developer-docs-v0/ru/wiki-api.md`
- `tests/fixtures/packs_wild/ecommerce-ui-v0/de/wiki-ecommerce.md`
- `tests/fixtures/packs_wild/ecommerce-ui-v0/en/wiki-cart.md`
- `tests/fixtures/packs_wild/ecommerce-ui-v0/en/wiki-ecommerce.md`
- `tests/fixtures/packs_wild/ecommerce-ui-v0/ru/wiki-ecommerce.md`
- `tests/fixtures/packs_wild/edtech-v0/de/wiki-lms.md`
- `tests/fixtures/packs_wild/edtech-v0/en/wiki-lms.md`
- `tests/fixtures/packs_wild/edtech-v0/ru/wiki-lms.md`
- `tests/fixtures/packs_wild/fintech-v0/de/wiki-payment.md`
- `tests/fixtures/packs_wild/fintech-v0/en/wiki-kyc.md`
- `tests/fixtures/packs_wild/fintech-v0/en/wiki-payment.md`
- `tests/fixtures/packs_wild/fintech-v0/ru/wiki-payment.md`
- `tests/fixtures/packs_wild/gaming-ui-v0/de/wiki-hud.md`
- `tests/fixtures/packs_wild/gaming-ui-v0/en/wiki-hud.md`
- `tests/fixtures/packs_wild/healthcare-ui-v0/de/wiki-ehr.md`
- `tests/fixtures/packs_wild/healthcare-ui-v0/en/wiki-ehr.md`
- `tests/fixtures/packs_wild/hr-ats-v0/de/wiki-ats.md`
- `tests/fixtures/packs_wild/hr-ats-v0/en/wiki-ats.md`
- `tests/fixtures/packs_wild/legal-docs-v0/de/wiki-contract.md`
- `tests/fixtures/packs_wild/legal-docs-v0/en/wiki-contract.md`
- `tests/fixtures/packs_wild/legal-docs-v0/ru/wiki-contract.md`
- `tests/fixtures/packs_wild/saas-ui-v0/de/wiki-dashboard.md`
- `tests/fixtures/packs_wild/saas-ui-v0/de/wiki-saas.md`
- `tests/fixtures/packs_wild/saas-ui-v0/en/wiki-dashboard.md`
- `tests/fixtures/packs_wild/saas-ui-v0/en/wiki-saas.md`
- `tests/fixtures/packs_wild/saas-ui-v0/ru/wiki-saas.md`
- `tests/fixtures/packs_wild/security-docs-v0/de/wiki-vuln.md`
- `tests/fixtures/packs_wild/security-docs-v0/en/wiki-vuln.md`
- `tests/fixtures/packs_wild/security-docs-v0/ru/wiki-vuln.md`

## Fetch errors (historical)

- `ru:OpenAPI:HTTP Error 404: Not Found`
- `ru:Электронная история болезни:HTTP Error 404: Not Found`
