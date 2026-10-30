"""German/Swedish compound splitter using dictionary word set."""

from __future__ import annotations

from collections.abc import Callable

from lexaudit.core.types import ClassifiedWord

SUPPORTED = frozenset({"de", "sv"})


def _can_split(word: str, known: set[str], *, min_part: int = 3) -> bool:
    w = word.casefold()
    if len(w) < min_part * 2:
        return False
    for i in range(min_part, len(w) - min_part + 1):
        left, right = w[:i], w[i:]
        if left in known and right in known:
            return True
        # optional Fugen-s for German
        if left.endswith("s") and left[:-1] in known and right in known:
            return True
        if left.endswith("es") and left[:-2] in known and right in known:
            return True
    return False


def make_compound_detector(
    locale: str, known_words: set[str]
) -> Callable[[ClassifiedWord], ClassifiedWord | None]:
    if locale not in SUPPORTED:

        def _noop(word: ClassifiedWord) -> ClassifiedWord | None:
            return None

        return _noop

    known = {k.casefold() for k in known_words}

    def detect(word: ClassifiedWord) -> ClassifiedWord | None:
        if word.status != "suspect":
            return None
        if _can_split(word.normalized, known):
            word.status = "ok"
            word.reason = "compound-split"
            word.detectors = sorted({*word.detectors, "compound"})
            word.tier = None
            return word
        return None

    return detect
