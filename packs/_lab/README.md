# Lab registry (thin stubs)

After 0.3.0 promote, **calques + fixtures live only under** `packs/<id>/`
(status `release-candidate`). Each `packs/_lab/<id>/` keeps a `pack.yaml` stub
(`status: lab`) so `lexaudit pack list --lab` still works, without a second
copy of YAML/fixtures in git (~1.4 MiB saved).

| Pack | Focus | Content SSOT |
|---|---|---|
| `saas-ui-v0` … `hr-ats-v0` (10) | domain coinages | `packs/<id>/` |

```bash
uv run python scripts/lab_pack_metrics.py --pack saas-ui-v0 --locale uk
uv run python scripts/run_lab_pack_metrics.py
uv run lexaudit pack list --lab
# install resolves content from packs/<id> when _lab has no calques/
uv run lexaudit pack install saas-ui-v0 --lab --dest /tmp/lexaudit-packs --force
```

Do **not** re-copy calques into `_lab/` — that recreates twin trees.
Promote notes: `docs/p1-0.3.0-prep.md` · index: `docs/p1-INDEX.md`.
