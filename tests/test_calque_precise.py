"""Precise calque-detector behaviour: pins every branch so mutants cannot hide."""

from __future__ import annotations

from pathlib import Path

import pytest

from lexaudit.core.types import ClassifiedWord
from lexaudit.detectors.calque import (
    CalqueRule,
    compile_prefix_re,
    default_calque_rules_dir,
    find_matching_rule,
    load_calque_rules,
    make_calque_detector,
    needle_matches_norm,
)


def _word(norm: str, status: str = "suspect", reason: str = "") -> ClassifiedWord:
    return ClassifiedWord(
        normalized=norm,
        surface=norm,
        count=1,
        status=status,  # type: ignore[arg-type]
        samples=[],
        reason=reason,
    )


def _rule(pattern: str, **kw: object) -> CalqueRule:
    base: dict[str, object] = {
        "pattern": pattern,
        "locale": "en",
        "reason": "r",
        "hint": "h",
        "severity": "likely",
        "source": "t",
    }
    base.update(kw)
    return CalqueRule(**base)  # type: ignore[arg-type]


def _write(tmp_path: Path, text: str) -> Path:
    f = tmp_path / "x.yaml"
    f.write_text(text, encoding="utf-8")
    return f


def test_loader_defaults_and_modes(tmp_path: Path) -> None:
    f = _write(
        tmp_path,
        "rules:\n"
        "  - {pattern: alpha, locale: en}\n"
        "  - {pattern: 'be*', locale: en}\n"
        "  - {pattern: gam, locale: en, match: prefix, severity: weak, reason: why,"
        " hint: use x, source: src1, override_ok: true}\n",
    )
    rules = {r.pattern: r for r in load_calque_rules(f)}
    a = rules["alpha"]
    assert (a.match, a.reason, a.hint, a.severity, a.source, a.override_ok) == (
        "exact",
        "calque",
        "",
        "likely",
        "x.yaml",
        False,
    )
    assert rules["be*"].match == "glob"
    g = rules["gam*"]  # prefix gets a trailing *, becomes glob
    assert g.match == "glob"
    assert (g.reason, g.hint, g.severity, g.source, g.override_ok) == (
        "why",
        "use x",
        "weak",
        "src1",
        True,
    )


def test_loader_skips_garbage_and_sorts(tmp_path: Path) -> None:
    assert load_calque_rules(tmp_path / "missing.yaml") == []
    f = _write(tmp_path, "- not-a-dict\n- {pattern: b, locale: en}\n- {pattern: a, locale: de}\n")
    ordered = [(r.locale, r.pattern) for r in load_calque_rules(f)]
    assert ordered == sorted(ordered)
    assert load_calque_rules(_write(tmp_path, "rules: 5\n")) == []
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "a.yaml").write_text("- {pattern: p1, locale: en}\n", encoding="utf-8")
    (tmp_path / "d" / "b.yml").write_text("- {pattern: p2, locale: en}\n", encoding="utf-8")
    assert [r.pattern for r in load_calque_rules(tmp_path / "d")] == ["p1", "p2"]


def test_default_rules_dir_exists() -> None:
    d = default_calque_rules_dir()
    assert d is not None and (d / "en.yaml").is_file()


def test_find_matching_rule_exact_glob_and_case() -> None:
    rules = [_rule("Alpha"), _rule("be*", match="glob"), _rule("lit", match="glob")]
    assert find_matching_rule(_word("alpha"), rules, "en") is rules[0]
    assert find_matching_rule(_word("alphax"), rules, "en") is None
    assert find_matching_rule(_word("beta"), rules, "en") is rules[1]
    assert find_matching_rule(_word("lit"), rules, "en") is rules[2]
    assert find_matching_rule(_word("lite"), rules, "en") is None
    assert find_matching_rule(_word("zzz"), [], "en") is None


@pytest.mark.parametrize(
    ("status", "override", "reason", "flips"),
    [
        ("suspect", False, "", True),
        ("foreign", False, "", True),
        ("unsure", False, "", True),
        ("morph-miss", False, "", True),
        ("ok", False, "hunspell", False),
        ("ok", True, "hunspell", True),
        ("ok", False, "pymorphy3", True),
        ("proper", False, "", False),
        ("calque", False, "", False),
    ],
)
def test_detector_status_matrix(status: str, override: bool, reason: str, flips: bool) -> None:
    detect = make_calque_detector("en", [_rule("zap", override_ok=override, severity="confirmed")])
    out = detect(_word("zap", status, reason))
    if not flips:
        assert out is None
        return
    assert out is not None
    assert out.status == "calque"
    assert out.reason == "r"
    assert out.tier == "confirmed"
    assert out.detectors == ["calque"]


def test_detector_merges_detectors_and_ignores_other_locale_and_bad_severity() -> None:
    detect = make_calque_detector(
        "en", [_rule("zap", severity="odd"), _rule("zap", locale="de", reason="de")]
    )
    w = _word("zap")
    w.detectors = ["hunspell", "calque"]
    w.tier = "weak"
    out = detect(w)
    assert out is not None
    assert out.detectors == ["calque", "hunspell"]
    assert out.reason == "r"  # the de rule is ignored
    assert out.tier == "weak"  # unknown severity leaves the tier untouched
    assert detect(_word("nomatch")) is None


def test_detector_prefers_exact_over_glob() -> None:
    detect = make_calque_detector(
        "en", [_rule("ze*", reason="glob", match="glob"), _rule("zebra", reason="exact")]
    )
    out = detect(_word("zebra"))
    assert out is not None and out.reason == "exact"


@pytest.mark.parametrize(
    ("norm", "needle", "expected"),
    [
        ("orientir", "orientir", True),
        ("orientirs", "orientir", True),
        ("xorientir", "orientir", False),
        ("blue-orientir", "orientir", True),
        ("blue-orientirx", "orientir", False),
        ("orientir", "  ORIENTIR ", True),
        ("orientirs", "orient*", True),
        ("other", "orient*", False),
        ("anything", "", False),
        ("anything", "   ", False),
        ("ORIENTIR", "orientir", True),
    ],
)
def test_needle_matches(norm: str, needle: str, expected: bool) -> None:
    assert needle_matches_norm(norm, needle, "en") is expected


def test_compile_prefix_re() -> None:
    rx = compile_prefix_re("a.b")
    assert rx.match("A.Bcd")
    assert not rx.match("axb")
    assert not rx.match("xa.b")
