# lexaudit (VS Code)

Shells out to the local `lexaudit` CLI. Detection only: no rewrite, no cloud.

Grew out of auditing multilingual courses and encyclopedias at
[FairHelm](https://fairhelm.com). Package and CLI:
[github.com/nareyko/lexaudit](https://github.com/nareyko/lexaudit).

## Requirements

Install the CLI first:

```bash
pipx install lexaudit
# or: uv tool install lexaudit
```

## Install the extension

| Editor | Store |
|---|---|
| VS Code | [Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=nareyko.vscode-lexaudit) |
| Cursor / VSCodium / other Open VSX clients | [Open VSX](https://open-vsx.org/extension/nareyko/vscode-lexaudit) (after publish) |

Or install a release `.vsix` from
[GitHub Releases](https://github.com/nareyko/lexaudit/releases).

## Commands

- `lexaudit: Audit workspace`: runs `lexaudit audit --check` and maps findings to Problems
- `lexaudit: Explain selection`: runs `lexaudit explain` on the selected word

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

MIT, same as the lexaudit package. See the repository root `LICENSE`.
