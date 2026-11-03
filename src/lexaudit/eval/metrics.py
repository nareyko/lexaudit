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


def _path_in_gold(path: str, gold: set[str]) -> bool:
    if path in gold:
        return True
    return any(g in path or path in g for g in gold)


def page_precision_at_k(
    ranked: Sequence[PageSuspectRank],
    bad_set: Sequence[str],
    k: int,
) -> dict[str, Any]:
    """
    Page Precision@K = |{top-K ∩ bad}| / K.

    ``bad_set`` holds gold defective page paths or path substrings (slugs).
    """
    gold = {p for p in bad_set}
    top = [r.path for r in ranked[:k]]
    hits = sum(1 for p in top if _path_in_gold(p, gold))
    precision = hits / k if k else 0.0
    return {"k": k, "hits": hits, "precision": precision, "top": top}


def page_recall_at_k(
    ranked: Sequence[PageSuspectRank],
    bad_set: Sequence[str],
    k: int,
) -> dict[str, Any]:
    """
    Page Recall@K = |{top-K ∩ bad}| / |bad|.

    With exactly 3 defective pages and K=2, perfect ranking yields R@2 = 2/3.
    """
    gold = {p for p in bad_set}
    n_bad = len(gold)
    top = [r.path for r in ranked[:k]]
    hits = sum(1 for p in top if _path_in_gold(p, gold))
    recall = hits / n_bad if n_bad else 0.0
    return {"k": k, "hits": hits, "n_bad": n_bad, "recall": recall, "top": top}


def page_at_k(
    ranked: Sequence[PageSuspectRank],
    gold_pages: Sequence[str],
    *,
    k: int = 10,
) -> dict[str, Any]:
    """Backward-compatible alias for :func:`page_precision_at_k`."""
    return page_precision_at_k(ranked, gold_pages, k)


def word_precision_recall(
    words: Sequence[ClassifiedWord],
    gold_known: Sequence[str],
    gold_unseen: Sequence[str],
    *,
    locale: str = "en",
    hit_statuses: frozenset[str] = NEEDLE_HIT_STATUSES,
) -> dict[str, Any]:
    """
    Word-level precision/recall split into known rules vs unseen neologisms.

    A gold token counts as a hit when any matching classified word has a status
    in ``hit_statuses`` (default: calque/invented). Precision uses unique
    predicted anomaly norms that match any gold token as TP, else FP.
    """
    known = list(gold_known)
    unseen = list(gold_unseen)
    combined = [*known, *unseen]

    def _hits(needles: Sequence[str]) -> tuple[int, int]:
        evaluated = 0
        hits = 0
        for needle in needles:
            matching = [w for w in words if needle_matches_norm(w.normalized, needle, locale)]
            if not matching:
                continue
            evaluated += 1
            if any(w.status in hit_statuses for w in matching):
                hits += 1
        return hits, evaluated

    known_hits, known_eval = _hits(known)
    unseen_hits, unseen_eval = _hits(unseen)
    comb_hits, comb_eval = _hits(combined)

    gold_norms: set[str] = set()
    for needle in combined:
        for w in words:
            if needle_matches_norm(w.normalized, needle, locale):
                gold_norms.add(w.normalized)

    pred_pos = [w for w in words if pred_is_anomaly(w.status)]
    tp = sum(
        1
        for w in pred_pos
        if w.normalized in gold_norms
        or any(needle_matches_norm(w.normalized, n, locale) for n in combined)
    )
    fp = len(pred_pos) - tp
    precision = tp / (tp + fp) if (tp + fp) else 0.0

    def _recall(hits: int, evaluated: int) -> float:
        return hits / evaluated if evaluated else 0.0

    return {
        "known_recall": _recall(known_hits, known_eval),
        "known_hits": known_hits,
        "known_evaluated": known_eval,
        "unseen_recall": _recall(unseen_hits, unseen_eval),
        "unseen_hits": unseen_hits,
        "unseen_evaluated": unseen_eval,
        "combined_recall": _recall(comb_hits, comb_eval),
        "combined_hits": comb_hits,
        "combined_evaluated": comb_eval,
        "word_precision": precision,
        "word_tp": tp,
        "word_fp": fp,
    }


def clean_page_fpr(
    words: Sequence[ClassifiedWord],
    *,
    clean_page_slugs: Sequence[str],
    clean_pages_total_tokens: int,
) -> dict[str, Any]:
    """
    False-positive rate on clean pages.

    Counts unique anomaly words whose samples fall on clean pages, then reports
    FP per 1000 tokens and the share of unique flagged norms among clean tokens.
    """
    clean = {s for s in clean_page_slugs}
    fp_words: set[str] = set()
    for w in words:
        if not pred_is_anomaly(w.status):
            continue
        if any(_path_in_gold(s.path, clean) for s in w.samples):
            fp_words.add(w.normalized)
    n_fp = len(fp_words)
    per_1k = (n_fp / clean_pages_total_tokens * 1000.0) if clean_pages_total_tokens else 0.0
    unique_rate = n_fp / clean_pages_total_tokens if clean_pages_total_tokens else 0.0
    return {
        "fp_unique_words": n_fp,
        "fp_words": sorted(fp_words),
        "clean_pages_total_tokens": clean_pages_total_tokens,
        "fp_per_1000_tokens": per_1k,
        "unique_word_fpr": unique_rate,
    }


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
