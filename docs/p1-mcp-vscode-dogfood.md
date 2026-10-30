# MCP / VS Code packaging (0.3.0)

Both surfaces call the **local** `lexaudit` CLI / library. There is no cloud
endpoint. Dictionaries still land in the user cache.

| Surface | Artifact | Hosting |
|---|---|---|
| MCP | `pip install 'lexaudit[mcp]'` → `lexaudit-mcp` stdio | none |
| MCP registry | `packages/mcp-lexaudit/server.json` | publish after PyPI 0.3.0 |
| VS Code | `packages/vscode-lexaudit` → `.vsix` via `npm run package` | Marketplace after owner go |

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

## VS Code extension

```bash
# Prefers lexaudit on PATH; falls back to uv run lexaudit from repo root
cd packages/vscode-lexaudit
npm run smoke
npm run package   # writes vscode-lexaudit-0.3.0.vsix
# Sideload: Developer → Install Extension from Location
# Or: vsce publish (owner go only, after PyPI CLI is installable)
```

Smoke checks: CLI `--help` + offline `findings.json` → Problems diagnostics parser.
Diagnostics come from `findings.json` or `--format json` stdout. Engine stays
single-sourced in Python.

## Docs deslop (soft gate)

```bash
bash scripts/docs_deslop_scan.sh
```

Ban-list + bold-spam (>2 bold spans per prose paragraph) on `README.md` + `docs/*.md`.

## Publish order (owner go)

1. PyPI `lexaudit==0.3.0` (wheel includes ten RC domain packs)
2. MCP registry submit using `packages/mcp-lexaudit/server.json`
3. VS Marketplace / Open VSX: `vsce publish` from `packages/vscode-lexaudit`
4. Push remotes / tag

## Do not

- Publish Marketplace / MCP registry before PyPI 0.3.0 is live
- Add a remote audit API in this track
