#!/usr/bin/env python3
"""Fail if bulky local research artifacts would be committed.

Checks ``git ls-files`` for dumps, CX corpora, tmp metrics, wheels, vsix.
Safe to run offline. Does not delete anything.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PREFIXES = (
    "dumps/",
    "tmp/",
    "gold/",
    "eval/",
    "dist/",
    ".venv/",
)
FORBIDDEN_SUFFIXES = (
    ".tmx",
    ".tmx.gz",
    ".vsix",
    ".whl",
    ".tar.gz",
)
FORBIDDEN_NAMES = (
    "lexaudit.config.local.yaml",
    "cx-corpora.ru2en.text.json.gz",
)


def tracked_files() -> list[str]:
    res = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [p for p in res.stdout.decode().split("\0") if p]


def main() -> int:
    bad: list[str] = []
    for path in tracked_files():
        if any(path.startswith(p) for p in FORBIDDEN_PREFIXES):
            bad.append(path)
            continue
        if any(path.endswith(s) for s in FORBIDDEN_SUFFIXES):
            # Allow docs that merely mention suffixes in name? none expected.
            bad.append(path)
            continue
        if Path(path).name in FORBIDDEN_NAMES:
            bad.append(path)
    if bad:
        print("hygiene FAIL — tracked forbidden paths:")
        for p in bad:
            print(f"  {p}")
        return 1
    print("hygiene OK — no dumps/tmp/wheels/vsix/local-config tracked")
    # Reminder for untracked local bulk (informational).
    for rel in ("dumps", "tmp", "dist"):
        p = ROOT / rel
        if p.is_dir():
            print(f"note: local `{rel}/` present (gitignored) — keep out of commits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
