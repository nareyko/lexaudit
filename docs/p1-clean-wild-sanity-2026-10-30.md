# Clean-domain + wild sanity · 2026-10-30

Track A4/E: pack rules on ordinary domain prose and Wikipedia wild extracts.
Clean pages must not raise calques. Wild hits stay exploratory (often 0).

Clean-domain calque FP total: **0**.
Wild calque unique sum: **0**.

Verdict: OK — clean-domain calque FP=0; wild calque sum is exploratory

| kind | pack | locale | pages | calque unique | sample |
|---|---|---|---:|---:|---|
| clean-domain | `developer-docs-v0` | en | 0 | 0 | — |
| clean-domain | `developer-docs-v0` | de | 2 | 0 | — |
| clean-domain | `developer-docs-v0` | ru | 2 | 0 | — |
| clean-domain | `ecommerce-ui-v0` | en | 0 | 0 | — |
| clean-domain | `ecommerce-ui-v0` | de | 1 | 0 | — |
| clean-domain | `ecommerce-ui-v0` | ru | 1 | 0 | — |
| clean-domain | `edtech-v0` | en | 0 | 0 | — |
| clean-domain | `edtech-v0` | de | 1 | 0 | — |
| clean-domain | `edtech-v0` | ru | 1 | 0 | — |
| clean-domain | `fintech-v0` | en | 0 | 0 | — |
| clean-domain | `fintech-v0` | de | 1 | 0 | — |
| clean-domain | `fintech-v0` | ru | 1 | 0 | — |
| clean-domain | `gaming-ui-v0` | en | 0 | 0 | — |
| clean-domain | `gaming-ui-v0` | de | 2 | 0 | — |
| clean-domain | `gaming-ui-v0` | ru | 2 | 0 | — |
| clean-domain | `healthcare-ui-v0` | en | 0 | 0 | — |
| clean-domain | `healthcare-ui-v0` | de | 1 | 0 | — |
| clean-domain | `healthcare-ui-v0` | ru | 1 | 0 | — |
| clean-domain | `hr-ats-v0` | en | 1 | 0 | — |
| clean-domain | `hr-ats-v0` | de | 2 | 0 | — |
| clean-domain | `hr-ats-v0` | ru | 1 | 0 | — |
| clean-domain | `legal-docs-v0` | en | 0 | 0 | — |
| clean-domain | `legal-docs-v0` | de | 1 | 0 | — |
| clean-domain | `legal-docs-v0` | ru | 1 | 0 | — |
| clean-domain | `saas-ui-v0` | en | 0 | 0 | — |
| clean-domain | `saas-ui-v0` | de | 1 | 0 | — |
| clean-domain | `saas-ui-v0` | ru | 1 | 0 | — |
| clean-domain | `security-docs-v0` | en | 0 | 0 | — |
| clean-domain | `security-docs-v0` | de | 2 | 0 | — |
| clean-domain | `security-docs-v0` | ru | 2 | 0 | — |
| wild | `developer-docs-v0` | de | 2 | 0 | — |
| wild | `developer-docs-v0` | en | 1 | 0 | — |
| wild | `developer-docs-v0` | ru | 1 | 0 | — |
| wild | `ecommerce-ui-v0` | de | 1 | 0 | — |
| wild | `ecommerce-ui-v0` | en | 1 | 0 | — |
| wild | `ecommerce-ui-v0` | ru | 1 | 0 | — |
| wild | `edtech-v0` | de | 1 | 0 | — |
| wild | `edtech-v0` | en | 1 | 0 | — |
| wild | `edtech-v0` | ru | 1 | 0 | — |
| wild | `fintech-v0` | de | 1 | 0 | — |
| wild | `fintech-v0` | en | 2 | 0 | — |
| wild | `fintech-v0` | ru | 1 | 0 | — |
| wild | `gaming-ui-v0` | de | 1 | 0 | — |
| wild | `gaming-ui-v0` | en | 1 | 0 | — |
| wild | `healthcare-ui-v0` | de | 1 | 0 | — |
| wild | `healthcare-ui-v0` | en | 1 | 0 | — |
| wild | `hr-ats-v0` | de | 1 | 0 | — |
| wild | `hr-ats-v0` | en | 1 | 0 | — |
| wild | `legal-docs-v0` | de | 1 | 0 | — |
| wild | `legal-docs-v0` | en | 0 | 0 | — |
| wild | `legal-docs-v0` | ru | 1 | 0 | — |
| wild | `saas-ui-v0` | de | 2 | 0 | — |
| wild | `saas-ui-v0` | en | 1 | 0 | — |
| wild | `saas-ui-v0` | ru | 1 | 0 | — |
| wild | `security-docs-v0` | de | 1 | 0 | — |
| wild | `security-docs-v0` | en | 0 | 0 | — |
| wild | `security-docs-v0` | ru | 1 | 0 | — |

## Reproduce

```bash
uv run python scripts/run_clean_wild_sanity.py
uv run python scripts/check_pack_density.py
```

Do not commit `tmp/clean-wild/`.
