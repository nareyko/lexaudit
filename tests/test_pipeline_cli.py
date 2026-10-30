"""Pipeline and CLI integration on temp monorepo-like tree."""

from __future__ import annotations

import json
import os
from pathlib import Path

from click.testing import CliRunner

from lexaudit.cli.main import main
from lexaudit.config import load_config
from lexaudit.core.pipeline import run_locale_audit


def _mini_repo(tmp_path: Path) -> Path:
    academy = tmp_path / "infra" / "corpus-ci" / "pending-academy-articles" / "sys"
    academy.mkdir(parents=True)
    doc = {
        "translations": {
            "en": {
                "title": "Boat survey overview",
                "excerpt": "A solid boat hull.",
                "metaDescription": "Survey guide",
                "bodyMarkdown": "The boat has a sound hull and deck.",
            }
        }
    }
    (academy / "demo.json").write_text(json.dumps(doc), encoding="utf-8")
    proper = tmp_path / "proper.yaml"
    proper.write_text("version: 1\nbrands_yards:\n  - AcmeCorp\n", encoding="utf-8")
    acronyms = tmp_path / "acronyms.yaml"
    acronyms.write_text("version: 1\nitems:\n  - EPIRB\n", encoding="utf-8")
    allow = tmp_path / "allow.yaml"
    allow.write_text(
        "version: 2\nsection_markers:\n  - Overview\nlocale_loans: []\n",
        encoding="utf-8",
    )
    hunspell_env = os.environ.get("LEXAUDIT_HUNSPELL_ROOT")
    hunspell_local = hunspell_env or str(
        Path(__file__).resolve().parents[3] / "frontend" / "tmp" / "hunspell-local"
    )
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        "\n".join(
            [
                f"repo_root: {tmp_path}",
                f"output_dir: {tmp_path / 'out'}",
                "locales: [en]",
                "sources: [academy]",
                f"proper_names_path: {proper}",
                f"acronyms_path: {acronyms}",
                f"allowlist_path: {allow}",
                "enable_morph: false",
                "enable_compound: false",
                "enable_foreign: false",
                "enable_calque: false",
                "hunspell:",
                f"  local_root: {hunspell_local}",
            ]
        ),
        encoding="utf-8",
    )
    return cfg


def test_run_locale_audit(tmp_path: Path) -> None:
    cfg_path = _mini_repo(tmp_path)
    cfg = load_config(cfg_path)
    words, _pages, paths = run_locale_audit(cfg, "en", freeze_generated_at="1970-01-01T00:00:00Z")
    assert words
    assert paths["report"].is_file()
    assert any(w.normalized == "boat" for w in words)


def test_run_locale_audit_compound_de_first_pass_seed(tmp_path: Path) -> None:
    """Compound splits in classify when both parts are in proper/maritime seed (I5-1)."""
    from unittest.mock import patch

    academy = tmp_path / "infra" / "corpus-ci" / "pending-academy-articles" / "sys"
    academy.mkdir(parents=True)
    doc = {
        "translations": {
            "de": {
                "title": "Welt",
                "excerpt": "Weltumsegelung",
                "metaDescription": "Welt",
                "bodyMarkdown": "Weltumsegelung und Umsegelung.",
            }
        }
    }
    (academy / "demo.json").write_text(json.dumps(doc), encoding="utf-8")
    proper = tmp_path / "proper.yaml"
    proper.write_text(
        "version: 1\nmaritime_domain_terms:\n  - Welt\n  - Umsegelung\n",
        encoding="utf-8",
    )
    acronyms = tmp_path / "acronyms.yaml"
    acronyms.write_text("version: 1\nitems: []\n", encoding="utf-8")
    allow = tmp_path / "allow.yaml"
    allow.write_text("version: 2\nsection_markers: []\nlocale_loans: []\n", encoding="utf-8")
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(
        "\n".join(
            [
                f"repo_root: {tmp_path}",
                f"output_dir: {tmp_path / 'out'}",
                "locales: [de]",
                "sources: [academy]",
                f"proper_names_path: {proper}",
                f"acronyms_path: {acronyms}",
                f"allowlist_path: {allow}",
                "enable_morph: false",
                "enable_compound: true",
                "enable_foreign: false",
                "enable_calque: false",
            ]
        ),
        encoding="utf-8",
    )
    cfg = load_config(cfg_path)

    class RejectGlued:
        dict_id = "mock-de"

        def list_misspelled(self, words: list[str]) -> set[str]:
            return {w for w in words if w.casefold() == "weltumsegelung"}

    with patch("lexaudit.core.pipeline.resolve_checker", return_value=RejectGlued()):
        words, _pages, _paths = run_locale_audit(
            cfg, "de", freeze_generated_at="1970-01-01T00:00:00Z"
        )
    by = {w.normalized: w for w in words}
    assert by["welt"].status == "proper"
    assert by["umsegelung"].status == "proper"
    assert by["weltumsegelung"].status == "ok"
    assert "compound" in by["weltumsegelung"].detectors


def test_run_locale_audit_compound_de(tmp_path: Path) -> None:
    from unittest.mock import patch

    academy = tmp_path / "infra" / "corpus-ci" / "pending-academy-articles" / "sys"
    academy.mkdir(parents=True)
    doc = {
        "translations": {
            "de": {
                "title": "Rumpf",
                "excerpt": "Rumpf Deck",
                "metaDescription": "Rumpf",
                "bodyMarkdown": "Rumpf Deck und Rumpfdeck. Rumpf. Deck.",
            }
        }
    }
    (academy / "demo.json").write_text(json.dumps(doc), encoding="utf-8")
    proper = tmp_path / "proper.yaml"
    proper.write_text("version: 1\nbrands_yards: []\n", encoding="utf-8")
    acronyms = tmp_path / "acronyms.yaml"
    acronyms.write_text("version: 1\nitems: []\n", encoding="utf-8")
    allow = tmp_path / "allow.yaml"
    allow.write_text("version: 2\nsection_markers: []\nlocale_loans: []\n", encoding="utf-8")
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(
        "\n".join(
            [
                f"repo_root: {tmp_path}",
                f"output_dir: {tmp_path / 'out'}",
                "locales: [de]",
                "sources: [academy]",
                f"proper_names_path: {proper}",
                f"acronyms_path: {acronyms}",
                f"allowlist_path: {allow}",
                "enable_morph: false",
                "enable_compound: true",
                "enable_foreign: false",
                "enable_calque: false",
            ]
        ),
        encoding="utf-8",
    )
    cfg = load_config(cfg_path)

    class Selective:
        dict_id = "mock-de"

        def list_misspelled(self, words: list[str]) -> set[str]:
            # Accept rumpf/deck forms; reject the glued compound so compound detector runs.
            bad = set()
            for w in words:
                if w.casefold() == "rumpfdeck":
                    bad.add(w)
            return bad

    with patch("lexaudit.core.pipeline.resolve_checker", return_value=Selective()):
        words, _pages, paths = run_locale_audit(
            cfg, "de", freeze_generated_at="1970-01-01T00:00:00Z"
        )
    assert paths["report"].is_file()
    by = {w.normalized: w for w in words}
    assert by["rumpf"].status == "ok"
    assert by["deck"].status == "ok"
    assert by["rumpfdeck"].status == "ok"
    assert "compound" in by["rumpfdeck"].detectors
    assert by["rumpfdeck"].reason == "compound-split"
    assert words == sorted(words, key=lambda w: (-w.count, w.normalized))


def test_cli_audit_rank_diff(tmp_path: Path) -> None:
    cfg_path = _mini_repo(tmp_path)
    runner = CliRunner()
    r1 = runner.invoke(
        main,
        [
            "audit",
            "--config",
            str(cfg_path),
            "--locale",
            "en",
            "--freeze-at",
            "1970-01-01T00:00:00Z",
        ],
    )
    assert r1.exit_code == 0, r1.output
    r2 = runner.invoke(main, ["rank", "--config", str(cfg_path), "--locale", "en"])
    assert r2.exit_code == 0, r2.output
    out_dir = tmp_path / "out" / "en"
    report = out_dir / "report.json"
    diff_out = tmp_path / "diff.json"
    r3 = runner.invoke(
        main,
        ["diff", "--baseline", str(report), "--current", str(report), "--out", str(diff_out)],
    )
    assert r3.exit_code == 0, r3.output
    data = json.loads(diff_out.read_text(encoding="utf-8"))
    assert data["counts"]["new"] == 0
