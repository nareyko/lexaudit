"""Smoke tests for empty package."""

from __future__ import annotations

from click.testing import CliRunner

from lexaudit import __version__
from lexaudit.cli.main import main


def test_ping() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["ping"])
    assert result.exit_code == 0
    assert __version__ in result.output
