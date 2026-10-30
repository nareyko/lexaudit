#!/usr/bin/env bash
# Soft dogfood: audit FairHelm host docs/strategy notes with submodule lexaudit.
# Detection-only. Never fails the shell on findings (exit 0 after report).
# Classifies CHECK needles into known (config needles) vs unexpected.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LEX="$ROOT/tools/lexaudit"
CFG="$ROOT/lexaudit.config.yaml"
OUT="$ROOT/frontend/tmp/lexaudit-dogfood"

if [[ ! -f "$CFG" ]]; then
  echo "missing $CFG" >&2
  exit 2
fi

mkdir -p "$OUT"
cd "$LEX"

echo "== doctor =="
uv run lexaudit doctor --config "$CFG" || true

echo "== pack list (release + lab) =="
uv run lexaudit pack list --lab | head -20

echo "== soft audit en (academy+packs via FairHelm config) =="
set +e
uv run lexaudit audit --config "$CFG" --locale en --check
rc=$?
set -e
echo "audit_exit=$rc (soft dogfood: non-zero OK when calques remain)"

SUMMARY="$ROOT/frontend/tmp/lexaudit/en/summary.md"
FINDINGS="$ROOT/frontend/tmp/lexaudit/en/findings.json"
if [[ -f "$SUMMARY" ]]; then
  echo "== summary head =="
  head -40 "$SUMMARY"
fi

if [[ -f "$FINDINGS" ]]; then
  echo "== needle classification (en) =="
  uv run python - "$CFG" "$FINDINGS" <<'PY'
import json, sys
from pathlib import Path

cfg_path, findings_path = Path(sys.argv[1]), Path(sys.argv[2])
# minimal YAML needles parse (no PyYAML dependency required for list items)
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
words: set[str] = set()
if isinstance(data, list):
    rows = data
elif isinstance(data, dict):
    rows = data.get("findings") or data.get("items") or data.get("words") or []
else:
    rows = []
for row in rows:
    if isinstance(row, dict):
        w = row.get("word") or row.get("token") or row.get("needle")
        if isinstance(w, str) and w:
            words.add(w.lower())
    elif isinstance(row, str):
        words.add(row.lower())

hit_known = sorted(w for w in words if w in {k.lower() for k in known})
hit_other = sorted(w for w in words if w not in {k.lower() for k in known})
print(f"known_needles_in_findings={hit_known or '[]'}")
print(f"other_tokens_sample={hit_other[:20] or '[]'}")
print(f"known_count={len(hit_known)} other_count={len(hit_other)}")
# soft expectation after denseness/orientir Dual-write scrub:
expected_cleared = {"orientir", "orientirs", "denseness"}
still = sorted(expected_cleared & {w.lower() for w in words})
print(f"scrub_needles_still_present={still or '[]'}")
PY
fi

echo "dogfood done"
exit 0
