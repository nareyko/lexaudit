"""Select weak/likely words on top-ranked pages for LLM labeling (I6-1)."""

from __future__ import annotations

from dataclasses import dataclass

from lexaudit.config import LexauditConfig
from lexaudit.core.rank import rank_pages, word_rank_weight
from lexaudit.core.types import ClassifiedWord, Tier, VocabSample
from lexaudit.llm.context_snippet import format_context_snippet, load_scope_text


@dataclass(frozen=True)
class LabelTarget:
    word: str
    normalized: str
    surface: str
    tier: Tier
    status: str
    path: str
    scope: str
    context: str
    rank_weight: float


def parse_tier_filter(raw: str) -> frozenset[Tier]:
    parts = [p.strip().casefold() for p in raw.split(",") if p.strip()]
    allowed: set[Tier] = set()
    for p in parts:
        if p not in ("confirmed", "likely", "weak"):
            msg = f"unknown tier {p!r}; use confirmed, likely, weak"
            raise ValueError(msg)
        allowed.add(p)  # type: ignore[arg-type]
    if not allowed:
        msg = "tiers must list at least one of confirmed, likely, weak"
        raise ValueError(msg)
    return frozenset(allowed)


def select_label_targets(
    words: list[ClassifiedWord],
    *,
    locale: str,
    top_pages: int,
    top_words: int,
    tiers: frozenset[Tier],
    cfg: LexauditConfig,
) -> tuple[list[LabelTarget], list[str]]:
    """Return up to ``top_words`` targets from the top ``top_pages`` ranked pages."""
    pages = rank_pages(
        words,
        mode=cfg.rank_mode,  # type: ignore[arg-type]
        weights=cfg.rank_weights,
        needles=cfg.needles,
        locale=locale,
    )
    page_paths = [p.path for p in pages[: max(top_pages, 0)]]
    path_set = set(page_paths)
    weights = cfg.rank_weights
    candidates: list[tuple[float, str, ClassifiedWord, VocabSample]] = []
    for w in words:
        if w.tier not in tiers:
            continue
        sample: VocabSample | None = None
        for s in sorted(w.samples, key=lambda x: (x.path, x.scope)):
            if s.path in path_set:
                sample = s
                break
        if sample is None:
            continue
        rw = word_rank_weight(w, locale=locale, weights=weights, needles=cfg.needles)
        candidates.append((rw, w.normalized, w, sample))
    candidates.sort(key=lambda row: (-row[0], row[1]))
    seen: set[str] = set()
    targets: list[LabelTarget] = []
    for rw, _norm, w, sample in candidates:
        if w.normalized in seen:
            continue
        seen.add(w.normalized)
        text = load_scope_text(cfg.repo_root, sample.path, sample.scope, locale)
        if text:
            ctx = format_context_snippet(
                path=sample.path,
                scope=sample.scope,
                text=text,
                word=w.normalized,
                surface=w.surface,
            )
        else:
            ctx = f"{sample.path}#{sample.scope}: ...{w.surface}..."
        targets.append(
            LabelTarget(
                word=w.normalized,
                normalized=w.normalized,
                surface=w.surface,
                tier=w.tier or "weak",
                status=w.status,
                path=sample.path,
                scope=sample.scope,
                context=ctx,
                rank_weight=rw,
            )
        )
        if len(targets) >= top_words:
            break
    return targets, page_paths
