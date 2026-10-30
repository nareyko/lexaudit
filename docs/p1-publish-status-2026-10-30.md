# Publish status · lexaudit (2026-10-30)

## Done

| Step | Result |
|---|---|
| PyPI `0.3.0` | https://pypi.org/project/lexaudit/0.3.0/ |
| PyPI `0.3.1` | https://pypi.org/project/lexaudit/0.3.1/ (mcp-name in README) |
| Tag / Release | `v0.3.0`, `v0.3.1` |
| MCP registry | `io.github.nareyko/lexaudit@0.3.1` published |
| VS Marketplace | https://marketplace.visualstudio.com/items?itemName=nareyko.vscode-lexaudit (`0.3.1`+; `0.3.2` FairHelm README) |
| Open VSX | ⚠ uploaded but **inactive** — not searchable until Publisher Agreement |

## Open VSX · inactive (Cursor / VSCodium «Extension Not Found»)

`ovsx publish` returns success, then API says not found / namespace lists
0 extensions. Versions sit inactive until the Eclipse **Publisher Agreement**
is signed on the same GitHub identity that owns the PAT.

Owner (browser, once):

1. https://open-vsx.org → GitHub login (same account as the token)
2. Profile → **Log in with Eclipse** → https://accounts.eclipse.org  
3. Back on Open VSX profile → **Show Publisher Agreement** → Agree  
4. User Settings → Extensions: delete any inactive `vscode-lexaudit` rows  
5. Tell agent to republish, or locally:
   ```bash
   cd packages/vscode-lexaudit
   npx ovsx publish vscode-lexaudit-0.3.3.vsix -p "$OVSX_PAT"
   ```
6. Verify: `curl -s https://open-vsx.org/api/nareyko/vscode-lexaudit | jq .version`

Until then Cursor/VSCodium cannot install by id. Workaround: install the
`.vsix` from GitHub Releases via Extensions → Install from VSIX.
Marketplace (VS Code) is separate and already live.
