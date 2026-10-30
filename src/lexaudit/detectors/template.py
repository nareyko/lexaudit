"""Template / section-marker detector (allowlist already covers most)."""

from __future__ import annotations

from lexaudit.core.types import ClassifiedWord


def make_template_detector(markers: set[str]) -> object:
    folded = set(markers)

    def detect(word: ClassifiedWord) -> ClassifiedWord | None:
        if word.normalized in folded:
            word.status = "template"
            word.reason = "section-marker"
            word.detectors = sorted({*word.detectors, "template"})
            word.tier = None
            return word
        return None

    return detect
