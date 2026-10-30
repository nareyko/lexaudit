from __future__ import annotations

import pytest


def test_mcp_server_module_imports() -> None:
    import lexaudit.mcp_server as ms

    assert callable(ms.main)
    assert callable(ms._run_audit)
    assert callable(ms.build_mcp)
    assert callable(ms.list_tool_names)


def test_mcp_tools_registered_without_network() -> None:
    pytest.importorskip("mcp")
    from lexaudit.mcp_server import build_mcp, list_tool_names

    names = list_tool_names(build_mcp())
    assert "audit" in names
    assert "explain" in names
    assert "expand_needle" in names
    assert "fetch_dicts" in names


def test_identical_segment_and_chrome_extras() -> None:
    from lexaudit.detectors.bilingual import (
        detect_pair_leftovers,
        identical_segment_leftovers,
    )

    src = "Please verify denseness before release.\nSave your preferences now permanently.\n"
    tgt = "Please verify denseness before release.\nСохраните настройки. denseness остался.\n"
    segs = identical_segment_leftovers(src, tgt, path="ru/x.md")
    assert any(w.reason == "bilingual-identical-segment" for w in segs)
    hits = detect_pair_leftovers(
        src,
        tgt,
        source_locale="en",
        target_locale="ru",
        path="ru/x.md",
        extra_chrome=frozenset({"preferences"}),
    )
    norms = {w.normalized for w in hits}
    assert "denseness" in norms
