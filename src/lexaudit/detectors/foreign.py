"""Foreign-language detector via alphabet n-grams and other-locale dictionaries."""

from __future__ import annotations

import regex  # type: ignore[import-untyped]

from lexaudit.core.types import ClassifiedWord

CYRILLIC = regex.compile(r"^[\p{Cyrillic}'\u2019-]+$", regex.VERSION1)
LATIN = regex.compile(r"^[\p{Latin}'\u2019-]+$", regex.VERSION1)

CYRILLIC_LOCALES = frozenset({"ru", "uk"})
LATIN_LOCALES = frozenset({"en", "de", "pl", "es", "sv"})

_META_SCOPES = frozenset(
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

RuForeignContext = str  # heading | quotes | url | proper-seed | mid-body


def is_title_case_brand(surface: str, normalized: str) -> bool:
    """Single-word Title Case token (typical brand/model seed in RU copy)."""
    s = surface if surface else normalized
    if len(s) < 2:
        return False
    return s[0].isupper() and s[1:].islower()


def _scope_kind(scope: str) -> str:
    s = scope.casefold()
    if "url" in s:
        return "url"
    if "quote" in s:
        return "quotes"
    # JSON corpus adapter: bodyMarkdown scope (see sources/collect.py)
    if s in {"body", "bodymarkdown"} or s.startswith("body"):
        return "body"
    if s in _META_SCOPES or s.startswith("meta") or s.startswith("heading"):
        return "heading"
    return "heading"


def classify_ru_foreign_context(word: ClassifiedWord) -> RuForeignContext:
    """Classify RU Latin foreign token by sample scopes and surface shape."""
    if is_title_case_brand(word.surface, word.normalized):
        return "proper-seed"
    kinds = {_scope_kind(s.scope) for s in word.samples}
    if "body" not in kinds:
        if "url" in kinds:
            return "url"
        if "quotes" in kinds:
            return "quotes"
        return "heading"
    if kinds == {"body"}:
        return "mid-body"
    if "url" in kinds:
        return "url"
    if "quotes" in kinds:
        return "quotes"
    return "mid-body"


def foreign_reason_with_context(base: str, word: ClassifiedWord, locale: str) -> str:
    if locale in CYRILLIC_LOCALES and LATIN.match(word.normalized):
        ctx = classify_ru_foreign_context(word)
        return f"{base}:{ctx}"
    return base


def _mark_foreign(word: ClassifiedWord, base_reason: str, locale: str) -> ClassifiedWord:
    word.status = "foreign"
    word.reason = foreign_reason_with_context(base_reason, word, locale)
    word.detectors = sorted({*word.detectors, "foreign"})
    return word


def make_foreign_detector(
    locale: str,
    other_locale_words: dict[str, set[str]] | None = None,
) -> object:
    others = other_locale_words or {}

    def detect(word: ClassifiedWord) -> ClassifiedWord | None:
        if word.status != "suspect":
            return None
        n = word.normalized
        if locale in CYRILLIC_LOCALES and LATIN.match(n):
            # Latin token in Cyrillic locale
            for loc, vocab in others.items():
                if loc in LATIN_LOCALES and n in vocab:
                    return _mark_foreign(word, f"latin-in-{locale}-via-{loc}", locale)
            if len(n) >= 4:
                return _mark_foreign(word, f"latin-script-in-{locale}", locale)
        if locale in LATIN_LOCALES and CYRILLIC.match(n):
            return _mark_foreign(word, f"cyrillic-in-{locale}", locale)
        # cross-dict hit without script clash
        for loc, vocab in others.items():
            if loc == locale:
                continue
            if n in vocab and len(n) >= 5:
                return _mark_foreign(word, f"dict-hit-{loc}", locale)
        return None

    return detect
