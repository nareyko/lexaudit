"""Cross-locale pairing and detectors."""

from __future__ import annotations

from pathlib import Path

from lexaudit.core.types import ClassifiedWord, TextChunk, VocabSample
from lexaudit.detectors.crosslocale import (
    aggregate_norms_from_chunks,
    group_unmatched_share_by_path,
    load_embedding_cache,
    make_crosslocale_detector,
    pair_chunks_by_path,
    pairing_stats,
    save_embedding_cache,
)


def test_pair_chunks() -> None:
    ru = [TextChunk("a.json", "body", "текст", "academy")]
    en = [
        TextChunk("a.json", "body", "text", "academy"),
        TextChunk("b.json", "body", "x", "academy"),
    ]
    pairs, u_ru, u_en = pair_chunks_by_path(ru, en)
    assert len(pairs) == 1
    assert not u_ru
    assert len(u_en) == 1
    st = pairing_stats(pairs, u_ru, u_en)
    assert st["paired"] == 1
    assert st["unmatched_ru"] == 0
    assert st["unmatched_other"] == 1
    assert st["unmatched_share"] == 0.5


def test_pair_unmatched_ru_and_empty_stats() -> None:
    ru = [TextChunk("only-ru.json", "title", "текст", "academy")]
    pairs, u_ru, u_en = pair_chunks_by_path(ru, [])
    assert pairs == []
    assert len(u_ru) == 1
    assert u_en == []
    st = pairing_stats([], [], [])
    assert st == {"paired": 0, "unmatched_ru": 0, "unmatched_other": 0, "unmatched_share": 0.0}


def test_crosslocale_boost_and_skips() -> None:
    det = make_crosslocale_detector({"boat", "hull"})
    w = ClassifiedWord(
        normalized="xxyzzyq",
        surface="xxyzzyq",
        count=1,
        status="suspect",
        samples=[VocabSample("a", "body")],
        tier="weak",
        reason="unknown",
    )
    out = det(w)
    assert out is not None
    assert out.tier == "likely"
    assert "+no-pair" in out.reason
    assert "crosslocale" in out.detectors
    # already in paired set → no boost
    assert (
        det(
            ClassifiedWord(
                normalized="boat",
                surface="boat",
                count=1,
                status="suspect",
                samples=[VocabSample("a", "body")],
                tier="weak",
            )
        )
        is None
    )
    # ok status skipped
    assert (
        det(
            ClassifiedWord(
                normalized="zzz",
                surface="zzz",
                count=1,
                status="ok",
                samples=[VocabSample("a", "body")],
            )
        )
        is None
    )
    # invented + None tier → likely
    inv = ClassifiedWord(
        normalized="qwertyui",
        surface="qwertyui",
        count=1,
        status="invented",
        samples=[VocabSample("a", "body")],
        tier=None,
    )
    out2 = det(inv)
    assert out2 is not None
    assert out2.tier == "likely"


def test_aggregate_and_group_and_cache(tmp_path: Path) -> None:
    chunks = [
        TextChunk("p.md", "body", "Boat hull", "academy"),
        TextChunk("p.md", "title", "Deck", "academy"),
        TextChunk("q.md", "body", "Rudder", "academy"),
    ]
    norms = aggregate_norms_from_chunks(chunks, "en")
    assert "boat" in norms
    assert "hull" in norms
    grouped = group_unmatched_share_by_path(chunks)
    assert grouped["p.md"] == 2
    assert grouped["q.md"] == 1
    assert list(grouped.keys()) == sorted(grouped.keys())

    missing = tmp_path / "missing.json"
    assert load_embedding_cache(missing) == {}
    cache_path = tmp_path / "emb.json"
    save_embedding_cache(cache_path, {"b": [0.2], "a": [0.1]})
    loaded = load_embedding_cache(cache_path)
    assert list(loaded.keys()) == ["a", "b"]
    assert loaded["a"] == [0.1]
