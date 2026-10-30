"""Assemble post-classification detectors for a locale audit run."""

from __future__ import annotations

from typing import cast

from lexaudit.config import LexauditConfig
from lexaudit.core.classify import DetectorFn
from lexaudit.detectors.calque import (
    default_calque_rules_dir,
    load_calque_rules,
    make_calque_detector,
)
from lexaudit.detectors.compound import make_compound_detector
from lexaudit.detectors.english_leak import make_english_leak_detector
from lexaudit.detectors.foreign import make_foreign_detector
from lexaudit.detectors.morph import make_morph_detector


def build_post_detectors(
    cfg: LexauditConfig,
    locale: str,
    compound_known: set[str],
) -> tuple[list[DetectorFn], dict[str, int]]:
    """Return detector chain and zeroed stats keys for report.json."""
    dets: list[DetectorFn] = []
    stats: dict[str, int] = {}
    if cfg.enable_morph:
        dets.append(make_morph_detector(locale))
        stats["morph"] = 0
    if cfg.enable_compound:
        dets.append(make_compound_detector(locale, compound_known))
        stats["compound"] = 0
    if cfg.enable_foreign:
        dets.append(cast(DetectorFn, make_foreign_detector(locale)))
        stats["foreign"] = 0
        dets.append(cast(DetectorFn, make_english_leak_detector(locale)))
        stats["english_leak"] = 0
    if cfg.enable_calque:
        rules_dir = cfg.calque_rules_dir or default_calque_rules_dir()
        if rules_dir is not None:
            rules = load_calque_rules(rules_dir)
            dets.append(make_calque_detector(locale, rules))
            stats["calque"] = 0
    return dets, stats
