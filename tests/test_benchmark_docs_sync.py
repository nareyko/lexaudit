"""Fail when README / docs synthetic-benchmark tables drift from recomputed metrics."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "reproduce_benchmark_table.py"


def _load_reproduce_module() -> object:
    spec = importlib.util.spec_from_file_location("reproduce_benchmark_table", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_benchmark_docs_sync() -> None:
    mod = _load_reproduce_module()
    errors = mod.check_docs_sync()  # type: ignore[attr-defined]
    assert errors == [], "benchmark docs out of sync:\n" + "\n".join(f"- {e}" for e in errors)
