# DE loan policy (lab · bilingual)

Status: agent review signed 2026-10-30 (`docs/p1-owner-review-bilingual.md`).
Does **not** flip package `enable_bilingual` default.

## Question

German product/docs copy often keeps English UI nouns (`Dashboard`, `Toast`,
`Store`, `Upload`, `Inbox` as a mail folder). Should those tokens sit in
`DEFAULT_INTENTIONAL_LOANS` (global) or only in corpus-local extras?

## Decision

| Bucket | Tokens (examples) | Where |
|---|---|---|
| Brand / protocol / runtime | `API`, `JSON`, `HTTP`, `FastAPI`, `Pydantic`, … | `DEFAULT_INTENTIONAL_LOANS` |
| DE UI loans (common, short) | `dashboard`, `toast`, `store`, `upload`, `download`, `inbox` (folder sense) | Corpus `intentional-extra` / gold `intentional` — **not** DEFAULT |
| Leftover English | Full EN clauses left identical; verbs/adjectives (`please`, `verify`, `select`); partial calques (`popup message` next to `Toast`) | Gold `leftover` |

Rationale: putting DE UI loans into DEFAULT would hide RU leftovers that reuse the
same Latin surface (`toast`, `inbox`, `dashboard`) on imperfect community and
live Weblate samples.

## Evidence (live Weblate · hosted.weblate.org · 2026-10-30)

| Signal | Example | Policy read |
|---|---|---|
| Identical EN string in RU | Soapbox `Onboarding complete` | leftover |
| Loan kept, gloss added | Dicio RU `Toast (всплывающие сообщения)` | `toast` leftover for RU; DE single `Toast` may be intentional |
| DE keeps Dashboard | Galette / GnuCash / Webmin strings | intentional on polished DE pages |
| DE keeps Store + Toast compound | GooseMod `Toast-Benachrichtigung` / `Store` | `store` intentional; compounds may evade exact token match |
| Full EN paragraph untranslated | Soapbox inbox confirmation; Navigate CMS marketplace | leftover (high-severity) |

Fixtures: `tests/fixtures/bilingual/live_weblate/` (+ `SOURCES.md`).

## Evidence (Crowdin-synced GitHub mirrors · 2026-10-30)

| Signal | Example | Policy read |
|---|---|---|
| DE keeps Dashboard | Jellyfin Web `Dashboard > Libraries` | intentional on polished DE |
| DE keeps Download / Upload | Immich / Jellyfin action labels | intentional on polished DE |
| RU still has Dashboard leftover | Jellyfin RU fixture wrap | leftover (do not globalize DE loans) |

Fixtures: `tests/fixtures/bilingual/live_crowdin/` (+ `SOURCES.md`).
Crowdin REST API itself needs a token (401); mirrors substitute for this pass.

## Ship implication

- Lab ship bars on live_weblate / live_crowdin may pass with mixed leftover +
  intentional gold when extras are basename-scoped.
- Default-on still **blocked** until owner signs
  `docs/p1-owner-review-bilingual.md`.
