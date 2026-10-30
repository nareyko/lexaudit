# Product shell checklist · VS Code + MCP (0.3.0)

Owner-executable. Local packaging already done; publish needs accounts.

## Already in repo

| Item | Path / note |
|---|---|
| VS Code extension | `packages/vscode-lexaudit/` (v0.3.0, MIT LICENSE, smoke + `npm run package`) |
| Local `.vsix` | build artifact (gitignored); regenerate with `npm run package` |
| MCP entrypoint | `lexaudit-mcp` via `pip install 'lexaudit[mcp]'` |
| MCP metadata | `packages/mcp-lexaudit/server.json` |
| Dogfood doc | `docs/p1-mcp-vscode-dogfood.md` |
| Publish runbook | `docs/p1-owner-publish-runbook-2026-10-30.md` |
| Docs index | `docs/p1-INDEX.md` |

## VS Code Marketplace

| # | Step | Owner | Status |
|---|---|---|---|
| 1 | Create publisher on [Marketplace manage](https://marketplace.visualstudio.com/manage) id=`nareyko` | owner | ☑ |
| 2 | Add PNG icon 128×128 (not SVG) to `packages/vscode-lexaudit/` + `package.json` `icon` | agent | ☑ `icon.png` |
| 3 | Confirm README images are HTTPS only (no local SVG embeds in Marketplace README) | agent | ☑ no images in README |
| 4 | `vsce login nareyko` (or Trusted Publishing / OIDC) | owner | ☑ |
| 5 | After PyPI 0.3.0 live: `vsce publish` | owner | ☑ [Marketplace](https://marketplace.visualstudio.com/items?itemName=nareyko.vscode-lexaudit) |
| 6 | Open VSX (Cursor / VSCodium) — see publish-status | owner | □ `OVSX_PAT` |

Refs: [Publishing Extensions](https://code.visualstudio.com/api/working-with-extensions/publishing-extension).

## MCP official registry

| # | Step | Owner | Status |
|---|---|---|---|
| 1 | PyPI upload `lexaudit==0.3.0` with `mcp` extra installable | agent | ☑ 0.3.0 live; 0.3.1 for mcp-name |
| 2 | Verify `server.json` name `io.github.nareyko/lexaudit`, description ≤100 chars | agent | ☑ |
| 3 | Install `mcp-publisher`; GitHub auth for `io.github.nareyko/*` namespace | agent | ☑ login OK 2026-10-30 |
| 4 | `mcp-publisher publish` from `packages/mcp-lexaudit/` | agent | ☑ `0.3.1` |
| 5 | Add CI smoke: import FastMCP tools without network LLM | agent | ☑ `test_mcp_smoke` |

Refs: [Registry auth](https://modelcontextprotocol.io/registry/authentication) ·
[server.json requirements](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/official-registry-requirements.md).

## Quality shell

| # | Step | Status |
|---|---|---|
| 1 | Skip LocalAI smoke unless `LEXAUDIT_LOCALAI_SMOKE=1` and health OK | ☑ agent |
| 2 | Document `uv sync --extra dev` then `uv run python -m pytest` | ☑ cli-reference + CONTRIBUTING |
| 3 | Privacy statement one-liner in VS Code README (local CLI only; no telemetry) | ☑ |

## Order

PyPI → MCP registry → VS Marketplace → git tag/push remotes.
