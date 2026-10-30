from pathlib import Path

from lexaudit.sources.collect import collect_all, collect_files
from lexaudit.sources.formats import (
    collect_docusaurus,
    collect_html_file,
    collect_mkdocs,
    collect_po_file,
    collect_vitepress,
    collect_xliff_file,
    html_to_text,
)

FIX = Path(__file__).parent / "fixtures" / "formats"


def test_html_strips_script() -> None:
    text = html_to_text("<p>Hi</p><script>bad()</script><p>orientir</p>")
    assert "bad" not in text
    assert "orientir" in text


def test_po_and_xliff_and_html() -> None:
    po = collect_po_file(FIX / "po" / "messages.po", "messages.po")
    assert any("orientir" in c.text for c in po)
    assert any("denseness" in c.text for c in po)
    xl = collect_xliff_file(FIX / "xliff" / "sample.xliff", "sample.xliff")
    assert any("orientir" in c.text for c in xl)
    ht = collect_html_file(FIX / "html" / "page.html", "page.html")
    assert any("orientir" in c.text for c in ht)


def test_mkdocs_docusaurus_vitepress() -> None:
    mk = collect_mkdocs(FIX / "mkdocs", "en")
    assert mk and any("orientir" in c.text for c in mk)
    du = collect_docusaurus(FIX / "docusaurus", "en")
    assert du and any("denseness" in c.text for c in du)
    vp = collect_vitepress(FIX / "vitepress", "en")
    assert vp and any("surveyness" in c.text for c in vp)


def test_collect_files_walks_new_suffixes() -> None:
    chunks = collect_files(FIX / "html", "en", files_paths=(FIX / "html",))
    assert any(c.source == "files" for c in chunks)


def test_collect_all_source_flags() -> None:
    chunks = collect_all(FIX / "mkdocs", "en", sources={"mkdocs"})
    assert chunks
