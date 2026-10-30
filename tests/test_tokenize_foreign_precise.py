"""Pin tokenizer stripping and foreign-context classification exactly."""

from __future__ import annotations

import pytest

from lexaudit.core.tokenize import strip_for_tokenize, tokenize, tokenize_with_surface
from lexaudit.core.types import ClassifiedWord, VocabSample
from lexaudit.detectors.foreign import (
    _scope_kind,
    classify_ru_foreign_context,
    is_title_case_brand,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("---\ntitle: hidden\n---\nvisible", "visible"),
        ("a ```code block``` b", "a   b"),
        ("a `inline` b", "a   b"),
        ("see https://example.com/x now", "see   now"),
        ("mail me@example.org now", "mail   now"),
        ("visit example.com now", "visit   now"),
        ("a <b>tag</b> c", "a  tag  c"),
        ("**bold** and _it_ ~x~ |t| > # h", "bold  and  it   x   t        h"),
        ("[text](http://x.io/y)", "[text] "),
    ],
)
def test_strip_for_tokenize(raw: str, expected: str) -> None:
    out = strip_for_tokenize(raw)
    assert " ".join(out.split()) == " ".join(expected.split())


def test_frontmatter_only_when_at_start() -> None:
    assert "title" in strip_for_tokenize("intro\n---\ntitle: shown\n---\nx")
    assert "hidden" not in strip_for_tokenize("---\r\ntitle: hidden\r\n---\r\nvisible")


def test_nfc_normalization() -> None:
    assert tokenize("cafe\u0301", locale="en") == ["caf\u00e9"]


def test_tokenize_filters() -> None:
    assert tokenize("12345 hr36 a bb", locale="en") == ["hr36", "bb"]
    assert tokenize("ab abc", locale="en", min_length=3) == ["abc"]
    assert tokenize("ab", locale="en", min_length=2) == ["ab"]
    assert tokenize("don't well-known l\u2019eau", locale="en") == [
        "don't",
        "well-known",
        "l\u2019eau",
    ]


def test_tokenize_with_surface() -> None:
    got = tokenize_with_surface("Boat 99 x Keel", locale="en", min_length=2)
    assert got == [
        {"normalized": "boat", "surface": "Boat"},
        {"normalized": "keel", "surface": "Keel"},
    ]
    assert tokenize_with_surface("abc ab", locale="en", min_length=3) == [
        {"normalized": "abc", "surface": "abc"}
    ]
    assert tokenize_with_surface("ab", locale="en") == [{"normalized": "ab", "surface": "ab"}]


@pytest.mark.parametrize(
    ("surface", "norm", "expected"),
    [
        ("Boat", "boat", True),
        ("BOAT", "boat", False),
        ("boat", "boat", False),
        ("B", "b", False),
        ("Bo", "bo", True),
        ("", "Boat", True),  # empty surface falls back to normalized
        ("", "boat", False),
        ("", "Bo", True),
    ],
)
def test_title_case_brand(surface: str, norm: str, expected: bool) -> None:
    assert is_title_case_brand(surface, norm) is expected


@pytest.mark.parametrize(
    ("scope", "kind"),
    [
        ("pageURL", "url"),
        ("url", "url"),
        ("quotes", "quotes"),
        ("Quote", "quotes"),
        ("body", "body"),
        ("bodyMarkdown", "body"),
        ("body-extra", "body"),
        ("title", "heading"),
        ("metaDescription", "heading"),
        ("heading-3", "heading"),
        ("unknown", "heading"),
        ("my-url-quote", "url"),
    ],
)
def test_scope_kind(scope: str, kind: str) -> None:
    assert _scope_kind(scope) == kind


def _w(surface: str, scopes: list[str]) -> ClassifiedWord:
    return ClassifiedWord(
        normalized=surface.casefold(),
        surface=surface,
        count=1,
        status="foreign",
        samples=[VocabSample("a.md", s) for s in scopes],
    )


@pytest.mark.parametrize(
    ("surface", "scopes", "ctx"),
    [
        ("Boat", ["body"], "proper-seed"),
        ("boat", ["body"], "mid-body"),
        ("boat", ["bodyMarkdown", "body"], "mid-body"),
        ("boat", ["title"], "heading"),
        ("boat", [], "heading"),
        ("boat", ["url"], "url"),
        ("boat", ["quotes"], "quotes"),
        ("boat", ["url", "quotes"], "url"),
        ("boat", ["body", "url"], "url"),
        ("boat", ["body", "quotes"], "quotes"),
        ("boat", ["body", "url", "quotes"], "url"),
        ("boat", ["body", "title"], "mid-body"),
    ],
)
def test_ru_foreign_context(surface: str, scopes: list[str], ctx: str) -> None:
    assert classify_ru_foreign_context(_w(surface, scopes)) == ctx
