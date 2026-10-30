#!/usr/bin/env python3
"""Dry-run (default) promote of packs/_lab/<id> → packs/<id> for 0.3.0 prep.

Does not publish, tag, or bump the package version. Use --apply only after
owner go (docs/p1-0.3.0-prep.md). Always runs lab_pack_metrics first.

After promote, ``packs/_lab/<id>`` may be a thin stub (pack.yaml only); content
SSOT is ``packs/<id>/``.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lab_pack_metrics import measure  # noqa: E402

from lexaudit.packs import pack_content_dir  # noqa: E402

LAB = ROOT / "packs" / "_lab"
RELEASE = ROOT / "packs"
LOCALES = ("en", "de", "es", "pl", "ru", "sv", "uk")


def _validate(pack_id: str) -> list[str]:
    errors: list[str] = []
    stub = LAB / pack_id
    meta_path = stub / "pack.yaml"
    if not meta_path.is_file():
        return [f"missing lab stub pack.yaml for {pack_id}"]
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
    if not isinstance(meta, dict):
        return [f"invalid pack.yaml for {pack_id}"]
    if meta.get("license") != "MIT":
        errors.append("license must be MIT")
    if meta.get("status") != "lab":
        errors.append("status must be lab on the _lab stub")
    try:
        content = pack_content_dir(pack_id, prefer_lab=True)
    except FileNotFoundError as exc:
        return [str(exc)]
    for loc in LOCALES:
        fx = content / "fixtures" / loc
        if not fx.is_dir():
            continue
        try:
            report = measure(pack_id, loc)
        except FileNotFoundError as exc:
            errors.append(str(exc))
            continue
        if not report.get("lab_rank_ok"):
            errors.append(f"{pack_id}/{loc}: lab_rank_ok=false")
        recall = float(report.get("known_rule_recall") or 0.0)
        if recall < 0.85:
            errors.append(f"{pack_id}/{loc}: recall {recall} < 0.85")
    return errors


def _apply(pack_id: str) -> Path:
    """Copy full lab tree if present; otherwise content already in packs/."""
    src = LAB / pack_id
    dest = RELEASE / pack_id
    if dest.exists():
        return dest
    if not (src / "calques").is_dir():
        msg = (
            f"cannot --apply {pack_id}: packs/_lab has no calques/ "
            f"(already promoted?). Content should be under packs/{pack_id}/"
        )
        raise FileNotFoundError(msg)
    shutil.copytree(src, dest)
    meta_path = dest / "pack.yaml"
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
    if isinstance(meta, dict):
        meta["status"] = "release-candidate"
        meta_path.write_text(
            yaml.safe_dump(meta, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    return dest


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("pack_id", help="Lab pack id (e.g. saas-ui-v0)")
    p.add_argument(
        "--apply",
        action="store_true",
        help="Actually copy into packs/ (default is dry-run)",
    )
    args = p.parse_args()

    errors = _validate(args.pack_id)
    if errors:
        for err in errors:
            print(f"FAIL {err}", file=sys.stderr)
        return 1

    release = RELEASE / args.pack_id
    if release.is_dir() and (release / "calques").is_dir():
        print(f"OK already promoted {args.pack_id} → packs/{args.pack_id}/")
        if args.apply:
            print("nothing to copy (thin _lab stub; content SSOT is packs/)")
        else:
            print("dry-run metrics green")
        return 0

    print(f"OK validate {args.pack_id}")
    if not args.apply:
        print("dry-run only; re-run with --apply after owner go")
        return 0

    try:
        dest = _apply(args.pack_id)
    except FileNotFoundError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print(f"promoted -> {dest} (status=release-candidate)")
    print("Still not a PyPI/Release attach — finish docs/p1-0.3.0-prep.md checklist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
