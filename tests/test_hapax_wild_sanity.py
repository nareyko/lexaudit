from __future__ import annotations

from pathlib import Path

from lexaudit.core.rank import word_rank_weight
from lexaudit.core.types import ClassifiedWord, VocabSample


def test_long_coinage_outranks_short_alnum_code() -> None:
    long = ClassifiedWord(
        normalized="dashboardishness",
        surface="dashboardishness",
        count=1,
        status="suspect",
        samples=[VocabSample(path="wiki.md", scope="body")],
        reason="unknown",
        detectors=["hunspell"],
        tier="weak",
    )
    code = ClassifiedWord(
        normalized="x7k2",
        surface="x7k2",
        count=1,
        status="suspect",
        samples=[VocabSample(path="wiki.md", scope="body")],
        reason="unknown",
        detectors=["hunspell"],
        tier="weak",
    )
    assert word_rank_weight(long, locale="en") > word_rank_weight(code, locale="en")


def test_packs_wild_seed_exists() -> None:
    root = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "packs_wild"
    assert (root / "SOURCES.md").is_file()
    md = list(root.rglob("wiki-*.md"))
    assert len(md) >= 20
    # Slug filenames only — no title-named Cyrillic/long duplicates in git.
    assert all("wiki-" in p.name and p.name.isascii() for p in md)


def test_packs_field_clean_domain_fixtures() -> None:
    root = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "packs_field"
    clean = list(root.rglob("02-clean-domain.md"))
    assert len(clean) >= 30


def test_mcp_server_json_registry_shape() -> None:
    import json

    path = (
        Path(__file__).resolve().parents[1]
        / "packages"
        / "mcp-lexaudit"
        / "server.json"
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["name"] == "io.github.nareyko/lexaudit"
    assert len(data["description"]) <= 100
    assert data["version"] == "0.3.0"
