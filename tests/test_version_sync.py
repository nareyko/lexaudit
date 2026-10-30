from __future__ import annotations

import re
from pathlib import Path

import lexaudit


def test_package_version_matches_pyproject() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    assert m is not None
    assert lexaudit.__version__ == m.group(1)


def test_action_yml_pins_current_major_minor() -> None:
    root = Path(__file__).resolve().parents[1]
    action = (root / "action.yml").read_text(encoding="utf-8")
    major_minor = ".".join(lexaudit.__version__.split(".")[:2])
    assert f"lexaudit>={major_minor}" in action or f"lexaudit>={lexaudit.__version__}" in action
