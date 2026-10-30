"""Property-based and fuzz tests using Hypothesis."""

from __future__ import annotations

import random

from hypothesis import given, settings
from hypothesis import strategies as st

from lexaudit.core.rank import rank_pages_by_suspects, rank_pages_weighted, rank_unique_key
from lexaudit.core.tokenize import DIGITS_ONLY_RE, casefold, strip_for_tokenize, tokenize
from lexaudit.core.types import ClassifiedWord, Tier, VocabSample, VocabStatus
from lexaudit.detectors.compound import _can_split


@given(
    raw=st.text(min_size=0, max_size=400),
    locale=st.sampled_from(["en", "de", "ru", "pl", "es", "sv", "uk"]),
    min_len=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=80, deadline=None)
def test_tokenize_invariants_never_crash(raw: str, locale: str, min_len: int) -> None:
    plain = strip_for_tokenize(raw)
    assert isinstance(plain, str)
    tokens = tokenize(raw, locale=locale, min_length=min_len)
    for tok in tokens:
        assert len(tok) >= min_len
        assert not DIGITS_ONLY_RE.match(tok)
        assert tok == casefold(tok, locale)


@given(
    word=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu")),
        min_size=0,
        max_size=30,
    ),
    parts=st.sets(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll",)),
            min_size=3,
            max_size=10,
        ),
        max_size=15,
    ),
)
@settings(max_examples=60, deadline=None)
def test_compound_split_invariants(word: str, parts: set[str]) -> None:
    res = _can_split(word, parts)
    assert isinstance(res, bool)
    if len(word) < 6:
        assert res is False


_WORD_STRAT = st.builds(
    ClassifiedWord,
    normalized=st.from_regex(r"[a-z\u0430-\u044f]{2,12}", fullmatch=True),
    surface=st.from_regex(r"[A-Za-z\u0410-\u042f\u0430-\u044f]{2,12}", fullmatch=True),
    count=st.integers(min_value=1, max_value=20),
    status=st.sampled_from(
        ["ok", "proper", "acronym", "template", "suspect", "foreign", "calque", "invented"]
    ),
    samples=st.lists(
        st.builds(
            VocabSample,
            path=st.sampled_from(["docs/a.md", "docs/b.md", "docs/c.md"]),
            scope=st.sampled_from(["title", "body", "bodyMarkdown"]),
        ),
        min_size=1,
        max_size=3,
    ),
    tier=st.sampled_from([None, "confirmed", "likely", "weak"]),
    reason=st.sampled_from(["", "hunspell", "english-leak", "latin-script-in-ru:mid-body"]),
)


@given(words=st.lists(_WORD_STRAT, min_size=0, max_size=25), seed=st.integers(0, 10000))
@settings(max_examples=50, deadline=None)
def test_rank_order_invariance_and_template_exclusion(
    words: list[ClassifiedWord], seed: int
) -> None:
    # Deduplicate by normalized so each word has a unique key as in classify_occurrences
    by_norm: dict[str, ClassifiedWord] = {}
    for w in words:
        by_norm[w.normalized] = w
    unique_words = list(by_norm.values())
    shuffled = list(unique_words)
    random.Random(seed).shuffle(shuffled)

    r1 = rank_pages_weighted(unique_words, locale="ru", needles=["orientir", "чеклист"])
    r2 = rank_pages_weighted(shuffled, locale="ru", needles=["orientir", "чеклист"])
    assert [(p.path, p.score, p.unique_suspects) for p in r1] == [
        (p.path, p.score, p.unique_suspects) for p in r2
    ]

    raw1 = rank_pages_by_suspects(unique_words, locale="ru", needles=["orientir", "чеклист"])
    raw2 = rank_pages_by_suspects(shuffled, locale="ru", needles=["orientir", "чеклист"])
    assert [(p.path, p.score, p.unique_suspects) for p in raw1] == [
        (p.path, p.score, p.unique_suspects) for p in raw2
    ]


def test_rank_monotonicity_when_adding_calque() -> None:
    base = [
        ClassifiedWord(
            normalized="xxyz",
            surface="xxyz",
            count=1,
            status=cast_status("suspect"),
            samples=[VocabSample("docs/a.md", "body")],
            tier=cast_tier("weak"),
        )
    ]
    before = rank_pages_weighted(base, locale="en")
    extra = [
        *base,
        ClassifiedWord(
            normalized="orientir",
            surface="orientir",
            count=2,
            status=cast_status("calque"),
            samples=[VocabSample("docs/a.md", "body")],
            tier=cast_tier("confirmed"),
        ),
    ]
    after = rank_pages_weighted(extra, locale="en")
    assert after[0].score > before[0].score
    assert rank_unique_key("чеклисте", locale="ru", needles=["чеклист"]) == rank_unique_key(
        "чеклист", locale="ru", needles=["чеклист"]
    )


def cast_status(s: str) -> VocabStatus:
    return s  # type: ignore[return-value]


def cast_tier(t: str) -> Tier:
    return t  # type: ignore[return-value]
