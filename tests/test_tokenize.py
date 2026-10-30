"""Tokenize and classify unit tests."""

from __future__ import annotations

from lexaudit.core.aggregate import add_tokens
from lexaudit.core.classify import classify_occurrences, probe_forms
from lexaudit.core.rank import rank_pages_by_suspects
from lexaudit.core.tokenize import casefold, strip_for_tokenize, tokenize, tokenize_with_surface
from lexaudit.core.types import ClassifiedWord, VocabOccurrence, VocabSample


class MockChecker:
    dict_id = "mock"

    def list_misspelled(self, words: list[str]) -> set[str]:
        bad: set[str] = set()
        for w in words:
            lower = w.lower()
            if lower == "xxyzzyq":
                bad.add(w)
            if w == "rumpf":
                bad.add(w)
        return bad


def test_strips_frontmatter_links_urls_code() -> None:
    raw = """---
title: x
---
See [AcmeCorp](https://example.org/path) and `code` plus
```
ignored block
```
hello world
"""
    plain = strip_for_tokenize(raw)
    assert "example.org" not in plain
    assert "ignored block" not in plain
    tokens = tokenize(plain, locale="en")
    for expected in ("see", "acmecorp", "and", "plus", "hello", "world"):
        assert expected in tokens


def test_frontmatter_strip_only_once() -> None:
    """Only the leading YAML fence is removed (sub count=1, not 2)."""
    raw = """---
title: one
---
bodyword
---
title: two
---
tailword
"""
    plain = strip_for_tokenize(raw)
    assert "bodyword" in plain
    assert "tailword" in plain
    # Second fence pair is body content after first strip — keep a marker.
    assert "title" in plain or "two" in plain


def test_keeps_hyphen_apostrophe_skips_digits() -> None:
    tokens = tokenize("centre-cockpit's 42 hr36 boats", locale="en")
    assert "centre-cockpit's" in tokens
    assert "hr36" in tokens
    assert "boats" in tokens
    assert "42" not in tokens
    # min_length filters single letters; digits-only still skipped
    assert tokenize("a bb 7", locale="en", min_length=2) == ["bb"]
    assert tokenize("a bb 7", locale="en", min_length=1) == ["a", "bb"]
    surfaces = tokenize_with_surface("A boat", locale="en", min_length=2)
    assert {"normalized": "boat", "surface": "boat"} in surfaces or any(
        t["normalized"] == "boat" for t in surfaces
    )
    assert tokenize_with_surface("x 99", locale="en", min_length=2) == []
    # email / html / chrome / bare domains stripped
    plain = strip_for_tokenize("Write me@ex.com and github.com/nareyko and <b>bold</b> **hi**")
    assert "me@ex.com" not in plain
    assert "github.com" not in plain
    assert "com" not in tokenize(plain, locale="en")
    assert "<b>" not in plain
    assert "bold" in plain or "hi" in plain


def test_casefold_locale() -> None:
    assert casefold("Rumpf", "de") == "rumpf"
    assert casefold("Лодка", "ru") == "лодка"


def test_unicode_tokens_de_pl_ru_sv_uk() -> None:
    assert "überholung" in tokenize("Überholung", locale="de")
    assert "łódka" in tokenize("Łódka", locale="pl")
    assert "яхта" in tokenize("Яхта", locale="ru")
    assert "skrov" in tokenize("Skrov", locale="sv")
    assert "човен" in tokenize("Човен", locale="uk")


def test_classify_allowlist_ok_suspect() -> None:
    occ_map: dict[str, VocabOccurrence] = {}
    add_tokens(
        occ_map,
        [
            {"normalized": "acmecorp", "surface": "AcmeCorp"},
            {"normalized": "boat", "surface": "boat"},
            {"normalized": "xxyzzyq", "surface": "xxyzzyq"},
            {"normalized": "rumpf", "surface": "Rumpf"},
        ],
        path="a.md",
        scope="body",
    )
    classified = classify_occurrences(
        occurrences=occ_map,
        proper={"acmecorp"},
        acronyms=set(),
        templates=set(),
        checker=MockChecker(),
    )
    by = {c.normalized: c.status for c in classified}
    assert by["acmecorp"] == "proper"
    assert by["boat"] == "ok"
    assert by["xxyzzyq"] == "suspect"
    assert by["rumpf"] == "ok"


def test_probe_forms_capitalised() -> None:
    forms = probe_forms("rumpf", "rumpf")
    assert "rumpf" in forms
    assert "Rumpf" in forms


def test_tokenize_with_surface() -> None:
    tokens = tokenize_with_surface("NorthWind Marine", locale="en")
    assert tokens[0] == {"normalized": "northwind", "surface": "NorthWind"}


def test_rank_pages() -> None:
    ranked = rank_pages_by_suspects(
        [
            ClassifiedWord(
                normalized="aaa",
                surface="aaa",
                count=2,
                status="suspect",
                samples=[
                    VocabSample("a.json", "body"),
                    VocabSample("b.json", "body"),
                ],
            ),
            ClassifiedWord(
                normalized="bbb",
                surface="bbb",
                count=1,
                status="suspect",
                samples=[VocabSample("a.json", "body")],
            ),
            ClassifiedWord(
                normalized="ccc",
                surface="ccc",
                count=9,
                status="ok",
                samples=[VocabSample("a.json", "body")],
            ),
        ]
    )
    assert ranked[0].path == "a.json"
    assert ranked[0].unique_suspects == 2
    assert ranked[1].path == "b.json"
    assert ranked[1].unique_suspects == 1
