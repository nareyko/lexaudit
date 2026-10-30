from __future__ import annotations

from pathlib import Path

from lexaudit.config import LexauditConfig, load_config
from lexaudit.core.types import ClassifiedWord, TextChunk, VocabSample
from lexaudit.detectors.crosslocale import (
    aggregate_norms_from_chunks,
    make_crosslocale_detector,
    pair_chunks_by_path,
)


def test_make_crosslocale_boosts_unpaired_suspect() -> None:
    detect = make_crosslocale_detector({"shared"})
    lone = ClassifiedWord(
        normalized="lonelytoken",
        surface="lonelytoken",
        count=1,
        status="suspect",
        samples=[VocabSample(path="ru/a.md", scope="body")],
        reason="unknown",
        detectors=["hunspell"],
        tier="weak",
    )
    shared = ClassifiedWord(
        normalized="shared",
        surface="shared",
        count=1,
        status="suspect",
        samples=[VocabSample(path="ru/a.md", scope="body")],
        reason="unknown",
        detectors=["hunspell"],
        tier="weak",
    )
    assert detect(lone) is not None
    assert "crosslocale" in lone.detectors
    assert lone.tier == "likely"
    assert detect(shared) is None


def test_pair_chunks_and_aggregate(tmp_path: Path) -> None:
    ru = [TextChunk(path="a.md", scope="body", text="один два denseness", source="files")]
    en = [TextChunk(path="a.md", scope="body", text="one two denseness", source="files")]
    pairs, unmatched_ru, unmatched_en = pair_chunks_by_path(ru, en)
    assert len(pairs) == 1
    assert unmatched_ru == []
    assert unmatched_en == []
    norms = aggregate_norms_from_chunks(en, "en")
    assert "denseness" in norms
    assert "one" in norms


def test_config_crosslocale_reference_default() -> None:
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "examples" / "lexaudit.config.example.yaml")
    assert cfg.enable_crosslocale is False
    assert cfg.crosslocale_reference_locale == "en"


def test_pipeline_crosslocale_pass_skipped_for_reference(tmp_path: Path) -> None:
    from lexaudit.core.pipeline import apply_crosslocale_pass

    cfg = LexauditConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        locales=["en"],
        sources=["files"],
        files_paths=(tmp_path,),
        enable_crosslocale=True,
        crosslocale_reference_locale="en",
    )
    (tmp_path / "a.md").write_text("hello world\n", encoding="utf-8")
    words = [
        ClassifiedWord(
            normalized="hello",
            surface="hello",
            count=1,
            status="ok",
            samples=[],
            reason="hunspell",
            detectors=["hunspell"],
        )
    ]
    stats: dict[str, int] = {}
    out = apply_crosslocale_pass(
        words,
        cfg,
        "en",
        academy_root=tmp_path,
        packs_root=tmp_path,
        stats=stats,
    )
    assert out is words
    assert stats.get("crosslocale") == 0
