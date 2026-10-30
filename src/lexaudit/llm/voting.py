"""Multipass LLM voting (N=3, temperature > 0)."""

from __future__ import annotations

from collections import Counter
from typing import Any

from lexaudit.llm.client import LlmClient
from lexaudit.llm.label import ALLOWED, load_label_prompt


def vote_label(
    clients: list[LlmClient],
    *,
    locale: str,
    word: str,
    context: str,
    path: str,
    temperature: float = 0.4,
    passes_per_client: int = 1,
) -> dict[str, Any]:
    """Run N labeled passes and return majority vote + stability stats."""
    system, user_template = load_label_prompt()
    user = (
        user_template.replace("{{locale}}", locale)
        .replace("{{word}}", word)
        .replace("{{context}}", context)
        .replace("{{path}}", path)
    )
    labels: list[str] = []
    raw: list[dict[str, Any]] = []
    for client in clients:
        for _ in range(passes_per_client):
            # Bust cache key slightly by appending pass salt into context for voting only
            parsed = client.chat_json(
                system=system,
                user=user,
                prompt_version="label-v1-vote",
                word=word,
                context=f"{context}||vote",
                temperature=temperature,
            )
            label = str(parsed.get("label") or "unsure")
            if label not in ALLOWED:
                label = "unsure"
            labels.append(label)
            raw.append(parsed)
    counts = Counter(labels)
    winner, win_n = counts.most_common(1)[0]
    stability = win_n / len(labels) if labels else 0.0
    return {
        "label": winner,
        "votes": len(labels),
        "stability": stability,
        "counts": dict(sorted(counts.items())),
        "raw": raw,
    }
