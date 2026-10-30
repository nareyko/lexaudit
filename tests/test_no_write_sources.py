"""Ensure lexaudit never writes into audited corpus source trees."""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "lexaudit"

# Write sinks that are allowed (reports, cache, gold outputs under lexaudit).
ALLOWED_WRITE_FILES = {
    "report/write.py",
    "report/diff.py",  # baseline diff output only
    "report/curated_queue.py",  # curated rewrite queue markdown
    "curated/queue.py",  # curated queue JSON/markdown (I2)
    "llm/client.py",  # disk cache only
    "llm/emit.py",  # llm-labels.json under output_dir
    "cli/main.py",  # may create output dirs via report
    "detectors/crosslocale.py",  # embedding cache under output dir
}


def test_no_source_tree_writes() -> None:
    """Fail if open(..., 'w') / write_text appear outside allowlisted modules."""
    pattern = re.compile(r"""(?:\.write_text\(|open\([^)]*["']w)""")
    offenders: list[str] = []
    for path in SRC.rglob("*.py"):
        rel = path.relative_to(SRC).as_posix()
        if rel in ALLOWED_WRITE_FILES:
            continue
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            offenders.append(rel)
    assert offenders == [], f"unexpected write sites: {offenders}"
