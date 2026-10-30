"""Dictionary download (stubbed network) and the pure-Python Hunspell fallback."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from lexaudit.cli.main import main
from lexaudit.detectors import dictfetch
from lexaudit.detectors.hunspell import (
    HunspellChecker,
    HunspellConfig,
    ProperOnlyChecker,
    SpyllsChecker,
    resolve_checker,
)

AFF = b"SET UTF-8\n"
DIC = b"3\nboat\nsail\nkeel\n"


def _fake_fetch(url: str) -> bytes:
    if url.endswith(".aff"):
        return AFF
    if url.endswith(".dic"):
        return DIC
    return b"license text"


def _no_binary_cfg(dict_dir: Path) -> HunspellConfig:
    return HunspellConfig(
        binary="/definitely/not/here/hunspell", dict_dirs=(str(dict_dir),), local_root="/nope"
    )


def test_cache_dir_env_and_xdg(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LEXAUDIT_DICT_DIR", str(tmp_path / "a"))
    assert dictfetch.cache_dir() == tmp_path / "a"
    monkeypatch.delenv("LEXAUDIT_DICT_DIR")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "x"))
    assert dictfetch.cache_dir() == tmp_path / "x" / "lexaudit" / "dictionaries"


def test_fetch_dictionary_writes_files(tmp_path: Path) -> None:
    stem = dictfetch.fetch_dictionary("en", tmp_path, fetch=_fake_fetch)
    assert stem == tmp_path / "en_GB"
    assert (tmp_path / "en_GB.aff").read_bytes() == AFF
    assert (tmp_path / "en_GB.dic").read_bytes() == DIC
    assert (tmp_path / "en_GB.license.txt").read_bytes() == b"license text"


def test_fetch_dictionary_survives_missing_license(tmp_path: Path) -> None:
    def fetch(url: str) -> bytes:
        if url.endswith("license"):
            raise OSError("404")
        return _fake_fetch(url)

    dictfetch.fetch_dictionary("de", tmp_path, fetch=fetch)
    assert (tmp_path / "de_DE.dic").is_file()
    assert not (tmp_path / "de_DE.license.txt").exists()


def test_fetch_dictionary_unknown_locale(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no downloadable"):
        dictfetch.fetch_dictionary("xx", tmp_path, fetch=_fake_fetch)


def test_spylls_fallback_checks_words(tmp_path: Path) -> None:
    dictfetch.fetch_dictionary("en", tmp_path, fetch=_fake_fetch)
    checker = resolve_checker("en", _no_binary_cfg(tmp_path))
    assert isinstance(checker, SpyllsChecker)
    assert checker.list_misspelled(["boat", "zzqx"]) == {"zzqx"}
    assert checker.list_misspelled([]) == set()


def test_resolve_checker_without_dictionary(tmp_path: Path) -> None:
    assert isinstance(resolve_checker("zh", _no_binary_cfg(tmp_path / "empty")), ProperOnlyChecker)


def test_binary_preferred_when_available(tmp_path: Path) -> None:
    dictfetch.fetch_dictionary("en", tmp_path, fetch=_fake_fetch)
    script = tmp_path / "fake-hunspell"
    script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    script.chmod(0o755)
    cfg = HunspellConfig(binary=str(script), dict_dirs=(str(tmp_path),), local_root="/nope")
    assert isinstance(resolve_checker("en", cfg), HunspellChecker)


def test_fetch_dicts_cli(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LEXAUDIT_DICT_DIR", str(tmp_path))
    runner = CliRunner()
    orig = dictfetch.fetch_dictionary

    def stub(loc: str, dest: Path, fetch: dictfetch.Fetcher = _fake_fetch) -> Path:
        return orig(loc, dest, fetch=_fake_fetch)

    monkeypatch.setattr(dictfetch, "fetch_dictionary", stub)
    res = runner.invoke(main, ["fetch-dicts", "--locale", "en"])
    assert res.exit_code == 0, res.output
    assert "en: downloaded" in res.output
    again = runner.invoke(main, ["fetch-dicts", "--locale", "en"])
    assert "already installed" in again.output
    forced = runner.invoke(main, ["fetch-dicts", "--locale", "en", "--force"])
    assert "downloaded" in forced.output
    bad = runner.invoke(main, ["fetch-dicts", "--locale", "xx"])
    assert bad.exit_code != 0 and "unknown locale" in bad.output


def test_fetch_dicts_cli_reports_network_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("LEXAUDIT_DICT_DIR", str(tmp_path))

    def boom(loc: str, dest: Path, fetch: dictfetch.Fetcher = _fake_fetch) -> Path:
        raise OSError("offline")

    monkeypatch.setattr(dictfetch, "fetch_dictionary", boom)
    res = CliRunner().invoke(main, ["fetch-dicts", "--locale", "en"])
    assert res.exit_code != 0 and "download failed" in res.output
