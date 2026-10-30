"""Classifier order, probes, tiers - mutation-dense."""

from __future__ import annotations

from lexaudit.core.aggregate import add_tokens
from lexaudit.core.classify import assign_tier, capitalize, classify_occurrences, probe_forms
from lexaudit.core.types import VocabOccurrence
from lexaudit.detectors.foreign import make_foreign_detector
from lexaudit.detectors.morph import make_morph_detector


class AllMissChecker:
    dict_id = "all-miss"

    def list_misspelled(self, words: list[str]) -> set[str]:
        return set(words)


class AllOkChecker:
    dict_id = "all-ok"

    def list_misspelled(self, words: list[str]) -> set[str]:
        return set()


class SelectiveChecker:
    dict_id = "sel"

    def __init__(self, bad: set[str]) -> None:
        self.bad = bad

    def list_misspelled(self, words: list[str]) -> set[str]:
        return {w for w in words if w in self.bad}


def test_capitalize_and_probe_forms() -> None:
    assert capitalize("rumpf") == "Rumpf"
    assert capitalize("") == ""
    assert capitalize("A") == "A"
    forms = probe_forms("rumpf", "Rumpf")
    assert "rumpf" in forms
    assert "Rumpf" in forms
    # surface == capitalized normalized → unique set
    forms2 = probe_forms("boat", "boat")
    assert forms2.count("boat") == 1 if "boat" in forms2 else True
    assert "Boat" in probe_forms("boat", "boat")


def test_tier_all_branches() -> None:
    assert assign_tier("ok", detectors=[], count=99) is None
    assert assign_tier("proper", detectors=["proper"], count=1) is None
    assert assign_tier("acronym", detectors=["acronym"], count=1) is None
    assert assign_tier("template", detectors=["template"], count=1) is None
    assert assign_tier("foreign", detectors=["foreign"], count=3) == "confirmed"
    assert assign_tier("calque", detectors=["calque"], count=3) == "confirmed"
    assert assign_tier("invented", detectors=["x"], count=3) == "confirmed"
    assert assign_tier("foreign", detectors=["foreign"], count=2) == "likely"
    assert assign_tier("morph-miss", detectors=["morph"], count=1) == "likely"
    assert assign_tier("suspect", detectors=["crosslocale"], count=1) == "likely"
    assert assign_tier("suspect", detectors=["hunspell"], count=1) == "weak"
    assert assign_tier("unsure", detectors=["hunspell"], count=9) == "weak"


def test_proper_acronym_template_short_circuit() -> None:
    occ: dict[str, VocabOccurrence] = {}
    add_tokens(
        occ,
        [
            {"normalized": "acmecorp", "surface": "AcmeCorp"},
            {"normalized": "epirb", "surface": "EPIRB"},
            {"normalized": "overview", "surface": "Overview"},
        ],
        path="a.md",
        scope="title",
    )

    class RecordingMiss(AllMissChecker):
        def __init__(self) -> None:
            self.probed: list[str] = []

        def list_misspelled(self, words: list[str]) -> set[str]:
            self.probed.extend(words)
            return set(words)

    checker = RecordingMiss()
    classified = classify_occurrences(
        occurrences=occ,
        proper={"acmecorp"},
        acronyms={"epirb"},
        templates={"overview"},
        checker=checker,
    )
    by = {c.normalized: c for c in classified}
    assert by["acmecorp"].status == "proper"
    assert by["acmecorp"].reason == "proper-names"
    assert by["acmecorp"].detectors == ["proper"]
    assert by["epirb"].status == "acronym"
    assert by["epirb"].reason == "acronyms"
    assert by["epirb"].detectors == ["acronym"]
    assert by["overview"].status == "template"
    assert by["overview"].reason == "section-marker"
    assert by["overview"].detectors == ["template"]
    assert by["acmecorp"].tier is None
    # Allowlisted norms must not be sent to hunspell (kills or→and on skip).
    probed_l = {w.casefold() for w in checker.probed}
    assert "acmecorp" not in probed_l
    assert "epirb" not in probed_l
    assert "overview" not in probed_l


def test_hunspell_ok_vs_suspect_and_sort() -> None:
    occ: dict[str, VocabOccurrence] = {}
    add_tokens(
        occ,
        [
            {"normalized": "boat", "surface": "boat"},
            {"normalized": "xxyzzyq", "surface": "xxyzzyq"},
            {"normalized": "zzzrare", "surface": "zzzrare"},
        ],
        path="a.md",
        scope="body",
    )
    # boost zzzrare count
    add_tokens(occ, [{"normalized": "zzzrare", "surface": "zzzrare"}], path="b.md", scope="body")
    classified = classify_occurrences(
        occurrences=occ,
        proper=set(),
        acronyms=set(),
        templates=set(),
        checker=SelectiveChecker({"xxyzzyq", "Xxyzzyq", "zzzrare", "Zzzrare"}),
    )
    by = {c.normalized: c for c in classified}
    assert by["boat"].status == "ok"
    assert by["boat"].reason == "hunspell"
    assert by["xxyzzyq"].status == "suspect"
    assert by["xxyzzyq"].reason == "unknown"
    assert by["xxyzzyq"].tier == "weak"
    # sorted by -count then normalized
    assert classified[0].normalized == "zzzrare"
    assert classified[0].count == 2


def test_post_detector_break_and_update() -> None:
    occ: dict[str, VocabOccurrence] = {}
    add_tokens(
        occ,
        [{"normalized": "offshore", "surface": "offshore"}],
        path="a.md",
        scope="body",
    )

    def keep_suspect(word):  # type: ignore[no-untyped-def]
        word.reason = "still-suspect"
        return word

    classified = classify_occurrences(
        occurrences=occ,
        proper=set(),
        acronyms=set(),
        templates=set(),
        checker=AllMissChecker(),
        post_detectors=[keep_suspect, make_foreign_detector("ru")],
    )
    assert classified[0].status == "foreign"
    assert "foreign" in classified[0].detectors


def test_maritime_proper_untouched_by_morph_post_detector() -> None:
    """I5-3: marina/offshore stay proper; morph never downgrades allowlist hits."""
    occ: dict[str, VocabOccurrence] = {}
    add_tokens(
        occ,
        [
            {"normalized": "marina", "surface": "Marina"},
            {"normalized": "offshore", "surface": "Offshore"},
        ],
        path="a.md",
        scope="body",
    )
    classified = classify_occurrences(
        occurrences=occ,
        proper={"marina", "offshore"},
        acronyms=set(),
        templates=set(),
        checker=AllMissChecker(),
        post_detectors=[make_morph_detector("de")],
    )
    by = {c.normalized: c for c in classified}
    assert by["marina"].status == "proper"
    assert by["offshore"].status == "proper"
    assert "morph" not in by["marina"].detectors
    assert "morph" not in by["offshore"].detectors


def test_post_none_skips() -> None:
    occ: dict[str, VocabOccurrence] = {}
    add_tokens(
        occ,
        [{"normalized": "xyzabcq", "surface": "xyzabcq"}],
        path="a.md",
        scope="body",
    )

    def noop(_word):  # type: ignore[no-untyped-def]
        return None

    classified = classify_occurrences(
        occurrences=occ,
        proper=set(),
        acronyms=set(),
        templates=set(),
        checker=AllMissChecker(),
        post_detectors=[noop],
    )
    assert classified[0].status == "suspect"


def test_all_ok_checker_marks_ok() -> None:
    occ: dict[str, VocabOccurrence] = {}
    add_tokens(
        occ,
        [{"normalized": "anything", "surface": "anything"}],
        path="a.md",
        scope="body",
    )
    classified = classify_occurrences(
        occurrences=occ,
        proper=set(),
        acronyms=set(),
        templates=set(),
        checker=AllOkChecker(),
    )
    assert classified[0].status == "ok"
