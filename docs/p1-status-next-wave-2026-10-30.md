# Status after research · next wave · 2026-10-30

## Snapshot

| Area | State |
|---|---|
| Package version | 0.3.0 local (not on PyPI) |
| Pack density | 10/10 × **7 locales** green |
| Bilingual FP | held-out + anchors P=R=1.0 |
| Crosslocale | `ref_present` default; **`ref_ok`** mode (C2) available |
| Phrase rules | en 5 · de 5 · ru 5 |
| Product shell | icon + MCP smoke + publish runbook + PyPI workflow stub |
| Hygiene | `check_repo_hygiene.py` — dumps/tmp/vsix not tracked |
| Docs index | `docs/p1-INDEX.md` |
| Owner path | `docs/p1-owner-publish-runbook-2026-10-30.md` |
| Version sync | `__version__` ↔ pyproject `0.3.0`; Action pin ≥0.3.0 |

## Latest local closures

| Item | Landing |
|---|---|
| Version drift 0.2.0 leftover | `__init__.py` + `action.yml` + sync test |
| RU phrase bank | +1 → 5 (parity with en/de) |
| P1 docs navigation | `p1-INDEX.md` |
| Stale lab plan wording | points at 0.3.0 RC + index |
| Twin `packs/_lab` trees | thin stubs only; `pack_content_dir` + hygiene gate |

## Still owner-only

1. Push + PyPI Trusted Publishing  
2. MCP registry + VS Marketplace  
3. Tag `v0.3.0` + FairHelm submodule bump on remotes  

Local agent prep for 0.3.0 is otherwise **complete** — remaining thin spots need
accounts (see runbook). Re-scan with `scripts/check_repo_hygiene.py` before publish.

## Do not commit

`dumps/`, `cx-corpora.*`, `*.tmx*`, `tmp/**`, `dist/**`, `*.vsix`, `*.whl`,
`gold/`, `eval/`, `lexaudit.config.local.yaml`.
