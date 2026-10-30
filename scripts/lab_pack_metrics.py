#!/usr/bin/env python3
"""Measure known-rule recall for a lab pack fixture tree (local only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lexaudit.config import LexauditConfig  # noqa: E402
from lexaudit.core.pipeline import run_locale_audit  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--pack",
        required=True,
        help="Pack id under packs/_lab/ (e.g. saas-ui-v0)",
    )
    p.add_argument("--locale", default="en")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    pack_dir = ROOT / "packs" / "_lab" / args.pack
    rules = pack_dir / "calques"
    fixtures = pack_dir / "fixtures" / args.locale
    if not rules.is_dir() or not fixtures.is_dir():
        print(f"missing rules or fixtures under {pack_dir}", file=sys.stderr)
        return 2

    cfg = LexauditConfig(
        repo_root=pack_dir,
        locales=[args.locale],
        sources=["files"],
        files_paths=(fixtures.resolve(),),
        calque_rules_dir=rules.resolve(),
        output_dir=(ROOT / "tmp" / "lab-packs" / args.pack / args.locale).resolve(),
    )
    words, pages, _ = run_locale_audit(
        cfg, args.locale, freeze_generated_at="1970-01-01T00:00:00Z"
    )
    flagged = {
        w.normalized
        for w in words
        if w.status in {"calque", "invented", "suspect", "foreign"}
        or (w.tier in {"confirmed", "likely"} and w.status != "ok")
    }
    # Known defects file should contribute calques; clean should not dominate.
    defect_pages = [p for p in pages if "defect-known" in p.path]
    clean_pages = [p for p in pages if "clean" in p.path]
    known_hits = sum(1 for w in words if w.status == "calque")
    report = {
        "pack": args.pack,
        "locale": args.locale,
        "pages": len(pages),
        "calque_words": known_hits,
        "flagged_unique": len(flagged),
        "top_pages": [
            {"path": p.path, "score": p.score, "unique_suspects": p.unique_suspects}
            for p in pages[:6]
        ],
        "defect_known_top": bool(defect_pages) and pages[0].path == defect_pages[0].path
        if pages and defect_pages
        else False,
        "clean_score_max": max((p.score for p in clean_pages), default=0.0),
        "defect_known_score": defect_pages[0].score if defect_pages else None,
    }
    # Soft ship bar for lab: defect-known outranks clean when both exist.
    ok = True
    if defect_pages and clean_pages:
        ok = report["defect_known_score"] is not None and report["defect_known_score"] > report[
            "clean_score_max"
        ]
    report["lab_rank_ok"] = ok
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            f"{args.pack}/{args.locale}: calques={known_hits} "
            f"lab_rank_ok={ok} clean_max={report['clean_score_max']} "
            f"defect={report['defect_known_score']}"
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
