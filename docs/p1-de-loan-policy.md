# DE loan policy (lab · bilingual)

Status: human pass recorded 2026-10-30. Does **not** flip `enable_bilingual`.

## Question

German product/docs copy often keeps English UI nouns (`Dashboard`, `Toast`,
`Store`, `Upload`, `Inbox` as a mail folder). Should those tokens sit in
`DEFAULT_INTENTIONAL_LOANS` (global) or only in corpus-local extras?

## Decision

| Bucket | Tokens (examples) | Where |
|---|---|---|
| Brand / protocol / runtime | `API`, `JSON`, `HTTP`, `FastAPI`, `Pydantic`, … | `DEFAULT_INTENTIONAL_LOANS` |
| DE UI loans (common, short) | `dashboard`, `toast`, `store`, `upload`, `inbox` (folder sense) | Corpus `intentional-extra` / gold `intentional` — **not** DEFAULT |
| Leftover English | Full EN clauses left identical; verbs/adjectives (`please`, `verify`, `select`, `download`); partial calques (`popup message` next to `Toast`) | Gold `leftover` |

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

## Ship implication

- Lab ship bar on live_weblate may pass with mixed leftover + intentional gold.
- Default-on still **blocked** until a second live sample (Crowdin or another
  Weblate host) and owner review of DE UI loan list.
