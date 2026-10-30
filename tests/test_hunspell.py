"""Hunspell wrapper - live smoke + mocked path/env logic."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lexaudit.detectors.hunspell import (
    BATCH_SIZE,
    LOCALE_DICTS,
    HunspellChecker,
    HunspellConfig,
    ProperOnlyChecker,
    _default_dict_dirs,
    find_dict,
    resolve_binary,
    resolve_checker,
)


def _default_hunspell_local() -> Path:
    env = os.environ.get("LEXAUDIT_HUNSPELL_ROOT")
    if env:
        return Path(env)
    # Optional monorepo vendor dir: repo_root/frontend/tmp/hunspell-local
    return Path(__file__).resolve().parents[3] / "frontend" / "tmp" / "hunspell-local"


LOCAL = _default_hunspell_local()


def test_locale_dicts_and_batch() -> None:
    assert LOCALE_DICTS == {
        "en": ["en_GB", "en_US"],
        "de": ["de_DE"],
        "pl": ["pl_PL"],
        "ru": ["ru_RU"],
        "es": ["es_ES", "es_MX"],
        "sv": ["sv_SE", "sv_FI"],
        "uk": ["uk_UA"],
        "ar": ["ar", "ar_SA", "ar_EG"],
        "he": ["he_IL"],
        "zh": [],
    }
    assert BATCH_SIZE == 2000


def test_proper_only_checker() -> None:
    c = ProperOnlyChecker()
    assert c.dict_id == "proper-only"
    assert c.list_misspelled([]) == set()
    assert c.list_misspelled(["a", "b"]) == {"a", "b"}


def test_default_dict_dirs_order(tmp_path: Path) -> None:
    local = tmp_path / "hunspell-local"
    hun = local / "usr" / "share" / "hunspell"
    hun.mkdir(parents=True)
    cfg = HunspellConfig(dict_dirs=(str(tmp_path / "extra"),), local_root=str(local))
    dirs = _default_dict_dirs(cfg)
    assert dirs[0] == tmp_path / "extra"
    assert hun in dirs
    assert Path("/usr/share/hunspell") in dirs


def test_find_dict_none_for_zh_and_missing(tmp_path: Path) -> None:
    cfg = HunspellConfig(dict_dirs=(str(tmp_path),), local_root=None)
    assert find_dict("zh", cfg) is None
    with patch("lexaudit.detectors.hunspell._default_dict_dirs", return_value=[tmp_path]):
        assert find_dict("en", cfg) is None


def test_find_dict_picks_first_existing(tmp_path: Path) -> None:
    d = tmp_path / "dicts"
    d.mkdir()
    (d / "en_US.aff").write_text("SET UTF-8\n", encoding="utf-8")
    (d / "en_US.dic").write_text("1\nboat\n", encoding="utf-8")
    cfg = HunspellConfig(dict_dirs=(str(d),), local_root=str(tmp_path / "no-hunspell-root"))
    # Only this directory: user caches and system dictionaries must not leak into the test.
    with patch("lexaudit.detectors.hunspell._default_dict_dirs", return_value=[d]):
        found = find_dict("en", cfg)
    assert found is not None
    assert found[0] == "en_US"
    assert found[1].endswith("en_US")


def test_resolve_checker_falls_back_proper_only(tmp_path: Path) -> None:
    cfg = HunspellConfig(dict_dirs=(str(tmp_path),))
    checker = resolve_checker("zh", cfg)
    assert isinstance(checker, ProperOnlyChecker)


@patch("lexaudit.detectors.hunspell.subprocess.run")
def test_resolve_binary_explicit_and_env(mock_run: MagicMock, tmp_path: Path) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="hunspell 1.7", stderr="")
    local = tmp_path / "root"
    lib = local / "usr" / "lib" / "x86_64-linux-gnu"
    lib.mkdir(parents=True)
    bin_path = local / "usr" / "bin" / "hunspell"
    bin_path.parent.mkdir(parents=True)
    bin_path.write_text("#!/bin/sh\n", encoding="utf-8")

    cfg = HunspellConfig(
        binary="/custom/hunspell",
        local_root=str(local),
        ld_library_path_extra="/extra/lib",
    )
    binary, env = resolve_binary(cfg)
    assert binary == "/custom/hunspell"
    assert "/extra/lib" in env["LD_LIBRARY_PATH"]
    assert str(lib) in env["LD_LIBRARY_PATH"]

    cfg2 = HunspellConfig(local_root=str(local))
    binary2, _env2 = resolve_binary(cfg2)
    assert binary2 == str(bin_path)


@patch("lexaudit.detectors.hunspell.subprocess.run")
def test_resolve_binary_unusable_raises(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=127, stdout="", stderr="")
    with pytest.raises(RuntimeError, match="not usable"):
        resolve_binary(HunspellConfig(binary="/missing/hunspell"))


@patch("lexaudit.detectors.hunspell.subprocess.run")
def test_list_misspelled_batches(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="badword\n\n", stderr="")
    checker = HunspellChecker(
        dict_id="en_US",
        dict_path="/dicts/en_US",
        binary="hunspell",
        env={},
    )
    assert checker.list_misspelled([]) == set()
    bad = checker.list_misspelled(["good", "badword"])
    assert "badword" in bad
    assert mock_run.called
    args = mock_run.call_args[0][0]
    assert args[0] == "hunspell"
    assert args[1] == "-d"
    assert args[2] == "/dicts/en_US"
    assert args[3] == "-l"


def test_hunspell_accepts_known_en_word() -> None:
    if not LOCAL.exists():
        return
    cfg = HunspellConfig(local_root=str(LOCAL))
    checker = resolve_checker("en", cfg)
    bad = checker.list_misspelled(["boat", "xxyzzyqboat"])
    assert "boat" not in bad
    assert "xxyzzyqboat" in bad


def test_hunspell_de_capital_probe() -> None:
    if not LOCAL.exists():
        return
    cfg = HunspellConfig(local_root=str(LOCAL))
    checker = resolve_checker("de", cfg)
    bad = checker.list_misspelled(["rumpf", "Rumpf"])
    assert "Rumpf" not in bad or "rumpf" not in bad


def test_default_dict_dirs_include_user_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LEXAUDIT_DICT_DIR", str(tmp_path / "cache"))
    cfg = HunspellConfig(local_root=str(tmp_path / "none"))
    dirs = _default_dict_dirs(cfg)
    assert tmp_path / "cache" in dirs
    assert dirs.index(tmp_path / "cache") < dirs.index(Path("/usr/share/hunspell"))
