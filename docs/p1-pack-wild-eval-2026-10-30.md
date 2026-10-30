# Pack wild eval (Wikipedia) · 2026-10-30

Exploratory: RC pack rules against CC BY-SA Wikipedia summaries in
`tests/fixtures/packs_wild/`. Not a precision gold — hits need human review.

Rows: 27. Refresh corpus: `uv run python scripts/fetch_wiki_pack_samples.py`.

| Pack | Locale | pages | calque unique | sample |
|---|---|---:|---:|---|
| `developer-docs-v0` | de | 2 | 0 | — |
| `developer-docs-v0` | en | 1 | 0 | — |
| `developer-docs-v0` | ru | 1 | 0 | — |
| `ecommerce-ui-v0` | de | 1 | 0 | — |
| `ecommerce-ui-v0` | en | 1 | 0 | — |
| `ecommerce-ui-v0` | ru | 1 | 0 | — |
| `edtech-v0` | de | 1 | 0 | — |
| `edtech-v0` | en | 1 | 0 | — |
| `edtech-v0` | ru | 1 | 0 | — |
| `fintech-v0` | de | 1 | 0 | — |
| `fintech-v0` | en | 2 | 0 | — |
| `fintech-v0` | ru | 1 | 0 | — |
| `gaming-ui-v0` | de | 1 | 0 | — |
| `gaming-ui-v0` | en | 1 | 0 | — |
| `healthcare-ui-v0` | de | 1 | 0 | — |
| `healthcare-ui-v0` | en | 1 | 0 | — |
| `hr-ats-v0` | de | 1 | 0 | — |
| `hr-ats-v0` | en | 1 | 0 | — |
| `legal-docs-v0` | de | 1 | 0 | — |
| `legal-docs-v0` | en | 0 | 0 | — |
| `legal-docs-v0` | ru | 1 | 0 | — |
| `saas-ui-v0` | de | 2 | 0 | — |
| `saas-ui-v0` | en | 1 | 0 | — |
| `saas-ui-v0` | ru | 1 | 0 | — |
| `security-docs-v0` | de | 1 | 0 | — |
| `security-docs-v0` | en | 0 | 0 | — |
| `security-docs-v0` | ru | 1 | 0 | — |

## Note

Encyclopedic prose rarely contains SaaS coinages; low calque counts are expected.
Use this to catch accidental over-matching (brands/common words), not for recall.
