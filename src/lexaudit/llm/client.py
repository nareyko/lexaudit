"""OpenAI-compatible LocalAI client with disk cache."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx

from lexaudit.config import LlmProfile


def context_hash(context: str) -> str:
    return hashlib.sha256(context.encode("utf-8")).hexdigest()[:16]


def cache_key(
    *,
    model: str,
    prompt_version: str,
    word: str,
    context: str,
) -> str:
    raw = "|".join([model, prompt_version, word, context_hash(context)])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class LlmClient:
    def __init__(self, profile: LlmProfile, cache_dir: Path | None = None) -> None:
        self.profile = profile
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
        self._calls = 0
        self._cache_hits = 0

    @property
    def calls(self) -> int:
        return self._calls

    @property
    def cache_hits(self) -> int:
        return self._cache_hits

    def _cache_path(self, key: str) -> Path | None:
        if not self.cache_dir:
            return None
        return self.cache_dir / f"{key}.json"

    def get_cached(self, key: str) -> dict[str, Any] | None:
        path = self._cache_path(key)
        if path is None or not path.is_file():
            return None
        self._cache_hits += 1
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        return data

    def put_cached(self, key: str, value: dict[str, Any]) -> None:
        path = self._cache_path(key)
        if path is None:
            return
        path.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def chat_json(
        self,
        *,
        system: str,
        user: str,
        prompt_version: str,
        word: str,
        context: str,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        key = cache_key(
            model=self.profile.model,
            prompt_version=prompt_version,
            word=word,
            context=context,
        )
        cached = self.get_cached(key)
        if cached is not None:
            return cached

        temp = self.profile.temperature if temperature is None else temperature
        url = self.profile.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.profile.model,
            "temperature": temp,
            "max_tokens": 256,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        headers: dict[str, str] = {}
        api_key = os.environ.get(self.profile.api_key_env) or os.environ.get("LEXAUDIT_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        last_err: Exception | None = None
        for attempt in range(self.profile.max_retries + 1):
            try:
                self._calls += 1
                with httpx.Client(timeout=self.profile.timeout_s, headers=headers) as client:
                    resp = client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                content = data["choices"][0]["message"]["content"]
                parsed = _extract_json(content)
                parsed["_raw"] = content
                parsed["_model"] = self.profile.model
                parsed["_prompt_version"] = prompt_version
                self.put_cached(key, parsed)
                return parsed
            except Exception as exc:
                last_err = exc
                time.sleep(1.5 * (attempt + 1))
        assert last_err is not None
        raise last_err


def _extract_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()
    # find first { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    data = json.loads(text)
    if not isinstance(data, dict):
        msg = "LLM response is not a JSON object"
        raise TypeError(msg)
    return data


def list_models(base_url: str = "http://127.0.0.1:8501/v1", timeout_s: float = 30.0) -> list[str]:
    url = base_url.rstrip("/") + "/models"
    with httpx.Client(timeout=timeout_s) as client:
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.json()
    return sorted(str(item.get("id") or item.get("name") or "") for item in data.get("data", []))
