"""V5-1: exact 1-based line:col on multiline md / po / html."""

from __future__ import annotations

from pathlib import Path

from lexaudit.core.aggregate import add_tokens
from lexaudit.core.tokenize import offset_to_line_col, tokenize_with_surface
from lexaudit.core.types import VocabOccurrence
from lexaudit.report.ci import build_findings, format_location
from lexaudit.sources.formats import collect_html_file, collect_po_file, html_to_text

FIX = Path(__file__).parent / "fixtures" / "formats"


def test_offset_to_line_col_multiline() -> None:
    text = "alpha\nbeta gamma\ndelta"
    # "gamma" starts after "beta " on line 2
    start = text.index("gamma")
    end = start + len("gamma")
    line, sc, ec = offset_to_line_col(text, start, end)
    assert (line, sc, ec) == (2, 6, 11)


def test_tokenize_line_col_multiline_md() -> None:
    raw = "# Title\n\nFirst line here.\nSecond orientir word.\n"
    tokens = tokenize_with_surface(raw, locale="en")
    hit = next(t for t in tokens if t["normalized"] == "orientir")
    assert hit["line"] == 4
    assert hit["start_col"] == 8
    assert hit["end_col"] == 16
    assert raw.splitlines()[3][hit["start_col"] - 1 : hit["end_col"] - 1] == "orientir"


def test_add_tokens_propagates_line_col_with_base() -> None:
    occ: dict[str, VocabOccurrence] = {}
    tokens = tokenize_with_surface("hello orientir\n", locale="en")
    add_tokens(occ, tokens, path="a.md", scope="body", line_base=10)
    sample = occ["orientir"].samples[0]
    assert sample.line == 10
    assert sample.start_col == 7
    assert sample.end_col == 15


def test_po_chunk_line_col() -> None:
    chunks = collect_po_file(FIX / "po" / "messages.po", "messages.po")
    assert chunks
    orient = next(c for c in chunks if "orientir" in c.text)
    tokens = tokenize_with_surface(orient.text, locale="en")
    hit = next(t for t in tokens if t["normalized"] == "orientir")
    assert hit["line"] == 1
    assert hit["start_col"] == 1
    # File-absolute line via line_base on the msgstr row
    occ: dict[str, VocabOccurrence] = {}
    add_tokens(
        occ,
        tokens,
        path=orient.path,
        scope=orient.scope,
        line_base=orient.line_base,
    )
    sample = occ["orientir"].samples[0]
    assert sample.line == orient.line_base
    assert sample.start_col == 1


def test_html_chunk_line_col() -> None:
    chunks = collect_html_file(FIX / "html" / "page.html", "page.html")
    assert chunks
    text = chunks[0].text
    assert "orientir" in text
    tokens = tokenize_with_surface(text, locale="en")
    hit = next(t for t in tokens if t["normalized"] == "orientir")
    line_text = text.splitlines()[hit["line"] - 1]
    assert line_text[hit["start_col"] - 1 : hit["end_col"] - 1] == "orientir"
    # Extracted HTML text keeps the span as a contiguous token
    assert "orientir" in html_to_text((FIX / "html" / "page.html").read_text(encoding="utf-8"))


def test_format_location_and_findings_cols(tmp_path: Path) -> None:
    from lexaudit.core.types import ClassifiedWord, VocabSample

    assert format_location("a.md", 3, 5) == "a.md:3:5"
    assert format_location("a.md", 3, None) == "a.md:3"
    f = tmp_path / "note.md"
    f.write_text("one\ntwo orientir three\n", encoding="utf-8")
    words = [
        ClassifiedWord(
            "orientir",
            "orientir",
            1,
            "calque",
            [VocabSample("note.md", "body", line=2, start_col=5, end_col=13)],
            reason="loan",
            hint="ballpark",
            source_id="ru-origin",
        )
    ]
    rows = build_findings(words, locale="en", repo_root=tmp_path)
    assert rows[0]["line"] == 2
    assert rows[0]["start_col"] == 5
    assert rows[0]["end_col"] == 13
