#!/usr/bin/env bash
# Anti-AI deslop gate for lexaudit README + docs (+ CONTRIBUTING/SECURITY).
# Aligned with FairHelm ban-list EN words/phrases + U2-BOLD-SPAM (>2 bold spans
# per prose paragraph). Not GPTZero / not a SaaS humanizer.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 - <<'PY'
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(".")
paths = [
    Path("README.md"),
    Path("CONTRIBUTING.md"),
    Path("SECURITY.md"),
    *sorted(Path("docs").glob("*.md")),
    *sorted(Path("packages").glob("*/README.md")),
]
# FairHelm ban-list EN + lexaudit extras (case-insensitive).
ban = re.compile(
    r"\b(?:delve(?:s|d|ing)?|tapestry|seamless(?:ly)?|leverage(?:s|d|ing)?|"
    r"resonate(?:s|d|ing)?|testament|game[- ]changer|furthermore|moreover|"
    r"utilize(?:s|d|ing)?|empower(?:s|ed|ing)?|streamline(?:s|d|ing)?|"
    r"holistic|revolutionize(?:s|d|ing)?|cutting[- ]edge|"
    r"state[- ]of[- ]the[- ]art|pivotal)\b|"
    r"\bat its core\b|"
    r"\bin today's(?: world)?\b|"
    r"\bit(?:'s| is) important to note\b|"
    r"\bit is worth noting\b|"
    r"\bplease note that\b|"
    r"\bcomprehensive guide\b|"
    r"\bunlock the power\b|"
    r"\bleverage AI\b|"
    r"\bas an AI language model\b|"
    r"\bin conclusion\b|"
    r"\bto summarize\b|"
    r"\bin a nutshell\b|"
    r"\bживая карточка\b|"
    r"\bчужой шаблон\b|"
    r"\bсюда не пишем\b|"
    r"\bошибка шаблона\b|"
    r"\bдавайте разберёмся\b|"
    r"\bважно отметить\b|"
    r"\bстоит (?:подчеркнуть|отметить)\b|"
    r"\bв современном мире\b|"
    r"\bв заключение\b",
    re.I,
)
bold_re = re.compile(r"\*\*[^*]+\*\*")
# Decorative symbol spam in prose (FairHelm symbols C) — allow 1–2, fail on denser.
sym_re = re.compile(r"[—…·]")

errors: list[str] = []
for path in paths:
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8")
    for m in ban.finditer(text):
        line_no = text[: m.start()].count("\n") + 1
        errors.append(f"{path}:{line_no}: ban phrase {m.group(0)!r}")
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
        stripped = para.lstrip()
        if stripped.startswith("#") or stripped.startswith("|"):
            continue
        n = len(bold_re.findall(para))
        if n > 2:
            preview = para.replace("\n", " ")[:80]
            errors.append(f"{path}: bold-spam {n} in paragraph: {preview!r}")
        # Skip list-heavy / license one-liners with intentional middots in meta lines
        if stripped.startswith("- Author:") or stripped.startswith("- License:"):
            continue
        s = len(sym_re.findall(para))
        if s >= 4:
            preview = para.replace("\n", " ")[:80]
            errors.append(f"{path}: symbol-spam {s} (—…·) in paragraph: {preview!r}")

if errors:
    print("docs_deslop FAIL")
    for e in errors[:60]:
        print(" ", e)
    raise SystemExit(1)
print(f"docs_deslop OK ({len(paths)} files)")
PY
