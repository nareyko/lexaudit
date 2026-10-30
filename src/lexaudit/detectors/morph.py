"""Morphology post-detector for ru/uk via pymorphy3."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from lexaudit.core.types import ClassifiedWord

SUPPORTED = frozenset({"ru", "uk"})


@lru_cache(maxsize=4)
def _morph(locale: str) -> Any:
    import pymorphy3  # type: ignore[import-untyped]

    if locale == "uk":
        return pymorphy3.MorphAnalyzer(lang="uk")
    return pymorphy3.MorphAnalyzer(lang="ru")


def make_morph_detector(locale: str) -> Any:
    """Return a post-detector that upgrades morphologically known suspects to ok."""

    if locale not in SUPPORTED:

        def _noop(word: ClassifiedWord) -> ClassifiedWord | None:
            return None

        return _noop

    analyzer = _morph(locale)

    def detect(word: ClassifiedWord) -> ClassifiedWord | None:
        if word.status != "suspect":
            return None
        parses = analyzer.parse(word.surface) or analyzer.parse(word.normalized)
        if not parses:
            return None
        best = parses[0]
        # Only clear false hunspell misses for known dictionary forms.
        # Do not invent morph-miss here - leave unknown for foreign/calque/suspect.
        if getattr(best, "is_known", False) and best.score >= 0.5:
            word.status = "ok"
            word.reason = "pymorphy3"
            word.detectors = sorted({*word.detectors, "morph"})
            word.tier = None
            return word
        return None

    return detect
