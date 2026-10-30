"""English stopword leak detector (DE body chains)."""

from __future__ import annotations

from lexaudit.core.types import ClassifiedWord

ENGLISH_LEAK_STOPWORDS = frozenset({"of", "the", "and", "to", "for", "with"})

# Locales where short English function words in body are ranked as low-weight leaks.
# Cyrillic locales (ru/uk) rely on foreign-script detection instead.
ENGLISH_LEAK_LOCALES = frozenset({"de", "es", "pl", "sv"})


def _has_body_sample(word: ClassifiedWord) -> bool:
    # Academy JSON adapter: bodyMarkdown scope (see sources/collect.py).
    return any(
        s.scope.casefold() in {"body", "bodymarkdown"} or s.scope.casefold().startswith("body")
        for s in word.samples
    )


def make_english_leak_detector(locale: str) -> object:
    if locale not in ENGLISH_LEAK_LOCALES:

        def noop(word: ClassifiedWord) -> ClassifiedWord | None:
            return None

        return noop

    def detect(word: ClassifiedWord) -> ClassifiedWord | None:
        if word.status != "suspect":
            return None
        n = word.normalized.casefold()
        if n not in ENGLISH_LEAK_STOPWORDS:
            return None
        if not _has_body_sample(word):
            return None
        word.status = "foreign"
        word.reason = "english-leak"
        word.detectors = sorted({*word.detectors, "english_leak", "foreign"})
        return word

    return detect
