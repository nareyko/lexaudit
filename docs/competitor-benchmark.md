# Competitor benchmark (v0.4 Stage V6-1)

Generated: `2026-11-03T15:38:29Z`

Same gold set: synthetic-demo **42 pages** (7 locales × 6) + `gold/real_bench` consensus anomalies.

## Summary table

| Tool | Available | Backend | Word P | Word R | Page P@3 | Clean FP / 1k | Time |
|---|---|---|---:|---:|---:|---:|---:|
| lexaudit | yes | run_locale_audit | 10.7% | 92.9% | 100.0% | 35.7 | 5.53s |
| hunspell | yes | HunspellChecker | 5.7% | 58.5% | 33.3% | 73.1 | 8.47s |
| cspell | yes | /home/vadim/.nvm/versions/node/v24.12.0/bin/npx --yes cspell | 2.4% | 95.4% | 0.0% | 436.4 | 6.16s |
| vale | skipped (vale binary not found) | — | N/A | N/A | N/A | N/A | N/A |
| languagetool | skipped (language_tool_python not importable and no local server on :8010) | — | N/A | N/A | N/A | N/A | N/A |

## How to read this honestly

- **LanguageTool** usually wins on *grammar / agreement / punctuation* — that is not
  lexaudit's product job. When LT is available, expect higher generic flag volume and
  better catch-rate on GEC typos, not on bilingual calques.
- **lexaudit** wins on *calque / false-friend ranking*, domain allowlists, lower
  clean-page FPR, and rewrite-queue **page P@3** (weighted scores on the synthetic
  42-page gold). Spellcheckers that only count OOV tokens often bury planted calques
  under jargon-heavy clean pages — compare Clean FP / 1k and P@3 in the table.
- **Hunspell / cspell / Vale** are useful baselines. They do not ship FairHelm
  (or your) domain lists, and they do not rank a multi-page corpus for a rewrite agent.
- Rows marked **skipped** mean the binary/package was missing on the runner.
  CI should call `python scripts/benchmark_competitors.py --lexaudit-only` so the
  table still materializes without installing competitors.

## Reproduce

```bash
uv run python scripts/benchmark_competitors.py
uv run python scripts/benchmark_competitors.py --lexaudit-only  # CI / smoke
```

Machine snapshot: `{"hunspell": true, "cspell": true, "vale": false, "languagetool": false, "lexaudit": true}`
