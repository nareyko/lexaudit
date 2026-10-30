"""Classification pipeline - detector order fixed by tests."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from lexaudit.core.types import ClassifiedWord, Tier, VocabOccurrence, VocabStatus


class DictChecker(Protocol):
    dict_id: str

    def list_misspelled(self, words: list[str]) -> set[str]: ...


DetectorFn = Callable[[ClassifiedWord], ClassifiedWord | None]


def capitalize(word: str) -> str:
    if not word:
        return word
    return word[0].upper() + word[1:]


def probe_forms(normalized: str, surface: str) -> list[str]:
    forms = {normalized, surface, capitalize(normalized)}
    return [f for f in forms if f]


def assign_tier(status: VocabStatus, *, detectors: list[str], count: int) -> Tier | None:
    """Assign confidence tier for anomaly statuses."""
    if status in {"ok", "proper", "acronym", "template"}:
        return None
    if status in {"foreign", "calque", "invented"} and count >= 3:
        return "confirmed"
    if status in {"foreign", "calque", "invented", "morph-miss"}:
        return "likely"
    if "crosslocale" in detectors:
        return "likely"
    return "weak"


def classify_occurrences(
    *,
    occurrences: dict[str, VocabOccurrence],
    proper: set[str],
    acronyms: set[str],
    templates: set[str],
    checker: DictChecker,
    post_detectors: list[DetectorFn] | None = None,
) -> list[ClassifiedWord]:
    """
    Detector order:
    1. proper / acronym / template allowlists
    2. hunspell → ok or candidate
    3. optional post-detectors (morph, compound, foreign, calque, ...)
    4. remainder → suspect
    """
    all_probes: set[str] = set()
    for occ in occurrences.values():
        if occ.normalized in proper or occ.normalized in acronyms or occ.normalized in templates:
            continue
        for p in probe_forms(occ.normalized, occ.surface):
            all_probes.add(p)

    misspelled = checker.list_misspelled(sorted(all_probes))
    post = post_detectors or []
    classified: list[ClassifiedWord] = []

    for occ in occurrences.values():
        detectors: list[str] = []
        reason = ""
        status: VocabStatus
        if occ.normalized in proper:
            status = "proper"
            detectors = ["proper"]
            reason = "proper-names"
        elif occ.normalized in acronyms:
            status = "acronym"
            detectors = ["acronym"]
            reason = "acronyms"
        elif occ.normalized in templates:
            status = "template"
            detectors = ["template"]
            reason = "section-marker"
        else:
            probes = probe_forms(occ.normalized, occ.surface)
            any_ok = any(p not in misspelled for p in probes)
            if any_ok:
                status = "ok"
                detectors = ["hunspell"]
                reason = "hunspell"
            else:
                status = "suspect"
                detectors = ["hunspell"]
                reason = "unknown"

        word = ClassifiedWord(
            normalized=occ.normalized,
            surface=occ.surface,
            count=occ.count,
            status=status,
            samples=list(occ.samples),
            reason=reason,
            detectors=detectors,
        )

        if word.status == "suspect":
            for det in post:
                updated = det(word)
                if updated is None:
                    continue
                word = updated
                # Cleared or confirmed calque/invented → stop.
                # foreign / morph-miss / unsure → keep going so later calque
                # can still override (e.g. RU denseness latin → foreign → calque).
                if word.status in {"ok", "calque", "invented", "template", "proper", "acronym"}:
                    break
        if word.status == "ok":
            # Calque override (e.g. EN denseness): post-detectors that return None
            # for ok (morph/foreign/compound) are no-ops; override_ok calques flip.
            for det in post:
                updated = det(word)
                if updated is not None and updated.status != "ok":
                    word = updated
                    break
        elif word.status == "foreign":
            # Final calque pass when foreign won earlier in the same post list.
            for det in post:
                updated = det(word)
                if updated is not None and updated.status == "calque":
                    word = updated
                    break

        word.tier = assign_tier(word.status, detectors=word.detectors, count=word.count)
        classified.append(word)

    classified.sort(key=lambda w: (-w.count, w.normalized))
    return classified
