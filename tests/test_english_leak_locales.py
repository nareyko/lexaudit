from __future__ import annotations

from lexaudit.core.types import ClassifiedWord, VocabSample
from lexaudit.detectors.english_leak import ENGLISH_LEAK_LOCALES, make_english_leak_detector


def _suspect(norm: str) -> ClassifiedWord:
    return ClassifiedWord(
        normalized=norm,
        surface=norm,
        count=2,
        status="suspect",
        samples=[VocabSample(path="x.md", scope="body")],
        reason="unknown",
        detectors=["hunspell"],
        tier="weak",
    )


def test_english_leak_locales_include_romance_and_nordic() -> None:
    assert frozenset({"de", "es", "pl", "sv"}) == ENGLISH_LEAK_LOCALES


def test_english_leak_fires_on_es_and_skips_ru() -> None:
    es = make_english_leak_detector("es")
    ru = make_english_leak_detector("ru")
    word_es = _suspect("the")
    word_ru = _suspect("the")
    assert es(word_es) is not None
    assert word_es.status == "foreign"
    assert ru(word_ru) is None
    assert word_ru.status == "suspect"
