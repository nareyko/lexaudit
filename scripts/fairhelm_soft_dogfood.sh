#!/usr/bin/env bash
# Soft dogfood: audit FairHelm host docs/strategy notes with submodule lexaudit.
# Detection-only. Never fails the shell on findings (exit 0 after report).
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

if [[ -f "$ROOT/frontend/tmp/lexaudit/en/summary.md" ]]; then
  echo "== summary head =="
  head -40 "$ROOT/frontend/tmp/lexaudit/en/summary.md"
fi

echo "dogfood done"
exit 0
