# Status after research · next wave · 2026-10-30

## Snapshot

| Area | State |
|---|---|
| Package version | 0.3.0 local (not on PyPI) |
| Lab / RC packs | 10 promoted; lab metrics failed=0 |
| Pack field (seeded held-out) | mean recall 0.975 |
| Pack wild (Wikipedia) | 33 CC BY-SA slug summaries in `tests/fixtures/packs_wild/` (~288K) |
| Bilingual | opt-in; identical-segment + `bilingual_chrome_path`; default false |
| Crosslocale | opt-in; `ref_present` mode + slug pairing helpers; default false |
| Product shell | `.vsix` + `server.json` ready; Marketplace/MCP not published |
| Plan | `docs/p1-next-wave-plan-2026-10-30.md` |

## What we researched (local, no accounts)

- Wikimedia Content Translation: keep dumps out of git (`.gitignore` `dumps/`, `*.tmx`, `cx-corpora.*`)
- Wikipedia REST summaries as legal short extracts (fetch script + prune stale title-named files)
- Industry untranslated QA: narrow allowlists + reasons; FP budget ~10%
- Loanword literature: prefer ok-in-EN / suspect-in-target (`ref_present`)
- MCP registry + VS Marketplace publish requirements (owner-only later)

## Thin spots → done locally this wave

| Thin spot | Fix landed |
|---|---|
| Pack proof on wild text | `fetch_wiki_pack_samples.py` + 33 pages + `run_pack_wild_metrics.py` + `p1-pack-wild-eval` |
| Bilingual noise | `identical_segment_leftovers` + chrome path + cyrillic onboarding fixtures |
| Crosslocale inert | `ref_present` default mode; slug pairing; dogfood tracks `crosslocale_hits` / `delta_likely` |
| Phrase / hapax | phrase seeds in en/de/ru calques; hapax wild sanity test |
| LocalAI smoke flake | gated by `LEXAUDIT_LOCALAI_SMOKE=1` + health |
| Repo bloat | prune title-named wiki dupes; ignore dumps / tmp metrics / vsix / whl |

## Still owner-only (external accounts)

1. PyPI publish 0.3.0  
2. MCP registry + VS Marketplace  
3. Git remote push after publish go  

## Reproduce local artifacts

```bash
uv run python scripts/fetch_wiki_pack_samples.py   # network; writes short extracts only
uv run python scripts/run_pack_wild_metrics.py      # tmp/ + docs report
uv run python scripts/run_crosslocale_dogfood.py
uv run python scripts/run_pack_field_metrics.py
```

Do **not** commit: `dumps/`, CX dumps, `tmp/**`, `*.vsix`, `*.whl`, `gold/`, `eval/`.
