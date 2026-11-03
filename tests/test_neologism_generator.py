"""V4-3: synthetic mashup neologisms across 7 locales; codes stay filtered."""

from __future__ import annotations

import itertools

import pytest

from lexaudit.core.types import ClassifiedWord, VocabSample
from lexaudit.detectors.neologism import (
    _is_catalog_code,
    make_neologism_detector,
    score_neologism,
)

LOCALES = ("en", "de", "es", "pl", "ru", "sv", "uk")

# Locale roots / affixes used only in this test generator (not in detector source).
_ROOTS: dict[str, tuple[str, ...]] = {
    "en": ("dock", "walk", "pier", "deck", "haul", "bilge", "keel"),
    "de": ("steg", "leine", "rumpf", "hafen", "bug", "kiel"),
    "es": ("muelle", "cubierta", "casco", "fondeo", "proa"),
    "pl": ("keja", "poklad", "kadlub", "cumy", "dziob"),
    "ru": ("пирс", "палуб", "корпус", "трап", "шкив"),
    "uk": ("причал", "палуб", "корпус", "трап", "шкіа"),
    "sv": ("brygga", "däck", "skrov", "bog", "köl"),
}

_AFFIXES: dict[str, tuple[str, ...]] = {
    "en": ("ish", "ness", "like"),
    "de": ("ig", "lich", "heit"),
    "es": ("ezca", "alezca", "ismo"),
    "pl": ("owaty", "owski", "ność"),
    "ru": ("овый", "ность", "ость"),
    "uk": ("овий", "ність", "ість"),
    "sv": ("ig", "aktig", "ning"),
}

_GLUE_SECONDS: dict[str, tuple[str, ...]] = {
    "en": ("check", "walk", "survey"),
    "de": ("check", "manöver", "runde"),
    "es": ("chequeo", "revision", "mira"),
    "pl": ("check", "przeglad", "ogląd"),
    "ru": ("осмотр", "проверка", "обход"),
    "uk": ("огляд", "перевірка", "обхід"),
    "sv": ("check", "runda", "koll"),
}

_CATALOG_CODES = (
    "rtkepsilon",
    "vbkzeta",
    "jkltheta",
    "dfkappa",
    "mnvdelta",
    "sku42ab",
    "а1б2в3",
)


def _mashups_for(locale: str, *, limit: int = 24) -> list[str]:
    roots = _ROOTS[locale]
    affixes = _AFFIXES[locale]
    seconds = _GLUE_SECONDS[locale]
    out: list[str] = []
    for a, b, suf in itertools.product(roots, seconds, affixes):
        # root+root+affix coinages
        out.append(f"{a}{b}{suf}")
        if len(out) >= limit:
            break
    for a, b in itertools.product(roots[:4], seconds[:3]):
        glued = f"{a}{b}"
        if len(glued) >= 10:
            out.append(glued)
        if len(out) >= limit + 8:
            break
    # Dedup, keep longer mashups first.
    uniq = sorted(set(out), key=lambda w: (-len(w), w))
    return uniq[:limit]


def _suspect(token: str) -> ClassifiedWord:
    return ClassifiedWord(
        normalized=token.casefold(),
        surface=token,
        count=1,
        status="suspect",
        samples=[VocabSample(path="gen.md", scope="body")],
        reason="unknown",
        detectors=["hunspell"],
        tier="weak",
    )


@pytest.mark.parametrize("locale", LOCALES)
def test_generated_mashups_catch_many(locale: str) -> None:
    detect = make_neologism_detector(locale)
    mashups = _mashups_for(locale)
    assert len(mashups) >= 12
    hits = 0
    for token in mashups:
        word = _suspect(token)
        updated = detect(word)
        if updated is not None and updated.status == "invented":
            hits += 1
            assert updated.tier == "likely"
            assert "neologism" in updated.detectors
    # Detector must catch a solid majority of synthetic mashups (not every hapax).
    assert hits / len(mashups) >= 0.5, f"{locale}: only {hits}/{len(mashups)} mashups caught"


def test_catalog_codes_filtered() -> None:
    for code in _CATALOG_CODES:
        assert _is_catalog_code(code), code
        for locale in ("en", "de", "ru"):
            info = score_neologism(code, locale)
            assert info["catalog_code"] is True
            assert info["invented"] is False
            detect = make_neologism_detector(locale)
            word = _suspect(code)
            updated = detect(word)
            if updated is not None:
                assert updated.status != "invented"


def test_detector_does_not_hardcode_benchmark_needles() -> None:
    """Regression: detector/rank must not embed synthetic-demo needles as literals."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1]
    paths = (
        root / "src" / "lexaudit" / "detectors" / "neologism.py",
        root / "src" / "lexaudit" / "core" / "rank.py",
    )
    forbidden = (
        "dockwalkish",
        "vinylester",
        "haulout",
        "pantanalezca",
        "kejowaty",
        "bryggcheckig",
        "stegmanöverig",
        "пирсовыйосмотр",
        "причальноогляд",
    )
    for src in paths:
        text = src.read_text(encoding="utf-8").casefold()
        for needle in forbidden:
            assert needle.casefold() not in text, f"hardcoded needle {needle!r} in {src.name}"


def test_plain_short_hapax_not_always_invented() -> None:
    detect = make_neologism_detector("en")
    word = _suspect("xyzzy")
    updated = detect(word)
    assert updated is None or updated.status != "invented"


@pytest.mark.parametrize(
    "locale,token",
    [
        ("en", "dockwalkish"),
        ("de", "stegmanöverig"),
        ("es", "pantanalezca"),
        ("pl", "kejowaty"),
        ("sv", "bryggcheckig"),
        ("ru", "пирсовыйосмотр"),
        ("uk", "причальноогляд"),
    ],
)
def test_open_set_synthetic_demo_tokens_invented(locale: str, token: str) -> None:
    """Sanity on demo open-set tokens without baking them into detector logic."""
    detect = make_neologism_detector(locale)
    updated = detect(_suspect(token))
    assert updated is not None
    assert updated.status == "invented"


def test_domain_term_downweight_outranks_clean_jargon() -> None:
    from lexaudit.core.classify import apply_domain_term_candidates
    from lexaudit.core.rank import word_rank_weight

    neo = _suspect("dockwalkish")
    neo.status = "invented"
    neo.detectors = ["hunspell", "neologism"]
    neo.reason = "neologism-affix-mash"
    neo.tier = "likely"

    jargon = ClassifiedWord(
        normalized="vinylester",
        surface="vinylester",
        count=2,
        status="suspect",
        samples=[
            VocabSample(path="p03.md", scope="body", line=3),
            VocabSample(path="p03.md", scope="body", line=4),
        ],
        reason="unknown",
        detectors=["hunspell"],
        tier="weak",
    )
    apply_domain_term_candidates([jargon])
    assert jargon.reason == "domain-term-candidate"
    assert word_rank_weight(neo, locale="en") > word_rank_weight(jargon, locale="en")
    assert word_rank_weight(jargon, locale="en") <= 0.05
