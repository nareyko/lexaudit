"""Download Hunspell dictionaries into a per-user cache (no root, no system packages).

Dictionaries are **not bundled** with lexaudit: each one has its own license
(MIT, MPL, LGPL, GPL). They are fetched on request from the public
``wooorm/dictionaries`` mirror and stored under the user cache directory.
"""

from __future__ import annotations

import contextlib
import os
import urllib.request
from collections.abc import Callable
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/wooorm/dictionaries/main/dictionaries"

# locale -> (upstream folder, local dictionary id used by lexaudit)
SOURCES: dict[str, tuple[str, str]] = {
    "en": ("en-GB", "en_GB"),
    "de": ("de", "de_DE"),
    "es": ("es", "es_ES"),
    "pl": ("pl", "pl_PL"),
    "ru": ("ru", "ru_RU"),
    "sv": ("sv", "sv_SE"),
    "uk": ("uk", "uk_UA"),
}

Fetcher = Callable[[str], bytes]


def cache_dir() -> Path:
    """Per-user dictionary cache (``$LEXAUDIT_DICT_DIR`` or the XDG cache)."""
    override = os.environ.get("LEXAUDIT_DICT_DIR")
    if override:
        return Path(override)
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "lexaudit" / "dictionaries"


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "lexaudit"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data: bytes = resp.read()
    return data


def fetch_dictionary(locale: str, dest: Path, fetch: Fetcher = _http_get) -> Path:
    """Download one locale into ``dest`` and return the path stem (no extension)."""
    if locale not in SOURCES:
        msg = f"no downloadable dictionary for locale {locale!r}; known: {sorted(SOURCES)}"
        raise ValueError(msg)
    folder, dict_id = SOURCES[locale]
    dest.mkdir(parents=True, exist_ok=True)
    for ext in ("aff", "dic"):
        (dest / f"{dict_id}.{ext}").write_bytes(fetch(f"{BASE_URL}/{folder}/index.{ext}"))
    # The license text is a courtesy copy: never block the download if it is missing.
    with contextlib.suppress(OSError):
        (dest / f"{dict_id}.license.txt").write_bytes(fetch(f"{BASE_URL}/{folder}/license"))
    return dest / dict_id
