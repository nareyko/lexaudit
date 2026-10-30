# CLI reference

**In plain words:** lexaudit is used from a terminal with short commands. The ones you need first are `doctor` (check your computer), `audit` (check your texts), and `explain` (why was this word flagged). All commands only read your files. Terms: [glossary](glossary.md).

All audit and ranking commands are **read-only** on corpus sources. They only write under `output_dir` (and optional curated queue / LLM label JSON / diff JSON).

`--config` is optional on all commands: if omitted, `lexaudit` auto-discovers `./lexaudit.config.yaml` in the working directory or falls back to zero-config Markdown documentation mode (`sources: [files]`).

```bash
uv sync
uv run lexaudit --help
```

When invoked as a submodule from a host repository root:

```bash
uv run --directory tools/lexaudit lexaudit <cmd> --config /abs/path/to/lexaudit.config.yaml ...
```

---

## `init`

Create a starter `lexaudit.config.yaml` and `dicts/` directory (`proper-names.yaml`, `acronyms.yaml`, `allowlist.yaml`) for a project.

```bash
uv run lexaudit init
uv run lexaudit init --dir ./my-docs --force
```

---

## `fetch-dicts`

Download the spelling dictionaries into your user cache (`~/.cache/lexaudit/dictionaries`, or the folder in `LEXAUDIT_DICT_DIR`). No admin rights, no `apt`, no `brew`. Each dictionary keeps its upstream license, saved next to it as `*.license.txt`.

```bash
uv run lexaudit fetch-dicts                 # all 7 languages (about 25 MB)
uv run lexaudit fetch-dicts --locale en --locale de
```

---

## `doctor`

Check environment readiness: confirms CPU-only mode (no GPU required), lists which of the 7 language dictionaries are installed (and tells you to run `fetch-dicts` if some are missing), reports whether the optional system `hunspell` program is present (if not, the built-in Python checker is used), checks `pymorphy3`, and counts bundled calque rules.

```bash
uv run lexaudit doctor
uv run lexaudit doctor --config ./lexaudit.config.yaml
```

---

## `audit`

Run full vocabulary inventory for one or more locales (across configured sources or specific `--path` files/folders).

```bash
uv run lexaudit audit --locale en
uv run lexaudit audit --path ./my-article.md --locale ru
uv run lexaudit audit --config ./lexaudit.config.yaml --locale en,de,es,pl,ru,sv,uk
uv run lexaudit audit --config ./lexaudit.config.yaml --locale ru --freeze-at 1970-01-01T00:00:00Z
```

Writes under `output_dir/<locale>/`:

| File | Content |
|---|---|
| `report.json` | Schema `v1` full document |
| `words.json` | Word list (agent-friendly) |
| `suspect.csv` | Anomaly inventory sorted by count |
| `pages.csv` | Ranked pages |
| `summary.md` | Status counts |
| `queue.md` / `queue.json` | Page rewrite queue |

---

## `rank`

Re-rank pages from an existing `words.json` report (without re-collecting sources).

```bash
# default: weighted mode from configuration
uv run lexaudit rank --locale ru

uv run lexaudit rank --locale ru --mode raw
uv run lexaudit rank --locale ru --mode weighted \
  --needles=orientir,denseness,чеклист --require-needle
uv run lexaudit rank --locale ru --sources=academy
uv run lexaudit rank --locale ru --sources=docs
uv run lexaudit rank --locale ru --curated /abs/path/rewrite-queue.md
```

| Flag | Effect |
|---|---|
| `--mode raw\|weighted` | Unique count vs weighted score (default `weighted`) |
| `--needles=a,b` | Boost / stem-family keys |
| `--require-needle` | Emit only pages matching at least one needle |
| `--sources=academy` | Filter by source bucket (`academy`, `model_pack` / `packs`, or `docs` / `files`) |
| `--curated PATH` | Append `pending` rows to Markdown or JSON queue (no duplicate slugs) |

---

## `expand-needle`

Find pages where a needle stem or glob appears in existing `words.json` reports.

```bash
uv run lexaudit expand-needle --needle orientir --locale en,de
uv run lexaudit expand-needle --needle 'чеклист*' --locale ru --json
uv run lexaudit expand-needle --needle denseness --locale all \
  --write-queue /abs/path/rewrite-queue-2.md
```

Standard output TSV: `locale path count status norm surface`.

---

## `label` (optional LLM)

Classify `weak`/`likely` words on top-ranked pages with disk caching. **No source writes.**  
Supports local endpoints (Ollama / LocalAI) or cloud OpenAI-compatible APIs via `api_key_env` (default `OPENAI_API_KEY`).

```bash
uv run lexaudit label --locale ru \
  --top-pages 20 --top-words 50 --tiers likely,weak --profile cpu
```

Output: `output_dir/<locale>/llm-labels.json`.

---

## `eval product` / `eval regression`

```bash
uv run lexaudit eval product --config ./lexaudit.config.yaml
uv run lexaudit eval product --config ./lexaudit.config.yaml --k 10 --json
uv run lexaudit eval regression --config ./lexaudit.config.yaml
```

- **product** - `needle_recall`, `page@K` against `gold_slugs` from configuration, and suspect counts  
- **regression** - soft `CLEAR` / `FAIL` check per slug in `gold_slugs` (always exits `0`)

---

## `diff`

```bash
uv run lexaudit diff \
  --baseline ./tmp/lexaudit/ru/report.json \
  --current ./tmp/lexaudit/ru/report.json \
  --out /tmp/lexaudit-diff.json
```

Soft CI wrapper: `bash scripts/ci_soft_audit.sh` (never fails on new anomalies).

---

## `explain`

Explain how a single word is classified (`ok`, `proper`, `acronym`, `foreign`, `calque`, `suspect`), which detectors fired, and what editorial hint applies.

```bash
uv run lexaudit explain orientir --locale en
uv run lexaudit explain предпокупочный --locale ru --json
```

---

## `ping`

```bash
uv run lexaudit ping
# -> lexaudit 0.1.0
```
