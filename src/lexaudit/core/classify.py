"""Classification pipeline - detector order fixed by tests."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Protocol

from lexaudit.core.types import ClassifiedWord, Tier, VocabOccurrence, VocabStatus

_HEADING_SCOPES = frozenset(
    {
        "title",
        "h1",
        "h2",
        "h3",
        "heading",
        "excerpt",
        "metadescription",
        "meta",
    }
)

DOMAIN_TERM_REASON = "domain-term-candidate"


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


def _scope_is_heading(scope: str) -> bool:
    s = scope.casefold()
    if s in _HEADING_SCOPES:
        return True
    return s.startswith("heading") or s.startswith("h1") or s.startswith("title")


def max_path_count(word: ClassifiedWord) -> int:
    """Best-effort per-page occurrence count from samples (+ global count fallback)."""
    if not word.samples:
        return word.count
    counts = Counter(s.path for s in word.samples)
    peak = max(counts.values()) if counts else 0
    # When all samples share one path, trust global count (samples are capped).
    if len(counts) == 1:
        return max(peak, word.count)
    return max(peak, 1)


def is_domain_term_candidate(word: ClassifiedWord) -> bool:
    """Unknown token repeated on a page or appearing in title/H1 scope."""
    if word.status in {"ok", "proper", "acronym", "template", "calque"}:
        return False
    if any(_scope_is_heading(s.scope) for s in word.samples):
        return True
    return max_path_count(word) >= 2


def apply_domain_term_candidates(words: list[ClassifiedWord]) -> list[ClassifiedWord]:
    """Tag recurring / heading unknowns as glossary candidates; demote false inventeds."""
    for word in words:
        if not is_domain_term_candidate(word):
            continue
        # Repeated technical terms should not stay as invented coinages.
        if word.status == "invented" and "neologism" in word.detectors:
            word.status = "suspect"
            word.tier = "weak"
        word.reason = DOMAIN_TERM_REASON
        word.detectors = sorted({*word.detectors, "domain-term"})
        if word.tier is None and word.status not in {"ok", "proper", "acronym", "template"}:
            word.tier = "weak"
    return words


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
                # Cleared or confirmed calque → stop.
                # invented stays open so a later calque rule can still win.
                # foreign / morph-miss / unsure → keep going for the same reason.
                if word.status in {"ok", "calque", "template", "proper", "acronym"}:
                    break
        if word.status == "ok":
            # Calque override (e.g. EN denseness): post-detectors that return None
            # for ok (morph/foreign/compound) are no-ops; override_ok calques flip.
            for det in post:
                updated = det(word)
                if updated is not None and updated.status != "ok":
                    word = updated
                    break
        elif word.status in {"foreign", "invented"}:
            # Final calque pass when foreign/neologism won earlier in the same post list.
            for det in post:
                updated = det(word)
                if updated is not None and updated.status == "calque":
                    word = updated
                    break

        word.tier = assign_tier(word.status, detectors=word.detectors, count=word.count)
        classified.append(word)

    apply_domain_term_candidates(classified)
    classified.sort(key=lambda w: (-w.count, w.normalized))
    return classified
