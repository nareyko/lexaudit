#!/usr/bin/env python3
"""Precision/recall for bilingual Latin-leak on gold CSV (lab only)."""

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
    length_ratio_signal,
    untranslated_latin_in_target,
)


def _load_gold(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _load_extra_loans(path: Path | None) -> frozenset[str]:
    if path is None or not path.is_file():
        return frozenset()
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip().casefold()
        if not s or s.startswith("#"):
            continue
        out.add(s)
    return frozenset(out)


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
    p.add_argument(
        "--extra-loans",
        type=Path,
        default=None,
        help="Optional token list merged into allowlist for non-seeded files",
    )
    p.add_argument(
        "--seeded-basename",
        default="seeded-leak.md",
        help="Basename that keeps DEFAULT loans only (no --extra-loans merge)",
    )
    p.add_argument("--json", action="store_true")
    p.add_argument("--min-precision", type=float, default=0.75)
    p.add_argument("--min-recall", type=float, default=0.60)
    p.add_argument("--label", default="held-out", help="Report label")
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

    extra = _load_extra_loans(args.extra_loans)
    loans_official = frozenset(DEFAULT_INTENTIONAL_LOANS | extra)
    loans_seeded = DEFAULT_INTENTIONAL_LOANS

    predicted: set[tuple[str, str, str]] = set()
    length_ratios: list[float] = []
    official_alarms = 0
    for tgt_loc in sorted({r["target_locale"] for r in rows} | {"ru", "de"}):
        src_root = args.fixtures / "en"
        tgt_root = args.fixtures / tgt_loc
        if not tgt_root.is_dir():
            continue
        for md in sorted(tgt_root.glob("*.md")):
            rel = md.name
            src = src_root / rel
            if not src.is_file():
                continue
            src_text = src.read_text(encoding="utf-8")
            tgt_text = md.read_text(encoding="utf-8")
            length_ratios.append(length_ratio_signal(src_text, tgt_text))
            loans = loans_seeded if rel == args.seeded_basename else loans_official
            hits = untranslated_latin_in_target(
                src_text,
                tgt_text,
                path=f"{tgt_loc}/{rel}",
                intentional_loans=loans,
            )
            seeded_exists = (args.fixtures / "en" / args.seeded_basename).is_file()
            if seeded_exists and rel != args.seeded_basename:
                official_alarms += len(hits)
            for w in hits:
                predicted.add((tgt_loc, rel, w.normalized))

    # If gold only lists seeded rows, restrict scoring to those paths
    gold_paths = {rel for _, rel, _ in leftover_gold | intentional_gold}
    predicted_scored = (
        {k for k in predicted if k[1] in gold_paths} if gold_paths else predicted
    )

    tp = len(predicted_scored & leftover_gold)
    fp = len(predicted_scored - leftover_gold)
    fn = len(leftover_gold - predicted_scored)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    intentional_fp = predicted_scored & intentional_gold

    report = {
        "label": args.label,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "intentional_fp": sorted(f"{a}/{b}:{c}" for a, b, c in intentional_fp),
        "false_positives": sorted(
            f"{a}/{b}:{c}" for a, b, c in (predicted_scored - leftover_gold)
        )[:30],
        "false_negatives": sorted(
            f"{a}/{b}:{c}" for a, b, c in (leftover_gold - predicted_scored)
        )[:30],
        "length_ratio_mean": round(sum(length_ratios) / max(1, len(length_ratios)), 4),
        "official_alarm_count": official_alarms,
        "extra_loans": len(extra),
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
            f"bilingual {args.label}: P={precision:.3f} R={recall:.3f} F1={f1:.3f} "
            f"intentional_fp={len(intentional_fp)} official_alarms={official_alarms} "
            f"ship_bar={ok}"
        )
        if report["false_negatives"]:
            print("FN sample:", ", ".join(report["false_negatives"][:8]))
        if report["false_positives"]:
            print("FP sample:", ", ".join(report["false_positives"][:8]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
