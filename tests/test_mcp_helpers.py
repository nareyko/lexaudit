"""MCP helper coverage without requiring the optional ``mcp`` package."""

from __future__ import annotations

from pathlib import Path

from lexaudit.mcp_server import _run_audit


def test_run_audit_on_fixture_md(tmp_path: Path) -> None:
    sample = tmp_path / "page.md"
    sample.write_text(
        "# Notes\n\nUse working rule figures, not denseness or orientir leftovers.\n",
        encoding="utf-8",
    )
    out = _run_audit(str(sample), locale="en")
    assert "texts" in out and "findings" in out
    assert isinstance(out["texts"], list)
    assert isinstance(out["findings"], list)
    words = {str(row.get("word", "")).lower() for row in out["findings"] if isinstance(row, dict)}
    statuses = {str(row.get("status", "")) for row in out["findings"] if isinstance(row, dict)}
    assert out["texts"], "expected at least one ranked text"
    assert "denseness" in words or "orientir" in words or "calque" in statuses
