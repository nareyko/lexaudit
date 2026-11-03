"""Sentence-window context filters for false friends / gated calques."""

from __future__ import annotations

from lexaudit.core.types import ClassifiedWord, TextChunk, VocabSample
from lexaudit.detectors.calque import (
    CalqueRule,
    apply_phrase_calque_pass,
    context_allows,
    make_calque_detector,
    rule_matches_text,
    split_sentences,
)


def _ff(**kw: object) -> CalqueRule:
    base: dict[str, object] = {
        "pattern": "actualmente",
        "locale": "es",
        "reason": "ff-actualmente",
        "hint": "en realidad / actualmente(=now)",
        "severity": "confirmed",
        "source": "t",
        "kind": "false_friend",
        "source_lang": "en",
        "override_ok": True,
        "match": "exact",
        "context_require": ("acuerdo",),
        "context_forbid": ("trabajo", "años"),
    }
    base.update(kw)
    return CalqueRule(**base)  # type: ignore[arg-type]


def test_split_sentences_basic() -> None:
    parts = split_sentences("Uno. Dos!\nTres")
    assert parts == ["Uno.", "Dos!", "Tres"]


def test_context_allows_require_and_forbid() -> None:
    rule = _ff()
    assert context_allows(rule, "Actualmente no estoy de acuerdo.", "es")
    assert not context_allows(rule, "Actualmente trabajo en Madrid.", "es")
    assert not context_allows(rule, "Actualmente tengo tres años aquí.", "es")
    # context_allows ignores the pattern; require-only sentence still passes.
    assert context_allows(rule, "Hoy no estoy de acuerdo.", "es")
    assert not rule_matches_text(rule, "Hoy no estoy de acuerdo.")


def test_rule_matches_text_sentence_window() -> None:
    rule = _ff()
    pos = "Actualmente no estoy de acuerdo con esa cifra."
    neg = "Actualmente trabajo en la oficina."
    mixed = "Actualmente trabajo en la oficina. Actualmente no estoy de acuerdo con esa cifra."
    assert rule_matches_text(rule, pos)
    assert not rule_matches_text(rule, neg)
    # Second sentence should still fire even if first is clean.
    assert rule_matches_text(rule, mixed)


def test_token_detector_skips_context_rules() -> None:
    rule = _ff()
    detect = make_calque_detector("es", [rule])
    word = ClassifiedWord(
        normalized="actualmente",
        surface="Actualmente",
        count=1,
        status="ok",
        samples=[VocabSample("a.md", "body")],
        reason="hunspell",
    )
    assert detect(word) is None


def test_body_pass_flags_contextual_false_friend() -> None:
    rule = _ff()
    chunks = [
        TextChunk(
            path="es/a.md",
            scope="body",
            text="Actualmente no estoy de acuerdo con esa cifra.",
            source="files",
        )
    ]
    words = apply_phrase_calque_pass([], chunks, [rule], locale="es")
    assert any(w.normalized == "actualmente" and w.status == "calque" for w in words)
    clean = [
        TextChunk(
            path="es/b.md",
            scope="body",
            text="Actualmente trabajo en Madrid.",
            source="files",
        )
    ]
    assert apply_phrase_calque_pass([], clean, [rule], locale="es") == []
