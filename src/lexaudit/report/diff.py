"""Baseline diff for report.json files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _word_index(doc: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    idx: dict[tuple[str, str], dict[str, Any]] = {}
    for loc in doc.get("locales") or []:
        locale = loc["locale"]
        for w in loc.get("words") or []:
            idx[(locale, w["norm"])] = w
    return idx


def diff_reports(baseline: Path, current: Path) -> dict[str, Any]:
    base = json.loads(baseline.read_text(encoding="utf-8"))
    cur = json.loads(current.read_text(encoding="utf-8"))
    bi = _word_index(base)
    ci = _word_index(cur)
    new = []
    gone = []
    tier_changed = []
    for key, w in sorted(ci.items()):
        if key not in bi:
            new.append(
                {"locale": key[0], "norm": key[1], "status": w.get("status"), "tier": w.get("tier")}
            )
        else:
            old = bi[key]
            if old.get("tier") != w.get("tier") or old.get("status") != w.get("status"):
                tier_changed.append(
                    {
                        "locale": key[0],
                        "norm": key[1],
                        "from_status": old.get("status"),
                        "to_status": w.get("status"),
                        "from_tier": old.get("tier"),
                        "to_tier": w.get("tier"),
                    }
                )
    for key, w in sorted(bi.items()):
        if key not in ci:
            gone.append(
                {"locale": key[0], "norm": key[1], "status": w.get("status"), "tier": w.get("tier")}
            )
    return {
        "new": new,
        "gone": gone,
        "tier_changed": tier_changed,
        "counts": {
            "new": len(new),
            "gone": len(gone),
            "tier_changed": len(tier_changed),
        },
    }
