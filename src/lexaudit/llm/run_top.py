"""Run LLM labels on a top-page / tier slice (detection-only, cached)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lexaudit.config import LexauditConfig, LlmProfile
from lexaudit.core.types import ClassifiedWord
from lexaudit.llm.client import LlmClient, list_models
from lexaudit.llm.label import label_word
from lexaudit.llm.top_slice import LabelTarget, select_label_targets


def localai_is_up(base_url: str = "http://127.0.0.1:8501/v1", timeout_s: float = 3.0) -> bool:
    try:
        list_models(base_url, timeout_s=timeout_s)
        return True
    except Exception:
        return False


def resolve_llm_profile(cfg: LexauditConfig, profile_name: str) -> LlmProfile:
    profile = cfg.llm_profiles.get(profile_name)
    if profile is None:
        known = ", ".join(sorted(cfg.llm_profiles)) or "(none in config)"
        msg = f"unknown llm profile {profile_name!r}; config has: {known}"
        raise KeyError(msg)
    if not profile.model:
        msg = f"llm profile {profile_name!r} has empty model"
        raise ValueError(msg)
    return profile


def cache_dir_for(cfg: LexauditConfig) -> Path:
    if cfg.llm_cache_dir is not None:
        return cfg.llm_cache_dir
    return cfg.output_dir / "llm-cache"


def label_result_row(
    target: LabelTarget,
    locale: str,
    *,
    llm: dict[str, object],
) -> dict[str, Any]:
    hint = str(llm.get("rationale") or llm.get("hint") or "")[:200]
    conf_raw = llm.get("confidence")
    confidence = float(conf_raw) if isinstance(conf_raw, (int, float)) else 0.0
    return {
        "word": target.word,
        "norm": target.normalized,
        "locale": locale,
        "path": target.path,
        "scope": target.scope,
        "tier": target.tier,
        "status": target.status,
        "class": str(llm.get("label") or "unsure"),
        "hint": hint,
        "confidence": confidence,
        "model": str(llm.get("model") or ""),
        "prompt_version": str(llm.get("prompt_version") or ""),
    }


def run_top_labels(
    cfg: LexauditConfig,
    locale: str,
    words: list[ClassifiedWord],
    *,
    top_pages: int,
    top_words: int,
    tiers_raw: str,
    profile_name: str,
    client: LlmClient | None = None,
) -> tuple[list[dict[str, Any]], list[str], dict[str, int]]:
    from lexaudit.llm.top_slice import parse_tier_filter

    tier_set = parse_tier_filter(tiers_raw)
    targets, page_paths = select_label_targets(
        words,
        locale=locale,
        top_pages=top_pages,
        top_words=top_words,
        tiers=tier_set,
        cfg=cfg,
    )
    stats = {"targets": len(targets), "llm_calls": 0, "cache_hits": 0}
    if not targets:
        return [], page_paths, stats

    llm_client = client
    if llm_client is None:
        profile = resolve_llm_profile(cfg, profile_name)
        llm_client = LlmClient(profile, cache_dir=cache_dir_for(cfg))

    rows: list[dict[str, Any]] = []
    for target in targets:
        llm_out = label_word(
            llm_client,
            locale=locale,
            word=target.word,
            context=target.context,
            path=target.path,
        )
        rows.append(label_result_row(target, locale, llm=llm_out))
    stats["llm_calls"] = llm_client.calls
    stats["cache_hits"] = llm_client.cache_hits
    return rows, page_paths, stats
