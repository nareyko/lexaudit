"""Tier assignment rules."""

from __future__ import annotations

from lexaudit.core.classify import assign_tier


def test_tier_rules() -> None:
    assert assign_tier("ok", detectors=["hunspell"], count=10) is None
    assert assign_tier("proper", detectors=["proper"], count=1) is None
    assert assign_tier("invented", detectors=["hunspell"], count=5) == "confirmed"
    assert assign_tier("invented", detectors=["hunspell"], count=1) == "likely"
    assert assign_tier("morph-miss", detectors=["morph"], count=1) == "likely"
    assert assign_tier("calque", detectors=["calque"], count=1) == "likely"
    assert assign_tier("foreign", detectors=["foreign"], count=1) == "likely"
    assert assign_tier("suspect", detectors=["hunspell"], count=1) == "weak"
    assert assign_tier("suspect", detectors=["hunspell", "crosslocale"], count=1) == "likely"
