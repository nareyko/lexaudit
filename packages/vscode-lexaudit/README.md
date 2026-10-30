# lexaudit (VS Code)

Shells out to the local `lexaudit` CLI. Detection only — no rewrite, no cloud.

## Requirements

Install the CLI first:

```bash
pipx install lexaudit
# or: uv tool install lexaudit
```

## Commands

- `lexaudit: Audit workspace` — runs `lexaudit audit --check` and maps findings to Problems
- `lexaudit: Explain selection` — runs `lexaudit explain` on the selected word

## Settings

| Setting | Default | Meaning |
|---|---|---|
| `lexaudit.locale` | `en` | Locale for the CLI |
| `lexaudit.cli` | `lexaudit` | Binary name or absolute path |

Optional: put `lexaudit.config.yaml` in the workspace root.

## Smoke (developers)

```bash
cd packages/vscode-lexaudit
npm run smoke
npm run package   # writes a .vsix (publish separately)
```

## Privacy

Runs entirely on your machine via the local CLI. No telemetry, no cloud audit
endpoint, no account required.

## License

MIT — same as the lexaudit package. See the repository root `LICENSE`.
