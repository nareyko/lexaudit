"""Soft CI fixture: audit + diff vs baseline (I8-3)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "ci-soft-fixture"
FH_HUNSPELL = ROOT / "../../frontend/tmp/hunspell-local/usr/bin/hunspell"


def test_ci_soft_fixture_diff_zero_drift() -> None:
    cfg = FIX / "lexaudit.config.yaml"
    if not FH_HUNSPELL.is_file():
        cfg = FIX / "lexaudit.config.ci.yaml"
    baseline = FIX / "baseline" / "en" / "report.json"
    assert baseline.is_file(), "committed baseline missing"
    subprocess.run(
        [
            "uv",
            "run",
            "lexaudit",
            "audit",
            "--config",
            str(cfg),
            "--locale",
            "en",
            "--freeze-at",
            "1970-01-01T00:00:00Z",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    current = FIX / "out" / "en" / "report.json"
    assert current.is_file()
    diff_out = FIX / "out" / "ci-soft-diff.json"
    subprocess.run(
        [
            "uv",
            "run",
            "lexaudit",
            "diff",
            "--baseline",
            str(baseline),
            "--current",
            str(current),
            "--out",
            str(diff_out),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(diff_out.read_text(encoding="utf-8"))
    assert data["counts"]["new"] == 0
    assert data["counts"]["gone"] == 0
