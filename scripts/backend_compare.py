#!/usr/bin/env python3
"""Compare hunspell binary path vs forced SpyllsChecker on the synthetic demo."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from lexaudit.config import load_config
from lexaudit.core.pipeline import run_locale_audit
from lexaudit.core.types import PageSuspectRank
from lexaudit.detectors import hunspell as hunspell_mod
from lexaudit.detectors.hunspell import SpyllsChecker, find_dict
from lexaudit.eval.metrics import page_at_k

ROOT = Path(__file__).resolve().parents[1]


def _average_precision(ranked_pages: list[PageSuspectRank], gold_slugs: list[str]) -> float:
    hits = 0
    sum_prec = 0.0
    for idx, page in enumerate(ranked_pages, 1):
        if any(slug in page.path for slug in gold_slugs):
            hits += 1
            sum_prec += hits / idx
    return sum_prec / 3.0


def run_with_backend(name: str, force_spylls: bool) -> dict[str, Any]:
    cfg = load_config(ROOT / "examples" / "synthetic-demo" / "lexaudit.config.yaml")
    gold = list(cfg.gold_slugs)
    orig = hunspell_mod.resolve_checker

    def _forced(locale: str, hcfg: Any) -> Any:
        found = find_dict(locale, hcfg)
        if found is None:
            return orig(locale, hcfg)
        dict_id, dict_path = found
        if force_spylls:
            return SpyllsChecker(dict_id=dict_id, dict_path=dict_path)
        return orig(locale, hcfg)

    hunspell_mod.resolve_checker = _forced  # type: ignore[assignment]
    t0 = time.perf_counter()
    maps: list[float] = []
    p2s: list[float] = []
    p3s: list[float] = []
    status_sets: dict[str, set[str]] = {}
    try:
        for loc in ("en",):
            words, pages, _ = run_locale_audit(cfg, loc, freeze_generated_at="1970-01-01T00:00:00Z")
            maps.append(_average_precision(pages, gold))
            p2s.append(float(page_at_k(pages, gold, k=2)["precision"]))
            p3s.append(float(page_at_k(pages, gold, k=3)["precision"]))
            status_sets[loc] = {f"{w.normalized}:{w.status}" for w in words}
    finally:
        hunspell_mod.resolve_checker = orig  # type: ignore[assignment]
    elapsed = time.perf_counter() - t0
    return {
        "backend": name,
        "p_at_2": round(sum(p2s) / len(p2s), 4),
        "p_at_3": round(sum(p3s) / len(p3s), 4),
        "map": round(sum(maps) / len(maps), 4),
        "seconds": round(elapsed, 3),
        "status_sets": {k: sorted(v) for k, v in status_sets.items()},
    }


def main() -> int:
    a = run_with_backend("default_resolve", force_spylls=False)
    b = run_with_backend("spylls", force_spylls=True)
    sa = set(a["status_sets"].get("en", []))
    sb = set(b["status_sets"].get("en", []))
    overlap = len(sa & sb) / max(1, len(sa | sb))
    out = {
        "default_resolve": {k: v for k, v in a.items() if k != "status_sets"},
        "spylls": {k: v for k, v in b.items() if k != "status_sets"},
        "en_status_jaccard": round(overlap, 4),
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    if overlap < 0.5:
        print("WARN: large backend disagreement on EN statuses", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
