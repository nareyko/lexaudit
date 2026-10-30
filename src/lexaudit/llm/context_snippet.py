"""Read-only corpus snippets for LLM labeling context."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _extract_translation_scope(data: dict[str, Any], locale: str, scope: str) -> str | None:
    translations = data.get("translations")
    if isinstance(translations, dict):
        block = translations.get(locale)
        if isinstance(block, dict):
            text = block.get(scope)
            if isinstance(text, str) and text.strip():
                return text
    return None


def _extract_pack_row_scope(data: dict[str, Any], locale: str, scope: str) -> str | None:
    rows = data.get("packRows") or data.get("rows") or []
    if not isinstance(rows, list):
        return None
    for row in rows:
        if not isinstance(row, dict) or row.get("locale") != locale:
            continue
        payload = row.get("payload") or row
        if isinstance(payload, dict):
            text = payload.get(scope)
            if isinstance(text, str) and text.strip():
                return text
    return None


def load_scope_text(repo_root: Path, path: str, scope: str, locale: str) -> str | None:
    """Load reader-facing text for a report sample path + scope (read-only)."""
    full = repo_root / path
    if not full.is_file():
        return None
    if full.suffix.lower() in (".md", ".markdown"):
        try:
            raw = full.read_text(encoding="utf-8")
        except OSError:
            return None
        return raw if raw.strip() else None
    try:
        data = json.loads(full.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    found = _extract_translation_scope(data, locale, scope) or _extract_pack_row_scope(
        data, locale, scope
    )
    if found is not None:
        return found
    direct = data.get(scope)
    return direct if isinstance(direct, str) else None


def format_context_snippet(
    *,
    path: str,
    scope: str,
    text: str,
    word: str,
    surface: str,
    radius: int = 48,
) -> str:
    """Gold-style context line: path#scope: ...snippet..."""
    hay = text
    needle = surface or word
    idx = hay.casefold().find(needle.casefold())
    if idx < 0:
        idx = hay.casefold().find(word.casefold())
    if idx < 0:
        snippet = hay[: min(len(hay), radius * 2)]
    else:
        start = max(0, idx - radius)
        end = min(len(hay), idx + max(len(needle), len(word)) + radius)
        snippet = hay[start:end]
    snippet = snippet.replace("\n", " ").strip()
    return f"{path}#{scope}: ...{snippet}..."
