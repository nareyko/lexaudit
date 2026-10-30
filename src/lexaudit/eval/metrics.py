"""Precision / recall on gold sets (mark unreviewed when owner review missing)."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from lexaudit.core.types import ClassifiedWord, PageSuspectRank
from lexaudit.detectors.calque import needle_matches_norm

# template is not an anomaly for rewrite-queue metrics (still a vocab status).
ANOMALY = frozenset({"foreign", "calque", "invented", "morph-miss", "suspect", "unsure"})
NEEDLE_HIT_STATUSES = frozenset({"calque", "invented"})


def load_gold_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def gold_is_anomaly(label: str) -> bool:
    return label in ANOMALY


def pred_is_anomaly(status: str) -> bool:
    return status in ANOMALY


def compute_metrics(
    gold_rows: list[dict[str, Any]],
    predictions: dict[str, ClassifiedWord],
    *,
    review_status: str = "unreviewed",
) -> dict[str, Any]:
    """predictions keyed by normalized word (casefold)."""
    tp = fp = fn = tn = 0
    by_status: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    by_tier: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0})
    by_detector: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0})

    for g in gold_rows:
        norm = g["word"].casefold()
        gold_pos = gold_is_anomaly(g["label"])
        pred = predictions.get(norm)
        if pred is None:
            if gold_pos:
                fn += 1
                by_status[g["label"]]["fn"] += 1
            continue
        pred_pos = pred_is_anomaly(pred.status)
        if gold_pos and pred_pos:
            tp += 1
            by_status[g["label"]]["tp"] += 1
            tier = pred.tier or "none"
            by_tier[tier]["tp"] += 1
            for d in pred.detectors:
                by_detector[d]["tp"] += 1
        elif (not gold_pos) and pred_pos:
            fp += 1
            by_status[pred.status]["fp"] += 1
            tier = pred.tier or "none"
            by_tier[tier]["fp"] += 1
            for d in pred.detectors:
                by_detector[d]["fp"] += 1
        elif gold_pos and not pred_pos:
            fn += 1
            by_status[g["label"]]["fn"] += 1
        else:
            tn += 1

    def pr(tp_: int, fp_: int, fn_: int) -> dict[str, float]:
        precision = tp_ / (tp_ + fp_) if (tp_ + fp_) else 0.0
        recall = tp_ / (tp_ + fn_) if (tp_ + fn_) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        return {"precision": precision, "recall": recall, "f1": f1}

    return {
        "counts": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "overall": pr(tp, fp, fn),
        "by_status": {k: dict(v) for k, v in sorted(by_status.items())},
        "by_tier": {k: dict(v) for k, v in sorted(by_tier.items())},
        "by_detector": {k: dict(v) for k, v in sorted(by_detector.items())},
        "review_status": review_status,
    }


def page_at_k(
    ranked: Sequence[PageSuspectRank],
    gold_pages: Sequence[str],
    *,
    k: int = 10,
) -> dict[str, Any]:
    """Precision@K for page ranking: fraction of top-K paths in the gold set."""
    gold = {p for p in gold_pages}
    top = [r.path for r in ranked[:k]]
    hits = sum(1 for p in top if p in gold or any(g in p or p in g for g in gold))
    precision = hits / k if k else 0.0
    return {"k": k, "hits": hits, "precision": precision, "top": top}


def needle_recall(
    needles: Sequence[str],
    words: Sequence[ClassifiedWord],
    *,
    locale: str = "en",
    hit_statuses: frozenset[str] = NEEDLE_HIT_STATUSES,
) -> dict[str, Any]:
    """
    Fraction of needles that appear in ``words`` and are labeled calque/invented.

    Needles with no corpus match are skipped (not counted as misses).
    Target after I1: ≥ 0.9.
    """
    details: list[dict[str, Any]] = []
    evaluated = 0
    hits = 0
    for needle in needles:
        matching = [w for w in words if needle_matches_norm(w.normalized, needle, locale)]
        if not matching:
            details.append({"needle": needle, "present": False, "hit": False, "statuses": []})
            continue
        evaluated += 1
        statuses = sorted({w.status for w in matching})
        hit = any(w.status in hit_statuses for w in matching)
        if hit:
            hits += 1
        details.append(
            {
                "needle": needle,
                "present": True,
                "hit": hit,
                "statuses": statuses,
                "words": sorted({w.normalized for w in matching}),
            }
        )
    recall = hits / evaluated if evaluated else 1.0
    return {
        "recall": recall,
        "hits": hits,
        "evaluated": evaluated,
        "skipped_absent": sum(1 for d in details if not d["present"]),
        "details": details,
    }


def clear_regression(
    slugs: Sequence[str],
    words: Sequence[ClassifiedWord],
    needles: Sequence[str],
    *,
    locale: str = "en",
) -> dict[str, Any]:
    """
    CLEAR check: for each slug, none of the needles remain as calque/invented/suspect
    on paths containing that slug (ship queue #1-#11 regression).
    """
    results: list[dict[str, Any]] = []
    all_clear = True
    for slug in slugs:
        offenders: list[dict[str, str]] = []
        for w in words:
            if w.status not in ANOMALY:
                continue
            if not any(needle_matches_norm(w.normalized, n, locale) for n in needles):
                continue
            paths = [s.path for s in w.samples if slug in s.path]
            if paths:
                offenders.append(
                    {
                        "word": w.normalized,
                        "status": w.status,
                        "path": paths[0],
                    }
                )
        clear = not offenders
        if not clear:
            all_clear = False
        results.append({"slug": slug, "clear": clear, "offenders": offenders})
    return {"all_clear": all_clear, "results": results}


def render_metrics_md(metrics: dict[str, Any], title: str) -> str:
    o = metrics["overall"]
    c = metrics["counts"]
    lines = [
        f"# {title}",
        "",
        f"Review status: **{metrics.get('review_status', 'unreviewed')}**",
        "",
        f"TP={c['tp']} FP={c['fp']} FN={c['fn']} TN={c['tn']}",
        "",
        f"precision={o['precision']:.3f} recall={o['recall']:.3f} f1={o['f1']:.3f}",
        "",
        "## By detector",
        "",
        "| detector | tp | fp |",
        "|---|---|---|",
    ]
    for d, v in metrics.get("by_detector", {}).items():
        lines.append(f"| {d} | {v.get('tp', 0)} | {v.get('fp', 0)} |")
    lines.extend(["", "## By tier", "", "| tier | tp | fp |", "|---|---|---|"])
    for t, v in metrics.get("by_tier", {}).items():
        lines.append(f"| {t} | {v.get('tp', 0)} | {v.get('fp', 0)} |")
    lines.append("")
    return "\n".join(lines)
