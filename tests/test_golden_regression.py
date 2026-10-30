"""End-to-end golden regression and read-only sandbox verification."""

from __future__ import annotations

import hashlib
from pathlib import Path

from click.testing import CliRunner

from lexaudit.cli.main import main
from lexaudit.config import load_config
from lexaudit.core.pipeline import run_locale_audit
from lexaudit.core.types import VocabOccurrence


class DeterministicMockChecker:
    dict_id = "mock-en"

    def list_misspelled(self, words: list[str]) -> set[str]:
        ok_words = {
            "project",
            "guide",
            "solid",
            "hull",
            "deck",
            "denseness",
            "water",
            "and",
            "on",
            "this",
            "has",
        }
        return {w for w in words if w.casefold() not in ok_words}


def _sha256_tree(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_golden_regression_and_readonly_sandbox(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    corpus_dir = tmp_path / "corpus"
    docs = corpus_dir / "docs"
    docs.mkdir(parents=True)
    (corpus_dir / "README.md").write_text(
        "# AcmeCorp Guide\n\nA solid hull and deck on water.\n",
        encoding="utf-8",
    )
    (docs / "calque-page.md").write_text(
        "# Overview\n\nThis orientir and denseness guide has xxyzzyq.\n",
        encoding="utf-8",
    )
    dicts = corpus_dir / "dicts"
    dicts.mkdir()
    (dicts / "proper.yaml").write_text("version: 1\nitems:\n  - AcmeCorp\n", encoding="utf-8")
    (dicts / "acronyms.yaml").write_text("version: 1\nitems:\n  - EPIRB\n", encoding="utf-8")
    (dicts / "allow.yaml").write_text(
        "version: 2\nsection_markers:\n  - Overview\nlocale_loans: []\n",
        encoding="utf-8",
    )
    cfg_path = tmp_path / "lexaudit.config.yaml"
    out_a = tmp_path / "out_a"
    out_b = tmp_path / "out_b"
    cfg_path.write_text(
        "\n".join(
            [
                f"repo_root: {corpus_dir}",
                f"output_dir: {out_a}",
                "locales: [en]",
                "sources: [files]",
                f"proper_names_path: {dicts / 'proper.yaml'}",
                f"acronyms_path: {dicts / 'acronyms.yaml'}",
                f"allowlist_path: {dicts / 'allow.yaml'}",
                "needles: [orientir, denseness]",
                "gold_slugs: [calque-page]",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "lexaudit.core.pipeline.resolve_checker",
        lambda locale, hun: DeterministicMockChecker(),
    )

    before_hashes = _sha256_tree(corpus_dir)

    cfg_a = load_config(cfg_path)
    words_a, pages_a, _ = run_locale_audit(cfg_a, "en", freeze_generated_at="1970-01-01T00:00:00Z")

    cfg_b = load_config(cfg_path)
    cfg_b.output_dir = out_b
    _words_b, _pages_b, _ = run_locale_audit(
        cfg_b, "en", freeze_generated_at="1970-01-01T00:00:00Z"
    )

    # 1. Source corpus and dictionaries are untouched (read-only guarantee)
    assert _sha256_tree(corpus_dir) == before_hashes

    # 2. Byte-for-byte determinism across runs
    report_files = (
        "report.json",
        "words.json",
        "suspect.csv",
        "pages.csv",
        "summary.md",
        "queue.md",
    )
    for fname in report_files:
        assert (out_a / "en" / fname).read_bytes() == (out_b / "en" / fname).read_bytes()

    # 3. Golden classification checks (including bundled calque rules + denseness override_ok)
    by_norm = {w.normalized: w for w in words_a}
    assert by_norm["acmecorp"].status == "proper"
    assert by_norm["overview"].status == "template"
    assert by_norm["hull"].status == "ok"
    assert by_norm["orientir"].status == "calque"
    assert by_norm["denseness"].status == "calque"
    assert by_norm["xxyzzyq"].status == "suspect"

    # 4. Ranking: calque-page is ranked first and README.md has 0 suspects
    assert len(pages_a) == 1
    assert pages_a[0].path == "docs/calque-page.md"
    assert pages_a[0].score > pages_a[0].unique_suspects

    # 5. CLI expand-needle and eval product work on the generated report
    runner = CliRunner()
    res_exp = runner.invoke(
        main,
        ["expand-needle", "--config", str(cfg_path), "--needle", "orientir", "--locale", "en"],
    )
    assert res_exp.exit_code == 0
    assert "docs/calque-page.md" in res_exp.output

    res_prod = runner.invoke(main, ["eval", "product", "--config", str(cfg_path)])
    assert res_prod.exit_code == 0
    assert "needle_recall=1.000" in res_prod.output
    assert _sha256_tree(corpus_dir) == before_hashes
    _ = VocabOccurrence
