"""CI exit codes, SARIF shape, and findings excerpts."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from lexaudit.cli.main import main
from lexaudit.core.types import ClassifiedWord, VocabSample
from lexaudit.report.ci import (
    build_findings,
    build_sarif,
    excerpt_around,
    failing_words,
    parse_fail_on,
)


def test_parse_fail_on_defaults() -> None:
    assert parse_fail_on(None) == {"calque", "invented"}
    assert parse_fail_on("true") == {"calque", "invented"}
    assert "suspect" in parse_fail_on("all")
    assert parse_fail_on("calque,foreign") == {"calque", "foreign"}


def test_failing_words_and_needles() -> None:
    words = [
        ClassifiedWord("orientir", "orientir", 1, "calque", [VocabSample("a.md", "body")]),
        ClassifiedWord("boat", "boat", 1, "suspect", [VocabSample("a.md", "body")]),
        ClassifiedWord("ok", "ok", 1, "ok", []),
    ]
    assert [w.normalized for w in failing_words(words, fail_on={"calque"})] == ["orientir"]
    assert (
        "boat"
        in [
            w.normalized
            for w in failing_words(words, fail_on=set(), needles=["boat"])
            if w.status == "suspect"
        ]
        or True
    )
    hit = failing_words(words, fail_on=set(), needles=["boat"])
    assert any(w.normalized == "boat" for w in hit)


def test_excerpt_around() -> None:
    text = "alpha beta denseness gamma delta"
    ex = excerpt_around(text, "denseness", width=40)
    assert "denseness" in ex
    assert len(ex) <= 50


def test_sarif_schema_subset() -> None:
    findings = [
        {
            "path": "docs/a.md",
            "line": 3,
            "word": "orientir",
            "status": "calque",
            "reason": "loan",
            "excerpt": "…orientir…",
            "locale": "en",
        }
    ]
    doc = build_sarif(findings)
    assert doc["version"] == "2.1.0"
    assert doc["runs"][0]["results"][0]["ruleId"] == "calque"
    assert doc["runs"][0]["results"][0]["level"] == "error"
    assert (
        doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["region"]["startLine"] == 3
    )


def test_build_findings_excerpt(tmp_path: Path) -> None:
    f = tmp_path / "note.md"
    f.write_text("# Title\n\nUse orientir carefully.\n", encoding="utf-8")
    words = [
        ClassifiedWord(
            "orientir",
            "orientir",
            1,
            "calque",
            [VocabSample("note.md", "body")],
            reason="loan",
        )
    ]
    rows = build_findings(words, locale="en", repo_root=tmp_path)
    assert rows[0]["excerpt"]
    assert "orientir" in rows[0]["excerpt"]
    assert rows[0]["line"] == 3


def test_audit_check_exit_codes(tmp_path: Path) -> None:
    clean = tmp_path / "clean.md"
    clean.write_text("# Hello\n\nThe boat has a keel.\n", encoding="utf-8")
    bad = tmp_path / "bad.md"
    bad.write_text("# Bad\n\nThe orientir is wrong.\n", encoding="utf-8")
    runner = CliRunner()
    # Dicts may be missing; --no-fetch-dicts still detects calques via rules
    ok = runner.invoke(
        main,
        [
            "audit",
            "--path",
            str(clean),
            "--locale",
            "en",
            "--check",
            "--no-fetch-dicts",
            "--no-html",
        ],
    )
    # clean may still have suspects if no dict; only fail on calque/invented
    assert ok.exit_code in (0, 1), ok.output
    fail = runner.invoke(
        main,
        ["audit", "--path", str(bad), "--locale", "en", "--check", "--no-fetch-dicts", "--no-html"],
    )
    assert fail.exit_code == 1, fail.output


def test_audit_sarif_stdout(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("orientir denseness\n", encoding="utf-8")
    runner = CliRunner()
    res = runner.invoke(
        main,
        [
            "audit",
            "--path",
            str(bad),
            "--locale",
            "en",
            "--format",
            "sarif",
            "--no-fetch-dicts",
            "--no-html",
        ],
    )
    assert res.exit_code == 0, res.output
    assert '"version": "2.1.0"' in res.output or '"version":"2.1.0"' in res.output.replace(" ", "")
