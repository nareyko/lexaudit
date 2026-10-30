# Status after research · next wave · 2026-10-30

## Snapshot

| Area | State |
|---|---|
| Package version | 0.3.0 local (not on PyPI) |
| Lab / RC packs | 10 promoted; lab metrics failed=0 |
| Pack field (seeded held-out) | mean recall 0.975 |
| Pack wild (Wikipedia seed) | 9 CC BY-SA summaries in `tests/fixtures/packs_wild/` |
| Bilingual | opt-in; chrome stop shipped; default false |
| Crosslocale | opt-in; dogfood no delta; default false |
| Product shell | `.vsix` + `server.json` ready; Marketplace/MCP not published |
| Plan | `docs/p1-next-wave-plan-2026-10-30.md` |

## What we researched

- Wikimedia Content Translation API/dumps for parallel leftovers
- Wikipedia REST summaries as legal short extracts (probe succeeded for API / SaaS / e-commerce × en/ru/de)
- Industry untranslated QA: narrow allowlists + reasons; FP budget ~10%
- Loanword literature: do not confuse cognates with leftovers; prefer ok-in-EN / suspect-in-target
- MCP registry + VS Marketplace publish requirements

## Still thin → how to fix

| Thin spot | Why it matters | Fix (from plan) |
|---|---|---|
| Pack proof on wild text | Marketplace reputation | Expand `packs_wild` + precision gold on hits (Track A) |
| Bilingual noise | Opt-in trust | Segment-identical check + cyrillic harvest + FP budget (Track B) |
| Crosslocale inert | Dead feature risk | Same-slug pairing + boost when ok in EN / suspect in target (Track C) |
| Shell unpublished | Distribution | Owner accounts + checklist (Track D) |
| Phrase / hapax / fixtures | Detector depth | Phrase seeds, wiki hapax regression, extra clean fixtures (Track E) |
| LocalAI smoke flake | CI noise | Gate behind env + health (Track D) |

## Not thin / locked

- Detection-only (no rewrite)
- No yacht packs in public
- Bilingual & crosslocale stay default false until bars in the plan pass
- Push remotes only after publish go

## Immediate next (implementation)

1. `fetch_wiki_pack_samples.py` + expand wild corpus  
2. Crosslocale C1+C2 + re-dogfood  
3. Bilingual segment-identical soft detector  
4. Quarantine LocalAI smoke; MCP unit smoke  
5. Owner: PyPI / MCP / Marketplace when ready  

## Reproduce research artifacts

```bash
# Wikipedia seed already under tests/fixtures/packs_wild/
uv run python scripts/run_pack_field_metrics.py
uv run python scripts/run_crosslocale_dogfood.py
uv run python scripts/render_field_eval_charts.py
```
