# P1 MCP / VS Code dogfood (nothing hosted)

## Architecture

Both surfaces call the **local** `lexaudit` CLI / library. There is no cloud
endpoint. Dictionaries still land in the user cache.

| Surface | How to run | Hosting |
|---|---|---|
| MCP | `pip install 'lexaudit[mcp]'` then `lexaudit-mcp` via stdio | none |
| VS Code | sideload `packages/vscode-lexaudit` | none |

## Cursor / Claude Desktop MCP snippet

```json
{
  "mcpServers": {
    "lexaudit": {
      "command": "lexaudit-mcp"
    }
  }
}
```

Tools: `audit`, `explain`, `expand_needle`, `fetch_dicts`.

## VS Code lab extension

```bash
# Prefers `lexaudit` on PATH; falls back to `uv run lexaudit` from repo root
cd packages/vscode-lexaudit
node extension.js --smoke
# In VS Code: Developer: Install Extension from Location → this folder
# Command palette: "lexaudit: Audit workspace"
```

Smoke checks: CLI `--help` + offline `findings.json` → Problems diagnostics parser.
Diagnostics come from `findings.json` or `--format json` stdout. Engine stays
single-sourced in Python.

## Docs deslop (soft gate)

```bash
bash scripts/docs_deslop_scan.sh
```

Ban-list + bold-spam (>2 `**…**` per prose paragraph) on `README.md` + `docs/*.md`.
Wired into `scripts/fairhelm_soft_dogfood.sh`.

## Do not

- Publish to VS Marketplace / Open VSX / Glama / Smithery until owner go.
- Add a remote audit API in this track.
