"""Contract: every calque rule with examples must hit all positives and miss all negatives."""

from __future__ import annotations

from pathlib import Path

import pytest

from lexaudit.detectors.calque import load_calque_rules, rule_matches_text

RULES_DIR = Path(__file__).resolve().parents[1] / "rules" / "calques"
LOCALES = ("en", "de", "es", "pl", "ru", "sv", "uk")


def _rules_with_examples() -> list[tuple[str, object]]:
    rows: list[tuple[str, object]] = []
    for locale in LOCALES:
        path = RULES_DIR / f"{locale}.yaml"
        for rule in load_calque_rules(path):
            if rule.positive_examples or rule.negative_examples:
                rows.append((f"{locale}:{rule.pattern}:{rule.reason}", rule))
    return rows


@pytest.mark.parametrize(("label", "rule"), _rules_with_examples())
def test_calque_examples_contract(label: str, rule: object) -> None:
    assert rule.positive_examples or rule.negative_examples, label  # type: ignore[attr-defined]
    for i, example in enumerate(rule.positive_examples):  # type: ignore[attr-defined]
        assert rule_matches_text(rule, example), (  # type: ignore[arg-type]
            f"{label} positive[{i}] must fire:\n{example!r}"
        )
    for i, example in enumerate(rule.negative_examples):  # type: ignore[attr-defined]
        assert not rule_matches_text(rule, example), (  # type: ignore[arg-type]
            f"{label} negative[{i}] must not fire:\n{example!r}"
        )


def _pattern_covers(rule_pattern: str, required: str) -> bool:
    rp = rule_pattern.casefold()
    rq = required.casefold()
    if rq == rp or rq in rp or (rp.rstrip("*") and rq.startswith(rp.rstrip("*"))):
        return True
    return rp.rstrip("*") in rq


def test_contract_has_required_v3_cases() -> None:
    """Smoke: required V3-4 needles exist with examples."""
    required = {
        "uk": ["приймати участь", "в залежності від"],
        "ru": ["делает смысл"],
        "es": ["actualmente", "librería"],
        "de": ["realisieren"],
        "pl": ["ewentualnie", "aktualnie"],
        "en": ["orientir"],
        "sv": ["eventuellt"],
    }
    for locale, patterns in required.items():
        rules = load_calque_rules(RULES_DIR / f"{locale}.yaml")
        for pat in patterns:
            matches = [r for r in rules if _pattern_covers(r.pattern, pat)]
            assert matches, f"missing required pattern {locale}:{pat}"
            hit = next((r for r in matches if r.positive_examples and r.negative_examples), None)
            assert hit is not None, f"{locale}:{pat} needs positive_examples and negative_examples"
