#!/usr/bin/env python3
"""Spot-check RC pack calque density (en/de/ru). Exit 1 if under floors.

Does not download anything. Safe CI gate for Track E.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "packs"

FLOORS = {
    "en": 20,
    "de": 12,
    "ru": 12,
    "es": 12,
    "pl": 12,
    "sv": 12,
    "uk": 12,
}
SKIP = {"core-calques-v1", "_lab"}


def rule_count(path: Path) -> int:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rules = data.get("rules") if isinstance(data, dict) else data
    return len(rules) if isinstance(rules, list) else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows: list[dict[str, object]] = []
    failed: list[str] = []
    for pack_dir in sorted(p for p in PACKS.iterdir() if p.is_dir()):
        if pack_dir.name in SKIP or pack_dir.name.startswith("_"):
            continue
        calques = pack_dir / "calques"
        if not calques.is_dir():
            continue
        row: dict[str, object] = {"pack": pack_dir.name}
        for loc, floor in FLOORS.items():
            path = calques / f"{loc}.yaml"
            n = rule_count(path) if path.is_file() else 0
            row[loc] = n
            if n < floor:
                failed.append(f"{pack_dir.name}/{loc}:{n}<{floor}")
        rows.append(row)

    if args.json:
        import json

        print(json.dumps({"rows": rows, "failed": failed}, indent=2, ensure_ascii=False))
    else:
        print("pack density (en≥20 · de/ru/es/pl/sv/uk≥12)")
        for r in rows:
            mark = (
                "OK"
                if not any(f.startswith(str(r["pack"]) + "/") for f in failed)
                else "FAIL"
            )
            locs = " ".join(f"{loc}={r[loc]}" for loc in FLOORS)
            print(f"  {mark} {r['pack']}: {locs}")
        if failed:
            print("failed:", ", ".join(failed))
        else:
            print(f"all {len(rows)} packs green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
