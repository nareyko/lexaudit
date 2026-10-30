# vscode-lexaudit (P1 lab, unpublished)

Shells out to the `lexaudit` CLI. **Not** on the VS Code Marketplace.

## Install (dogfood)

1. Put `lexaudit` on your PATH (`pipx install lexaudit` or `uv tool install lexaudit`).
2. VS Code → Developer: Install Extension from Location → this folder.
3. Command palette: `lexaudit: Audit workspace` or `lexaudit: Explain selection`.

## Smoke

```bash
node extension.js --smoke
```

See [docs/p1-mcp-vscode-dogfood.md](../../docs/p1-mcp-vscode-dogfood.md).
