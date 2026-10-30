"""Report writer determinism and schema."""

from __future__ import annotations

from pathlib import Path

from lexaudit.core.types import ClassifiedWord, PageSuspectRank, VocabSample
from lexaudit.report.write import build_report_doc, write_reports


def _word(status: str = "suspect") -> ClassifiedWord:
    return ClassifiedWord(
        normalized="xxyzzyq",
        surface="Xxyzzyq",
        count=2,
        status=status,  # type: ignore[arg-type]
        samples=[VocabSample("a.md", "body")],
        tier="weak",
        reason="unknown",
        detectors=["hunspell"],
    )


def test_write_reports_deterministic(tmp_path: Path) -> None:
    words = [_word("suspect"), _word("ok")]
    words[1] = ClassifiedWord(
        normalized="boat",
        surface="boat",
        count=5,
        status="ok",
        samples=[VocabSample("a.md", "body")],
        detectors=["hunspell"],
        reason="hunspell",
    )
    pages = [PageSuspectRank(path="a.md", unique_suspects=1, sample_words=["xxyzzyq"], score=1.0)]
    a = tmp_path / "a"
    b = tmp_path / "b"
    for out in (a, b):
        write_reports(
            out_dir=out,
            locale="en",
            words=words,
            pages=pages,
            config_hash="abc",
            freeze_generated_at="1970-01-01T00:00:00Z",
            detector_stats={"hunspell": 2},
        )
    for name in ("report.json", "words.json", "suspect.csv", "pages.csv", "summary.md", "queue.md"):
        assert (a / name).read_text(encoding="utf-8") == (b / name).read_text(encoding="utf-8")


def test_build_report_doc_validates() -> None:
    doc = build_report_doc(
        locale="en",
        words=[_word("proper")],
        pages=[],
        config_hash="x",
        generated_at="1970-01-01T00:00:00Z",
    )
    assert doc["schema_version"] == "1"
    assert doc["locales"][0]["stats"]["proper"] == 1
