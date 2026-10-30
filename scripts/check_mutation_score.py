#!/usr/bin/env python3
"""Fail if mutmut kill rate is below threshold (default 80%).

Only mutants whose source file is listed in ``setup.cfg`` ``[mutmut]
paths_to_mutate`` are scored — matches the CI mutate scope after path trims.
"""

from __future__ import annotations

import argparse
import configparser
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def paths_to_mutate() -> set[str]:
    cfg = configparser.ConfigParser()
    cfg.read(ROOT / "setup.cfg")
    raw = cfg.get("mutmut", "paths_to_mutate", fallback="")
    return {p.strip() for p in raw.split(",") if p.strip()}


def score(cache: Path, *, only_paths: set[str] | None) -> tuple[int, int, float, dict[str, int]]:
    con = sqlite3.connect(cache)
    if only_paths:
        q = ",".join("?" * len(only_paths))
        rows = dict(
            con.execute(
                f"""
                select m.status, count(*)
                from Mutant m
                join Line l on m.line = l.id
                join SourceFile sf on l.sourcefile = sf.id
                where sf.filename in ({q})
                group by m.status
                """,
                tuple(sorted(only_paths)),
            ).fetchall()
        )
    else:
        rows = dict(con.execute("select status, count(*) from Mutant group by status").fetchall())
    killed = int(rows.get("ok_killed", 0))
    survived = int(rows.get("bad_survived", 0))
    # treat timeouts / suspicious / leftover untested as not-killed for gate
    other = sum(int(v) for k, v in rows.items() if k not in {"ok_killed", "bad_survived"})
    total = killed + survived + other
    rate = (killed / total * 100.0) if total else 0.0
    return killed, total, rate, rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--cache", type=Path, default=ROOT / ".mutmut-cache")
    p.add_argument("--min-percent", type=float, default=80.0)
    p.add_argument(
        "--all-files",
        action="store_true",
        help="Score every mutant in the cache (ignore setup.cfg paths_to_mutate)",
    )
    args = p.parse_args()
    if not args.cache.is_file():
        print(f"missing mutmut cache: {args.cache}", file=sys.stderr)
        return 2
    scope = None if args.all_files else paths_to_mutate()
    killed, total, rate, rows = score(args.cache, only_paths=scope)
    scope_note = "setup.cfg paths" if scope else "all cache files"
    print(
        f"mutation score: {rate:.1f}% ({killed}/{total} killed); "
        f"gate ≥ {args.min_percent:.0f}% [{scope_note}]"
    )
    print(f"  status breakdown: {rows}")
    if total == 0:
        print("FAIL: no mutants in scope", file=sys.stderr)
        return 1
    if rate + 1e-9 < args.min_percent:
        print("FAIL: mutation kill rate below threshold", file=sys.stderr)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
