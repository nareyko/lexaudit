# Contributing

`lexaudit` is created and maintained by **Vadim Nareyko**
([github.com/nareyko](https://github.com/nareyko)).

## Dual license

| Contribution surface | License |
|---|---|
| Package code, docs, YAML rules, packs in this repository | **MIT** ([LICENSE](LICENSE)) |
| Future **hosted** multi-tenant SaaS that exposes lexaudit as a network service | **AGPL-3.0-or-later** ([LICENSE-AGPL-HOSTED.md](LICENSE-AGPL-HOSTED.md)) |

By contributing you agree your patches to this repository are licensed under the
**MIT License**. See [docs/licensing.md](docs/licensing.md).

## Checks

```bash
uv sync --extra dev
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict src/
uv run python -m pytest
uv run python scripts/check_pack_density.py
uv run python scripts/check_repo_hygiene.py
```

0.3.0 prep / publish docs: [docs/p1-INDEX.md](docs/p1-INDEX.md).
Do not commit `dumps/`, `tmp/`, `dist/`, `*.vsix`, `*.whl`, `docs/images/*.jpg`,
or `lexaudit.config.local.yaml`. Diagrams in git are SVG only.
