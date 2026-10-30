# Owner publish runbook · lexaudit 0.3.0

Live progress: [`p1-publish-status-2026-10-30.md`](p1-publish-status-2026-10-30.md)
(`main` + `v0.3.0` + GitHub Release already pushed). Remaining steps need
**your PyPI / Marketplace accounts**. No secrets belong in the repo.

Remote: `git@github.com:nareyko/lexaudit.git` (`main` may be many commits ahead
of `origin` after the local prep wave — expect a large first push).

## Preconditions (already done locally)

- Version `0.3.0` in `pyproject.toml` / `__version__` / Action pin / VS Code + MCP
- Ten RC packs in `packs/` (wheel force-include; no `packs/_lab` content)
- `packs/_lab/` = thin `pack.yaml` stubs only (`pack list --lab`)
- Docs diagrams = SVG SSOT (`docs/images/*.jpg` gitignored)
- CI: density / bilingual ship bar / hygiene / pytest
- Trusted Publishing stub: `.github/workflows/publish-pypi.yml`
  (`workflow_dispatch`, confirm string `publish-0.3.0`, environment `pypi`)
- FairHelm soft dogfood (bilingual **off**): en/de/ru `--check` exit 0, calque=0,
  scrub needles clear, CLEAR regression 11/11 (re-run
  `bash scripts/fairhelm_soft_dogfood.sh` before publish if unsure)

## Do not put in git

`dumps/`, CX corpora, `tmp/**`, `dist/**`, `*.vsix`, `*.whl`, `docs/images/*.jpg`,
`gold/`, `eval/`, `lexaudit.config.local.yaml`, PyPI / Marketplace / OVSX tokens.

Local bulk on disk (regenerable; safe to delete anytime):

```bash
# optional disk cleanup inside tools/lexaudit
rm -rf tmp/lab-debug* tmp/wiki-probe tmp/clean-wild tmp/pack-wild \
       tmp/pack-field tmp/crosslocale-dogfood tmp/bilingual-matrix \
       tmp/synthetic-demo-out tmp/lab-packs tmp/lexaudit
# dumps/cx-corpora*.gz — research only; already gzipped; keep or delete locally
```

## Order

### 0. Last local gate (optional, cheap)

```bash
cd tools/lexaudit
uv run python scripts/check_repo_hygiene.py
uv run python scripts/run_lab_pack_metrics.py   # expect 70 rows, failed=0
bash scripts/docs_deslop_scan.sh
```

### 1. Push lexaudit `main` (first)

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

Confirm `server.json`: name `io.github.nareyko/lexaudit`, description ≤100 chars
(currently 97), version `0.3.0`.

### 4. VS Code Marketplace

```bash
cd packages/vscode-lexaudit
npm run package          # local .vsix (gitignored)
vsce login nareyko
vsce publish
```

Optional Open VSX (same `.vsix`, separate account):

```bash
npx ovsx publish packages/vscode-lexaudit/vscode-lexaudit-0.3.0.vsix -p "$OVSX_TOKEN"
```

Do not commit the token or the `.vsix`.

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

Tag the **same** commit you pushed to `main` (or a follow-up that only bumps
metadata). FairHelm submodule pointer should match `v0.3.0`.

## Verify after publish

```bash
pipx install 'lexaudit==0.3.0'
lexaudit doctor
pip install 'lexaudit[mcp]==0.3.0'
lexaudit-mcp --help || true
```

Defaults stay `enable_bilingual: false` and `enable_crosslocale: false` —
FairHelm main config matches that.
