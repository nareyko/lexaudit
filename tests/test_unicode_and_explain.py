"""Unicode NFD->NFC normalization, direct --path audit, and lexaudit explain CLI tests."""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

from click.testing import CliRunner

from lexaudit.cli.main import main
from lexaudit.core.tokenize import casefold, tokenize, tokenize_with_surface


def test_unicode_nfd_normalized_to_nfc_before_tokenize() -> None:
    # Decomposed Russian 'морской' (и + combining breve) and German 'Törn' (o + combining diaeresis)
    ru_nfd = unicodedata.normalize("NFD", "морской")
    de_nfd = unicodedata.normalize("NFD", "Törn")
    assert len(ru_nfd) > len("морской")
    assert len(de_nfd) > len("Törn")

    ru_tokens = tokenize(ru_nfd, locale="ru")
    de_tokens = tokenize(de_nfd, locale="de")
    assert ru_tokens == ["морской"]
    assert de_tokens == ["törn"]
    assert unicodedata.is_normalized("NFC", ru_tokens[0])
    assert unicodedata.is_normalized("NFC", de_tokens[0])

    surf = tokenize_with_surface(de_nfd, locale="de")
    assert surf == [{"normalized": "törn", "surface": "Törn"}]
    assert casefold(de_nfd, "de") == "törn"


def test_cli_explain_plain_and_json() -> None:
    runner = CliRunner()
    res = runner.invoke(main, ["explain", "orientir", "--locale", "en"])
    assert res.exit_code == 0
    assert "status: calque" in res.output
    assert "editorial hint:" in res.output

    res_json = runner.invoke(main, ["explain", "предпокупочный", "--locale", "ru", "--json"])
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert data["status"] == "calque"
    assert data["locale"] == "ru"
    assert "осмотр перед покупкой" in data["hint"]


def test_cli_audit_single_markdown_file_via_path_flag(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    article = tmp_path / "draft.md"
    article.write_text("# Draft Guide\n\nCheck this orientir figure.\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    res = runner.invoke(main, ["audit", "--path", str(article), "--locale", "en"])
    assert res.exit_code == 0
    report = json.loads((tmp_path / "tmp" / "lexaudit" / "en" / "report.json").read_text("utf-8"))
    words = {w["norm"]: w["status"] for w in report["locales"][0]["words"]}
    assert words["orientir"] == "calque"
