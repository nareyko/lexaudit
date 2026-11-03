"""Smoke: competitor benchmark script runs in --lexaudit-only without failing CI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "benchmark_competitors.py"


def test_competitor_benchmark_lexaudit_only_smoke(tmp_path: Path) -> None:
    out_json = tmp_path / "competitor-benchmark.json"
    out_md = tmp_path / "competitor-benchmark.md"
    work = tmp_path / "work"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--lexaudit-only",
            "--locales",
            "en",
            "--no-real-bench",
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
            "--work-dir",
            str(work),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert out_json.is_file()
    assert out_md.is_file()

    report = json.loads(out_json.read_text(encoding="utf-8"))
    assert report["lexaudit_only"] is True
    assert set(report["tools"]) >= {
        "lexaudit_strict",
        "lexaudit_full",
        "hunspell",
        "cspell",
        "vale",
        "languagetool",
    }

    for key in ("lexaudit_strict", "lexaudit_full"):
        lex = report["tools"][key]
        assert lex["available"] is True
        assert lex["word_precision"] is not None
        assert lex["page_p_at_3"] is not None
        assert lex["seconds"] is not None and lex["seconds"] >= 0

    for name in ("hunspell", "cspell", "vale", "languagetool"):
        row = report["tools"][name]
        assert row["available"] is False
        assert "lexaudit-only" in (row.get("skipped_reason") or "")
        assert row["word_precision"] is None
        assert row["page_p_at_3"] is None

    md = out_md.read_text(encoding="utf-8")
    assert "Competitor benchmark" in md
    assert "lexaudit (strict" in md
    assert "lexaudit (full" in md
    assert "N/A" in md or "skipped" in md
