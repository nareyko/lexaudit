# Publish status · lexaudit (2026-10-30)

## Done

| Step | Result |
|---|---|
| PyPI `0.3.0` | https://pypi.org/project/lexaudit/0.3.0/ |
| PyPI `0.3.1` | https://pypi.org/project/lexaudit/0.3.1/ (mcp-name in README) |
| Tag / Release | `v0.3.0`, `v0.3.1` |
| MCP registry | `io.github.nareyko/lexaudit@0.3.1` published |
| VS Marketplace | https://marketplace.visualstudio.com/items?itemName=nareyko.vscode-lexaudit |

## Remaining · Open VSX (Cursor / VSCodium)

Microsoft Marketplace does **not** feed Cursor or VSCodium. Those use
[Open VSX](https://open-vsx.org/).

1. GitHub login → https://open-vsx.org/user-settings/profile  
2. Link Eclipse account + **Publisher Agreement**  
3. Create token: https://open-vsx.org/user-settings/tokens → put in `OVSX_PAT` (local only)  
4. Once per publisher id:
   ```bash
   npx ovsx create-namespace nareyko -p "$OVSX_PAT"
   ```
5. Publish the packaged `.vsix` (extension `0.3.2`+ with FairHelm origin in README):
   ```bash
   cd packages/vscode-lexaudit
   npm run package
   npx ovsx publish vscode-lexaudit-0.3.2.vsix -p "$OVSX_PAT"
   ```
6. Listing: https://open-vsx.org/extension/nareyko/vscode-lexaudit  

Optional: claim verified namespace ownership on Open VSX after first publish.
