# Publish status · lexaudit 0.3.0 (2026-10-30)

Agent executed everything that does not need PyPI / Marketplace account setup.

## Done

| Step | Result |
|---|---|
| Push `main` | `7bc94b2..cbaad3e` → `origin/main` |
| Tag `v0.3.0` | annotated tag on `cbaad3e`, pushed |
| GitHub Release | https://github.com/nareyko/lexaudit/releases/tag/v0.3.0 |
| Release assets | `lexaudit-0.3.0-py3-none-any.whl`, `.tar.gz`, `vscode-lexaudit-0.3.0.vsix` |
| Local dogfood | soft dogfood + lab metrics failed=0 + CLEAR 11/11 + deslop + VS Code smoke |
| MCP `server.json` | `mcp-publisher validate` OK (schema deprecation warn only) |
| MCP login | `mcp-publisher login github --token=…` OK (`io.github.nareyko/*`) |

## Blocked on owner (accounts)

### 1. PyPI Trusted Publishing (blocks MCP + Marketplace order)

Workflow run failed:
https://github.com/nareyko/lexaudit/actions/runs/41090017047

Error: `invalid-publisher` — no matching Trusted Publisher on PyPI.

Create publisher on https://pypi.org/manage/project/lexaudit/settings/publishing/ :

| Field | Value |
|---|---|
| Owner | `nareyko` |
| Repository | `lexaudit` |
| Workflow | `publish-pypi.yml` |
| Environment | `pypi` |

Then re-run: Actions → **publish-pypi** → confirm `publish-0.3.0`.

Verify: `pip index versions lexaudit` shows `0.3.0` (currently only 0.1.0 / 0.2.0).

### 2. MCP registry (after PyPI 0.3.0 is live)

```bash
# binary already validated; re-login if needed
mcp-publisher login github   # or --token "$GH_TOKEN"
cd packages/mcp-lexaudit && mcp-publisher publish
```

Last attempt returned 400: PyPI `lexaudit==0.3.0` not found yet.

### 3. VS Code Marketplace

`.vsix` built and attached to the GitHub Release. Needs publisher login:

```bash
cd packages/vscode-lexaudit
npx @vscode/vsce login nareyko
npx @vscode/vsce publish
# optional Open VSX: npx ovsx publish vscode-lexaudit-0.3.0.vsix -p "$OVSX_TOKEN"
```

No `VSCE_PAT` / `OVSX_TOKEN` in this environment.

## FairHelm

Submodule `tools/lexaudit` already points at `v0.3.0` (`cbaad3e`). Push FairHelm when you want the pointer on origin.
