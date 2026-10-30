# Owner review · bilingual default-on (checklist)

Status: **awaiting owner**. Lab evidence is ready; `enable_bilingual` stays false
in shipped defaults until this page is signed off.

## Evidence already in-repo

| Corpus | Path | Ship bar (lab) |
|---|---|---|
| Synthetic held-out | `tests/fixtures/bilingual/heldout/` | pass |
| Official docs + seeded | `tests/fixtures/bilingual/real_public/` | pass |
| Community reconstructions | `tests/fixtures/bilingual/community/` | pass |
| Live Weblate | `tests/fixtures/bilingual/live_weblate/` | pass |
| Crowdin-via-GitHub | `tests/fixtures/bilingual/live_crowdin/` | pass (this pass) |
| DE loan policy | `docs/p1-de-loan-policy.md` | recorded |

Reproduce:

```bash
uv run python scripts/bilingual_metrics.py
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
