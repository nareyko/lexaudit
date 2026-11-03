"""Compound, morph, and template detectors."""

from __future__ import annotations

from lexaudit.core.types import ClassifiedWord, VocabSample
from lexaudit.detectors.compound import SUPPORTED, _can_split, make_compound_detector
from lexaudit.detectors.morph import make_morph_detector
from lexaudit.detectors.template import make_template_detector


def _suspect(norm: str, surface: str | None = None, status: str = "suspect") -> ClassifiedWord:
    return ClassifiedWord(
        normalized=norm,
        surface=surface or norm,
        count=1,
        status=status,  # type: ignore[arg-type]
        samples=[VocabSample("a.md", "body")],
        detectors=["hunspell"],
    )


def test_supported_locales() -> None:
    assert "de" in SUPPORTED
    assert "sv" in SUPPORTED
    assert "en" not in SUPPORTED


def test_can_split_direct_and_fugen() -> None:
    known = {"segel", "schiff", "boot", "arbeit", "nehmer"}
    assert _can_split("segelboot", known) is True
    assert _can_split("ab", known) is False  # too short
    assert _can_split("arbeitnehmer", known) is True
    # Fugen-s: arbeit + s + nehmer style via left.endswith("s")
    known2 = {"arbeit", "zeit"}
    assert _can_split("arbeitszeit", known2) is True
    known3 = {"haus", "tür"}
    assert _can_split("haustür", known3) is True
    # es fugen
    known4 = {"kind", "wagen"}
    assert _can_split("kindeswagen", known4) is True
    assert _can_split("xxxxxyyyyy", {"aaaa", "bbbb"}) is False


def test_compound_split_known_parts() -> None:
    det = make_compound_detector("de", {"segel", "schiff", "boot", "rumpf"})
    out = det(_suspect("segelboot"))
    assert out is not None
    assert out.status == "ok"
    assert out.reason == "compound-split"
    assert out.tier is None
    assert "compound" in out.detectors
    assert det(_suspect("xyzzyqboat")) is None
    assert det(_suspect("segelboot", status="ok")) is None


def test_compound_maritime_glue_parts() -> None:
    """Maritime lemmas from proper-names pack split glued DE compounds (I5-2)."""
    known = {"vorkauf", "besichtigung", "welt", "umsegelung", "törn", "planung"}
    det = make_compound_detector("de", known)
    for word in ("vorkaufsbesichtigung", "weltumsegelung", "törnplanung"):
        out = det(_suspect(word))
        assert out is not None, word
        assert out.status == "ok"
        assert out.reason == "compound-split"


def test_compound_sv_and_noop_en() -> None:
    det_sv = make_compound_detector("sv", {"segel", "båt"})
    # may or may not split depending on å folding - at least noop path for non-split
    assert det_sv(_suspect("xyz")) is None
    det = make_compound_detector("en", {"boat", "house"})
    assert det(_suspect("boathouse")) is None


def test_compound_hyphen_tech_and_suffix() -> None:
    det = make_compound_detector("de", {"version", "wert", "beobacht"})
    out = det(_suspect("api-versionierung"))
    assert out is not None
    assert out.status == "ok"
    assert out.reason == "compound-hyphen"
    out2 = det(_suspect("max-age-werte"))
    assert out2 is not None
    assert out2.status == "ok"
    out3 = det(_suspect("beobachtbarkeit"))
    assert out3 is not None
    assert out3.status == "ok"
    assert out3.reason in {"compound-suffix", "compound-split"}
    out4 = det(_suspect("commit"))
    assert out4 is not None
    assert out4.reason == "tech-term"


def test_compound_sv_fugen_and_het() -> None:
    det = make_compound_detector("sv", {"uppdatering", "observerbar", "sökväg", "version"})
    assert det(_suspect("uppdateringstoken")) is not None
    assert det(_suspect("observerbarhet")) is not None
    assert det(_suspect("sökvägsversioner")) is not None
    assert det(_suspect("tokenautentisering")) is not None


def test_template_detector() -> None:
    det = make_template_detector({"overview", "faq"})
    out = det(_suspect("overview"))
    assert out is not None
    assert out.status == "template"
    assert out.reason == "section-marker"
    assert out.tier is None
    assert "template" in out.detectors
    assert "hunspell" in out.detectors
    assert out.detectors == sorted(out.detectors)
    assert all(d in {"hunspell", "template"} for d in out.detectors)
    assert det(_suspect("boat")) is None


def test_morph_known_russian() -> None:
    det = make_morph_detector("ru")
    out = det(_suspect("лодка", "Лодка"))
    assert out is not None
    assert out.status == "ok"
    assert det(_suspect("xxyzzyqboat")) is None
    assert det(_suspect("лодка", status="ok")) is None


def test_morph_noop_for_en() -> None:
    det = make_morph_detector("en")
    assert det(_suspect("boats")) is None
