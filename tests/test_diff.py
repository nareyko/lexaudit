"""Baseline diff - new / gone / tier / status."""

from __future__ import annotations

import json
from pathlib import Path

from lexaudit.report.diff import diff_reports


def _minimal(locale: str, words: list[dict]) -> dict:
    stats = {"ok": 0, "proper": 0, "acronym": 0, "suspect": 0, "all": 0}
    return {
        "schema_version": "1",
        "generated_at": "1970-01-01T00:00:00Z",
        "lexaudit_version": "0.1.0",
        "config_hash": "x",
        "locales": [{"locale": locale, "stats": stats, "words": words, "pages": []}],
    }


def _word(norm: str, status: str = "suspect", tier: str | None = "weak") -> dict:
    return {
        "word": norm,
        "norm": norm,
        "status": status,
        "tier": tier,
        "reason": "",
        "detectors": [],
        "count": 1,
        "samples": [],
        "occurrences": [],
    }


def test_diff_new_gone_tier(tmp_path: Path) -> None:
    base = _minimal("en", [_word("a", tier="weak")])
    cur = _minimal("en", [_word("a", tier="likely"), _word("b")])
    bp = tmp_path / "base.json"
    cp = tmp_path / "cur.json"
    bp.write_text(json.dumps(base), encoding="utf-8")
    cp.write_text(json.dumps(cur), encoding="utf-8")
    d = diff_reports(bp, cp)
    assert d["counts"]["new"] == 1
    assert d["counts"]["tier_changed"] == 1
    assert d["counts"]["gone"] == 0
    assert d["new"][0] == {"locale": "en", "norm": "b", "status": "suspect", "tier": "weak"}
    assert d["tier_changed"][0]["from_tier"] == "weak"
    assert d["tier_changed"][0]["to_tier"] == "likely"
    assert d["tier_changed"][0]["locale"] == "en"
    assert d["tier_changed"][0]["norm"] == "a"


def test_diff_gone_and_status_change(tmp_path: Path) -> None:
    base = _minimal(
        "ru",
        [_word("old", status="suspect", tier="weak"), _word("flip", status="ok", tier=None)],
    )
    cur = _minimal("ru", [_word("flip", status="suspect", tier="likely")])
    bp = tmp_path / "base.json"
    cp = tmp_path / "cur.json"
    bp.write_text(json.dumps(base), encoding="utf-8")
    cp.write_text(json.dumps(cur), encoding="utf-8")
    d = diff_reports(bp, cp)
    assert d["counts"]["gone"] == 1
    assert d["gone"][0] == {"locale": "ru", "norm": "old", "status": "suspect", "tier": "weak"}
    assert d["counts"]["tier_changed"] == 1
    ch = d["tier_changed"][0]
    assert ch["from_status"] == "ok"
    assert ch["to_status"] == "suspect"
    assert ch["from_tier"] is None
    assert ch["to_tier"] == "likely"


def test_diff_empty_locales(tmp_path: Path) -> None:
    empty = {
        "schema_version": "1",
        "generated_at": "1970-01-01T00:00:00Z",
        "lexaudit_version": "0.1.0",
        "config_hash": "x",
        "locales": [],
    }
    bp = tmp_path / "base.json"
    cp = tmp_path / "cur.json"
    bp.write_text(json.dumps(empty), encoding="utf-8")
    cp.write_text(json.dumps(empty), encoding="utf-8")
    d = diff_reports(bp, cp)
    assert d["counts"] == {"new": 0, "gone": 0, "tier_changed": 0}


def test_diff_identical_no_change(tmp_path: Path) -> None:
    doc = _minimal("de", [_word("rumpf", status="ok", tier=None)])
    bp = tmp_path / "base.json"
    cp = tmp_path / "cur.json"
    bp.write_text(json.dumps(doc), encoding="utf-8")
    cp.write_text(json.dumps(doc), encoding="utf-8")
    d = diff_reports(bp, cp)
    assert d["counts"]["new"] == 0
    assert d["counts"]["gone"] == 0
    assert d["counts"]["tier_changed"] == 0
