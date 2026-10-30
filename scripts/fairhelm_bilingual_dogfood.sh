#!/usr/bin/env bash
# Soft bilingual dogfood: FairHelm academy EN↔RU/DE with DE extras.
# Does not flip package enable_bilingual default. Exit 0 after report.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LEX="$ROOT/tools/lexaudit"
CFG="$ROOT/lexaudit.config.bilingual.yaml"
OUT="$ROOT/frontend/tmp/lexaudit-bilingual"
LOCALES="${LEXAUDIT_BILINGUAL_DOGFOOD_LOCALES:-ru,de}"

if [[ ! -f "$CFG" ]]; then
  echo "missing $CFG" >&2
  exit 2
fi

mkdir -p "$OUT"
cd "$LEX"

echo "== bilingual doctor =="
uv run lexaudit doctor --config "$CFG" || true

echo "== soft bilingual audit ${LOCALES} =="
set +e
uv run lexaudit audit --config "$CFG" --locale "$LOCALES" --check
rc=$?
set -e
echo "audit_exit=$rc (soft: non-zero OK when leftovers remain)"

IFS=',' read -r -a LOC_ARR <<< "$LOCALES"
for loc in "${LOC_ARR[@]}"; do
  loc="${loc// /}"
  SUMMARY="$OUT/${loc}/summary.md"
  FINDINGS="$OUT/${loc}/findings.json"
  if [[ -f "$SUMMARY" ]]; then
    echo "== summary head (${loc}) =="
    head -30 "$SUMMARY"
  fi
  if [[ -f "$FINDINGS" ]]; then
    echo "== bilingual findings (${loc}) =="
    uv run python - "$FINDINGS" "$loc" <<'PY'
import json, sys
from collections import Counter
from pathlib import Path

findings_path, loc = Path(sys.argv[1]), sys.argv[2]
data = json.loads(findings_path.read_text(encoding="utf-8"))
rows = data if isinstance(data, list) else (data.get("findings") or data.get("items") or [])
status_c: Counter[str] = Counter()
bilingual = Counter()
for row in rows:
    if not isinstance(row, dict):
        continue
    status_c[str(row.get("status") or "?")] += 1
    reason = str(row.get("reason") or "")
    dets = row.get("detectors") or []
    is_bi = reason.startswith("bilingual") or (
        isinstance(dets, list) and "bilingual" in dets
    )
    if is_bi:
        w = str(row.get("word") or row.get("token") or row.get("normalized") or "")
        if w:
            bilingual[w.casefold()] += 1
print(f"locale={loc}")
print(f"status_counts={dict(status_c)}")
print(f"bilingual_unique={len(bilingual)} sample={sorted(bilingual)[:20]}")
PY
  fi
done

echo "bilingual dogfood done"
exit 0
