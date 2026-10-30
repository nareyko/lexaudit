# vscode-lexaudit (P1 lab, unpublished)

Shells out to the `lexaudit` CLI. Not published to the VS Code Marketplace in 0.2.0.

## Planned commands

- `lexaudit.auditWorkspace` → `lexaudit audit --path . --check --format json`
- `lexaudit.explainSelection` → `lexaudit explain <word> --locale …`

Diagnostics are loaded from `findings.json` or SARIF produced by the CLI so the
engine stays single-sourced.
