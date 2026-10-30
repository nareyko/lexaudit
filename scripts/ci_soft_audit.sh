#!/usr/bin/env bash
# Soft CI: audit fixture corpus, diff vs committed baseline — never fails on new anomalies (I8-3).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIX="${ROOT}/tests/fixtures/ci-soft-fixture"
ART="${ROOT}/artifacts"
mkdir -p "${ART}"

CFG="${FIX}/lexaudit.config.yaml"
FH_LOCAL="${ROOT}/../../frontend/tmp/hunspell-local/usr/bin/hunspell"
if [[ ! -x "${FH_LOCAL}" ]]; then
  CFG="${FIX}/lexaudit.config.ci.yaml"
fi

cd "${FIX}"
uv run --directory "${ROOT}" lexaudit audit \
  --config "${CFG}" \
  --locale en \
  --freeze-at 1970-01-01T00:00:00Z

uv run --directory "${ROOT}" lexaudit diff \
  --baseline "${FIX}/baseline/en/report.json" \
  --current "${FIX}/out/en/report.json" \
  --out "${ART}/diff.json"

export LEXAUDIT_ART="${ART}"
uv run --directory "${ROOT}" python - <<'PY'
import json
import os
from pathlib import Path

art = Path(os.environ["LEXAUDIT_ART"])
diff_path = art / "diff.json"
summary_path = art / "soft-audit-summary.md"
data = json.loads(diff_path.read_text(encoding="utf-8"))
counts = data.get("counts", {})
lines = [
    "# lexaudit soft audit (I8-3)",
    "",
    "Detection-only drift vs committed baseline. **This job never fails on new anomalies.**",
    "",
    f"- new: {counts.get('new', 0)}",
    f"- gone: {counts.get('gone', 0)}",
    f"- tier_changed: {counts.get('tier_changed', 0)}",
    f"- status_changed: {counts.get('status_changed', 0)}",
    "",
    "Full diff: `artifacts/diff.json`",
]
summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
PY

exit 0
