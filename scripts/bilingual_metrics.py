#!/usr/bin/env python3
"""Precision/recall for bilingual Latin-leak on held-out gold CSV (lab only)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lexaudit.detectors.bilingual import (  # noqa: E402
    DEFAULT_INTENTIONAL_LOANS,
    untranslated_latin_in_target,
)


def _load_gold(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fixtures",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "bilingual" / "heldout",
    )
    p.add_argument(
        "--gold",
        type=Path,
        default=ROOT
        / "tests"
        / "fixtures"
        / "bilingual"
        / "heldout"
        / "gold-leftovers.csv",
    )
    p.add_argument("--json", action="store_true")
    p.add_argument("--min-precision", type=float, default=0.75)
    p.add_argument("--min-recall", type=float, default=0.60)
    args = p.parse_args()

    rows = _load_gold(args.gold)
    leftover_gold: set[tuple[str, str, str]] = set()
    intentional_gold: set[tuple[str, str, str]] = set()
    for row in rows:
        key = (row["target_locale"], row["rel_path"], row["token"].casefold())
        if row["label"] == "leftover":
            leftover_gold.add(key)
        elif row["label"] == "intentional":
            intentional_gold.add(key)

    predicted: set[tuple[str, str, str]] = set()
    length_ratios: list[float] = []
    for tgt_loc in sorted({r["target_locale"] for r in rows}):
        src_root = args.fixtures / "en"
        tgt_root = args.fixtures / tgt_loc
        for md in sorted(tgt_root.glob("*.md")):
            rel = md.name
            src = src_root / rel
            if not src.is_file():
                continue
            src_text = src.read_text(encoding="utf-8")
            tgt_text = md.read_text(encoding="utf-8")
            from lexaudit.detectors.bilingual import length_ratio_signal

            length_ratios.append(length_ratio_signal(src_text, tgt_text))
            hits = untranslated_latin_in_target(
                src_text,
                tgt_text,
                path=f"{tgt_loc}/{rel}",
                intentional_loans=DEFAULT_INTENTIONAL_LOANS,
            )
            for w in hits:
                predicted.add((tgt_loc, rel, w.normalized))

    tp = len(predicted & leftover_gold)
    fp = len(predicted - leftover_gold)
    fn = len(leftover_gold - predicted)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    # Intentional tokens must not be predicted
    intentional_fp = predicted & intentional_gold

    report = {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "intentional_fp": sorted(f"{a}/{b}:{c}" for a, b, c in intentional_fp),
        "false_positives": sorted(f"{a}/{b}:{c}" for a, b, c in (predicted - leftover_gold))[:30],
        "false_negatives": sorted(f"{a}/{b}:{c}" for a, b, c in (leftover_gold - predicted))[:30],
        "length_ratio_mean": round(sum(length_ratios) / max(1, len(length_ratios)), 4),
        "lab_precision_ok": precision >= args.min_precision,
        "lab_recall_ok": recall >= args.min_recall,
        "lab_intentional_clean": len(intentional_fp) == 0,
    }
    ok = (
        report["lab_precision_ok"]
        and report["lab_recall_ok"]
        and report["lab_intentional_clean"]
    )
    report["lab_ship_bar"] = ok
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            f"bilingual held-out: P={precision:.3f} R={recall:.3f} F1={f1:.3f} "
            f"intentional_fp={len(intentional_fp)} ship_bar={ok}"
        )
        if report["false_negatives"]:
            print("FN sample:", ", ".join(report["false_negatives"][:8]))
        if report["false_positives"]:
            print("FP sample:", ", ".join(report["false_positives"][:8]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
