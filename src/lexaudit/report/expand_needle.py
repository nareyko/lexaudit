"""Scan words.json reports for needle hits (I3 expand-needle)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lexaudit.detectors.calque import needle_matches_norm

_STATUS_ORDER = (
    "calque",
    "invented",
    "foreign",
    "morph-miss",
    "suspect",
    "unsure",
    "ok",
    "proper",
    "acronym",
    "template",
)


@dataclass
class NeedlePageHit:
    locale: str
    path: str
    count: int
    status: str
    norm: str = ""
    surface: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "locale": self.locale,
            "path": self.path,
            "count": self.count,
            "status": self.status,
            "norm": self.norm,
            "surface": self.surface,
        }


@dataclass
class _Agg:
    count: int = 0
    status: str = "suspect"
    norms: set[str] = field(default_factory=set)
    surfaces: set[str] = field(default_factory=set)


def _status_rank(status: str) -> int:
    try:
        return _STATUS_ORDER.index(status)
    except ValueError:
        return len(_STATUS_ORDER)


def _pick_status(current: str, candidate: str) -> str:
    if _status_rank(candidate) < _status_rank(current):
        return candidate
    return current


def load_words_json(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    words = data.get("words")
    return list(words) if isinstance(words, list) else []


def scan_words_for_needle(
    words: list[dict[str, Any]],
    *,
    locale: str,
    needle: str,
) -> list[NeedlePageHit]:
    """Aggregate needle matches by page path from a ``words.json`` word list."""
    by_path: dict[str, _Agg] = {}
    for w in words:
        norm = str(w.get("norm") or w.get("word") or "")
        if not norm or not needle_matches_norm(norm, needle, locale):
            continue
        surface = str(w.get("surface") or norm)
        status = str(w.get("status") or "suspect")
        samples = w.get("samples") or []
        if not isinstance(samples, list) or not samples:
            continue
        per_path_samples: dict[str, int] = {}
        for s in samples:
            if not isinstance(s, dict):
                continue
            p = str(s.get("path") or "").strip()
            if not p:
                continue
            per_path_samples[p] = per_path_samples.get(p, 0) + 1
        word_count = int(w.get("count") or 0) or sum(per_path_samples.values())
        if len(per_path_samples) == 1:
            only_path = next(iter(per_path_samples))
            per_path_samples[only_path] = max(word_count, per_path_samples[only_path])
        for p, sample_hits in per_path_samples.items():
            agg = by_path.setdefault(p, _Agg())
            agg.count += max(sample_hits, 1)
            agg.status = _pick_status(agg.status, status)
            agg.norms.add(norm)
            agg.surfaces.add(surface)

    hits: list[NeedlePageHit] = []
    for path in sorted(by_path):
        agg = by_path[path]
        hits.append(
            NeedlePageHit(
                locale=locale,
                path=path,
                count=agg.count,
                status=agg.status,
                norm=",".join(sorted(agg.norms)),
                surface=",".join(sorted(agg.surfaces)),
            )
        )
    return hits


def scan_output_dir_for_needle(
    output_dir: Path,
    *,
    locales: list[str],
    needle: str,
) -> list[NeedlePageHit]:
    all_hits: list[NeedlePageHit] = []
    for loc in locales:
        words = load_words_json(output_dir / loc / "words.json")
        all_hits.extend(scan_words_for_needle(words, locale=loc, needle=needle))
    all_hits.sort(key=lambda h: (h.locale, h.path))
    return all_hits


def target_defects_label(needle: str) -> str:
    """Human column for curated queue ``target defects``."""
    n = needle.strip()
    if not n:
        return ""
    if "*" in n:
        return f"`{n}`"
    return f"`{n}*`"
