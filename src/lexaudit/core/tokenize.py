"""Tokenize / normalize - port of TS vocab prototype."""

from __future__ import annotations

import re
import unicodedata

import regex  # type: ignore[import-untyped]

FRONTMATTER_RE = re.compile(r"^---\r?\n[\s\S]*?\r?\n---\r?\n")  # pragma: no mutate
FENCED_CODE_RE = re.compile(r"```[\s\S]*?```")  # pragma: no mutate
INLINE_CODE_RE = re.compile(r"`[^`]+`")  # pragma: no mutate
URL_RE = re.compile(r"https?://[^\s)>\]]+", re.IGNORECASE)  # pragma: no mutate
BARE_DOMAIN_RE = re.compile(  # pragma: no mutate
    r"\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|org|net|io|dev|gov|edu)(?:/[\w./-]*)?",
    re.IGNORECASE,
)
MD_LINK_TARGET_RE = re.compile(r"\]\(([^)]+)\)")  # pragma: no mutate
EMAIL_RE = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.IGNORECASE)  # pragma: no mutate
HTML_TAG_RE = re.compile(r"</?[a-z][^>]*>", re.IGNORECASE)  # pragma: no mutate
MD_CHROME_RE = re.compile(r"[*_~|>#]+")  # pragma: no mutate
TOKEN_RE = regex.compile(  # pragma: no mutate
    r"[\p{L}\d]+(?:['\u2019-][\p{L}\d]+)*",
    regex.VERSION1,
)
DIGITS_ONLY_RE = re.compile(r"^\d+$")  # pragma: no mutate


def strip_for_tokenize(raw: str) -> str:
    """Normalize Unicode to NFC and strip markdown chrome / URLs / code."""
    s = unicodedata.normalize("NFC", raw)
    if s.startswith("---"):
        s = FRONTMATTER_RE.sub("\n", s, count=1)
    s = FENCED_CODE_RE.sub(" ", s)
    s = INLINE_CODE_RE.sub(" ", s)
    s = MD_LINK_TARGET_RE.sub("] ", s)
    s = URL_RE.sub(" ", s)
    s = EMAIL_RE.sub(" ", s)
    s = BARE_DOMAIN_RE.sub(" ", s)
    s = HTML_TAG_RE.sub(" ", s)
    s = MD_CHROME_RE.sub(" ", s)
    return s


def casefold(word: str, locale: str) -> str:
    """Locale-aware NFC normalization + lowercasing; falls back to Unicode casefold."""
    return unicodedata.normalize("NFC", word).casefold()


def tokenize(raw: str, *, locale: str, min_length: int = 2) -> list[str]:
    """Yield normalized tokens; digits-only skipped; codes like hr36 kept."""
    plain = strip_for_tokenize(raw)
    out: list[str] = []
    for match in TOKEN_RE.finditer(plain):
        surface = match.group(0)
        if DIGITS_ONLY_RE.match(surface):
            continue
        if len(surface) < min_length:
            continue
        out.append(casefold(surface, locale))
    return out


def tokenize_with_surface(raw: str, *, locale: str, min_length: int = 2) -> list[dict[str, str]]:
    """Tokenize keeping first-seen surface forms."""
    plain = strip_for_tokenize(raw)
    out: list[dict[str, str]] = []
    for match in TOKEN_RE.finditer(plain):
        surface = match.group(0)
        if DIGITS_ONLY_RE.match(surface):
            continue
        if len(surface) < min_length:
            continue
        out.append({"normalized": casefold(surface, locale), "surface": surface})
    return out
