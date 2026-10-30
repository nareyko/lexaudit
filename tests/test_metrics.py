"""Eval metrics - dense cases for mutation kill rate."""

from __future__ import annotations

import json
from pathlib import Path

from lexaudit.core.types import ClassifiedWord, PageSuspectRank, VocabSample
from lexaudit.eval.metrics import (
    ANOMALY,
    clear_regression,
    compute_metrics,
    gold_is_anomaly,
    load_gold_jsonl,
    needle_recall,
    page_at_k,
    pred_is_anomaly,
    render_metrics_md,
)


def _cw(
    norm: str,
    status: str,
    *,
    tier: str | None = None,
    detectors: list[str] | None = None,
) -> ClassifiedWord:
    return ClassifiedWord(
        normalized=norm,
        surface=norm,
        count=1,
        status=status,  # type: ignore[arg-type]
        samples=[VocabSample("a", "body")],
        tier=tier,  # type: ignore[arg-type]
        detectors=detectors or ["hunspell"],
    )


def _gold(word: str, label: str) -> dict:
    return {
        "id": word,
        "word": word,
        "label": label,
        "locale": "en",
        "context": "",
        "path": "a",
        "annotator": "t",
    }


def test_anomaly_sets() -> None:
    assert (
        frozenset({"foreign", "calque", "invented", "morph-miss", "suspect", "unsure"}) == ANOMALY
    )
    assert "template" not in ANOMALY
    assert "ok" not in ANOMALY
    for label in ANOMALY:
        assert gold_is_anomaly(label) is True
        assert pred_is_anomaly(label) is True
    assert gold_is_anomaly("ok") is False
    assert gold_is_anomaly("template") is False
    assert gold_is_anomaly("proper") is False
    assert pred_is_anomaly("ok") is False
    assert pred_is_anomaly("template") is False


def test_load_gold_jsonl_skips_blank(tmp_path: Path) -> None:
    p = tmp_path / "g.jsonl"
    p.write_text('{"word":"a","label":"ok"}\n\n{"word":"b","label":"invented"}\n', encoding="utf-8")
    rows = load_gold_jsonl(p)
    assert len(rows) == 2
    assert rows[0]["word"] == "a"
    assert rows[1]["label"] == "invented"


def test_compute_metrics_tp_tn_fp_fn_and_breakdowns() -> None:
    gold = [
        _gold("Xxyzzyq", "invented"),  # casefold key
        _gold("boat", "ok"),
        _gold("missing", "suspect"),  # FN - no prediction
        _gold("noise", "ok"),  # FP - predicted suspect
        _gold("calque_w", "calque"),
        _gold("foreign_w", "foreign"),
    ]
    pred = {
        "xxyzzyq": _cw("xxyzzyq", "suspect", tier="weak", detectors=["hunspell"]),
        "boat": _cw("boat", "ok", detectors=["hunspell"]),
        "noise": _cw("noise", "suspect", tier="likely", detectors=["foreign"]),
        "calque_w": _cw("calque_w", "calque", tier="confirmed", detectors=["calque"]),
        "foreign_w": _cw("foreign_w", "ok", detectors=["hunspell"]),  # FN: gold anomaly, pred ok
    }
    m = compute_metrics(gold, pred)
    assert m["counts"]["tp"] == 2  # xxyzzyq + calque_w
    assert m["counts"]["tn"] == 1  # boat
    assert m["counts"]["fp"] == 1  # noise
    assert m["counts"]["fn"] == 2  # missing + foreign_w
    assert m["review_status"] == "unreviewed"
    assert compute_metrics(gold, pred, review_status="reviewed")["review_status"] == "reviewed"
    assert m["by_status"]["invented"]["tp"] == 1
    assert m["by_status"]["invented"].get("fn", 0) == 0
    assert m["by_status"]["suspect"]["fn"] == 1
    assert m["by_status"]["suspect"]["fp"] == 1
    assert m["by_status"]["foreign"]["fn"] == 1
    assert m["by_status"]["calque"]["tp"] == 1
    assert m["by_tier"]["weak"]["tp"] == 1
    assert m["by_tier"]["likely"]["fp"] == 1
    assert m["by_tier"]["confirmed"]["tp"] == 1
    assert m["by_detector"]["hunspell"]["tp"] == 1
    assert m["by_detector"]["calque"]["tp"] == 1
    assert m["by_detector"]["foreign"]["fp"] == 1
    o = m["overall"]
    # tp=2 fp=1 fn=2 → precision 2/3, recall 2/4, f1 = 2*(2/3)*(1/2)/((2/3)+(1/2))
    assert o["precision"] == 2 / 3
    assert o["recall"] == 0.5
    assert abs(o["f1"] - (2 * (2 / 3) * 0.5) / ((2 / 3) + 0.5)) < 1e-9


def test_compute_metrics_empty_and_perfect() -> None:
    empty = compute_metrics([], {})
    assert empty["counts"] == {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    assert empty["overall"] == {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    gold = [_gold("a", "ok"), _gold("b", "invented")]
    pred = {"a": _cw("a", "ok"), "b": _cw("b", "invented", tier=None, detectors=["x"])}
    m = compute_metrics(gold, pred)
    assert m["counts"]["tp"] == 1
    assert m["counts"]["tn"] == 1
    assert m["overall"]["precision"] == 1.0
    assert m["overall"]["recall"] == 1.0
    assert m["overall"]["f1"] == 1.0
    # tier None → bucket "none"
    assert m["by_tier"]["none"]["tp"] == 1


def test_compute_metrics_missing_ok_is_ignored() -> None:
    gold = [_gold("gone", "ok")]
    m = compute_metrics(gold, {})
    assert m["counts"]["fn"] == 0
    assert m["counts"]["tp"] == 0


def test_render_metrics_md_tables() -> None:
    gold = [_gold("x", "invented"), _gold("y", "ok")]
    pred = {
        "x": _cw("x", "suspect", tier="weak", detectors=["hunspell"]),
        "y": _cw("y", "ok"),
    }
    m = compute_metrics(gold, pred)
    md = render_metrics_md(m, "Holdout EN")
    assert md.startswith("# Holdout EN")
    assert "Review status: **unreviewed**" in md
    assert "TP=1" in md
    assert "precision=" in md
    assert "| detector | tp | fp |" in md
    assert "| hunspell |" in md
    assert "| tier | tp | fp |" in md
    assert "| weak |" in md
    # default review_status when key missing
    slim = {
        "overall": {"precision": 0.5, "recall": 0.5, "f1": 0.5},
        "counts": {"tp": 1, "fp": 1, "fn": 1, "tn": 1},
        "by_detector": {},
        "by_tier": {},
    }
    md2 = render_metrics_md(slim, "t")
    assert "unreviewed" in md2


def test_load_roundtrip_json_types(tmp_path: Path) -> None:
    p = tmp_path / "g.jsonl"
    row = _gold("Zed", "morph-miss")
    p.write_text(json.dumps(row) + "\n", encoding="utf-8")
    assert load_gold_jsonl(p)[0]["label"] == "morph-miss"
    assert gold_is_anomaly("morph-miss") is True
    assert gold_is_anomaly("unsure") is True


def test_page_at_k() -> None:
    ranked = [
        PageSuspectRank(path="a/gold1.json", unique_suspects=3, sample_words=[], score=9.0),
        PageSuspectRank(path="b/noise.json", unique_suspects=2, sample_words=[], score=4.0),
        PageSuspectRank(path="c/gold2.json", unique_suspects=1, sample_words=[], score=3.0),
    ]
    m = page_at_k(ranked, ["gold1", "gold2"], k=2)
    assert m["hits"] == 1
    assert m["precision"] == 0.5


def test_needle_recall_gate() -> None:
    words = [
        _cw("orientir", "calque"),
        _cw("denseness", "calque"),
        _cw("предпокупочный", "calque"),
        _cw("чеклисте", "calque"),
        _cw("блувотер", "calque"),
        _cw("unrelated", "suspect"),
    ]
    needles = ["orientir", "denseness", "предпокуп", "чеклист", "блувотер", "absent-needle"]
    m = needle_recall(needles, words, locale="ru")
    assert m["evaluated"] == 5
    assert m["skipped_absent"] == 1
    assert m["recall"] >= 0.9
    # miss when present but still plain suspect
    bad = needle_recall(["orientir"], [_cw("orientir", "suspect")], locale="en")
    assert bad["recall"] == 0.0


def test_clear_regression_slugs() -> None:
    words = [
        ClassifiedWord(
            normalized="orientir",
            surface="orientir",
            count=1,
            status="calque",
            samples=[VocabSample("cruising/other-page.json", "body")],
        ),
        ClassifiedWord(
            normalized="boat",
            surface="boat",
            count=1,
            status="ok",
            samples=[VocabSample("cruising/hamburg-cuxhaven-unterelbe.json", "body")],
        ),
    ]
    m = clear_regression(
        ["hamburg-cuxhaven-unterelbe"],
        words,
        ["orientir", "denseness"],
        locale="en",
    )
    assert m["all_clear"] is True
    m2 = clear_regression(
        ["other-page"],
        words,
        ["orientir"],
        locale="en",
    )
    assert m2["all_clear"] is False
