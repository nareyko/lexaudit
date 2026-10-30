"""Product metrics and rewrite-queue regression (I7)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lexaudit.config import LexauditConfig
from lexaudit.core.rank import rank_pages
from lexaudit.core.types import ClassifiedWord, VocabSample
from lexaudit.eval.metrics import clear_regression, needle_recall, page_at_k

DEFAULT_GOLD_SLUGS: tuple[str, ...] = ()

# Default CLEAR needles for slug regression when config omits regression_needles and needles.
CLEAR_REGRESSION_NEEDLES: tuple[str, ...] = (
    "orientir",
    "denseness",
    "предпокуп",
    "блувотер",
    "чеклист",
)


def gold_slugs_for(cfg: LexauditConfig) -> tuple[str, ...]:
    return cfg.gold_slugs or DEFAULT_GOLD_SLUGS


def regression_needles_for(cfg: LexauditConfig) -> tuple[str, ...]:
    if cfg.regression_needles:
        return cfg.regression_needles
    if cfg.needles:
        return tuple(cfg.needles)
    return CLEAR_REGRESSION_NEEDLES


def words_from_json_payload(data: dict[str, object]) -> list[ClassifiedWord]:
    """Load classified words from words.json or report.json payload."""
    from typing import cast

    from lexaudit.core.types import Tier, VocabStatus

    words: list[ClassifiedWord] = []
    raw_words = data.get("words", [])
    if not isinstance(raw_words, list):
        return words
    for w in raw_words:
        if not isinstance(w, dict):
            continue
        words.append(
            ClassifiedWord(
                normalized=str(w["word"]),
                surface=str(w.get("surface") or w["word"]),
                count=int(w.get("count") or 0),
                status=cast(VocabStatus, str(w.get("status") or "suspect")),
                samples=[
                    VocabSample(
                        str(s["path"]),
                        str(s.get("field") or s.get("scope") or "body"),
                    )
                    for s in (w.get("samples") or [])
                    if isinstance(s, dict)
                ],
                tier=cast(Tier | None, w.get("tier")),
                reason=str(w.get("reason") or ""),
            )
        )
    return words


def load_locale_words(output_dir: Path, locale: str) -> list[ClassifiedWord]:
    path = output_dir / locale / "words.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = f"expected object in {path}"
        raise ValueError(msg)
    return words_from_json_payload(data)


def compute_product_metrics(cfg: LexauditConfig, *, k: int = 10) -> dict[str, Any]:
    """Needle recall, page@K on weighted rank, and status counts per locale."""
    slugs = list(gold_slugs_for(cfg))
    by_locale: dict[str, Any] = {}
    for loc in cfg.locales:
        words = load_locale_words(cfg.output_dir, loc)
        nr = needle_recall(cfg.needles, words, locale=loc)
        ranked = rank_pages(
            words,
            mode=cfg.rank_mode,  # type: ignore[arg-type]
            weights=cfg.rank_weights,
            needles=list(cfg.needles),
            locale=loc,
        )
        p_at_k = page_at_k(ranked, slugs, k=k)
        status_counts: dict[str, int] = {}
        for w in words:
            status_counts[w.status] = status_counts.get(w.status, 0) + 1
        by_locale[loc] = {
            "needle_recall": nr,
            "page_at_k": p_at_k,
            "status_counts": status_counts,
            "suspect": status_counts.get("suspect", 0),
        }
    return {"k": k, "gold_slugs": slugs, "locales": by_locale}


def slug_regression_clear(slug: str, cfg: LexauditConfig) -> dict[str, Any]:
    """CLEAR if no needle anomalies on this slug in any configured locale."""
    needles = list(regression_needles_for(cfg))
    locale_details: list[dict[str, Any]] = []
    clear = True
    for loc in cfg.locales:
        words = load_locale_words(cfg.output_dir, loc)
        one = clear_regression([slug], words, needles, locale=loc)
        row = one["results"][0]
        locale_details.append({"locale": loc, **row})
        if not row["clear"]:
            clear = False
    return {"slug": slug, "clear": clear, "locales": locale_details}


def run_regression_check(cfg: LexauditConfig) -> dict[str, Any]:
    slugs = gold_slugs_for(cfg)
    results = [slug_regression_clear(slug, cfg) for slug in slugs]
    return {
        "needles": list(regression_needles_for(cfg)),
        "all_clear": all(r["clear"] for r in results),
        "results": results,
    }
