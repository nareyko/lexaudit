"""Tokenize / normalize - port of TS vocab prototype."""

from __future__ import annotations

import re
import unicodedata
from typing import TypedDict

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


class TokenHit(TypedDict):
    normalized: str
    surface: str
    start: int
    end: int
    line: int
    start_col: int
    end_col: int


def _blank_keep_newlines(match: re.Match[str]) -> str:
    """Replace a match with spaces, preserving newlines so offsets stay aligned."""
    return "".join("\n" if ch == "\n" else " " for ch in match.group(0))


def strip_for_tokenize(raw: str) -> str:
    """Normalize Unicode to NFC and blank markdown chrome / URLs / code (length-stable)."""
    s = unicodedata.normalize("NFC", raw)
    if s.startswith("---"):
        s = FRONTMATTER_RE.sub(_blank_keep_newlines, s, count=1)
    s = FENCED_CODE_RE.sub(_blank_keep_newlines, s)
    s = INLINE_CODE_RE.sub(_blank_keep_newlines, s)
    s = MD_LINK_TARGET_RE.sub(lambda m: "]" + (" " * (len(m.group(0)) - 1)), s)
    s = URL_RE.sub(_blank_keep_newlines, s)
    s = EMAIL_RE.sub(_blank_keep_newlines, s)
    s = BARE_DOMAIN_RE.sub(_blank_keep_newlines, s)
    s = HTML_TAG_RE.sub(_blank_keep_newlines, s)
    s = MD_CHROME_RE.sub(_blank_keep_newlines, s)
    return s


def casefold(word: str, locale: str) -> str:
    """Locale-aware NFC normalization + lowercasing; falls back to Unicode casefold."""
    return unicodedata.normalize("NFC", word).casefold()


def offset_to_line_col(text: str, start: int, end: int) -> tuple[int, int, int]:
    """Map 0-based [start, end) char offsets to 1-based (line, start_col, end_col)."""
    if start < 0:
        start = 0
    if end < start:
        end = start
    if start > len(text):
        start = len(text)
    if end > len(text):
        end = len(text)
    line = text.count("\n", 0, start) + 1
    line_start = text.rfind("\n", 0, start) + 1
    start_col = start - line_start + 1
    if end > start and "\n" in text[start:end]:
        # Multi-line span: end_col is column on the last line of the span.
        last_nl = text.rfind("\n", start, end)
        end_col = end - last_nl
    else:
        end_col = start_col + (end - start)
    return line, start_col, end_col


def tokenize(raw: str, *, locale: str, min_length: int = 2) -> list[str]:
    """Yield normalized tokens; digits-only skipped; codes like hr36 kept."""
    hits = tokenize_with_surface(raw, locale=locale, min_length=min_length)
    return [t["normalized"] for t in hits]


def tokenize_with_surface(raw: str, *, locale: str, min_length: int = 2) -> list[TokenHit]:
    """Tokenize keeping surface forms and 1-based line/col within ``raw``."""
    nfc = unicodedata.normalize("NFC", raw)
    plain = strip_for_tokenize(nfc)
    # strip_for_tokenize already NFC-normalizes; keep original NFC for surface slices.
    out: list[TokenHit] = []
    for match in TOKEN_RE.finditer(plain):
        surface = nfc[match.start() : match.end()]
        if DIGITS_ONLY_RE.match(surface):
            continue
        if len(surface) < min_length:
            continue
        line, start_col, end_col = offset_to_line_col(nfc, match.start(), match.end())
        out.append(
            {
                "normalized": casefold(surface, locale),
                "surface": surface,
                "start": match.start(),
                "end": match.end(),
                "line": line,
                "start_col": start_col,
                "end_col": end_col,
            }
        )
    return out
