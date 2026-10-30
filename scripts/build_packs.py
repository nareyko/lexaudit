#!/usr/bin/env python3
"""Zip rule packs under packs/ into dist/packs with SHA-256 sidecars."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "packs"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    packs = ROOT / "packs"
    for pack_dir in sorted(p for p in packs.iterdir() if p.is_dir() and not p.name.startswith("_")):
        meta = pack_dir / "pack.yaml"
        if not meta.is_file():
            continue
        zip_path = OUT / f"{pack_dir.name}.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(pack_dir.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(pack_dir).as_posix())
        digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
        (OUT / f"{pack_dir.name}.zip.sha256").write_text(
            f"{digest}  {zip_path.name}\n", encoding="utf-8"
        )
        print(f"wrote {zip_path} sha256={digest[:12]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
