#!/usr/bin/env bash
# Soft dogfood: audit FairHelm Dual-write with submodule lexaudit.
# Detection-only. Never fails the shell on findings (exit 0 after report).
# Runs en+de+ru --check, classifies config needles, lab metrics, CLEAR regression.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LEX="$ROOT/tools/lexaudit"
CFG="$ROOT/lexaudit.config.yaml"
OUT="$ROOT/frontend/tmp/lexaudit-dogfood"
LOCALES="${LEXAUDIT_DOGFOOD_LOCALES:-en,de,ru}"

if [[ ! -f "$CFG" ]]; then
  echo "missing $CFG" >&2
  exit 2
fi

mkdir -p "$OUT"
cd "$LEX"

echo "== doctor =="
uv run lexaudit doctor --config "$CFG" || true

echo "== pack list (RC) =="
uv run lexaudit pack list | head -20
echo "== pack list --lab (stubs) =="
uv run lexaudit pack list --lab | head -15

echo "== soft audit ${LOCALES} (academy+packs via FairHelm config) =="
set +e
uv run lexaudit audit --config "$CFG" --locale "$LOCALES" --check
rc=$?
set -e
echo "audit_exit=$rc (soft dogfood: non-zero OK when calques remain)"

IFS=',' read -r -a LOC_ARR <<< "$LOCALES"
for loc in "${LOC_ARR[@]}"; do
  loc="${loc// /}"
  SUMMARY="$ROOT/frontend/tmp/lexaudit/${loc}/summary.md"
  FINDINGS="$ROOT/frontend/tmp/lexaudit/${loc}/findings.json"
  if [[ -f "$SUMMARY" ]]; then
    echo "== summary head (${loc}) =="
    head -25 "$SUMMARY"
  fi
  if [[ -f "$FINDINGS" ]]; then
    echo "== needle + calque classification (${loc}) =="
    uv run python - "$CFG" "$FINDINGS" "$loc" <<'PY'
import json, sys
from collections import Counter
from pathlib import Path

cfg_path, findings_path, loc = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
text = cfg_path.read_text(encoding="utf-8")
known: set[str] = set()
in_needles = False
for line in text.splitlines():
    if line.startswith("needles:"):
        in_needles = True
        continue
    if in_needles:
        if line.startswith("  - "):
            known.add(line[4:].strip().strip("\"'"))
        elif line and not line.startswith(" "):
            break

data = json.loads(findings_path.read_text(encoding="utf-8"))
rows = data if isinstance(data, list) else (data.get("findings") or data.get("items") or [])
words: set[str] = set()
status_c: Counter[str] = Counter()
calque_words: Counter[str] = Counter()
for row in rows:
    if not isinstance(row, dict):
        continue
    status_c[str(row.get("status") or "?")] += 1
    w = row.get("word") or row.get("token") or row.get("needle")
    if isinstance(w, str) and w:
        words.add(w.lower())
        if row.get("status") == "calque":
            calque_words[w.lower()] += 1

known_l = {k.lower() for k in known}
hit_known = sorted(w for w in words if w in known_l or any(w.startswith(k) for k in known_l))
# also stem hits for Cyrillic needles
for k in known_l:
    for w in words:
        if k in w and w not in hit_known:
            hit_known.append(w)
hit_known = sorted(set(hit_known))
print(f"locale={loc}")
print(f"status_counts={dict(status_c)}")
print(f"calque_unique={sorted(calque_words) or '[]'} calque_hits={sum(calque_words.values())}")
print(f"known_needles_in_findings={hit_known or '[]'}")
scrub = {"orientir", "orientirs", "denseness", "предпокуп", "блувотер", "чеклист", "рефит", "листинг", "апгрейд"}
still = sorted({w for w in words if any(s in w for s in scrub)})
print(f"scrub_stems_still_present={still or '[]'}")
PY
  fi
done

echo "== lab pack metrics =="
set +e
uv run python scripts/run_lab_pack_metrics.py
lab_rc=$?
set -e
echo "lab_metrics_exit=$lab_rc"

echo "== CLEAR regression =="
set +e
uv run lexaudit eval regression --config "$CFG"
reg_rc=$?
set -e
echo "regression_exit=$reg_rc (soft always 0 expected)"

echo "== docs deslop =="
set +e
bash scripts/docs_deslop_scan.sh
deslop_rc=$?
set -e
echo "docs_deslop_exit=$deslop_rc"

echo "== vscode extension smoke =="
set +e
(cd packages/vscode-lexaudit && LEXAUDIT_CLI="$(command -v lexaudit || true)" node extension.js --smoke)
vsc_rc=$?
set -e
echo "vscode_smoke_exit=$vsc_rc"

echo "dogfood done"
exit 0
