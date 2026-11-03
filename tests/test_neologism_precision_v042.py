"""v0.4.2 W1: neologism false-positive precision (DE/SV nouns, ES accent, DE gloss)."""

from __future__ import annotations

from lexaudit.core.types import ClassifiedWord, VocabSample
from lexaudit.detectors.foreign import make_foreign_detector
from lexaudit.detectors.neologism import make_neologism_detector, score_neologism


def _suspect(token: str) -> ClassifiedWord:
    return ClassifiedWord(
        normalized=token.casefold(),
        surface=token,
        count=1,
        status="suspect",
        samples=[VocabSample(path="t.md", scope="body")],
        reason="unknown",
        detectors=["hunspell"],
        tier="weak",
    )


def test_werftrechnung_not_invented() -> None:
    info = score_neologism("Werftrechnung", "de")
    assert info["invented"] is False
    assert info["affix_mash"] is False
    updated = make_neologism_detector("de")(_suspect("Werftrechnung"))
    assert updated is None or updated.status != "invented"


def test_catabaticos_not_calque_glue() -> None:
    info = score_neologism("catabáticos", "es")
    assert info["calque_glue"] is False
    assert info["invented"] is False
    updated = make_neologism_detector("es")(_suspect("catabáticos"))
    assert updated is None or updated.status != "invented"


def test_ausbildungstoern_is_foreign_not_invented() -> None:
    for locale in ("es", "pl", "ru", "uk"):
        info = score_neologism("Ausbildungstörn", locale)
        assert info["invented"] is False, locale
        assert info["foreign_diacritics"] is True, locale
        neo = make_neologism_detector(locale)(_suspect("Ausbildungstörn"))
        assert neo is None or neo.status != "invented", locale
        foreign = make_foreign_detector(locale)(_suspect("Ausbildungstörn"))
        assert foreign is not None
        assert foreign.status == "foreign"
        assert "de-orthography" in foreign.reason
