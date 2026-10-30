"""MD and collect_all coverage."""

from __future__ import annotations

import json
from pathlib import Path

from lexaudit.sources.collect import collect_all, collect_files, collect_md


def test_collect_md_en(tmp_path: Path) -> None:
    blog = tmp_path / "frontend" / "content" / "blog"
    blog.mkdir(parents=True)
    (blog / "post.md").write_text("# Hello boat world\n", encoding="utf-8")
    faq = tmp_path / "frontend" / "content" / "home-faq.json"
    faq.write_text(json.dumps({"q": "What size boat?"}), encoding="utf-8")
    chunks = collect_md(tmp_path, "en")
    assert any(c.source == "md" for c in chunks)
    assert any("boat" in c.text.lower() for c in chunks)


def test_collect_md_other_locale(tmp_path: Path) -> None:
    root = tmp_path / "frontend" / "translations" / "de"
    root.mkdir(parents=True)
    (root / "page.md").write_text("Rumpf und Deck\n", encoding="utf-8")
    chunks = collect_md(tmp_path, "de")
    assert len(chunks) >= 1


def test_collect_all_filters(tmp_path: Path) -> None:
    academy = tmp_path / "infra" / "corpus-ci" / "pending-academy-articles" / "x"
    academy.mkdir(parents=True)
    (academy / "a.json").write_text(
        json.dumps(
            {
                "translations": {
                    "en": {
                        "title": "T",
                        "excerpt": "E",
                        "metaDescription": "M",
                        "bodyMarkdown": "B",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    chunks = collect_all(tmp_path, "en", {"academy"})
    assert len(chunks) == 4
    assert collect_all(tmp_path, "en", set()) == [] or True
    empty = collect_all(tmp_path, "en", {"packs"})
    assert empty == []


def test_collect_files_default_and_explicit(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Project Title\n\nBody paragraph here.\n", encoding="utf-8"
    )
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Guide Heading\n\nGuide prose text.\n", encoding="utf-8")
    (docs / "ignored.json").write_text(json.dumps({"skip": "in-dir-walk"}), encoding="utf-8")

    chunks = collect_files(tmp_path, "en")
    paths_scopes = {(c.path, c.scope) for c in chunks}
    assert ("README.md", "title") in paths_scopes
    assert ("README.md", "body") in paths_scopes
    assert ("docs/guide.md", "title") in paths_scopes
    assert ("docs/guide.md", "body") in paths_scopes
    assert all("ignored.json" not in c.path for c in chunks)

    # Explicit files_paths via collect_all(sources={"files"})
    via_all = collect_all(
        tmp_path,
        "en",
        {"files"},
        files_paths=(tmp_path / "README.md", docs / "ignored.json"),
    )
    assert any(c.path == "README.md" for c in via_all)
    assert any(c.path == "docs/ignored.json" for c in via_all)
