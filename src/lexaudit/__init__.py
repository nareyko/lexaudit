"""lexaudit: locale vocabulary audit for inventeds, calques, and foreign slips."""

from __future__ import annotations

try:
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("lexaudit")
    except PackageNotFoundError:  # pragma: no cover - editable / src tree
        __version__ = "0.3.0"
except ImportError:  # pragma: no cover
    __version__ = "0.3.0"
