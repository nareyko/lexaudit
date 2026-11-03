# Competitor benchmark (v0.4 Stage V6-1 / P4-2)

Generated: `2026-11-03T19:09:38Z`

Same gold set: synthetic-demo **42 pages** (7 locales × 6) + `gold/real_bench` consensus anomalies.

## Summary table

| Tool | Available | Backend | Word P | Word R | Page P@3 | Clean FP / 1k | Time |
|---|---|---|---:|---:|---:|---:|---:|
| lexaudit (strict: calque + invented + likely) | yes | run_locale_audit | 54.5% | 92.9% | 100.0% | 3.3 | 5.62s |
| lexaudit (full: all anomalies incl. weak suspects) | yes | run_locale_audit | 14.3% | 92.9% | 100.0% | 22.7 | 5.62s |
| hunspell | yes | HunspellChecker | 7.1% | 80.8% | 33.3% | 73.1 | 9.11s |
| cspell | yes | /home/vadim/.nvm/versions/node/v24.12.0/bin/npx --yes cspell | 2.9% | 97.3% | 0.0% | 436.4 | 6.55s |
| vale | yes | /home/vadim/projects/fairhelm-2026/tools/lexaudit/tmp/bin/vale | 10.5% | 84.9% | 0.0% | 50.2 | 3.34s |
| languagetool | yes | language_tool_python | 12.9% | 63.0% | 0.0% | 31.8 | 50.05s |

## How to read this honestly

- **lexaudit (strict)** counts only `calque` / `invented` plus `confirmed`/`likely`
  tiers — the CI / rewrite-queue precision view.
- **lexaudit (full)** includes weak `suspect` noise — maximum recall for triage,
  higher Clean FP / 1k by design.
- **LanguageTool** usually wins on *grammar / agreement / punctuation* — that is not
  lexaudit's product job. When LT is available, expect higher generic flag volume and
  better catch-rate on GEC typos, not on bilingual calques.
- **lexaudit** wins on *calque / false-friend ranking*, domain allowlists, lower
  clean-page FPR (strict mode), and rewrite-queue **page P@3**.
- **Hunspell / cspell / Vale** are useful baselines. They do not ship FairHelm
  domain lists, and they do not rank a multi-page corpus for a rewrite agent.
- Rows marked **skipped** mean the binary/package was missing on the runner.
  CI should call `python scripts/benchmark_competitors.py --lexaudit-only`.
- Portable Vale: place the Linux x86_64 binary at `tmp/bin/vale` (gitignored).

## Reproduce

```bash
uv run python scripts/benchmark_competitors.py
uv run python scripts/benchmark_competitors.py --lexaudit-only  # CI / smoke
```

Machine snapshot: `{"hunspell": true, "cspell": true, "vale": true, "languagetool": true, "lexaudit_strict": true, "lexaudit_full": true}`
