"""Calque YAML rules - minimum counts and detector behaviour."""

from __future__ import annotations

from pathlib import Path

from lexaudit.core.aggregate import add_tokens
from lexaudit.core.classify import classify_occurrences
from lexaudit.core.types import ClassifiedWord, VocabOccurrence, VocabSample
from lexaudit.detectors.calque import load_calque_rules, make_calque_detector

RULES = Path(__file__).resolve().parents[1] / "rules" / "calques"


class AllOkChecker:
    dict_id = "all-ok"

    def list_misspelled(self, words: list[str]) -> set[str]:
        return set()


class AllMissChecker:
    dict_id = "all-miss"

    def list_misspelled(self, words: list[str]) -> set[str]:
        return set(words)


def test_rule_minimums() -> None:
    ru = load_calque_rules(RULES / "ru.yaml")
    en = load_calque_rules(RULES / "en.yaml")
    de = load_calque_rules(RULES / "de.yaml")
    assert len(ru) >= 30
    assert len(en) >= 15
    assert len(de) >= 15
    for rules in (ru, en, de):
        for r in rules:
            assert r.source
            assert r.pattern
            assert r.locale


def test_calque_detector_hits() -> None:
    rules = load_calque_rules(RULES / "ru.yaml")
    det = make_calque_detector("ru", rules)
    word = ClassifiedWord(
        normalized="листинг",
        surface="листинг",
        count=1,
        status="suspect",
        samples=[VocabSample("a.md", "body")],
        detectors=["hunspell"],
    )
    out = det(word)
    assert out is not None
    assert out.status == "calque"
    assert "calque" in out.detectors
    assert (
        det(
            ClassifiedWord(
                normalized="некалика",
                surface="некалика",
                count=1,
                status="suspect",
                samples=[VocabSample("a.md", "body")],
            )
        )
        is None
    )


def test_en_orientir_and_denseness_override_ok() -> None:
    rules = load_calque_rules(RULES / "en.yaml")
    det = make_calque_detector("en", rules)
    ori = det(
        ClassifiedWord(
            normalized="orientir",
            surface="orientir",
            count=1,
            status="suspect",
            samples=[VocabSample("a.md", "body")],
        )
    )
    assert ori is not None
    assert ori.status == "calque"
    assert ori.tier in {"confirmed", "likely"}
    compound = det(
        ClassifiedWord(
            normalized="pre-orientir",
            surface="pre-orientir",
            count=1,
            status="suspect",
            samples=[VocabSample("a.md", "body")],
        )
    )
    assert compound is not None
    assert compound.status == "calque"
    # denseness: hunspell-ok still becomes calque via override_ok
    dense = det(
        ClassifiedWord(
            normalized="denseness",
            surface="denseness",
            count=2,
            status="ok",
            samples=[VocabSample("a.md", "body")],
            detectors=["hunspell"],
            reason="hunspell",
        )
    )
    assert dense is not None
    assert dense.status == "calque"
    assert dense.tier in {"confirmed", "likely"}


def test_de_orientir_denseness() -> None:
    rules = load_calque_rules(RULES / "de.yaml")
    det = make_calque_detector("de", rules)
    hit = det(
        ClassifiedWord(
            normalized="orientir",
            surface="Orientir",
            count=1,
            status="suspect",
            samples=[VocabSample("a.md", "body")],
        )
    )
    assert hit is not None and hit.status == "calque"
    dense = det(
        ClassifiedWord(
            normalized="denseness",
            surface="denseness",
            count=1,
            status="ok",
            samples=[VocabSample("a.md", "body")],
        )
    )
    assert dense is not None and dense.status == "calque"


def test_ru_needle_globs_not_skeg_case() -> None:
    rules = load_calque_rules(RULES / "ru.yaml")
    det = make_calque_detector("ru", rules)
    for surface, norm in (
        ("предпокупочный", "предпокупочный"),
        ("предпокупочного", "предпокупочного"),
        ("чеклисте", "чеклисте"),
        ("блувотер", "блувотер"),
        ("блувотерный", "блувотерный"),
    ):
        out = det(
            ClassifiedWord(
                normalized=norm,
                surface=surface,
                count=1,
                status="suspect",
                samples=[VocabSample("a.md", "body")],
            )
        )
        assert out is not None, norm
        assert out.status == "calque"
        assert out.tier in {"confirmed", "likely"}
    # «на скеге» morphology - must NOT be flagged as calque/invented
    skeg = det(
        ClassifiedWord(
            normalized="скеге",
            surface="скеге",
            count=3,
            status="suspect",
            samples=[VocabSample("wiki/skeg.json", "body")],
        )
    )
    assert skeg is None


def test_denseness_override_through_classify() -> None:
    """Pipeline must flip hunspell-ok denseness to calque (post-detector)."""
    rules = load_calque_rules(RULES / "en.yaml")
    occ: dict[str, VocabOccurrence] = {}
    add_tokens(
        occ,
        [{"normalized": "denseness", "surface": "denseness"}],
        path="a.md",
        scope="body",
    )
    classified = classify_occurrences(
        occurrences=occ,
        proper=set(),
        acronyms=set(),
        templates=set(),
        checker=AllOkChecker(),
        post_detectors=[make_calque_detector("en", rules)],
    )
    assert classified[0].status == "calque"
    assert "calque" in classified[0].detectors


def test_ru_denseness_foreign_then_calque() -> None:
    """Latin denseness in RU: foreign first, then calque override."""
    from lexaudit.detectors.foreign import make_foreign_detector

    ru_rules = load_calque_rules(RULES / "ru.yaml")
    occ: dict[str, VocabOccurrence] = {}
    add_tokens(
        occ,
        [{"normalized": "denseness", "surface": "denseness"}],
        path="a.md",
        scope="body",
    )
    classified = classify_occurrences(
        occurrences=occ,
        proper=set(),
        acronyms=set(),
        templates=set(),
        checker=AllMissChecker(),
        post_detectors=[
            make_foreign_detector("ru"),
            make_calque_detector("ru", ru_rules),
        ],
    )
    assert classified[0].status == "calque"
    assert "calque" in classified[0].detectors


def test_load_calque_missing_and_dir(tmp_path: Path) -> None:
    assert load_calque_rules(tmp_path / "missing.yaml") == []
    d = tmp_path / "rules"
    d.mkdir()
    (d / "x.yaml").write_text(
        "rules:\n  - pattern: FooBar\n    locale: en\n",
        encoding="utf-8",
    )
    (d / "y.yml").write_text(
        "rules:\n  - pattern: Baz\n    locale: en\n    reason: custom\n"
        "    hint: try\n    severity: weak\n    source: manual\n",
        encoding="utf-8",
    )
    (d / "empty.yaml").write_text("rules: {}\n", encoding="utf-8")
    loaded = load_calque_rules(d)
    assert len(loaded) == 2
    by_pat = {r.pattern: r for r in loaded}
    assert by_pat["FooBar"].reason == "calque"
    assert by_pat["FooBar"].hint == ""
    assert by_pat["FooBar"].severity == "likely"
    assert by_pat["FooBar"].source == "x.yaml"
    assert by_pat["Baz"].reason == "custom"
    assert by_pat["Baz"].hint == "try"
    assert by_pat["Baz"].severity == "weak"
    assert by_pat["Baz"].source == "manual"
    det = make_calque_detector("en", loaded)
    hit = det(
        ClassifiedWord(
            normalized="foobar",
            surface="FooBar",
            count=1,
            status="suspect",
            samples=[VocabSample("a.md", "body")],
        )
    )
    assert hit is not None
    assert hit.tier == "likely"
    assert hit.reason == "calque"
    weak = det(
        ClassifiedWord(
            normalized="baz",
            surface="Baz",
            count=1,
            status="suspect",
            samples=[VocabSample("a.md", "body")],
        )
    )
    assert weak is not None
    assert weak.tier == "weak"
