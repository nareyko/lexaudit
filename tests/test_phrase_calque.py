from __future__ import annotations

from pathlib import Path

from lexaudit.core.types import ClassifiedWord, TextChunk, VocabSample
from lexaudit.detectors.calque import (
    CalqueRule,
    apply_phrase_calque_pass,
    load_calque_rules,
)


def test_phrase_calque_pass_flags_multiword() -> None:
    rules = [
        CalqueRule(
            pattern="into your own hands",
            locale="en",
            reason="phrase-test",
            hint="take charge",
            severity="confirmed",
            source="test",
            match="phrase",
        )
    ]
    chunks = [
        TextChunk(
            path="en/a.md",
            scope="body",
            text="Always take the rudder into your own hands before leaving.",
            source="files",
        )
    ]
    words = apply_phrase_calque_pass([], chunks, rules, locale="en")
    assert any(w.status == "calque" and "phrase" in w.detectors for w in words)
    assert any(w.normalized == "into_your_own_hands" for w in words)


def test_bundled_en_loads_phrase_rules() -> None:
    root = Path(__file__).resolve().parents[1] / "rules" / "calques"
    rules = load_calque_rules(root)
    phrases = [r for r in rules if r.locale == "en" and r.match == "phrase"]
    assert any("into your own hands" in r.pattern for r in phrases)


def test_phrase_does_not_match_token_detector_path() -> None:
    from lexaudit.detectors.calque import make_calque_detector

    rules = [
        CalqueRule(
            pattern="into your own hands",
            locale="en",
            reason="phrase-test",
            hint="",
            severity="confirmed",
            source="test",
            match="phrase",
        )
    ]
    detect = make_calque_detector("en", rules)
    word = ClassifiedWord(
        normalized="into",
        surface="into",
        count=1,
        status="suspect",
        samples=[VocabSample(path="x", scope="body")],
        reason="unknown",
        detectors=["hunspell"],
    )
    assert detect(word) is None
