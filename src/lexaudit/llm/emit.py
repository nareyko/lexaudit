"""Write LLM label batches under output_dir only (never corpus sources)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_llm_labels(
    out_path: Path,
    *,
    locale: str,
    labels: list[dict[str, Any]],
    page_paths: list[str],
    profile: str,
    tiers: str,
    stats: dict[str, int],
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "locale": locale,
        "profile": profile,
        "tiers": tiers,
        "top_page_paths": page_paths,
        "stats": stats,
        "labels": labels,
    }
    out_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out_path
