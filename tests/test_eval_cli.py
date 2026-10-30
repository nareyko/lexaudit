"""CLI: lexaudit eval product | regression."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from lexaudit.cli.main import main
from lexaudit.core.types import ClassifiedWord, VocabSample
from lexaudit.eval.product import (
    CLEAR_REGRESSION_NEEDLES,
    compute_product_metrics,
    run_regression_check,
    words_from_json_payload,
)

EVAL_GOLD_SLUGS: tuple[str, ...] = (
    "hamburg-cuxhaven-unterelbe-wochen-toern-gezeiten-haefen",
    "deutsche-bucht-elbe-tidal-windows-and-harbour-bars",
    "yacht-clearance-q-flag-zarpe-and-staging-ports",
    "turkey-temporary-admission-eu-flagged-yacht-winter-berth-customs",
    "charter-contract-night-sailing-sunset-sunrise-ban",
    "what-is-blue-water-sailing",
    "coastal-vs-offshore",
    "how-to-inspect-a-used-yacht",
    "yacht-survey-what-to-expect",
    "survey-checklist",
    "skeg",
)


def _write_words(out: Path, locale: str, words: list[ClassifiedWord]) -> None:
    loc_dir = out / locale
    loc_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "words": [
            {
                "word": w.normalized,
                "surface": w.surface,
                "count": w.count,
                "status": w.status,
                "samples": [{"path": s.path, "field": s.scope} for s in w.samples],
            }
            for w in words
        ]
    }
    (loc_dir / "words.json").write_text(json.dumps(payload), encoding="utf-8")


def _mini_eval_config(tmp_path: Path) -> Path:
    out = tmp_path / "out"
    slug = EVAL_GOLD_SLUGS[0]
    path = f"infra/corpus-ci/pending-academy-articles/cruising/{slug}.json"
    words_en = [
        ClassifiedWord(
            normalized="orientir",
            surface="orientir",
            count=1,
            status="calque",
            samples=[VocabSample(path, "body")],
        ),
        ClassifiedWord(
            normalized="boat",
            surface="boat",
            count=2,
            status="suspect",
            samples=[VocabSample("infra/corpus-ci/pending-academy-articles/other.json", "body")],
        ),
    ]
    _write_words(out, "en", words_en)
    _write_words(out, "de", [])
    _write_words(out, "ru", [])
    cfg = tmp_path / "cfg.yaml"
    gold_lines = "\n".join(f"  - {s}" for s in EVAL_GOLD_SLUGS)
    cfg.write_text(
        f"repo_root: {tmp_path}\noutput_dir: {out}\nlocales: [en, de, ru]\n"
        "needles: [orientir, denseness]\n"
        f"gold_slugs:\n{gold_lines}\n"
        "regression_needles: [orientir, denseness, предпокуп, блувотер, чеклист]\n",
        encoding="utf-8",
    )
    return cfg


def test_words_from_json_payload_roundtrip() -> None:
    data = {
        "words": [
            {
                "word": "x",
                "surface": "X",
                "count": 1,
                "status": "ok",
                "samples": [{"path": "p.json", "field": "body"}],
            }
        ]
    }
    ws = words_from_json_payload(data)
    assert len(ws) == 1
    assert ws[0].normalized == "x"


def test_compute_product_metrics_page_at_k(tmp_path: Path) -> None:
    from lexaudit.config import load_config

    cfg_path = _mini_eval_config(tmp_path)
    cfg = load_config(cfg_path)
    m = compute_product_metrics(cfg, k=10)
    en = m["locales"]["en"]
    assert en["page_at_k"]["k"] == 10
    assert en["page_at_k"]["hits"] >= 1
    assert en["needle_recall"]["recall"] == 1.0


def test_run_regression_clear_and_fail(tmp_path: Path) -> None:
    from lexaudit.config import load_config

    cfg_path = _mini_eval_config(tmp_path)
    cfg = load_config(cfg_path)
    report = run_regression_check(cfg)
    assert len(report["results"]) == len(EVAL_GOLD_SLUGS)
    by_slug = {r["slug"]: r for r in report["results"]}
    assert by_slug[EVAL_GOLD_SLUGS[0]]["clear"] is False
    assert all(by_slug[s]["clear"] for s in EVAL_GOLD_SLUGS[1:])


def test_cli_eval_product_and_regression(tmp_path: Path) -> None:
    cfg_path = _mini_eval_config(tmp_path)
    runner = CliRunner()
    r1 = runner.invoke(main, ["eval", "product", "--config", str(cfg_path)])
    assert r1.exit_code == 0, r1.output
    assert "page@10" in r1.output
    assert "needle_recall=" in r1.output
    r2 = runner.invoke(main, ["eval", "regression", "--config", str(cfg_path)])
    assert r2.exit_code == 0, r2.output
    assert f"{EVAL_GOLD_SLUGS[0]}: FAIL" in r2.output
    assert "CLEAR" in r2.output


def test_clear_regression_needles_exclude_skeg() -> None:
    assert "скеге" not in CLEAR_REGRESSION_NEEDLES
