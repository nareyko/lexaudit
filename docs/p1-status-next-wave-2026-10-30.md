# Status after research · next wave · 2026-10-30

## Snapshot

| Area | State |
|---|---|
| Package version | 0.3.0 local (not on PyPI) |
| Lab / RC packs | 10 promoted; DE/RU density ≥12 (spot-check OK) |
| Pack field | recall gold + `01-clean` + `02-clean-domain` × 10 packs × en/de/ru |
| Pack wild | 33 CC BY-SA Wikipedia summaries; calque hits ≈0 (expected encyclopedic) |
| Bilingual | identical-segment + length-ratio soft + URL/code strip + chrome path |
| Crosslocale | `ref_present`; dogfood +23 likely; default false |
| CX research | dump in `dumps/` (gitignored); ids + trimmed `cx_samples/` fixtures |
| Product shell | icon.png, server.json OK, MCP tool smoke, privacy README |
| Plan | `docs/p1-next-wave-plan-2026-10-30.md` |

## Local thin spots closed this session

| Item | Landing |
|---|---|
| B length-ratio → ranking signal | `length_ratio_leftovers` (weak foreign) |
| B URL/email/code noise | `strip_urls_emails_code` before leftover scans |
| E clean-domain fixtures | 30× `02-clean-domain.md` via writer script |
| A3 CX without repo bloat | notes + harvest script; dump gitignored |
| D shell checklist (agent) | icon, docs, MCP tool list smoke, privacy |
| Hygiene | parent ignores `lexaudit.config.local.yaml`; dumps stay out |

## Still owner-only

1. PyPI publish 0.3.0  
2. MCP registry + VS Marketplace (`vsce publish`)  
3. Git remote push / tag after publish go  

## Do not commit

`dumps/`, `cx-corpora.*`, `*.tmx*`, `tmp/**`, `*.vsix`, `*.whl`, `gold/`, `eval/`,
`lexaudit.config.local.yaml`.
