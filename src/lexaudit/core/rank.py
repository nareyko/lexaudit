"""Page ranking by unique suspects (raw) or weighted signals (I2)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from lexaudit.core.types import ClassifiedWord, PageSuspectRank
from lexaudit.detectors.foreign import is_title_case_brand

# template excluded from ranking (I2-5)
SUSPECT_STATUSES = frozenset({"suspect", "foreign", "calque", "invented", "morph-miss", "unsure"})

_META_FOREIGN_SCOPES = frozenset(
    {
        "title",
        "excerpt",
        "metadescription",
        "meta",
        "heading",
        "h1",
        "h2",
        "h3",
    }
)
_LATIN_RE = re.compile(r"[a-zA-Z]")


@dataclass(frozen=True)
class RankWeights:
    calque: float = 8.0
    needle: float = 6.0
    foreign_body_ru: float = 2.0
    foreign_meta: float = 0.2
    suspect_confirmed: float = 3.0
    suspect_likely: float = 1.5
    suspect_weak_hapax: float = 0.1


DEFAULT_RANK_WEIGHTS = RankWeights()

RankMode = Literal["raw", "weighted"]

# Longest-first RU/UK inflection tails for calque-family unique counts (I8-1).
_RU_STEM_SUFFIXES: tuple[str, ...] = (
    "\u0430\u043c\u0438",
    "\u044f\u043c\u0438",
    "\u043e\u0433\u043e",
    "\u0435\u0433\u043e",
    "\u043e\u043c\u0443",
    "\u0435\u043c\u0443",
    "\u0430\u0445",
    "\u044f\u0445",
    "\u043e\u043c",
    "\u0435\u043c",
    "\u0430\u043c",
    "\u044f\u043c",
    "\u043e\u0432",
    "\u0435\u0432",
    "\u0438\u0439",
    "\u044b\u0439",
    "\u0430\u044f",
    "\u044f\u044f",
    "\u043e\u0435",
    "\u0435\u0435",
    "\u0443\u044e",
    "\u044e\u044e",
    "\u044b",
    "\u0438",
    "\u0430",
    "\u044f",
    "\u0435",
    "\u0443",
    "\u043e",
    "\u043c",
)

SOURCE_BUCKET_MARKERS: tuple[tuple[str, str], ...] = (
    ("pending-academy-articles/", "academy"),
    ("pending-model-packs/", "model_pack"),
)


def page_source_bucket(path: str) -> str | None:
    """Map report path to academy | model_pack | docs bucket (I8-2)."""
    p = path.replace("\\", "/")
    for marker, bucket in SOURCE_BUCKET_MARKERS:
        if marker in p:
            return bucket
    if p.startswith("docs/") or p.lower().endswith((".md", ".markdown")):
        return "docs"
    return None


def normalize_source_filter(sources: Sequence[str] | None) -> frozenset[str] | None:
    if not sources:
        return None
    out: set[str] = set()
    for raw in sources:
        s = raw.strip().casefold()
        if not s:
            continue
        out.add(s)
        if s == "packs":
            out.add("model_pack")
        if s == "model_pack":
            out.add("packs")
        if s in ("files", "md"):
            out.add("docs")
        if s == "docs":
            out.add("files")
            out.add("md")
    return frozenset(out) if out else None


def filter_pages_by_sources(
    pages: list[PageSuspectRank],
    sources: Sequence[str] | None,
) -> list[PageSuspectRank]:
    wanted = normalize_source_filter(sources)
    if wanted is None:
        return pages
    kept: list[PageSuspectRank] = []
    for page in pages:
        bucket = page_source_bucket(page.path)
        if bucket is not None and bucket.casefold() in wanted:
            kept.append(page)
    return kept


def _ru_calque_stem(normalized: str) -> str:
    n = normalized.casefold()
    if len(n) < 5:
        return n
    for suffix in _RU_STEM_SUFFIXES:
        if len(n) > len(suffix) + 3 and n.endswith(suffix):
            return n[: -len(suffix)]
    return n


def rank_unique_key(
    normalized: str,
    *,
    locale: str,
    needles: Sequence[str] = (),
) -> str:
    """Collapse inflection / needle-family variants for unique_suspects (I8-1)."""
    if needles:
        matching = [nd for nd in needles if _needle_matches(normalized, nd)]
        if matching:
            canon = min(matching, key=lambda x: (len(x.casefold()), x.casefold())).casefold()
            return f"n:{canon}"
    if locale in ("ru", "uk"):
        return f"s:{_ru_calque_stem(normalized)}"
    return normalized.casefold()


def _needle_matches(normalized: str, needle: str) -> bool:
    n = normalized.casefold()
    nd = needle.casefold().strip()
    if not nd:
        return False
    return n == nd or n.startswith(nd) or nd in n


def _word_matches_needles(normalized: str, needles: Sequence[str]) -> bool:
    return any(_needle_matches(normalized, n) for n in needles)


def _is_meta_foreign_scope(scope: str) -> bool:
    s = scope.casefold()
    if s in _META_FOREIGN_SCOPES:
        return True
    if s.startswith("meta") or s.startswith("heading"):
        return True
    return "quote" in s or "url" in s


def _has_latin(text: str) -> bool:
    return bool(_LATIN_RE.search(text))


_LOW_WEIGHT_FOREIGN_CONTEXTS = frozenset(
    {"heading", "quotes", "url", "proper-seed", "english-leak"}
)


def foreign_context_from_reason(reason: str) -> str | None:
    if reason == "english-leak":
        return "english-leak"
    if ":" in reason:
        return reason.rsplit(":", 1)[1]
    return None


def _foreign_weight_for_word(
    word: ClassifiedWord,
    locale: str,
    weights: RankWeights,
) -> float:
    ctx = foreign_context_from_reason(word.reason)
    if ctx in _LOW_WEIGHT_FOREIGN_CONTEXTS:
        return weights.foreign_meta
    if ctx == "mid-body" and locale == "ru" and _has_latin(word.normalized):
        return weights.foreign_body_ru

    scopes = [s.scope for s in word.samples]
    has_body = any(
        sc.casefold() in {"body", "bodymarkdown"} or sc.casefold().startswith("body")
        for sc in scopes
    )
    meta_like = any(_is_meta_foreign_scope(sc) for sc in scopes)
    if locale == "ru" and is_title_case_brand(word.surface, word.normalized):
        return weights.foreign_meta
    if locale == "ru" and has_body and _has_latin(word.normalized):
        return weights.foreign_body_ru
    if meta_like and not has_body:
        return weights.foreign_meta
    if meta_like:
        return weights.foreign_meta
    if has_body:
        return weights.foreign_body_ru
    return weights.foreign_meta


def word_rank_weight(
    word: ClassifiedWord,
    *,
    locale: str,
    weights: RankWeights = DEFAULT_RANK_WEIGHTS,
    needles: Sequence[str] = (),
) -> float:
    """Contribution of one classified word to a page score (weighted mode)."""
    if word.status == "template" or word.status not in SUSPECT_STATUSES:
        return 0.0
    if needles and _word_matches_needles(word.normalized, needles):
        return weights.needle
    if word.status in ("calque", "invented"):
        return weights.calque
    if word.status == "foreign":
        return _foreign_weight_for_word(word, locale, weights)
    if word.status == "suspect":
        tier = word.tier
        if tier == "confirmed":
            return weights.suspect_confirmed
        if tier == "likely":
            return weights.suspect_likely
        if len(word.normalized) <= 3 or word.count == 1:
            return weights.suspect_weak_hapax
        return weights.suspect_likely
    return weights.suspect_weak_hapax


def rank_pages_by_suspects(
    words: list[ClassifiedWord],
    *,
    locale: str = "en",
    needles: Sequence[str] = (),
    sample_words: int = 12,
    source_filter: Sequence[str] | None = None,
) -> list[PageSuspectRank]:
    """Rank pages by unique suspect-like words (DESC), then path ASC (raw mode)."""
    needle_list = tuple(n.strip() for n in needles if n.strip())
    keys_by_path: dict[str, set[str]] = {}
    order: dict[str, list[str]] = {}
    for w in words:
        if w.status not in SUSPECT_STATUSES:
            continue
        ukey = rank_unique_key(w.normalized, locale=locale, needles=needle_list)
        for s in w.samples:
            bucket = keys_by_path.setdefault(s.path, set())
            if ukey not in bucket:
                bucket.add(ukey)
                order.setdefault(s.path, []).append(w.normalized)

    ranked: list[PageSuspectRank] = []
    for path, keys in keys_by_path.items():
        tops = order.get(path, [])[:sample_words]
        n = len(keys)
        ranked.append(
            PageSuspectRank(
                path=path,
                unique_suspects=n,
                sample_words=tops,
                score=float(n),
            )
        )
    ranked.sort(key=lambda r: (-r.unique_suspects, r.path))
    return filter_pages_by_sources(ranked, source_filter)


def rank_pages_weighted(
    words: list[ClassifiedWord],
    *,
    weights: RankWeights = DEFAULT_RANK_WEIGHTS,
    needles: Sequence[str] = (),
    locale: str = "en",
    sample_words: int = 12,
    require_needle: bool = False,
    source_filter: Sequence[str] | None = None,
) -> list[PageSuspectRank]:
    """Rank pages by weighted anomaly score (DESC), then path ASC."""
    needle_list = tuple(n.strip() for n in needles if n.strip())
    keys_by_path: dict[str, set[str]] = {}
    order: dict[str, list[str]] = {}
    page_score: dict[str, float] = {}
    page_has_needle: dict[str, bool] = {}
    scored_on_page: dict[str, set[str]] = {}

    for w in words:
        if w.status not in SUSPECT_STATUSES:
            continue
        ukey = rank_unique_key(w.normalized, locale=locale, needles=needle_list)
        w_weight = word_rank_weight(w, locale=locale, weights=weights, needles=needle_list)
        hits_needle = bool(needle_list and _word_matches_needles(w.normalized, needle_list))
        for s in w.samples:
            bucket = keys_by_path.setdefault(s.path, set())
            if ukey not in bucket:
                bucket.add(ukey)
                order.setdefault(s.path, []).append(w.normalized)
            if ukey not in scored_on_page.setdefault(s.path, set()):
                scored_on_page[s.path].add(ukey)
                page_score[s.path] = page_score.get(s.path, 0.0) + w_weight
            if hits_needle:
                page_has_needle[s.path] = True

    ranked: list[PageSuspectRank] = []
    for path, keys in keys_by_path.items():
        if require_needle and needle_list and not page_has_needle.get(path, False):
            continue
        tops = order.get(path, [])[:sample_words]
        ranked.append(
            PageSuspectRank(
                path=path,
                unique_suspects=len(keys),
                sample_words=tops,
                score=round(page_score.get(path, 0.0), 4),
            )
        )
    ranked.sort(key=lambda r: (-r.score, -r.unique_suspects, r.path))
    return filter_pages_by_sources(ranked, source_filter)


def rank_pages(
    words: list[ClassifiedWord],
    *,
    mode: RankMode = "weighted",
    weights: RankWeights = DEFAULT_RANK_WEIGHTS,
    needles: Sequence[str] = (),
    locale: str = "en",
    sample_words: int = 12,
    require_needle: bool = False,
    source_filter: Sequence[str] | None = None,
) -> list[PageSuspectRank]:
    if mode == "raw":
        return rank_pages_by_suspects(
            words,
            locale=locale,
            needles=needles,
            sample_words=sample_words,
            source_filter=source_filter,
        )
    return rank_pages_weighted(
        words,
        weights=weights,
        needles=needles,
        locale=locale,
        sample_words=sample_words,
        require_needle=require_needle,
        source_filter=source_filter,
    )
