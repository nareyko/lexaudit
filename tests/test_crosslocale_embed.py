"""Cross-locale embed cache helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from lexaudit.core.types import TextChunk
from lexaudit.detectors.crosslocale import (
    aggregate_norms_from_chunks,
    embed_texts,
    load_embedding_cache,
    save_embedding_cache,
)


def test_embed_cache_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "emb.json"
    cache = {"abc": [0.1, 0.2]}
    save_embedding_cache(path, cache)
    assert load_embedding_cache(path) == cache


def test_embed_texts_uses_cache_and_api(tmp_path: Path) -> None:
    cache: dict[str, list[float]] = {}
    path = tmp_path / "emb.json"

    class Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {"data": [{"index": 0, "embedding": [1.0, 2.0]}]}

    with patch("httpx.Client") as mock_client:
        inst = MagicMock()
        inst.__enter__.return_value = inst
        inst.__exit__.return_value = None
        inst.post.return_value = Resp()
        mock_client.return_value = inst
        vecs = embed_texts(
            ["hello"],
            base_url="http://127.0.0.1:8501/v1",
            model="bge-m3",
            cache=cache,
            cache_path=path,
        )
    assert vecs == [[1.0, 2.0]]
    assert path.is_file()
    # second call fully cached
    vecs2 = embed_texts(
        ["hello"],
        base_url="http://127.0.0.1:8501/v1",
        model="bge-m3",
        cache=cache,
        cache_path=path,
    )
    assert vecs2 == [[1.0, 2.0]]


def test_aggregate_norms() -> None:
    chunks = [TextChunk("a.md", "body", "Boat hull", "md")]
    norms = aggregate_norms_from_chunks(chunks, "en")
    assert "boat" in norms
