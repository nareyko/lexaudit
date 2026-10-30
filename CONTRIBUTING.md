# Contributing

`lexaudit` is created and maintained by **Vadim Nareyko** ([github.com/nareyko](https://github.com/nareyko)) under the **MIT License**. By contributing you agree your patches are licensed under the same terms. See [docs/licensing.md](docs/licensing.md) for the hosted-service AGPL note.

## Development setup

```bash
uv sync --extra dev
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict src/
uv run pytest
uv run python scripts/crap_report.py
uv run mutmut run && uv run python scripts/check_mutation_score.py --min-percent 80
```

## pre-commit

```yaml
repos:
  - repo: https://github.com/nareyko/lexaudit
    rev: v0.2.0
    hooks:
      - id: lexaudit
        args: ["--locale", "en"]
```

## Rules

- Detection only - never write auto-replacements into source corpora.
- Do not commit host dictionaries, structured corpus exports, or local `gold/` and `eval/` directories.
- Prefer tests that kill mutants over coverage-only assertions.
- Public documentation and examples must not contain absolute host paths (`/home/...`).
- Do not publish yacht/marine domain packs from this repository.
