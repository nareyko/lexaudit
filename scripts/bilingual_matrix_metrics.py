#!/usr/bin/env python3
"""Run bilingual leftover metrics for directed locale pairs (lab research).

Default ``--mode all`` = all pairs among V1 locales en/de/pl/ru/es/sv/uk (42).
"""

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
    length_ratio_signal,
    matrix_pairs,
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


def _score_pair(
    *,
    fixtures: Path,
    gold_rows: list[dict[str, str]],
    source_locale: str,
    target_locale: str,
    extra: frozenset[str],
    extra_locales: set[str],
    extra_basenames: set[str],
    seeded_basename: str,
    min_precision: float,
    min_recall: float,
) -> dict[str, object]:
    leftover_gold: set[tuple[str, str]] = set()
    intentional_gold: set[tuple[str, str]] = set()
    for row in gold_rows:
        if row.get("source_locale", "en") != source_locale:
            continue
        if row.get("target_locale") != target_locale:
            continue
        key = (row["rel_path"], row["token"].casefold())
        if row["label"] == "leftover":
            leftover_gold.add(key)
        elif row["label"] == "intentional":
            intentional_gold.add(key)

    src_root = fixtures / source_locale
    tgt_root = fixtures / target_locale
    predicted: set[tuple[str, str]] = set()
    length_ratios: list[float] = []
    page_count = 0
    alarm_count = 0

    if src_root.is_dir() and tgt_root.is_dir():
        loc_ok = (not extra_locales) or (target_locale.casefold() in extra_locales)
        for md in sorted(tgt_root.glob("*.md")):
            rel = md.name
            src = src_root / rel
            if not src.is_file():
                continue
            page_count += 1
            src_text = src.read_text(encoding="utf-8")
            tgt_text = md.read_text(encoding="utf-8")
            length_ratios.append(length_ratio_signal(src_text, tgt_text))
            base_ok = (not extra_basenames) or (rel in extra_basenames)
            if rel == seeded_basename:
                loans: frozenset[str] = DEFAULT_INTENTIONAL_LOANS
            elif loc_ok and base_ok and extra:
                loans = frozenset(DEFAULT_INTENTIONAL_LOANS | extra)
            else:
                loans = DEFAULT_INTENTIONAL_LOANS
            # Cyrillic detector ignores Latin loan allowlist; pass through anyway
            hits = detect_pair_leftovers(
                src_text,
                tgt_text,
                source_locale=source_locale,
                target_locale=target_locale,
                path=f"{target_locale}/{rel}",
                intentional_loans=loans if source_locale not in {"ru", "uk"} else None,
            )
            for w in hits:
                if (w.reason or "").startswith("bilingual-length-ratio"):
                    continue
                alarm_count += 1
                predicted.add((rel, w.normalized))

    gold_paths = {rel for rel, _ in leftover_gold | intentional_gold}
    has_gold = bool(leftover_gold or intentional_gold)
    predicted_scored = (
        {k for k in predicted if k[0] in gold_paths} if gold_paths else predicted
    )

    tp = len(predicted_scored & leftover_gold)
    fp = len(predicted_scored - leftover_gold)
    fn = len(leftover_gold - predicted_scored)
    precision = tp / (tp + fp) if (tp + fp) else (1.0 if has_gold and not predicted_scored else 0.0)
    recall = tp / (tp + fn) if (tp + fn) else (1.0 if has_gold and not leftover_gold else 0.0)
    # When no gold: unsupervised — precision/recall null
    if not has_gold:
        precision_out: float | None = None
        recall_out: float | None = None
        f1_out: float | None = None
        ship: bool | None = None
    else:
        precision_out = round(precision, 4)
        recall_out = round(recall, 4)
        f1_out = (
            round(2 * precision * recall / (precision + recall), 4)
            if (precision + recall)
            else 0.0
        )
        intentional_fp = predicted_scored & intentional_gold
        ship = (
            precision >= min_precision
            and recall >= min_recall
            and len(intentional_fp) == 0
        )

    intentional_fp_list = sorted(
        f"{rel}:{tok}" for rel, tok in (predicted_scored & intentional_gold)
    )
    return {
        "source_locale": source_locale,
        "target_locale": target_locale,
        "pair": f"{source_locale}→{target_locale}",
        "pages": page_count,
        "alarms": alarm_count,
        "gold_leftover": len(leftover_gold),
        "gold_intentional": len(intentional_gold),
        "has_gold": has_gold,
        "tp": tp if has_gold else None,
        "fp": fp if has_gold else None,
        "fn": fn if has_gold else None,
        "precision": precision_out,
        "recall": recall_out,
        "f1": f1_out,
        "intentional_fp": intentional_fp_list if has_gold else [],
        "length_ratio_mean": round(sum(length_ratios) / max(1, len(length_ratios)), 4),
        "lab_ship_bar": ship,
        "detector": (
            "cyrillic-overlap"
            if source_locale in {"ru", "uk"}
            else "latin-overlap"
        ),
        "false_positives": sorted(
            f"{a}:{b}" for a, b in (predicted_scored - leftover_gold)
        )[:12]
        if has_gold
        else [],
        "false_negatives": sorted(
            f"{a}:{b}" for a, b in (leftover_gold - predicted_scored)
        )[:12]
        if has_gold
        else [],
    }


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
    p.add_argument("--extra-loans", type=Path, default=None)
    p.add_argument("--extra-loans-locales", default="")
    p.add_argument("--extra-loans-basenames", default="")
    p.add_argument("--seeded-basename", default="seeded-leak.md")
    p.add_argument("--min-precision", type=float, default=0.75)
    p.add_argument("--min-recall", type=float, default=0.60)
    p.add_argument("--label", default="heldout-matrix")
    p.add_argument(
        "--mode",
        choices=("all", "anchors", "anchors_x_others"),
        default="all",
        help="all=42 V1 pairs; anchors=en/de/ru; anchors_x_others=anchors+es/pl/sv/uk",
    )
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional JSON report path",
    )
    args = p.parse_args()

    gold_rows = _load_gold(args.gold) if args.gold.is_file() else []
    extra = _load_extra_loans(args.extra_loans)
    extra_locales = {
        x.strip().casefold()
        for x in args.extra_loans_locales.split(",")
        if x.strip()
    }
    extra_basenames = {
        x.strip() for x in args.extra_loans_basenames.split(",") if x.strip()
    }

    pairs = []
    for src, tgt in matrix_pairs(mode=args.mode):
        pairs.append(
            _score_pair(
                fixtures=args.fixtures,
                gold_rows=gold_rows,
                source_locale=src,
                target_locale=tgt,
                extra=extra,
                extra_locales=extra_locales,
                extra_basenames=extra_basenames,
                seeded_basename=args.seeded_basename,
                min_precision=args.min_precision,
                min_recall=args.min_recall,
            )
        )

    scored = [r for r in pairs if r["has_gold"]]
    ship_ok = all(r["lab_ship_bar"] is True for r in scored) if scored else False
    failed = [r for r in scored if r["lab_ship_bar"] is not True]
    report = {
        "label": args.label,
        "mode": args.mode,
        "fixtures": str(args.fixtures),
        "pairs": pairs,
        "scored_pairs": len(scored),
        "unsupervised_pairs": sum(1 for r in pairs if not r["has_gold"]),
        "lab_ship_bar_all_scored": ship_ok,
        "failed_pairs": [r["pair"] for r in failed],
        "by_anchor": {
            loc: [
                r["pair"]
                for r in pairs
                if loc in (r["source_locale"], r["target_locale"])
            ]
            for loc in ("en", "de", "ru", "es", "pl", "sv", "uk")
        },
    }

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            f"bilingual matrix {args.label} mode={args.mode}: "
            f"pairs={len(pairs)} scored={len(scored)} unsupervised={report['unsupervised_pairs']} "
            f"ship_all={ship_ok} failed={report['failed_pairs']}"
        )
        for r in pairs:
            if r["has_gold"]:
                print(
                    f"  {r['pair']:7} [{r['detector']}] "
                    f"P={r['precision']} R={r['recall']} F1={r['f1']} "
                    f"alarms={r['alarms']} ship={r['lab_ship_bar']}"
                )
            else:
                print(
                    f"  {r['pair']:7} [{r['detector']}] unsupervised "
                    f"alarms={r['alarms']} pages={r['pages']} "
                    f"len_ratio={r['length_ratio_mean']}"
                )
        if args.out:
            print(f"wrote {args.out}")
    return 0 if (ship_ok or not scored) else 1


if __name__ == "__main__":
    raise SystemExit(main())
