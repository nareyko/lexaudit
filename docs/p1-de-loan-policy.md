# DE UI loans: extras / allowlist (not DEFAULT)

Status: agent review signed 2026-10-30 (`docs/p1-owner-review-bilingual.md`).
Does **not** flip package `enable_bilingual` default.

## Meaning (one paragraph)

In polished German product UI, short English nouns are often kept on purpose
(`Dashboard`, `Toast`, `Store`, `Download`, `Upload`, `Inbox` as a mail folder).
They are intentional loans, not untranslated leftovers. lexaudit must not treat
them as leftovers by default: the package `DEFAULT_INTENTIONAL_LOANS` stays
brand/protocol-shaped (`API`, `JSON`, `HTTP`, ...). DE UI nouns enter only through
corpus extras (bilingual) and optionally a project allowlist (monolingual foreign
pass). Putting them in DEFAULT would hide the same Latin surfaces when they are
real leftovers in RU/UK/community samples.

## Two layers

| Layer | What it clears | Where |
|---|---|---|
| **Bilingual leftover** (EN↔DE pair overlap) | Shared Latin token not leftover for target `de` | `bilingual_extra_loans_path` + `bilingual_extra_loans_locales: [de]`, or metrics `--extra-loans` |
| **Monolingual foreign** | Same token not `foreign` on a DE page audited alone | `dicts/allowlist.yaml` → `locale_loans` (project-scoped; prefer commented until needed) |

| Bucket | Tokens (examples) | Where |
|---|---|---|
| Brand / protocol / runtime | `API`, `JSON`, `HTTP`, `FastAPI`, `Pydantic`, ... | `DEFAULT_INTENTIONAL_LOANS` |
| DE UI loans (common, short) | `dashboard`, `toast`, `store`, `upload`, `download`, `inbox` (folder sense) | Extras / gold `intentional` (not DEFAULT) |
| Leftover English | Full EN clauses; verbs/adjectives (`please`, `verify`); partial calques | Gold / report as leftover |

## Consumer recipe (audit)

1. Copy the example extras list:

```text
examples/dicts/intentional-extra-de.txt
```

2. Point your opt-in bilingual config at it (see
   `examples/lexaudit.config.bilingual.yaml`):

```yaml
enable_bilingual: true
bilingual_pairs:
  - source_locale: en
    target_locale: de
    source_root: ./docs/en
    target_root: ./docs/de
bilingual_extra_loans_path: ./dicts/intentional-extra-de.txt
bilingual_extra_loans_locales: [de]   # required; empty locales = no merge in audit
```

3. Keep `enable_bilingual: false` in the package / default project config.
4. Do **not** add these six tokens to `DEFAULT_INTENTIONAL_LOANS` in code.
5. `inbox`: loan = folder label only. Identical English *paragraphs* stay leftover.

## Lab metrics recipe

Same token file, scoped by locale and optional basenames:

```bash
uv run python scripts/bilingual_metrics.py \
  --fixtures tests/fixtures/bilingual/live_crowdin \
  --gold tests/fixtures/bilingual/live_crowdin/gold-leftovers.csv \
  --extra-loans tests/fixtures/bilingual/live_crowdin/intentional-extra-de.txt \
  --extra-loans-locales de \
  --extra-loans-basenames jellyfin-dashboard.md,immich-actions.md
```

Fixture twins: `tests/fixtures/bilingual/live_weblate/intentional-extra-de.txt`,
`live_crowdin/intentional-extra-de.txt`.

## Evidence (live Weblate, hosted.weblate.org, 2026-10-30)

| Signal | Example | Policy read |
|---|---|---|
| Identical EN string in RU | Soapbox `Onboarding complete` | leftover |
| Loan kept, gloss added | Dicio RU `Toast (всплывающие сообщения)` | `toast` leftover for RU; DE single `Toast` may be intentional |
| DE keeps Dashboard | Galette / GnuCash / Webmin strings | intentional on polished DE pages |
| DE keeps Store + Toast compound | GooseMod `Toast-Benachrichtigung` / `Store` | `store` intentional; compounds may evade exact token match |
| Full EN paragraph untranslated | Soapbox inbox confirmation; Navigate CMS marketplace | leftover (high-severity) |

## Evidence (Crowdin-synced GitHub mirrors, 2026-10-30)

| Signal | Example | Policy read |
|---|---|---|
| DE keeps Dashboard | Jellyfin Web `Dashboard > Libraries` | intentional on polished DE |
| DE keeps Download / Upload | Immich / Jellyfin action labels | intentional on polished DE |
| RU still has Dashboard leftover | Jellyfin RU fixture wrap | leftover (do not globalize DE loans) |

Crowdin REST API needs a token (401); mirrors substitute for this pass.

## Ship implication

- Lab ship bars on live_weblate / live_crowdin may pass with mixed leftover +
  intentional gold when extras are basename-scoped.
- Package default-on stays **blocked**; consumer opt-in is fine after this policy.
- ES/PL/SV/UK: do not copy the DE list into DEFAULT or into a shared extras file
  for those targets unless a separate per-locale review exists.
