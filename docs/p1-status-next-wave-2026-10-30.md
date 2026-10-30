# Status after research · next wave · 2026-10-30

## Snapshot

| Area | State |
|---|---|
| Package version | 0.3.0 local (not on PyPI) |
| Pack density | 10/10 green (`check_pack_density.py`) |
| Pack field / clean | `02-clean-domain` calque FP=0 |
| Pack wild | exploratory; calque sum low (encyclopedic) |
| Bilingual FP budget | held-out + anchors **P=R=1.0**; soft cognate demote |
| Crosslocale | `ref_present`; dogfood +23 likely; default false |
| CX | dump gitignored; trimmed samples + grown cyrillic fixtures |
| Product shell | icon, MCP smoke, Trusted Publishing workflow stub |
| Plan | `docs/p1-next-wave-plan-2026-10-30.md` |

## Local thin spots closed (latest)

| Item | Landing |
|---|---|
| B5 FP budget | `p1-bilingual-fp-budget-2026-10-30.md`; length-ratio synthetic token |
| C3 cognate soft | `SOFT_COGNATE_DEMOTE` → tier weak |
| A4/E clean+wild sanity | `run_clean_wild_sanity.py` + report |
| E pack density gate | `check_pack_density.py` |
| Cyrillic harvest grow | `payments.md` / `dashboard.md` pairs |
| D Trusted Publishing stub | `.github/workflows/publish-pypi.yml` (dispatch only) |

## Still owner-only

1. PyPI publish 0.3.0 (workflow ready; needs PyPI OIDC env)  
2. MCP registry + VS Marketplace  
3. Git remote push / tag after publish go  

## Do not commit

`dumps/`, `cx-corpora.*`, `*.tmx*`, `tmp/**`, `*.vsix`, `*.whl`, `gold/`, `eval/`,
`lexaudit.config.local.yaml`.
