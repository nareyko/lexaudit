"""v0.4.2 W4: FairHelm md/translations must not reintroduce known calque needles."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# FairHelm repo root when lexaudit lives at tools/lexaudit.
REPO = Path(__file__).resolve().parents[3]
CONTENT_ROOTS = (
    REPO / "frontend" / "content",
    REPO / "frontend" / "translations",
)

# Needles from rewrite-queues #1-#4 (reader-facing calques).
NEEDLES = (
    r"orientir",
    r"denseness",
    r"предпокуп",
    r"przedzakup",
    r"чеклист",
    r"чек-лист",
    r"чекліст",
    r"чек-ліст",
    r"апгрейд",
    r"водотонnage",
)


@pytest.mark.skipif(
    not (REPO / "frontend" / "content").is_dir(),
    reason="FairHelm frontend tree not present (standalone lexaudit checkout)",
)
def test_fairhelm_md_translations_clear_of_known_calques() -> None:
    pattern = re.compile("|".join(NEEDLES), re.IGNORECASE)
    hits: list[str] = []
    for root in CONTENT_ROOTS:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".md", ".json"}:
                continue
            text = path.read_text(encoding="utf-8")
            for m in pattern.finditer(text):
                rel = path.relative_to(REPO).as_posix()
                hits.append(f"{rel}: {m.group(0)}")
                if len(hits) >= 20:
                    break
            if len(hits) >= 20:
                break
        if len(hits) >= 20:
            break
    assert hits == [], "known calque needles returned:\n" + "\n".join(hits)
