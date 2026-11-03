"""V5-3: .lexaudit-baseline.json suppression for --check."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from lexaudit.cli.main import main
from lexaudit.report.baseline import (
    apply_baseline_to_findings,
    load_baseline,
    write_baseline,
)


def test_write_and_load_baseline_roundtrip(tmp_path: Path) -> None:
    findings = [
        {
            "locale": "en",
            "path": "a.md",
            "normalized": "orientir",
            "status": "calque",
            "word": "orientir",
        },
        {
            "locale": "EN",
            "path": "a.md",
            "normalized": "Orientir",
            "status": "Calque",
            "word": "Orientir",
        },
    ]
    path = tmp_path / ".lexaudit-baseline.json"
    write_baseline(path, findings)
    keys = load_baseline(path)
    assert ("en", "a.md", "orientir", "calque") in keys
    assert len(keys) == 1
    marked = apply_baseline_to_findings(findings, keys)
    assert marked[0]["suppressed"] is True
    assert marked[1]["suppressed"] is True


def test_check_exit_zero_with_baseline_and_one_on_new(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("# Bad\n\nThe orientir is wrong.\n", encoding="utf-8")
    baseline = tmp_path / ".lexaudit-baseline.json"
    runner = CliRunner()

    # First run: write baseline covering current calques
    write = runner.invoke(
        main,
        [
            "audit",
            "--path",
            str(bad),
            "--locale",
            "en",
            "--no-fetch-dicts",
            "--no-html",
            "--write-baseline",
            str(baseline),
        ],
    )
    assert write.exit_code == 0, write.output
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["findings"], data

    covered = runner.invoke(
        main,
        [
            "audit",
            "--path",
            str(bad),
            "--locale",
            "en",
            "--check",
            "--no-fetch-dicts",
            "--no-html",
            "--baseline",
            str(baseline),
        ],
    )
    assert covered.exit_code == 0, covered.output

    # New bad word not in baseline → exit 1
    worse = tmp_path / "worse.md"
    worse.write_text("# Worse\n\nThe orientir and denseness are wrong.\n", encoding="utf-8")
    # denseness is also a known calque; ensure baseline only covers orientir from first file path
    # Use a fresh path so denseness is a new (locale, path, normalized, status)
    fresh_baseline = tmp_path / "orientir-only.json"
    write_baseline(
        fresh_baseline,
        [
            {
                "locale": "en",
                "path": str(worse.name),
                "normalized": "orientir",
                "status": "calque",
            }
        ],
    )
    # Path in findings is relative as given to --path (absolute resolved often)
    # Re-run write-baseline on worse, then remove denseness entry.
    prep = runner.invoke(
        main,
        [
            "audit",
            "--path",
            str(worse),
            "--locale",
            "en",
            "--no-fetch-dicts",
            "--no-html",
            "--write-baseline",
            str(tmp_path / "full.json"),
        ],
    )
    assert prep.exit_code == 0, prep.output
    full = json.loads((tmp_path / "full.json").read_text(encoding="utf-8"))
    only_orientir = {
        "schema_version": "1",
        "findings": [e for e in full["findings"] if e["normalized"] == "orientir"],
    }
    assert only_orientir["findings"]
    partial = tmp_path / "partial.json"
    partial.write_text(json.dumps(only_orientir, indent=2) + "\n", encoding="utf-8")

    with_new = runner.invoke(
        main,
        [
            "audit",
            "--path",
            str(worse),
            "--locale",
            "en",
            "--check",
            "--no-fetch-dicts",
            "--no-html",
            "--baseline",
            str(partial),
        ],
    )
    assert with_new.exit_code == 1, with_new.output
