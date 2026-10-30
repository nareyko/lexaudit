#!/usr/bin/env bash
# Soft anti-AI deslop gate for lexaudit README + docs (P1 lab).
# Fails on dense **bold** spam (>2 bold spans in a prose paragraph) and ban phrases.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 - <<'PY'
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(".")
paths = [Path("README.md"), *sorted(Path("docs").glob("*.md"))]
ban = re.compile(
    r"delve into|landscape of|in today's world|it'?s important to note|"
    r"comprehensive guide|unlock the power|leverage AI|"
    r"as an AI language model",
    re.I,
)
bold_re = re.compile(r"\*\*[^*]+\*\*")
errors: list[str] = []
for path in paths:
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8")
    for m in ban.finditer(text):
        errors.append(f"{path}: ban phrase {m.group(0)!r}")
    # paragraph = blank-line separated; skip fenced code
    chunks: list[str] = []
    buf: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.strip():
            if buf:
                chunks.append("\n".join(buf))
                buf = []
        else:
            buf.append(line)
    if buf:
        chunks.append("\n".join(buf))
    for para in chunks:
        if para.lstrip().startswith("#") or para.lstrip().startswith("|"):
            continue
        n = len(bold_re.findall(para))
        if n > 2:
            preview = para.replace("\n", " ")[:80]
            errors.append(f"{path}: bold-spam {n} in paragraph: {preview!r}")

if errors:
    print("docs_deslop FAIL")
    for e in errors[:40]:
        print(" ", e)
    raise SystemExit(1)
print(f"docs_deslop OK ({len(paths)} files)")
PY
