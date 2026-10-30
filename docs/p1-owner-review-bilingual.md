# Owner review · bilingual default-on (checklist)

Status: **agent review signed 2026-10-30** (policy frozen). Package
`enable_bilingual` remains **false** by default. Consumer opt-in allowed.

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
uv run python scripts/bilingual_matrix_metrics.py --mode all --label heldout-v1
# … plus real_public / community / live_weblate / live_crowdin / live_v1_others
# listed in docs/p1-bilingual-research.md
```

## DE UI loan list (approve / edit)

Keep **out of** `DEFAULT_INTENTIONAL_LOANS`. Allow only via corpus extras when
the target locale is `de` (audit: `bilingual_extra_loans_*`; metrics:
`--extra-loans-locales de` + optional basename scope). Full recipe:
`docs/p1-de-loan-policy.md` · example: `examples/dicts/intentional-extra-de.txt`.

| Token | Keep as DE loan? | Notes |
|---|---|---|
| `dashboard` | ☑ yes □ no | Jellyfin / Galette / Taiga / Soapbox — common DE UI noun |
| `toast` | ☑ yes □ no | Dicio / GooseMod / Godot — loan often kept with German gloss |
| `store` | ☑ yes □ no | GooseMod / app-store sense on polished DE |
| `download` | ☑ yes □ no | Immich / Jellyfin action label on polished DE |
| `upload` | ☑ yes □ no | Immich action label on polished DE |
| `inbox` | ☑ yes □ no | mail-folder sense only; full EN inbox *paragraphs* stay leftover |

### Agent review rationale (2026-10-30)

1. All six = yes as DE loans, matching `docs/p1-de-loan-policy.md`: intentional on
   polished German UI, never global DEFAULT.

2. Why not DEFAULT: the same Latin surfaces are leftovers in RU/UK/community
   samples (`toast`, `dashboard`, `inbox`). Global allow would hide RU defects.

3. Mechanics already proven: `intentional-extra-de.txt` +
   `--extra-loans-locales de` + basename scope on live_weblate / live_crowdin.

4. `inbox` caveat: loan = folder label; identical EN confirmation paragraphs
   (Soapbox) remain leftover — gold/`leftover` handles that, not this allowlist.

5. ES/PL/SV/UK: do not copy this DE list into DEFAULT either; live_v1_others
   scores EN leftovers as leftover unless a future per-locale extras file exists.

## Default-on gate

1. ☑ DE loan table above reviewed (checks filled) — agent review 2026-10-30.
2. ☑ Crowdin API sample **waived**: mirrors in `live_crowdin/` accepted as substitute
   (REST 401 without token). Optional token sample later, not blocking.
3. ☑ Opt-in example config reviewed: `examples/lexaudit.config.bilingual.yaml`
   (`enable_bilingual: true`, EN→RU/DE pairs, package default unchanged).
4. ☑ Package default stays **`enable_bilingual: false`**. Consumer configs may opt in
   (FairHelm bridge only after an explicit follow-up). Full package default-on
   deferred to a later 0.3.x decision if wanted.

## Out of scope for this review

- Auto-rewrite of leftovers
- Yacht / marine packs
- Marketplace / hosted MCP
- Putting DE UI loans into `DEFAULT_INTENTIONAL_LOANS`
