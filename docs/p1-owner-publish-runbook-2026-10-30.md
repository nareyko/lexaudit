# Owner publish runbook · lexaudit 0.3.0

Local gates are green. This runbook needs **your accounts** — the agent cannot
finish these steps. No secrets belong in the repo.

## Preconditions (already done locally)

- Version `0.3.0` in `pyproject.toml`
- Ten RC packs in `packs/`
- VS Code extension + `icon.png` + MCP `server.json`
- CI: density / bilingual ship bar / hygiene / pytest
- Trusted Publishing workflow stub: `.github/workflows/publish-pypi.yml`

## Do not put in git

`dumps/`, CX corpora, `tmp/**`, `dist/**`, `*.vsix`, `*.whl`, `gold/`, `eval/`,
`lexaudit.config.local.yaml`, PyPI/Marketplace tokens.

## Order

### 1. Push lexaudit `main` (first time after local commits)

```bash
cd tools/lexaudit
git push origin main
```

### 2. PyPI (Trusted Publishing)

1. Create PyPI project `lexaudit` pending publisher → GitHub
   `nareyko/lexaudit`, workflow `publish-pypi.yml`, environment `pypi`.
2. In GitHub repo: Environment `pypi` with protection rules you want.
3. Actions → **publish-pypi** → Run workflow → type `publish-0.3.0`.
4. Verify: `pip index versions lexaudit` shows `0.3.0`.

Fallback (not preferred): `uv publish` with API token — never commit the token.

### 3. MCP registry

```bash
cd packages/mcp-lexaudit
# install mcp-publisher; GitHub auth for io.github.nareyko/*
mcp-publisher login
mcp-publisher publish
```

Confirm `server.json` name `io.github.nareyko/lexaudit`, description ≤100 chars.

### 4. VS Code Marketplace

```bash
cd packages/vscode-lexaudit
npm run package          # local .vsix (gitignored)
vsce login nareyko
vsce publish
```

Optional: same `.vsix` → Open VSX.

### 5. Tag + FairHelm submodule bump

```bash
cd tools/lexaudit
git tag v0.3.0
git push origin v0.3.0
cd ../..   # FairHelm root
git add tools/lexaudit
git commit -m "chore(lexaudit): point submodule at v0.3.0"
# push FairHelm only when you want
```

## Verify after publish

```bash
pipx install 'lexaudit==0.3.0'
lexaudit doctor
pip install 'lexaudit[mcp]==0.3.0'
lexaudit-mcp --help || true
```
