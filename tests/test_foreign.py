"""Foreign detector - all branches."""

from __future__ import annotations

from lexaudit.core.rank import word_rank_weight
from lexaudit.core.types import ClassifiedWord, VocabSample
from lexaudit.detectors.english_leak import ENGLISH_LEAK_STOPWORDS, make_english_leak_detector
from lexaudit.detectors.foreign import (
    CYRILLIC_LOCALES,
    LATIN_LOCALES,
    classify_ru_foreign_context,
    make_foreign_detector,
)


def _word(
    norm: str,
    status: str = "suspect",
    *,
    scope: str = "body",
    surface: str | None = None,
) -> ClassifiedWord:
    return ClassifiedWord(
        normalized=norm,
        surface=surface if surface is not None else norm,
        count=1,
        status=status,  # type: ignore[arg-type]
        samples=[VocabSample("a.md", scope)],
        detectors=["hunspell"],
    )


def test_locale_sets() -> None:
    assert frozenset({"ru", "uk"}) == CYRILLIC_LOCALES
    assert frozenset({"en", "de", "pl", "es", "sv"}) == LATIN_LOCALES


def test_latin_in_russian_via_dict() -> None:
    det = make_foreign_detector("ru", {"en": {"offshore", "brokerage"}})
    out = det(_word("offshore"))
    assert out is not None
    assert out.status == "foreign"
    assert out.reason == "latin-in-ru-via-en:mid-body"
    assert out.detectors == ["foreign", "hunspell"]


def test_latin_in_russian_script_len() -> None:
    det = make_foreign_detector("ru")
    out = det(_word("hull"))
    assert out is not None
    assert out.status == "foreign"
    assert out.reason == "latin-script-in-ru:mid-body"
    assert out.detectors == ["foreign", "hunspell"]
    assert det(_word("gps")) is None  # len < 4


def test_cyrillic_in_english() -> None:
    det = make_foreign_detector("en")
    out = det(_word("лодка"))
    assert out is not None
    assert out.status == "foreign"
    assert out.reason == "cyrillic-in-en"
    assert out.detectors == ["foreign", "hunspell"]


def test_ok_not_touched() -> None:
    det = make_foreign_detector("ru")
    assert det(_word("лодка", status="ok")) is None


def test_dict_hit_other_locale_min_len() -> None:
    det = make_foreign_detector("de", {"en": {"brokerage", "boat"}})
    out = det(_word("brokerage"))
    assert out is not None
    assert out.reason == "dict-hit-en"
    assert out.status == "foreign"
    assert out.detectors == ["foreign", "hunspell"]
    # same locale skipped; short word < 5 ignored
    assert det(_word("boat")) is None
    det2 = make_foreign_detector("en", {"en": {"brokerage"}})
    assert det2(_word("brokerage")) is None
    # uk cyrillic locale also treats latin via dict
    det_uk = make_foreign_detector("uk", {"en": {"brokerage"}})
    assert det_uk(_word("brokerage")).reason == "latin-in-uk-via-en:mid-body"  # type: ignore[union-attr]


def test_no_match_returns_none() -> None:
    det = make_foreign_detector("pl")
    assert det(_word("łodka")) is None


def test_ru_foreign_context_in_title() -> None:
    det = make_foreign_detector("ru")
    out = det(_word("offshore", scope="title"))
    assert out is not None
    assert out.reason.endswith(":heading")


def test_ru_title_case_brand_is_proper_seed() -> None:
    w = _word("hallberg", surface="Hallberg")
    assert classify_ru_foreign_context(w) == "proper-seed"
    det = make_foreign_detector("ru")
    out = det(w)
    assert out is not None
    assert out.reason == "latin-script-in-ru:proper-seed"


def test_ru_foreign_quote_scope() -> None:
    w = _word("broker", scope="blockquote")
    assert classify_ru_foreign_context(w) == "quotes"
    det = make_foreign_detector("ru", {"en": {"broker"}})
    out = det(w)
    assert out is not None
    assert out.reason == "latin-in-ru-via-en:quotes"


def test_de_english_leak_stopwords() -> None:
    assert frozenset({"of", "the", "and", "to", "for", "with"}) == ENGLISH_LEAK_STOPWORDS
    det = make_english_leak_detector("de")
    out = det(_word("of"))
    assert out is not None
    assert out.status == "foreign"
    assert out.reason == "english-leak"
    assert "english_leak" in out.detectors
    assert det(_word("of", scope="title")) is None
    assert make_english_leak_detector("ru")(_word("of")) is None


def test_ru_mid_body_foreign_weight_higher_than_title_case() -> None:
    body = ClassifiedWord(
        normalized="hull",
        surface="hull",
        count=1,
        status="foreign",
        reason="latin-script-in-ru:mid-body",
        samples=[VocabSample("p.md", "body")],
    )
    brand = ClassifiedWord(
        normalized="hallberg",
        surface="Hallberg",
        count=1,
        status="foreign",
        reason="latin-script-in-ru:proper-seed",
        samples=[VocabSample("p.md", "body")],
    )
    leak = ClassifiedWord(
        normalized="of",
        surface="of",
        count=1,
        status="foreign",
        reason="english-leak",
        samples=[VocabSample("p.md", "body")],
    )
    assert word_rank_weight(body, locale="ru") == 2.0
    assert word_rank_weight(brand, locale="ru") == 0.2
    assert word_rank_weight(leak, locale="de") == 0.2
