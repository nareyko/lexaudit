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
    # Docs diagrams: SVG SSOT; raster exports stay local.
    ".jpg",
    ".jpeg",
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
    # Twin trees: promoted packs must not keep full calques under _lab/.
    lab = ROOT / "packs" / "_lab"
    if lab.is_dir():
        twins = [str(p.relative_to(ROOT)) for p in lab.glob("*/calques") if p.is_dir()]
        if twins:
            print("hygiene FAIL — duplicate lab calques (use packs/<id>/ only):")
            for t in twins:
                print(f"  {t}")
            return 1

    print("hygiene OK — no dumps/tmp/wheels/vsix/jpg/local-config tracked")
    # Reminder for untracked local bulk (informational).
    for rel in ("dumps", "tmp", "dist"):
        p = ROOT / rel
        if p.is_dir():
            print(f"note: local `{rel}/` present (gitignored) — keep out of commits")
    img = ROOT / "docs" / "images"
    if img.is_dir():
        jpg_local = list(img.glob("*.jpg"))
        if jpg_local:
            n = len(jpg_local)
            print(f"note: {n} local docs/images/*.jpg (gitignored) — SVG is SSOT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
