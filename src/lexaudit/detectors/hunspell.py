"""Hunspell wrapper - matches TS vocab prototype semantics."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lexaudit.detectors.dictfetch import cache_dir

LOCALE_DICTS: dict[str, list[str]] = {
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

BATCH_SIZE = 2000


@dataclass(frozen=True)
class HunspellConfig:
    binary: str | None = None
    dict_dirs: tuple[str, ...] = ()
    local_root: str | None = None  # e.g. frontend/tmp/hunspell-local
    ld_library_path_extra: str | None = None


@dataclass
class HunspellChecker:
    dict_id: str
    dict_path: str  # without extension
    binary: str
    env: dict[str, str]

    def list_misspelled(self, words: list[str]) -> set[str]:
        if not words:
            return set()
        bad: set[str] = set()
        for i in range(0, len(words), BATCH_SIZE):
            batch = words[i : i + BATCH_SIZE]
            payload = "\n".join(batch) + "\n"
            proc = subprocess.run(
                [self.binary, "-d", self.dict_path, "-l"],
                input=payload,
                capture_output=True,
                text=True,
                env=self.env,
                check=False,
            )
            for line in proc.stdout.splitlines():
                w = line.strip()
                if w:
                    bad.add(w)
        return bad


@dataclass
class SpyllsChecker:
    """Pure-Python Hunspell port: no system binary needed (slower start, same dictionaries)."""

    dict_id: str
    dict_path: str

    def list_misspelled(self, words: list[str]) -> set[str]:
        from spylls.hunspell import Dictionary  # lazy: heavy import

        dic = _spylls_dictionary(self.dict_path, Dictionary)
        return {w for w in words if w and not dic.lookup(w)}


_SPYLLS_CACHE: dict[str, object] = {}


def _spylls_dictionary(path: str, factory: Any) -> Any:
    if path not in _SPYLLS_CACHE:
        _SPYLLS_CACHE[path] = factory.from_files(path)
    return _SPYLLS_CACHE[path]


class ProperOnlyChecker:
    """zh / no-dict fallback: every probe is misspelled."""

    dict_id = "proper-only"

    def list_misspelled(self, words: list[str]) -> set[str]:
        return set(words)


def _effective_local_root(cfg: HunspellConfig) -> str | None:
    if cfg.local_root:
        return cfg.local_root
    env_root = os.environ.get("LEXAUDIT_HUNSPELL_ROOT")
    if env_root and Path(env_root).is_dir():
        return env_root
    # Optional vendor bundle when mounted inside a monorepo (../../frontend/tmp/hunspell-local)
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "frontend" / "tmp" / "hunspell-local"
        if (candidate / "usr" / "share" / "hunspell").is_dir():
            return str(candidate)
    return None


def _default_dict_dirs(cfg: HunspellConfig) -> list[Path]:
    dirs: list[Path] = []
    for d in cfg.dict_dirs:
        dirs.append(Path(d))
    local_root = _effective_local_root(cfg)
    if local_root:
        local = Path(local_root) / "usr" / "share" / "hunspell"
        if local.is_dir():
            dirs.append(local)
    dirs.append(cache_dir())
    dirs.extend([Path("/usr/share/hunspell"), Path("/usr/share/myspell/dicts")])
    return dirs


def resolve_binary(cfg: HunspellConfig) -> tuple[str, dict[str, str]]:
    env = os.environ.copy()
    local_root = _effective_local_root(cfg)
    if cfg.binary:
        binary = cfg.binary
    elif local_root and (Path(local_root) / "usr" / "bin" / "hunspell").is_file():
        binary = str(Path(local_root) / "usr" / "bin" / "hunspell")
    else:
        binary = "hunspell"

    lib_parts: list[str] = []
    if local_root:
        lib = Path(local_root) / "usr" / "lib" / "x86_64-linux-gnu"
        if lib.is_dir():
            lib_parts.append(str(lib))
    if cfg.ld_library_path_extra:
        lib_parts.append(cfg.ld_library_path_extra)
    if env.get("LD_LIBRARY_PATH"):
        lib_parts.append(env["LD_LIBRARY_PATH"])
    if lib_parts:
        env["LD_LIBRARY_PATH"] = ":".join(lib_parts)

    try:
        probe = subprocess.run(
            [binary, "-v"],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
    except OSError as exc:
        msg = f"hunspell binary not usable: {binary}"
        raise RuntimeError(msg) from exc
    if probe.returncode not in (0, 1) and not (probe.stdout or probe.stderr):
        msg = f"hunspell binary not usable: {binary}"
        raise RuntimeError(msg)
    return binary, env


def find_dict(locale: str, cfg: HunspellConfig) -> tuple[str, str] | None:
    candidates = LOCALE_DICTS.get(locale, [])
    if not candidates:
        return None
    dirs = _default_dict_dirs(cfg)
    for dict_id in candidates:
        for d in dirs:
            base = d / dict_id
            if base.with_suffix(".aff").is_file() and base.with_suffix(".dic").is_file():
                return dict_id, str(base)
    return None


def resolve_checker(
    locale: str, cfg: HunspellConfig
) -> HunspellChecker | SpyllsChecker | ProperOnlyChecker:
    found = find_dict(locale, cfg)
    if found is None:
        return ProperOnlyChecker()
    dict_id, dict_path = found
    try:
        binary, env = resolve_binary(cfg)
    except RuntimeError:
        return SpyllsChecker(dict_id=dict_id, dict_path=dict_path)
    return HunspellChecker(dict_id=dict_id, dict_path=dict_path, binary=binary, env=env)
