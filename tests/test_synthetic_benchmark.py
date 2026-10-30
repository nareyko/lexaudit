"""Stratified 42-page European ablation benchmark across 7 locales (EN, DE, ES, PL, RU, SV, UK)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from lexaudit.config import load_config
from lexaudit.core.pipeline import run_locale_audit
from lexaudit.core.types import PageSuspectRank
from lexaudit.eval.metrics import needle_recall, page_at_k

ROOT = Path(__file__).resolve().parents[1]
SYNTH_CFG = ROOT / "examples" / "synthetic-demo" / "lexaudit.config.yaml"

UNSEEN_NEOLOGISMS: dict[str, str] = {
    "en": "dockwalkish",
    "de": "stegmanöverig",
    "es": "pantanalezca",
    "pl": "kejowaty",
    "ru": "пирсовыйосмотр",
    "sv": "bryggcheckig",
    "uk": "причальноогляд",
}


def _average_precision(ranked_pages: list[PageSuspectRank], gold_slugs: list[str]) -> float:
    hits = 0
    sum_prec = 0.0
    for idx, page in enumerate(ranked_pages, 1):
        if any(slug in page.path for slug in gold_slugs):
            hits += 1
            sum_prec += hits / idx
    return sum_prec / 3.0


def test_seven_european_locales_stratified_ablation(tmp_path: Path) -> None:
    cfg = load_config(SYNTH_CFG)
    assert set(cfg.locales) == {"en", "de", "es", "pl", "ru", "sv", "uk"}
    gold = list(cfg.gold_slugs)
    assert len(gold) == 21  # 3 defective pages * 7 locales

    for loc in cfg.locales:
        # Ablation A: Naive Hunspell raw count (no allowlists, no morph/compound, no calques)
        raw_cfg = replace(
            cfg,
            output_dir=tmp_path / "ablation_a",
            proper_names_path=None,
            acronyms_path=None,
            allowlist_path=None,
            enable_morph=False,
            enable_compound=False,
            enable_calque=False,
            rank_mode="raw",
            needles=[],
        )
        _raw_words, raw_pages, _ = run_locale_audit(
            raw_cfg, loc, freeze_generated_at="1970-01-01T00:00:00Z"
        )
        assert len(raw_pages) >= 5
        raw_ap = _average_precision(raw_pages, gold)
        raw_p3 = page_at_k(raw_pages, gold, k=3)["precision"]
        assert raw_p3 <= 0.34

        # Ablation C: Full lexaudit weighted pipeline
        w_cfg = replace(cfg, output_dir=tmp_path / "ablation_c")
        words, pages, _ = run_locale_audit(w_cfg, loc, freeze_generated_at="1970-01-01T00:00:00Z")
        w_ap = _average_precision(pages, gold)
        w_p2 = page_at_k(pages, gold, k=2)["precision"]
        w_p3 = page_at_k(pages, gold, k=3)["precision"]
        nr_known = needle_recall(cfg.needles, words, locale=loc)
        nr_open = needle_recall([*cfg.needles, UNSEEN_NEOLOGISMS[loc]], words, locale=loc)

        # Known rule-covered pages rank at the top, while unseen jargon vs unseen hapax
        # neologism produces a realistic non-100% P@3 (~0.67) and open-set recall (~0.67-0.83)
        assert w_p2 == 1.0, f"{loc} P@2={w_p2}"
        assert 0.60 <= w_p3 < 1.0, f"{loc} P@3={w_p3} should reflect unseen jargon boundary"
        assert w_ap > raw_ap + 0.30, f"{loc} MAP did not improve significantly: {w_ap} vs {raw_ap}"
        assert nr_known["recall"] == 1.0
        assert 0.65 <= nr_open["recall"] < 1.0
