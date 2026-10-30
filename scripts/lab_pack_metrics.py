#!/usr/bin/env python3
"""Measure known-rule recall for a lab pack fixture tree (local only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lexaudit.config import LexauditConfig  # noqa: E402
from lexaudit.core.pipeline import run_locale_audit  # noqa: E402


def _patterns_for_locale(rules_dir: Path, locale: str) -> set[str]:
    path = rules_dir / f"{locale}.yaml"
    if not path.is_file():
        return set()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: set[str] = set()
    for row in data.get("rules") or []:
        if not isinstance(row, dict):
            continue
        pat = str(row.get("pattern") or "").strip().casefold()
        if pat:
            out.add(pat)
    return out


def measure(pack: str, locale: str) -> dict[str, object]:
    # Content SSOT is packs/<id> after promote; _lab may be a thin stub.
    from lexaudit.packs import pack_content_dir

    pack_dir = pack_content_dir(pack, prefer_lab=True)
    rules = pack_dir / "calques"
    fixtures = pack_dir / "fixtures" / locale
    if not rules.is_dir() or not fixtures.is_dir():
        raise FileNotFoundError(f"missing rules or fixtures under {pack_dir}")

    cfg = LexauditConfig(
        repo_root=pack_dir,
        locales=[locale],
        sources=["files"],
        files_paths=(fixtures.resolve(),),
        calque_rules_dir=rules.resolve(),
        output_dir=(ROOT / "tmp" / "lab-packs" / pack / locale).resolve(),
    )
    words, pages, _ = run_locale_audit(cfg, locale, freeze_generated_at="1970-01-01T00:00:00Z")
    flagged = {
        w.normalized
        for w in words
        if w.status in {"calque", "invented", "suspect", "foreign"}
        or (w.tier in {"confirmed", "likely"} and w.status != "ok")
    }
    defect_pages = [p for p in pages if "defect-known" in p.path]
    clean_pages = [p for p in pages if "clean" in p.path]
    known_hits = sum(1 for w in words if w.status == "calque")

    patterns = _patterns_for_locale(rules, locale)
    defect_text = ""
    if defect_pages:
        # pages store relative paths; read fixture file by basename match
        for path in fixtures.glob("*defect-known*"):
            defect_text += path.read_text(encoding="utf-8").casefold() + "\n"
    expected = {p for p in patterns if p in defect_text}
    found = {
        w.normalized.casefold()
        for w in words
        if w.status == "calque" and w.normalized.casefold() in expected
    }
    recall = (len(found) / len(expected)) if expected else 0.0

    report: dict[str, object] = {
        "pack": pack,
        "locale": locale,
        "pages": len(pages),
        "calque_words": known_hits,
        "flagged_unique": len(flagged),
        "known_patterns_in_defect": len(expected),
        "known_patterns_hit": len(found),
        "known_rule_recall": round(recall, 4),
        "top_pages": [
            {"path": p.path, "score": p.score, "unique_suspects": p.unique_suspects}
            for p in pages[:6]
        ],
        "defect_known_top": bool(defect_pages)
        and bool(pages)
        and pages[0].path == defect_pages[0].path,
        "clean_score_max": max((p.score for p in clean_pages), default=0.0),
        "defect_known_score": defect_pages[0].score if defect_pages else None,
    }
    ok = True
    if defect_pages and clean_pages:
        ok = report["defect_known_score"] is not None and float(
            report["defect_known_score"]
        ) > float(report["clean_score_max"])
    if expected:
        ok = ok and recall >= 0.85
    report["lab_rank_ok"] = ok
    report["lab_recall_ok"] = (not expected) or recall >= 0.85
    return report


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

    try:
        report = measure(args.pack, args.locale)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    ok = bool(report["lab_rank_ok"])
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            f"{args.pack}/{args.locale}: calques={report['calque_words']} "
            f"recall={report['known_rule_recall']} "
            f"lab_rank_ok={ok} clean_max={report['clean_score_max']} "
            f"defect={report['defect_known_score']}"
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
