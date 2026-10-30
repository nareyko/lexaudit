"""expand-needle CLI and needle matching (I3)."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from lexaudit.cli.main import main
from lexaudit.curated.queue import (
    CuratedRow,
    NeedleQueueHit,
    append_pending_from_needle_hits,
    load_curated,
)
from lexaudit.detectors.calque import needle_matches_norm
from lexaudit.report.expand_needle import scan_words_for_needle


def test_needle_matches_stem_family() -> None:
    assert needle_matches_norm("orientir", "orientir", "en")
    assert needle_matches_norm("orientirs", "orientir", "en")
    assert needle_matches_norm("budget-orientir", "orientir", "en")
    assert not needle_matches_norm("orientation", "orientir", "en")


def test_needle_matches_glob() -> None:
    assert needle_matches_norm("budget-orientir", "*-orientir", "en")
    assert not needle_matches_norm("orientir", "*-orientir", "en")


def _fixture_words() -> list[dict]:
    return [
        {
            "word": "orientir",
            "surface": "orientir",
            "status": "calque",
            "count": 3,
            "samples": [
                {"path": "systems/iso-9650-grab-bag-contents.json", "field": "body"},
                {"path": "systems/iso-9650-grab-bag-contents.json", "field": "title"},
                {"path": "cruising/demo.json", "field": "body"},
            ],
        },
        {
            "word": "boat",
            "surface": "boat",
            "status": "ok",
            "count": 10,
            "samples": [{"path": "systems/iso-9650-grab-bag-contents.json", "field": "body"}],
        },
        {
            "word": "orientirs",
            "surface": "orientirs",
            "status": "suspect",
            "count": 1,
            "samples": [{"path": "systems/propeller-shaft-seals.json", "field": "body"}],
        },
    ]


def test_scan_words_for_needle_aggregates_paths(tmp_path: Path) -> None:
    words_path = tmp_path / "en" / "words.json"
    words_path.parent.mkdir(parents=True)
    words_path.write_text(json.dumps({"words": _fixture_words()}), encoding="utf-8")
    hits = scan_words_for_needle(_fixture_words(), locale="en", needle="orientir")
    by_path = {h.path: h for h in hits}
    assert len(by_path) == 3
    sys_hit = by_path["systems/iso-9650-grab-bag-contents.json"]
    assert sys_hit.count == 2  # two samples on this path (word total count is 3 corpus-wide)
    assert sys_hit.status == "calque"
    assert "orientir" in sys_hit.norm


def test_expand_needle_cli_and_write_queue_no_dup(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / "en").mkdir()
    (out / "en" / "words.json").write_text(
        json.dumps({"words": _fixture_words()}), encoding="utf-8"
    )
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        "\n".join(
            [
                f"repo_root: {tmp_path}",
                f"output_dir: {out}",
                "locales: [en, de]",
                "sources: [academy]",
                "enable_morph: false",
                "enable_compound: false",
                "enable_foreign: false",
                "enable_calque: false",
            ]
        ),
        encoding="utf-8",
    )
    queue = tmp_path / "queue.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "expand-needle",
            "--config",
            str(cfg),
            "--needle",
            "orientir",
            "--locale",
            "en",
            "--write-queue",
            str(queue),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "systems/iso-9650-grab-bag-contents.json" in result.output
    assert "systems/propeller-shaft-seals.json" in result.output
    assert queue.is_file()
    body = queue.read_text(encoding="utf-8")
    assert "| # | status | slug / path |" in body
    rows = load_curated(queue)
    slugs = {r.path for r in rows}
    assert "systems/iso-9650-grab-bag-contents" in slugs
    assert "systems/propeller-shaft-seals" in slugs

    result2 = runner.invoke(
        main,
        [
            "expand-needle",
            "--config",
            str(cfg),
            "--needle",
            "orientir",
            "--write-queue",
            str(queue),
        ],
    )
    assert result2.exit_code == 0
    assert "queue +0 pending" in result2.output
    assert sum(1 for r in load_curated(queue) if r.status == "pending") == 3


def test_append_pending_from_needle_hits_skips_duplicate() -> None:
    rows = [
        CuratedRow(
            number=1,
            status="done",
            path="systems/foo",
            locales="EN",
            target_defects="`orientir*`",
            note="",
        )
    ]
    hits = [
        NeedleQueueHit("systems/foo.json", "en", "`orientir*`"),
        NeedleQueueHit("systems/bar.json", "en", "`orientir*`"),
    ]
    out, added = append_pending_from_needle_hits(rows, hits)
    assert added == 1
    paths = {r.path for r in out}
    assert "systems/foo" in paths
    assert "systems/bar" in paths
