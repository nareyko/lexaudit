# P1 MCP / VS Code dogfood (nothing hosted)

## Architecture

Both surfaces call the **local** `lexaudit` CLI / library. There is no FairHelm
or lexaudit cloud endpoint. Dictionaries still land in the user cache.

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
# Requires lexaudit on PATH
cd packages/vscode-lexaudit
node extension.js --smoke
# In VS Code: Developer: Install Extension from Location → this folder
# Command palette: "lexaudit: Audit workspace"
```

Diagnostics come from `findings.json` or `--format json` stdout. Engine stays
single-sourced in Python.

## Do not

- Publish to VS Marketplace / Open VSX / Glama / Smithery until owner go.
- Add a remote audit API in this track.
