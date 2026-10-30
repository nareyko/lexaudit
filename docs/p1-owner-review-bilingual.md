# Owner review · bilingual default-on (checklist)

Status: **awaiting owner**. Lab evidence is ready; `enable_bilingual` stays false
in shipped defaults until this page is signed off.

## Evidence already in-repo

| Corpus | Path | Ship bar (lab) |
|---|---|---|
| Synthetic held-out | `tests/fixtures/bilingual/heldout/` | pass |
| Held-out **V1 matrix** (42 pairs · en/de/pl/ru/es/sv/uk) | same + `es/pl/sv/uk` + `german-leak.md` | pass (26 scored; ship_all) |
| Official docs + seeded | `tests/fixtures/bilingual/real_public/` | pass (EN→*) |
| Community reconstructions | `tests/fixtures/bilingual/community/` | pass (EN→*) |
| Live Weblate | `tests/fixtures/bilingual/live_weblate/` | pass (EN→*) |
| Crowdin-via-GitHub | `tests/fixtures/bilingual/live_crowdin/` | pass (EN→*) |
| Live V1 others (es/pl/sv/uk Weblate) | `tests/fixtures/bilingual/live_v1_others/` | pass (en→es/pl/sv/uk) |
| DE loan policy | `docs/p1-de-loan-policy.md` | recorded |

Reproduce:

```bash
uv run python scripts/bilingual_metrics.py
uv run python scripts/bilingual_matrix_metrics.py --out tmp/bilingual-matrix/heldout.json
# … plus real_public / community / live_weblate / live_crowdin commands
# listed in docs/p1-bilingual-research.md
```

## DE UI loan list (approve / edit)

Keep **out of** `DEFAULT_INTENTIONAL_LOANS`. Allow only via corpus extras /
config allowlist when the target locale is `de` and the page is polished UI:

| Token | Keep as DE loan? | Notes |
|---|---|---|
| `dashboard` | □ yes □ no | Jellyfin / Galette / GnuCash |
| `toast` | □ yes □ no | Dicio / GooseMod |
| `store` | □ yes □ no | GooseMod |
| `download` | □ yes □ no | Immich / Jellyfin action label |
| `upload` | □ yes □ no | Immich |
| `inbox` | □ yes □ no | mail folder sense only |

## Default-on gate (all must be yes)

1. □ DE loan table above reviewed (checks filled).
2. □ Optional: authenticated Crowdin API sample accepted or explicitly waived.
3. □ Opt-in example config reviewed (`examples/lexaudit.config.bilingual.yaml`).
4. □ Owner sets `enable_bilingual: true` only in consumer configs first — package
   default remains false until a later minor (0.3.x) decision.

## Out of scope for this review

- Auto-rewrite of leftovers
- Yacht / marine packs
- Marketplace / hosted MCP
