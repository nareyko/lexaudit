# P1 lab: domain rule packs (not for yachting)

Status: research only. Not attached to the 0.2.0 release.

## Goal

Publish industry calque / false-friend packs that teams can install with
`lexaudit pack install …`, without shipping FairHelm marine content.

## Candidate industries (pick top 3 after corpus hunt)

| Industry | Why demand exists | Seed sources to mine |
|---|---|---|
| SaaS / product UI | AI translation of settings strings | Apple HIG glossaries, Material, Crowdin public style guides |
| Fintech / payments | Strict term lists, many EN loans | PSD2 glossaries, Stripe docs i18n issues |
| Healthcare / FHIR | Safety-critical wording | HL7 terminology, WHO style |
| Legal / compliance | False friends across EN-DE-FR | EU IATE excerpts (public), DGT style |
| E-commerce checkout | High-volume MT leftovers | Shopify Polaris translations, OpenCart locale bugs |
| Developer docs / API | Markdown docs-as-code | Microsoft Writing Style, Google developer docs |

## Method

1. Collect 50–100 public bilingual examples per industry (issues, changelogs, style guides).
2. Extract recurring wrong tokens (not full phrases unless rule-safe).
3. Cap at 20–40 rules per locale; severity mostly `likely`.
4. Build a mini stratified fixture like `examples/synthetic-demo` (clean vs defective).
5. Measure known-rule recall and open-set gap before any release.

## Hard rules

- No yacht / marine / survey-boat pack in the public repo.
- MIT license for packs.
- Keep packs under `packs/_lab/` until precision is measured; do not attach to GitHub Releases with 0.2.0.

## Next experiment

Draft empty pack shells for `saas-ui-v0` and `fintech-v0` under `packs/_lab/` once seed lists exist.
