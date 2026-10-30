# Publish status · lexaudit (2026-10-30)

## Done

| Step | Result |
|---|---|
| PyPI `0.3.0` | live — https://pypi.org/project/lexaudit/0.3.0/ (Trusted Publisher OK) |
| Tag / Release `v0.3.0` | https://github.com/nareyko/lexaudit/releases/tag/v0.3.0 |
| `0.3.1` patch | README `mcp-name` for MCP Registry ownership; re-publish needed |

## Remaining

| Step | Status |
|---|---|
| PyPI `0.3.1` | publish via workflow `publish-0.3.1` |
| MCP registry | after `0.3.1` on PyPI: `mcp-publisher publish` |
| VS Marketplace | needs `vsce login` / `VSCE_PAT` (still owner) |
