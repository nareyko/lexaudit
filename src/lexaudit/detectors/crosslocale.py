"""Cross-locale pairing and 'word without pair' tier boost."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from lexaudit.core.types import ClassifiedWord, TextChunk


def pair_chunks_by_path(
    ru_chunks: list[TextChunk],
    other_chunks: list[TextChunk],
) -> tuple[list[tuple[TextChunk, TextChunk]], list[TextChunk], list[TextChunk]]:
    """Pair RU↔other chunks sharing the same path+scope."""
    other_idx: dict[tuple[str, str], TextChunk] = {(c.path, c.scope): c for c in other_chunks}
    pairs: list[tuple[TextChunk, TextChunk]] = []
    unmatched_ru: list[TextChunk] = []
    matched_keys: set[tuple[str, str]] = set()
    for c in ru_chunks:
        key = (c.path, c.scope)
        o = other_idx.get(key)
        if o is None:
            unmatched_ru.append(c)
        else:
            pairs.append((c, o))
            matched_keys.add(key)
    unmatched_other = [c for c in other_chunks if (c.path, c.scope) not in matched_keys]
    return pairs, unmatched_ru, unmatched_other


def pairing_stats(
    pairs: list[tuple[TextChunk, TextChunk]],
    unmatched_ru: list[TextChunk],
    unmatched_other: list[TextChunk],
) -> dict[str, float | int]:
    total = len(pairs) + len(unmatched_ru) + len(unmatched_other)
    return {
        "paired": len(pairs),
        "unmatched_ru": len(unmatched_ru),
        "unmatched_other": len(unmatched_other),
        "unmatched_share": (len(unmatched_ru) + len(unmatched_other)) / total if total else 0.0,
    }


def make_crosslocale_detector(
    paired_norms_other: set[str],
    *,
    mode: str = "ref_present",
) -> object:
    """Boost suspect tiers using reference-locale vocab norms.

    Modes:
    - ``ref_present`` (default): token appears in the reference corpus — typical
      English leftover / loan surface that Hunspell flags in the target locale.
    - ``no_pair``: token is absent from the reference corpus (legacy lab mode).
    """

    def detect(word: ClassifiedWord) -> ClassifiedWord | None:
        if word.status not in {"suspect", "invented", "unsure", "morph-miss"}:
            return None
        present = word.normalized in paired_norms_other
        if mode == "no_pair":
            if present:
                return None
            tag = "+no-pair"
        else:
            if not present:
                return None
            tag = "+ref-present"
        word.detectors = sorted({*word.detectors, "crosslocale"})
        if word.tier == "weak" or word.tier is None:
            word.tier = "likely"
            word.reason = (word.reason or "unknown") + tag
        return word

    return detect


def path_slug_key(path: str) -> str:
    """Normalize path for cross-locale pairing (drop locale folder segment)."""
    parts = Path(path).as_posix().split("/")
    locales = {"en", "de", "es", "pl", "ru", "sv", "uk"}
    filtered = [p for p in parts if p.casefold() not in locales]
    return "/".join(filtered) if filtered else Path(path).name


def pair_chunks_by_slug(
    left: list[TextChunk],
    right: list[TextChunk],
) -> tuple[list[tuple[TextChunk, TextChunk]], list[TextChunk], list[TextChunk]]:
    """Pair chunks by slug key + scope (locale folder ignored)."""
    right_idx: dict[tuple[str, str], TextChunk] = {
        (path_slug_key(c.path), c.scope): c for c in right
    }
    pairs: list[tuple[TextChunk, TextChunk]] = []
    unmatched_left: list[TextChunk] = []
    matched: set[tuple[str, str]] = set()
    for c in left:
        key = (path_slug_key(c.path), c.scope)
        o = right_idx.get(key)
        if o is None:
            unmatched_left.append(c)
        else:
            pairs.append((c, o))
            matched.add(key)
    unmatched_right = [
        c for c in right if (path_slug_key(c.path), c.scope) not in matched
    ]
    return pairs, unmatched_left, unmatched_right


def load_embedding_cache(path: Path) -> dict[str, list[float]]:
    import json

    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: list(v) for k, v in sorted(data.items())}


def save_embedding_cache(path: Path, cache: dict[str, list[float]]) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = {k: cache[k] for k in sorted(cache)}
    path.write_text(
        json.dumps(ordered, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )


def embed_texts(
    texts: list[str],
    *,
    base_url: str,
    model: str,
    cache: dict[str, list[float]],
    cache_path: Path | None = None,
) -> list[list[float]]:
    """Embed via OpenAI-compatible /embeddings (bge-m3). Uses cache by text."""
    import hashlib

    import httpx

    out: list[list[float]] = []
    missing: list[tuple[int, str, str]] = []
    for i, text in enumerate(texts):
        key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if key in cache:
            out.append(cache[key])
        else:
            out.append([])  # placeholder
            missing.append((i, key, text))
    if missing:
        url = base_url.rstrip("/") + "/embeddings"
        payload = {"model": model, "input": [t for _, _, t in missing]}
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        vectors = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
        for (i, key, _text), vec in zip(missing, vectors, strict=True):
            cache[key] = list(vec)
            out[i] = list(vec)
        if cache_path is not None:
            save_embedding_cache(cache_path, cache)
    return out


def aggregate_norms_from_chunks(chunks: list[TextChunk], locale: str) -> set[str]:
    from lexaudit.core.tokenize import tokenize

    norms: set[str] = set()
    for c in chunks:
        norms.update(tokenize(c.text, locale=locale))
    return norms


def group_unmatched_share_by_path(
    unmatched: list[TextChunk],
) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for c in unmatched:
        counts[c.path] += 1
    return dict(sorted(counts.items()))
