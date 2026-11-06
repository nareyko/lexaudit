# lexaudit

**Finds odd, wrong or copied-from-another-language words in your texts, and tells you which pages to fix first.**

<!-- mcp-name: io.github.nareyko/lexaudit -->

## In plain words

You write or translate articles, courses or documentation. A normal spellchecker shouts about every brand name, abbreviation and long German word, and still misses the words that really hurt: a word copied from another language ("calque"), a real word used with the wrong meaning ("false friend"), or a word someone invented.

lexaudit reads your files, ignores the harmless things, and gives you a short ranked list: "look at this page first." It runs on an ordinary laptop in about a second. No graphics card, no internet, no account.

It only reports. It never changes your texts.

Unknown terms? See the [glossary](docs/glossary.md).  
0.3.0 prep and publish path: [docs/p1-INDEX.md](docs/p1-INDEX.md).

- Languages: English (`en`), German (`de`), Spanish (`es`), Polish (`pl`), Russian (`ru`), Swedish (`sv`), Ukrainian (`uk`)
- Hardware: CPU only
- Author: Vadim Nareyko ([github.com/nareyko](https://github.com/nareyko), Founder at [Arviser Sp. z o.o.](https://arviser.com/#open-proof))
- License: dual MIT package and AGPL-3.0-or-later hosted SaaS ([details](docs/licensing.md))

![How lexaudit works](docs/images/overview.svg)

---

## Try it in 30 seconds

```bash
pipx run lexaudit audit --path . --locale en --check
# or: uvx lexaudit audit --path . --locale en --check
```

Missing spelling dictionaries download automatically into your user cache. No GPU. No config file required. Exit code `1` means confirmed calques or invented words remain.

Optional helpers: `lexaudit doctor`, `lexaudit fetch-dicts`, `lexaudit init`.

### Check a file or a whole project

```bash
# One file or folder, no settings file needed
uv run lexaudit audit --path ./README.md --locale en

# Or create starter settings first, then check everything
uv run lexaudit init
uv run lexaudit audit --locale en
```

### Open the report

The reports are in the output folder, one subfolder per language. Start with `queue.md`:

```markdown
| score | unique_suspects | path | top_words |
|---|---|---|---|
| 12.0 | 2 | docs/en/en-04-defect-known-calques.md | orientir surveyness |
| 6.0 | 1 | docs/en/en-05-defect-false-friend.md | denseness |
| 1.6 | 2 | docs/en/en-03-clean-unseen-jargon.md | vinylester haulout |
```

A higher score means "look here first". `top_words` shows the words behind the score.

### Ask why a word was flagged

```bash
uv run lexaudit explain orientir --locale en
```

```text
word: orientir (normalized: orientir, locale: en)
status: calque (tier: confirmed)
reason: loan-calque-orientir | detectors: calque, hunspell
editorial hint: working rule / ballpark / figures - not orientir
```

### Reproduce our test results

```bash
uv run lexaudit audit --config examples/synthetic-demo/lexaudit.config.yaml
```

Then open `tmp/synthetic-demo-out/<language>/queue.md`.

---

## How good is it? An honest answer

We built a 42-page test set in all 7 languages: 21 clean technical pages and 21 pages with planted problems. Some problems are known to the rules, some are brand new words the rules have never seen. Details: [docs/synthetic-benchmark.md](docs/synthetic-benchmark.md).

![Benchmark results](docs/images/synthetic-benchmark.svg)

| Setup | Bad page in top 2 | Bad page in top 3 | Recall@2 | Recall@3 | MAP (0 to 1, higher is better) | Known problems found | Brand-new neologisms found | Combined planted problems | Clean-page FP / 1k tokens | Time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A. Plain spellchecker | 0.0% | 23.8% | 0.0% | 23.8% | 0.389 | 0.0% (0/26) | 0.0% (0/7) | 0.0% (0/33) | 81.2 | 0.48 s |
| B. Plus your word lists | 7.1% | 23.8% | 4.8% | 23.8% | 0.421 | 0.0% (0/26) | 0.0% (0/7) | 0.0% (0/33) | 47.1 | 0.56 s |
| C. Full lexaudit | 100.0% | 100.0% | 66.7% | 100.0% | 1.000 | 100.0% (26/26) | 100.0% (7/7) | 100.0% (33/33) | 47.1 | 2.97 s |

What this means:

- Pages with known problems come first in every language. The plain spellchecker puts clean pages first.
- Known-rule problems: **100.0%** (26/26). Unseen single-occurrence neologisms (Zipf + char n-gram / affix-glue): **100.0%** (7/7). Combined planted problems (honest fraction): **100.0%** (33/33).
- With exactly 3 defective pages per locale, `Recall@2` is **66.7%** when the top-2 slots are both bad (`Precision@2` = **100.0%**). `Precision@3` / `Recall@3` are **100.0%** (singleton inventeds outrank repeated domain jargon).
- Clean-page false positives: **47.1** unique flagged words per 1000 tokens (36 unique FP / 764 tokens).
- Domain terms that recur on a page (or sit in H1/title) are tagged `domain-term-candidate`, nearly zero-weighted in ranking, and listed under Suggested glossary additions.





---

## Documentation

Start with [`docs/README.md`](docs/README.md).

| Guide | What you learn |
|---|---|
| [Glossary](docs/glossary.md) | Every term in plain words |
| [Benchmark](docs/synthetic-benchmark.md) | The 42-page test, step by step |
| [Architecture](docs/architecture.md) | What goes in, what comes out |
| [Pipeline](docs/pipeline.md) | The gates every word passes |
| [CLI reference](docs/cli-reference.md) | All commands |
| [Agent workflow](docs/agent-workflow.md) | From report to fixed page |
| [Scores and metrics](docs/weights-and-metrics.md) | How pages are scored |

![Word classification ladder](docs/images/classify-pipeline.svg)

---

## More commands

```bash
# Re-rank pages, filter by source (docs, academy, model_pack)
uv run lexaudit rank --locale ru --mode weighted --sources=docs

# Add every page that contains a known bad word to your to-do list
uv run lexaudit expand-needle --needle orientir --locale all \
  --write-queue /abs/path/to/rewrite-queue.md

# Optional: ask a language model for a second opinion (your own endpoint)
uv run lexaudit label --locale ru --top-pages 20 --top-words 50 --tiers likely,weak --profile cpu

# Compare two runs
uv run lexaudit diff --baseline .../report.json --current .../report.json --out /tmp/diff.json
```

---

## For contributors

Setup and checks:

```bash
uv sync --extra dev
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict src/
uv run pytest
uv run python scripts/crap_report.py
uv run mutmut run && uv run python scripts/check_mutation_score.py --min-percent 80
uv build
```

Test layers: unit and integration tests (branch coverage 80% or more), the 7-language benchmark, property-based fuzzing (Hypothesis), golden regression with a read-only check of your files, JSON Schema contract, complexity gate (CRAP), mutation testing (kill rate 80% or more).

Pictures in `docs/images` are generated from code: run `python scripts/render_diagrams.py` (needs Inkscape and Pillow). Never edit the JPG files by hand.

## License

| What | License |
|---|---|
| **PyPI / this repo’s code** (CLI, library, YAML rules, packs) | **[MIT](LICENSE)** — use in products and private SaaS is fine under MIT |
| **Intended future hosted multi-tenant network service** (not shipped here) | Policy text: [AGPL-3.0-or-later](LICENSE-AGPL-HOSTED.md) — **not** a second license on the MIT wheel |
| Benchmark corpora & fetched spelling dictionaries | [LICENSE-THIRD-PARTY.md](LICENSE-THIRD-PARTY.md) + upstream `*.license.txt` |

Full wording: [docs/licensing.md](docs/licensing.md). Adding rules: [docs/contributing-rules.md](docs/contributing-rules.md).

## Origin and author

Created and maintained by Vadim Nareyko ([github.com/nareyko](https://github.com/nareyko)). It grew out of auditing multilingual courses and encyclopedias at [FairHelm](https://fairhelm.com).
