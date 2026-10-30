# Contributing

`lexaudit` is created and maintained by **Vadim Nareyko**
([github.com/nareyko](https://github.com/nareyko)).

## Dual license (lexaudit only)

This applies to **lexaudit**, not to FairHelm (FairHelm is proprietary).

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
uv run pytest
```
