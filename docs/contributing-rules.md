# Contributing a calque / false-friend rule

Detection-only: rules flag words; they never rewrite the user’s files.

## Checklist

1. **Locale file** — edit `rules/calques/<locale>.yaml` (one of `en`, `de`, `es`, `pl`, `ru`, `sv`, `uk`).
2. **Fields (required for new rules)**
   - `pattern` — token, glob (`*`), or multi-word phrase
   - `locale`
   - `kind` — `calque` or `false_friend`
   - `source_lang` — language the loan came from (e.g. `en`, `ru`)
   - `hint` — preferred rewrite (plain words)
   - `severity` — `confirmed` | `likely` | `weak`
   - `positive_examples` — ≥1 sentence where the rule **must** fire (write your own; no book quotes)
   - `negative_examples` — ≥1 sentence where it **must not** fire
3. **Context (when the word is also legitimate)** — use `context_require` / `context_forbid` so common words (`actualmente`, `realisieren`, `ewentualnie`, …) only match in the false sense.
4. **`override_ok: true`** — only when Hunspell accepts the form but the sense is still a calque (`denseness`, …).
5. **Tests** — `uv run pytest tests/test_calque_examples_contract.py -q` must stay green.
6. **Clean FPR** — if you touch high-frequency tokens, re-check real-clean:
   `uv run python scripts/build_real_benchmark.py --fpr-only` (or audit `tests/fixtures/real_bench/clean`).
7. **Do not** commit Wiktionary dumps; use `scripts/mine_calques_wiktionary.py` into `tmp/mined-calques/` then curate by hand.

## Issue template

Open a “Calque rule” issue via `.github/ISSUE_TEMPLATE/calque-rule.yml`.
