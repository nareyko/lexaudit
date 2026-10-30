from __future__ import annotations

from lexaudit.core.rank import word_rank_weight
from lexaudit.core.types import ClassifiedWord, VocabSample


def _word(norm: str, *, count: int = 1) -> ClassifiedWord:
    return ClassifiedWord(
        normalized=norm,
        surface=norm,
        count=count,
        status="suspect",
        samples=[VocabSample(path="x.md", scope="body")],
        reason="unknown",
        detectors=["hunspell"],
        tier="weak",
    )


def test_coinage_hapax_outranks_catalogue_code() -> None:
    coinage = word_rank_weight(_word("dockwalkish"), locale="en")
    code = word_rank_weight(_word("mnvdelta"), locale="en")
    assert coinage > code
    assert coinage >= 1.5
    assert code <= 0.1
