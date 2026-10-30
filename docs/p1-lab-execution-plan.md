# P1 lab execution plan (local only · no PyPI / no marketplace)

Status: **complete locally** (2026-10-30). Not part of the 0.2.0 Release assets.
Follow-ups done locally: real_public → community → live Weblate + DE loan policy.
`enable_bilingual` still false pending owner go / optional Crowdin sample.

## Goal

Finish three lab tracks with **measurable** outcomes, then run project gates
(pytest, anti-AI deslop, self-lexaudit). Ship decision for 0.3.0 stays with owner.

## Tracks

### A. Domain packs (non-yacht)

1. Corpus hunt notes + cited public sources (SaaS UI, fintech, developer docs).
2. Seed packs under `packs/_lab/{saas-ui-v0,fintech-v0,developer-docs-v0}/` with
   20–40 rules for `en`/`de`/`ru` (other locales thin stubs).
3. Mini stratified fixtures (clean / known defect / open-set) per pack.
4. `scripts/lab_pack_metrics.py` → known-rule recall + clean FP count.
5. Report in `docs/p1-domain-packs-research.md` (ship / iterate / drop).

**Ship bar:** known-rule recall ≥ 0.85 on pack fixture; clean pages not ranked above defects for known rules. No Release upload until owner go.

### B. Bilingual MD pairs (research + tests)

1. Protocol doc: annotation schema, intentional-loan allowlist, held-out split.
2. Fixtures: `tests/fixtures/bilingual/{train,heldout}/{en,ru,de}/`.
3. Gold CSV for held-out leftovers vs intentional English.
4. `scripts/bilingual_metrics.py` → precision / recall / F1 on held-out.
5. Detector: Latin-leak + allowlist; length-ratio logged, not failing.
6. Pytest covering protocol fixtures; `enable_bilingual` stays default `false`.

**Ship bar:** held-out precision ≥ 0.75 and recall ≥ 0.60 before considering default-on.

### C. MCP / VS Code (local dogfood only)

1. Document stdio MCP config (no hosting).
2. Minimal VS Code extension: shell-out to CLI, Problems from findings JSON.
3. Smoke: import MCP server; `lexaudit --help` via extension README commands.
4. No Marketplace / Glama / Smithery publish.

## Project gates (mandatory)

1. `ruff` + `mypy --strict` + `pytest` in `tools/lexaudit`.
2. Anti-AI deslop scan on README + `docs/**` (ban list + bold spam).
3. `lexaudit audit --check` on package docs with project allowlist.

## Out of scope

- Auto-rewrite, yacht packs, PyPI 0.3.0, Marketplace publish, hosted SaaS.
