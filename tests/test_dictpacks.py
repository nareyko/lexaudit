"""Dictionary loader - mutation-dense fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from lexaudit.dictpacks.loader import (
    build_allowlist,
    build_compound_known_lemmas,
    load_acronyms,
    load_proper_names,
    load_thin_allowlist,
    phrase_tokens,
    seed_from_pending_packs,
    seed_from_slug,
)


def test_phrase_tokens_compact_and_parts() -> None:
    toks = phrase_tokens("NorthWind-Marine", "en")
    assert "northwind-marine" in toks
    assert "northwindmarine" in toks
    # TOKEN_RE keeps hyphenated form as one token; space-separated yields parts
    spaced = phrase_tokens("NorthWind Marine", "en")
    assert "northwind" in spaced
    assert "marine" in spaced
    plain = phrase_tokens("boat", "en")
    assert "boat" in plain


def test_seed_from_slug_letter_prefix() -> None:
    toks = seed_from_slug("beneteau-oceanis", "en")
    assert "beneteau" in toks
    assert "oceanis" in toks or "beneteau-oceanis" in toks
    short = seed_from_slug("x", "en")
    assert "x" in short


def test_load_proper_and_acronyms(tmp_path: Path) -> None:
    proper = tmp_path / "proper-names.yaml"
    acronyms = tmp_path / "acronyms.yaml"
    proper.write_text(
        "version: 1\nbrands_yards:\n  - AcmeCorp\n  - NorthWind-Marine\nnested:\n  - A\n  - B\n",
        encoding="utf-8",
    )
    acronyms.write_text("version: 1\nitems:\n  - EPIRB\n  - DSC\n", encoding="utf-8")
    pset = load_proper_names(proper, "en")
    assert "acmecorp" in pset
    assert "northwindmarine" in pset
    aset = load_acronyms(acronyms, "en")
    assert "epirb" in aset
    assert "dsc" in aset
    # acronyms without items key falls back to full tree
    acronyms2 = tmp_path / "acr2.yaml"
    acronyms2.write_text("version: 1\nfoo:\n  - AIS\n", encoding="utf-8")
    assert "ais" in load_acronyms(acronyms2, "en")


def test_load_thin_allowlist_legacy_keys(tmp_path: Path) -> None:
    allow = tmp_path / "allowlist.yaml"
    allow.write_text(
        "version: 2\n"
        "section_markers:\n  - Overview\n  - 1\n"
        "locale_loans:\n  - сюрвей\n"
        "names:\n  - LegacyName\n"
        "acronyms:\n  - LEG\n"
        "extras:\n  - ExtraTok\n",
        encoding="utf-8",
    )
    markers, loans = load_thin_allowlist(allow, "en")
    assert "overview" in markers
    assert "сюрвей" in loans
    assert "legacyname" in loans
    assert "leg" in loans
    assert "extratok" in loans


def test_load_yaml_non_mapping_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(TypeError, match="expected mapping"):
        load_proper_names(bad, "en")


def test_seed_from_pending_packs(tmp_path: Path) -> None:
    assert seed_from_pending_packs(tmp_path / "missing", "en") == set()
    packs = tmp_path / "packs"
    brand = packs / "beneteau"
    model = brand / "oceanis-46"
    model.mkdir(parents=True)
    (packs / ".skip").mkdir()
    (brand / ".gitkeep").mkdir()
    toks = seed_from_pending_packs(packs, "en")
    assert "beneteau" in toks
    assert "oceanis" in toks or "oceanis-46" in toks


def test_build_allowlist_from_fixtures(tmp_path: Path) -> None:
    proper = tmp_path / "proper-names.yaml"
    acronyms = tmp_path / "acronyms.yaml"
    allow = tmp_path / "allowlist.yaml"
    packs = tmp_path / "packs"
    (packs / "jeanneau" / "sun-odyssey").mkdir(parents=True)
    proper.write_text(
        "version: 1\nbrands_yards:\n  - AcmeCorp\n  - NorthWind-Marine\n",
        encoding="utf-8",
    )
    acronyms.write_text("version: 1\nitems:\n  - EPIRB\n  - DSC\n", encoding="utf-8")
    allow.write_text(
        "version: 2\nsection_markers:\n  - Overview\nlocale_loans:\n  - сюрвей\n",
        encoding="utf-8",
    )
    pset, aset, tset = build_allowlist(
        locale="en",
        proper_names_path=proper,
        acronyms_path=acronyms,
        allowlist_path=allow,
        packs_root=packs,
        extra_slugs=["alpha-model"],
    )
    assert "acmecorp" in pset
    assert "northwind-marine" in pset
    assert "northwindmarine" in pset
    assert "epirb" in aset
    assert "overview" in tset
    assert "сюрвей" in pset
    assert "jeanneau" in pset
    assert "alpha" in pset or "alpha-model" in pset


def test_build_compound_known_lemmas() -> None:
    proper = {"marina", "offshore", "welt", "umsegelung"}
    acronyms = {"epirb"}
    known = build_compound_known_lemmas(proper, acronyms)
    assert known == proper | acronyms


def test_build_allowlist_skips_missing_paths(tmp_path: Path) -> None:
    pset, aset, tset = build_allowlist(
        locale="en",
        proper_names_path=tmp_path / "nope.yaml",
        acronyms_path=tmp_path / "nope2.yaml",
        allowlist_path=tmp_path / "nope3.yaml",
        packs_root=None,
        extra_slugs=None,
    )
    assert pset == set()
    assert aset == set()
    assert tset == set()
