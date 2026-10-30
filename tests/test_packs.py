from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from lexaudit.cli.main import main
from lexaudit.packs import install_pack, list_lab_packs, list_packs, verify_pack


def test_list_and_install_pack(tmp_path: Path, monkeypatch: object) -> None:
    rows = list_packs()
    assert any(r["id"] == "core-calques-v1" for r in rows)
    assert any(r["id"] == "saas-ui-v0" for r in rows)
    assert all(r.get("status") != "lab" for r in rows)
    assert any(r.get("status") == "release-candidate" for r in rows if r["id"] == "saas-ui-v0")
    rules = install_pack("core-calques-v1", dest=tmp_path, force=True)
    assert rules.is_dir()
    assert (rules / "en.yaml").is_file()
    assert verify_pack("core-calques-v1", dest=tmp_path) == rules
    # Promoted packs install without --lab
    saas = install_pack("saas-ui-v0", dest=tmp_path, force=True)
    assert (saas / "en.yaml").is_file()


def test_list_and_install_lab_pack(tmp_path: Path) -> None:
    lab = list_lab_packs()
    assert any(r["id"] == "saas-ui-v0" for r in lab)
    assert all(r.get("status") == "lab" for r in lab)
    combined = list_packs(include_lab=True)
    assert any(r["id"] == "saas-ui-v0" for r in combined)
    rules = install_pack("saas-ui-v0", dest=tmp_path, force=True, lab=True)
    assert rules.is_dir()
    assert (rules / "en.yaml").is_file()
    assert verify_pack("saas-ui-v0", dest=tmp_path) == rules


def test_install_unknown_lab_pack_raises(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(FileNotFoundError, match="unknown pack"):
        install_pack("no-such-lab-pack", dest=tmp_path, lab=True)


def test_pack_cli(tmp_path: Path) -> None:
    runner = CliRunner()
    listed = runner.invoke(main, ["pack", "list"])
    assert listed.exit_code == 0
    assert "core-calques-v1" in listed.output
    assert "saas-ui-v0" in listed.output
    assert "release-candidate" in listed.output

    lab_listed = runner.invoke(main, ["pack", "list", "--lab"])
    assert lab_listed.exit_code == 0
    assert "saas-ui-v0" in lab_listed.output
    assert "status=lab" in lab_listed.output

    installed = runner.invoke(
        main, ["pack", "install", "core-calques-v1", "--dest", str(tmp_path), "--force"]
    )
    assert installed.exit_code == 0, installed.output

    lab_installed = runner.invoke(
        main,
        [
            "pack",
            "install",
            "saas-ui-v0",
            "--lab",
            "--dest",
            str(tmp_path),
            "--force",
        ],
    )
    assert lab_installed.exit_code == 0, lab_installed.output
    verified = runner.invoke(main, ["pack", "verify", "saas-ui-v0", "--dest", str(tmp_path)])
    assert verified.exit_code == 0, verified.output
