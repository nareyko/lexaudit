# Status after research · next wave · 2026-10-30

## Snapshot

| Area | State |
|---|---|
| Package version | 0.3.0 local (not on PyPI) |
| Pack density | 10/10 × **7 locales** green |
| Bilingual FP | held-out + anchors P=R=1.0 |
| Crosslocale | `ref_present` default; **`ref_ok`** mode (C2) available |
| Phrase rules | en 5 · de 5 · ru 4 |
| Product shell | icon + MCP smoke + publish runbook + PyPI workflow stub |
| Hygiene | `check_repo_hygiene.py` — dumps/tmp/vsix not tracked |
| Owner path | `docs/p1-owner-publish-runbook-2026-10-30.md` |

## Latest local closures

| Item | Landing |
|---|---|
| 7-locale density + CI | `check_pack_density.py` + ci.yml |
| C2 `ref_ok` | hunspell-ok norms in reference locale |
| DE phrase bank | +2 → 5 phrases |
| Owner publish runbook | accounts-only steps, no secrets in git |
| Hygiene gate | CI + script; notes local `dumps/`/`tmp/`/`dist/` |

## Still owner-only

1. Push + PyPI Trusted Publishing  
2. MCP registry + VS Marketplace  
3. Tag `v0.3.0` + FairHelm submodule bump  

## Do not commit

`dumps/`, `cx-corpora.*`, `*.tmx*`, `tmp/**`, `dist/**`, `*.vsix`, `*.whl`,
`gold/`, `eval/`, `lexaudit.config.local.yaml`.
