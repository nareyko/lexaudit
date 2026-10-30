# lexaudit next-wave plan · 2026-10-30

Research-backed plan for the five open thin spots. Local only until publish go.
Detection stays detection-only (no auto-rewrite). Yacht packs stay out of public.

## Research inputs (fetched 2026-10-30)

| Topic | Sources | Takeaway for lexaudit |
|---|---|---|
| Parallel / wiki text | [Wikimedia Content Translation dumps & API](https://www.mediawiki.org/wiki/Content_translation/Published_translations); Wikipedia REST `page/summary`; OPUS | Prefer CX corpora (`source`+`user`, `striphtml`) or short summary extracts with CC BY-SA attribution; do not scrape HTML wholesale |
| Untranslated QA | ChatsControl untranslated check; Shipglot; eduKateSG QA profiles; Vexy QA gate notes | Identical source/target = warning with narrow allowlists (brands, URLs, acronyms) + reasons; avoid allowlist creep; track FP rate per check |
| Loanwords / cross-lingual | COLING 2022 loanword detection; bilingual lexicon from comparable corpora | Cognate ≠ leftover; crosslocale should use paired/comparable norms + optional phonetic/orthographic similarity, not embeddings on the audit path |
| MCP registry | [Official registry requirements](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/official-registry-requirements.md); auth namespaces `io.github.*` | PyPI first; `server.json` name must match GitHub namespace; description ≤100 chars; package ownership verified |
| VS Marketplace | [Publishing Extensions](https://code.visualstudio.com/api/working-with-extensions/publishing-extension) | Publisher account; no user SVG icon; HTTPS images; `vsce package` then publish; prefer Trusted Publishing / OIDC over long-lived PAT |

Probe already run: 9 Wikipedia summaries (API/SaaS/e-commerce × en/ru/de) →
`tests/fixtures/packs_wild/` (CC BY-SA attributed).

---

## Track A · Pack proof ≠ чужой сайт

### Problem
Lab + `packs_field` still seed pack-owned coinages. Marketplace needs evidence on
**external** prose.

### Approach (phased)

| Phase | What | Bar |
|---|---|---|
| A0 (done seed) | Wikipedia REST summaries → `packs_wild` | Attributed extracts on disk |
| A1 | Script `scripts/fetch_wiki_pack_samples.py` (UA, rate-limit, license footer) | Reproducible refresh |
| A2 | Expand topics per pack (3–5 pages × en/de/ru) from public encyclopedic/docs pages | ≥30 wild files |
| A3 | Optional CX dump slice (en→ru/de) for bilingual leftovers — not for calque packs | Documented dump URL + sample id list |
| A4 | Metrics: monolingual audit with each pack’s rules on wild text → precision of calque hits (manual gold sample N≥50) + clean rank sanity | Report + SVG; no silent “recall 1.0” on self-seeds |

### License / ethics
- Wikipedia: CC BY-SA — keep URL + license line in every file (as in seed).
- No full article dumps in git; short extracts only.
- Prefer reconstruct + attribute over verbatim long quotes from commercial docs.

### Best-practice alignment
Field eval must separate **recall on planted defects** from **precision on wild hits**.
Wild hits without gold are exploratory until a human labels a sample.

---

## Track B · Bilingual precision

### Problem
Token-overlap leftovers: high recall, noisy on shells/brands. Default-on blocked.

### How we solve it (layers)

1. Deterministic suppressions (ship)  
   Already: function-stop, intentional loans, kebab≥2, `DEFAULT_TEMPLATE_CHROME`.  
   Next: per-project extras (already DE UI); optional `bilingual_chrome_path` file;
   skip URLs/emails/code spans if not already stripped in tokenize.

2. Segment-level identical check (new, soft)  
   Industry practice: flag target≈source segment, not only shared tokens.  
   Emit `bilingual-identical-segment` at likely tier; allowlist brands with reasons.

3. Length-ratio escalate (existing soft → rank)  
   Wire soft length-ratio into page score when bilingual on (documented weight).

4. Cyrillic→Latin harvest  
   Grow `tests/fixtures/bilingual/cyrillic_to_latin/` from CX en↔ru samples
   (user≠source Cyrillic left in EN, or EN left in RU — both directions labeled).

5. FP budget  
   Per research: if a check’s FP rate is about 10%+ on held-out gold, narrow it or demote
   severity — do not disable globally without a reason log.

6. Default policy  
   Stay `enable_bilingual: false` until: chrome+segment checks green on live_* gold
   and FairHelm dogfood top-20 leftovers look like real prose defects.

### Non-goals
Embeddings in audit path; auto-rewrite of leftovers.

---

## Track C · Crosslocale usefulness

### Problem
Dogfood on field EN+RU: **no meaningful status delta**. Flag is wired but inert
for consumers.

### Root cause (code)
`make_crosslocale_detector` only boosts suspects with **no** norm in the reference
locale vocab. On encyclopedic/UI trees, most Latin suspects already appear in EN
norms → boost never fires. Path pairing also requires same path+scope; academy
materialize paths differ by locale folder.

### How we solve it

| Option | Idea | Verdict |
|---|---|---|
| C1 | Same-slug pairing for academy/wiki (ignore locale folder in path key) | Do first — unlocks real pairs |
| C2 | Boost only when reference locale marks token `ok`/`proper` but target marks `suspect` (true “foreign to target, normal in EN”) | High value; matches loanword intuition |
| C3 | Soft cognate filter: if token is near-identical orthography in both and ok in EN, demote leftover (anti-cognate FP) | Helps bilingual more than crosslocale |
| C4 | Keep embeddings off audit path; optional offline cache remains lab-only | Keep |

### Success bar
On a paired EN/RU wild or academy corpus: with C1+C2, suspect/likely counts or
page order **change in a documented, precision-positive way**; else leave docs as
“experimental / usually off”.

---

## Track D · Product shell (plan in repo)

Checklist artifact: `docs/p1-product-shell-checklist-2026-10-30.md` (this section
is the plan; checklist file is the executable owner list).

### VS Code Marketplace
1. Create publisher id (match `package.json` `publisher`: `nareyko`)
2. PNG icon 128×128 (no SVG); marketplace banners HTTPS only
3. `repository` / `bugs` / `homepage` already set — verify live GitHub URL after push
4. Privacy / license MIT already copied into extension folder
5. `vsce package` (done locally) → `vsce publish` after PyPI so CLI install docs work
6. Prefer GitHub Actions Trusted Publishing over long-lived PAT
7. Open VSX mirror optional same `.vsix`

### MCP registry
1. Publish `lexaudit` to PyPI with `[mcp]` extra
2. Align `packages/mcp-lexaudit/server.json`:
   - `name`: `io.github.nareyko/lexaudit` (GitHub auth namespace)
   - description ≤100 characters
   - package `registryType: pypi`, identifier `lexaudit`, version pinned
3. `mcp-publisher login` (GitHub) → `publish`
4. Add unit smoke for tool registration without live LLM

### CI / quality shell
- Quarantine `test_localai_smoke_*` behind env flag / skip if `:8501` unhealthy
- Document `uv sync --extra dev` for pytest (avoid host pytest shadowing)

---

## Track E · Rules / quality

| Item | Action |
|---|---|
| Phrase calques | Add 5–10 multiword rules per core locale from live_* / glossary defects |
| Pack DE gaps | Keep developer-docs DE ≥12; spot-check other packs’ de/ru density annually |
| Wild precision pass | After A2: label 50 wild calque hits → tune or drop noisy patterns |
| Hapax floor | Add regression: long coinage likely; short alnum codes stay weak; no FP spike on wiki wild |
| Fixtures | Add `02-clean-domain.md` per pack locale (ordinary domain words, no coinages) |
| Status | Flip pack `release-candidate` → `release` only after PyPI |

---

## Execution order (recommended)

```text
1. A1 fetch script + expand packs_wild (A2)          ✅ 2026-10-30
2. B segment-identical + chrome path; cyrillic grow  ✅ 2026-10-30
2b. B length-ratio + URL/code strip                  ✅ 2026-10-30
2c. B5 FP budget + C3 cognate soft demote            ✅ 2026-10-30
3. C1 slug pairing + C2 ref_present; re-dogfood      ✅ 2026-10-30
4. E phrase rules + hapax + 02-clean-domain          ✅ 2026-10-30
4b. A3 CX dump harvest (ids + tiny fixtures)         ✅ 2026-10-30
4c. A4/E clean+wild sanity + pack density gate       ✅ 2026-10-30
5. D agent shell (icon/docs/MCP smoke)               ✅ 2026-10-30
5b. D Trusted Publishing workflow stub               ✅ 2026-10-30
5c. D density×7 + hygiene CI + owner runbook         ✅ 2026-10-30
5d. C2 crosslocale `ref_ok` mode                     ✅ 2026-10-30
5e. Version sync + RU phrases + docs index           ✅ 2026-10-30
5f. D checklist items that need accounts             ⏳ owner
6. Publish go (PyPI → MCP → Marketplace → tag/push)  ⏳ owner
```


## Explicitly deferred
- Bilingual / crosslocale package default-on
- Auto-rewrite
- Yacht / marine packs in public
- Full CX dump in git
