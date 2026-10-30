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
    detect_pair_leftovers,
    intentional_loans_for_target,
    length_ratio_signal,
    load_extra_loans,
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
    p.add_argument(
        "--extra-loans",
        type=Path,
        default=None,
        help="Optional token list merged into allowlist for non-seeded files",
    )
    p.add_argument(
        "--extra-loans-locales",
        default="",
        help="Comma locales that may merge --extra-loans (empty = all non-seeded)",
    )
    p.add_argument(
        "--extra-loans-basenames",
        default="",
        help="Comma basenames that may merge --extra-loans (empty = all non-seeded)",
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
    p.add_argument(
        "--source-locale",
        default="en",
        help="Source locale folder under --fixtures (default en)",
    )
    args = p.parse_args()

    rows = _load_gold(args.gold)
    leftover_gold: set[tuple[str, str, str]] = set()
    intentional_gold: set[tuple[str, str, str]] = set()
    for row in rows:
        if row.get("source_locale", args.source_locale) != args.source_locale:
            continue
        key = (row["target_locale"], row["rel_path"], row["token"].casefold())
        if row["label"] == "leftover":
            leftover_gold.add(key)
        elif row["label"] == "intentional":
            intentional_gold.add(key)

    extra = load_extra_loans(args.extra_loans)
    extra_locales = frozenset(
        x.strip().casefold()
        for x in args.extra_loans_locales.split(",")
        if x.strip()
    )
    extra_basenames = {
        x.strip() for x in args.extra_loans_basenames.split(",") if x.strip()
    }

    predicted: set[tuple[str, str, str]] = set()
    length_ratios: list[float] = []
    official_alarms = 0
    src_locale = args.source_locale
    target_locales = sorted(
        {
            r["target_locale"]
            for r in rows
            if r.get("source_locale", src_locale) == src_locale
        }
        | ({"ru", "de"} if src_locale == "en" else set())
    )
    for tgt_loc in target_locales:
        if tgt_loc == src_locale:
            continue
        src_root = args.fixtures / src_locale
        tgt_root = args.fixtures / tgt_loc
        if not tgt_root.is_dir():
            continue
        # Empty --extra-loans-locales = allow extras on every target (lab metrics).
        # Basename filter still scopes to polished pages when set.
        loc_ok = (not extra_locales) or (tgt_loc.casefold() in extra_locales)
        for md in sorted(tgt_root.glob("*.md")):
            rel = md.name
            src = src_root / rel
            if not src.is_file():
                continue
            src_text = src.read_text(encoding="utf-8")
            tgt_text = md.read_text(encoding="utf-8")
            length_ratios.append(length_ratio_signal(src_text, tgt_text))
            base_ok = (not extra_basenames) or (rel in extra_basenames)
            if rel == args.seeded_basename:
                loans = DEFAULT_INTENTIONAL_LOANS
            elif loc_ok and base_ok and extra:
                # Metrics: empty locales means "all targets" — pass target itself.
                loans = intentional_loans_for_target(
                    tgt_loc,
                    extra=extra,
                    extra_locales=extra_locales or frozenset({tgt_loc.casefold()}),
                )
            else:
                loans = DEFAULT_INTENTIONAL_LOANS
            hits = detect_pair_leftovers(
                src_text,
                tgt_text,
                source_locale=src_locale,
                target_locale=tgt_loc,
                path=f"{tgt_loc}/{rel}",
                intentional_loans=loans if src_locale not in {"ru", "uk"} else None,
            )
            seeded_exists = (args.fixtures / src_locale / args.seeded_basename).is_file()
            if seeded_exists and rel != args.seeded_basename:
                official_alarms += len(hits)
            for w in hits:
                # Soft page signals are ranking-only — keep out of P/R gold.
                if (w.reason or "").startswith("bilingual-length-ratio"):
                    continue
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
