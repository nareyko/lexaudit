"""LLM client with httpx mock - cache and JSON extract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from lexaudit.config import LlmProfile
from lexaudit.llm.client import LlmClient, _extract_json, cache_key, list_models
from lexaudit.llm.label import label_word
from lexaudit.llm.voting import vote_label


def test_extract_json_fenced() -> None:
    raw = '```json\n{"label":"ok","confidence":0.9}\n```'
    assert _extract_json(raw)["label"] == "ok"


def test_cache_roundtrip(tmp_path: Path) -> None:
    client = LlmClient(LlmProfile(name="t", model="m"), cache_dir=tmp_path)
    key = cache_key(model="m", prompt_version="v1", word="boat", context="ctx")
    client.put_cached(key, {"label": "ok"})
    assert client.get_cached(key) == {"label": "ok"}
    assert client.cache_hits == 1


def test_chat_json_uses_cache(tmp_path: Path) -> None:
    profile = LlmProfile(name="t", model="mock", timeout_s=5, max_retries=0)
    client = LlmClient(profile, cache_dir=tmp_path)
    key = cache_key(model="mock", prompt_version="label-v1", word="boat", context="c")
    client.put_cached(key, {"label": "ok", "confidence": 1.0})
    out = client.chat_json(
        system="s",
        user="u",
        prompt_version="label-v1",
        word="boat",
        context="c",
    )
    assert out["label"] == "ok"
    assert client.calls == 0


def test_chat_json_http_mock(tmp_path: Path) -> None:
    profile = LlmProfile(name="t", model="mock", timeout_s=5, max_retries=0)
    client = LlmClient(profile, cache_dir=tmp_path)
    payload = {
        "choices": [{"message": {"content": json.dumps({"label": "foreign", "confidence": 0.8})}}]
    }

    class Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return payload

    with patch("lexaudit.llm.client.httpx.Client") as mock_client:
        inst = MagicMock()
        inst.__enter__.return_value = inst
        inst.__exit__.return_value = None
        inst.post.return_value = Resp()
        mock_client.return_value = inst
        out = client.chat_json(
            system="sys",
            user="user",
            prompt_version="label-v1",
            word="offshore",
            context="ru text offshore",
        )
    assert out["label"] == "foreign"
    assert client.calls == 1
    # second call hits cache
    out2 = client.chat_json(
        system="sys",
        user="user",
        prompt_version="label-v1",
        word="offshore",
        context="ru text offshore",
    )
    assert out2["label"] == "foreign"
    assert client.calls == 1


def test_label_word_invalid_label_becomes_unsure(tmp_path: Path) -> None:
    profile = LlmProfile(name="t", model="mock", timeout_s=5, max_retries=0)
    client = LlmClient(profile, cache_dir=tmp_path)
    key = cache_key(model="mock", prompt_version="label-v1", word="x", context="c")
    client.put_cached(key, {"label": "not-a-real-label", "confidence": 0.1, "rationale": "x"})
    out = label_word(client, locale="en", word="x", context="c", path="a.md")
    assert out["label"] == "unsure"


def test_vote_label_majority(tmp_path: Path) -> None:
    profile = LlmProfile(name="t", model="mock", timeout_s=5, max_retries=0)
    client = LlmClient(profile, cache_dir=tmp_path)
    # Pre-seed cache for vote prompt version with vote salt in context
    key = cache_key(
        model="mock",
        prompt_version="label-v1-vote",
        word="boat",
        context="ctx||vote",
    )
    client.put_cached(key, {"label": "ok", "confidence": 1.0})
    result = vote_label([client], locale="en", word="boat", context="ctx", path="a")
    assert result["label"] == "ok"
    assert result["votes"] == 1
    assert result["stability"] == 1.0


def test_list_models_mock() -> None:
    class Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {"data": [{"id": "b"}, {"id": "a"}]}

    with patch("lexaudit.llm.client.httpx.Client") as mock_client:
        inst = MagicMock()
        inst.__enter__.return_value = inst
        inst.__exit__.return_value = None
        inst.get.return_value = Resp()
        mock_client.return_value = inst
        assert list_models() == ["a", "b"]
