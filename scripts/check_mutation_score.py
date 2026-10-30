#!/usr/bin/env python3
"""Fail if mutmut kill rate is below threshold (default 80%)."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


def score(cache: Path) -> tuple[int, int, float]:
    con = sqlite3.connect(cache)
    rows = dict(con.execute("select status, count(*) from Mutant group by status").fetchall())
    killed = int(rows.get("ok_killed", 0))
    survived = int(rows.get("bad_survived", 0))
    # treat timeouts / suspicious as not-killed for gate purposes
    other = sum(int(v) for k, v in rows.items() if k not in {"ok_killed", "bad_survived"})
    total = killed + survived + other
    rate = (killed / total * 100.0) if total else 0.0
    return killed, total, rate


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--cache", type=Path, default=Path(".mutmut-cache"))
    p.add_argument("--min-percent", type=float, default=80.0)
    args = p.parse_args()
    if not args.cache.is_file():
        print(f"missing mutmut cache: {args.cache}", file=sys.stderr)
        return 2
    killed, total, rate = score(args.cache)
    print(f"mutation score: {rate:.1f}% ({killed}/{total} killed); gate ≥ {args.min_percent:.0f}%")
    if rate + 1e-9 < args.min_percent:
        print("FAIL: mutation kill rate below threshold", file=sys.stderr)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
