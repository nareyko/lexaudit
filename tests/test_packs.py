from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from lexaudit.cli.main import main
from lexaudit.packs import install_pack, list_packs, verify_pack


def test_list_and_install_pack(tmp_path: Path, monkeypatch: object) -> None:
    rows = list_packs()
    assert any(r["id"] == "core-calques-v1" for r in rows)
    rules = install_pack("core-calques-v1", dest=tmp_path, force=True)
    assert rules.is_dir()
    assert (rules / "en.yaml").is_file()
    assert verify_pack("core-calques-v1", dest=tmp_path) == rules


def test_pack_cli(tmp_path: Path) -> None:
    runner = CliRunner()
    listed = runner.invoke(main, ["pack", "list"])
    assert listed.exit_code == 0
    assert "core-calques-v1" in listed.output
    installed = runner.invoke(
        main, ["pack", "install", "core-calques-v1", "--dest", str(tmp_path), "--force"]
    )
    assert installed.exit_code == 0, installed.output
