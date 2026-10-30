"""Exact-value tests for page ranking: every weight, boundary and ordering is pinned."""

from __future__ import annotations

import pytest

from lexaudit.core import rank
from lexaudit.core.rank import (
    DEFAULT_RANK_WEIGHTS,
    RankWeights,
    _foreign_weight_for_word,
    _is_meta_foreign_scope,
    _needle_matches,
    _ru_calque_stem,
    filter_pages_by_sources,
    foreign_context_from_reason,
    normalize_source_filter,
    page_source_bucket,
    rank_pages,
    rank_pages_by_suspects,
    rank_pages_weighted,
    rank_unique_key,
    word_rank_weight,
)
from lexaudit.core.types import ClassifiedWord, PageSuspectRank, VocabSample

W = DEFAULT_RANK_WEIGHTS


def cw(
    norm: str,
    status: str = "suspect",
    *,
    tier: str | None = None,
    count: int = 2,
    reason: str = "",
    surface: str | None = None,
    samples: list[tuple[str, str]] | None = None,
) -> ClassifiedWord:
    return ClassifiedWord(
        normalized=norm,
        surface=surface or norm,
        count=count,
        status=status,  # type: ignore[arg-type]
        samples=[VocabSample(path=p, scope=s) for p, s in (samples or [("a.md", "body")])],
        tier=tier,  # type: ignore[arg-type]
        reason=reason,
    )


def test_default_weights_exact() -> None:
    assert (
        W.calque,
        W.needle,
        W.foreign_body_ru,
        W.foreign_meta,
        W.suspect_confirmed,
        W.suspect_likely,
        W.suspect_weak_hapax,
    ) == (8.0, 6.0, 2.0, 0.2, 3.0, 1.5, 0.1)
    assert {
        "suspect",
        "foreign",
        "calque",
        "invented",
        "morph-miss",
        "unsure",
    } == rank.SUSPECT_STATUSES


@pytest.mark.parametrize("suffix", rank._RU_STEM_SUFFIXES)
def test_every_ru_suffix_is_stripped(suffix: str) -> None:
    assert _ru_calque_stem("абвгд" + suffix) == "абвгд"


def test_ru_stem_boundaries() -> None:
    assert _ru_calque_stem("\u0422\u0415\u0421\u0422") == "тест"  # short: only casefolded
    assert _ru_calque_stem("абвы") == "абвы"  # len 4 < 5
    assert _ru_calque_stem("абвгы") == "абвг"  # len 5 > 1+3, stripped
    assert _ru_calque_stem("абвгд") == "абвгд"  # no suffix at all
    assert _ru_calque_stem("абвом") == "абво"  # len 5 == len("ом")+3: "ом" skipped, "м" used
    assert _ru_calque_stem("абвгам") == "абвг"  # len 6 > 5, stripped
    assert _ru_calque_stem("\u0410\u0411\u0412\u0413\u0410\u041c") == "абвг"  # casefolds first


@pytest.mark.parametrize(
    ("path", "bucket"),
    [
        ("x/pending-academy-articles/a.json", "academy"),
        ("x/pending-model-packs/a.json", "model_pack"),
        ("docs/readme.txt", "docs"),
        ("a/README.MD", "docs"),
        ("a/b.markdown", "docs"),
        ("a\\b\\pending-academy-articles\\c", "academy"),
        ("a/b.json", None),
    ],
)
def test_page_source_bucket(path: str, bucket: str | None) -> None:
    assert page_source_bucket(path) == bucket


def test_normalize_source_filter() -> None:
    assert normalize_source_filter(None) is None
    assert normalize_source_filter([]) is None
    assert normalize_source_filter(["  ", ""]) is None
    assert normalize_source_filter([" Academy "]) == {"academy"}
    assert normalize_source_filter(["packs"]) == {"packs", "model_pack"}
    assert normalize_source_filter(["model_pack"]) == {"model_pack", "packs"}
    assert normalize_source_filter(["files"]) == {"files", "docs"}
    assert normalize_source_filter(["md"]) == {"md", "docs"}
    assert normalize_source_filter(["docs"]) == {"docs", "files", "md"}


def test_filter_pages_by_sources() -> None:
    pages = [
        PageSuspectRank("docs/a.md", 1, [], 1.0),
        PageSuspectRank("x/pending-academy-articles/b", 1, [], 1.0),
        PageSuspectRank("other.json", 1, [], 1.0),
    ]
    assert filter_pages_by_sources(pages, None) is pages
    assert [p.path for p in filter_pages_by_sources(pages, ["docs"])] == ["docs/a.md"]
    assert [p.path for p in filter_pages_by_sources(pages, ["academy"])] == [
        "x/pending-academy-articles/b"
    ]
    assert filter_pages_by_sources(pages, ["nothing"]) == []


def test_needle_matches() -> None:
    assert _needle_matches("orientir", "orientir")
    assert _needle_matches("orientirs", "ORIENTIR")
    assert _needle_matches("xorientirx", "orientir")  # substring
    assert _needle_matches("orientir", "  orientir  ")
    assert not _needle_matches("other", "orientir")
    assert not _needle_matches("anything", "")
    assert not _needle_matches("anything", "   ")


def test_rank_unique_key() -> None:
    assert rank_unique_key("Word", locale="en") == "word"
    assert rank_unique_key("абвгам", locale="ru") == "s:абвг"
    assert rank_unique_key("абвгам", locale="uk") == "s:абвг"
    assert rank_unique_key("абвгам", locale="de") == "абвгам"
    assert rank_unique_key("orientirs", locale="en", needles=["orientir"]) == "n:orientir"
    # shortest needle wins; ties broken alphabetically
    assert rank_unique_key("zorientirx", locale="en", needles=["orientir", "orient"]) == "n:orient"
    assert rank_unique_key("abc", locale="en", needles=["b", "a"]) == "n:a"
    assert rank_unique_key("other", locale="en", needles=["orientir"]) == "other"


@pytest.mark.parametrize(
    ("scope", "meta"),
    [
        ("title", True),
        ("TITLE", True),
        ("excerpt", True),
        ("metaDescription", True),
        ("meta-x", True),
        ("heading-2", True),
        ("h1", True),
        ("h2", True),
        ("h3", True),
        ("quotes", True),
        ("my-url", True),
        ("body", False),
        ("bodyMarkdown", False),
        ("h4", False),
    ],
)
def test_is_meta_foreign_scope(scope: str, meta: bool) -> None:
    assert _is_meta_foreign_scope(scope) is meta


def test_foreign_context_from_reason() -> None:
    assert foreign_context_from_reason("english-leak") == "english-leak"
    assert foreign_context_from_reason("foreign:mid-body") == "mid-body"
    assert foreign_context_from_reason("a:b:heading") == "heading"
    assert foreign_context_from_reason("plain") is None
    assert foreign_context_from_reason("") is None


def test_weights_object_is_used_not_defaults() -> None:
    w = RankWeights(
        calque=80,
        needle=60,
        foreign_body_ru=20,
        foreign_meta=2,
        suspect_confirmed=30,
        suspect_likely=15,
        suspect_weak_hapax=1,
    )
    assert word_rank_weight(cw("x", "calque"), locale="en", weights=w) == 80
    assert word_rank_weight(cw("x", "suspect", tier="confirmed"), locale="en", weights=w) == 30
    assert word_rank_weight(cw("x", "suspect", tier="likely"), locale="en", weights=w) == 15
    assert word_rank_weight(cw("x", "unsure"), locale="en", weights=w) == 1
    assert word_rank_weight(cw("x", "foreign", reason="a:heading"), locale="en", weights=w) == 2
    assert word_rank_weight(cw("x", "suspect", tier="weak", count=1), locale="en", weights=w) == 1
    assert (
        word_rank_weight(cw("abc", "suspect", tier="weak"), locale="en", weights=w)
        == 1  # short word
    )
    assert (
        word_rank_weight(cw("abcdef", "suspect", tier="weak", count=5), locale="en", weights=w)
        == 15
    )
    assert (
        word_rank_weight(cw("zneedle", "suspect"), locale="en", weights=w, needles=["needle"]) == 60
    )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("template", 0.0),
        ("ok", 0.0),
        ("proper", 0.0),
        ("acronym", 0.0),
        ("calque", 8.0),
        ("invented", 8.0),
        ("morph-miss", 0.1),
        ("unsure", 0.1),
    ],
)
def test_word_rank_weight_by_status(status: str, expected: float) -> None:
    assert word_rank_weight(cw("word", status), locale="en") == expected


def test_suspect_tiers_and_hapax_boundaries() -> None:
    f = lambda **kw: word_rank_weight(cw(**kw), locale="en")  # noqa: E731
    assert f(norm="longword", tier="confirmed") == 3.0
    assert f(norm="longword", tier="likely") == 1.5
    assert f(norm="abc", tier="weak", count=5) == 0.1  # len <= 3
    assert f(norm="abcd", tier="weak", count=5) == 1.5  # len 4, not hapax
    assert f(norm="abcd", tier="weak", count=1) == 0.1  # hapax
    assert f(norm="abcd", tier="weak", count=2) == 1.5
    assert f(norm="abcd", tier=None, count=3) == 1.5


def test_needle_beats_everything_and_requires_needles() -> None:
    word = cw("orientir", "calque")
    assert word_rank_weight(word, locale="en", needles=["orientir"]) == 6.0
    assert word_rank_weight(word, locale="en", needles=[]) == 8.0
    assert word_rank_weight(word, locale="en", needles=["zzz"]) == 8.0
    assert word_rank_weight(cw("orientir", "template"), locale="en", needles=["orientir"]) == 0.0


@pytest.mark.parametrize(
    ("locale", "reason", "surface", "norm", "scopes", "expected"),
    [
        ("de", "english-leak", "of", "of", ["body"], 0.2),
        ("ru", "x:heading", "foo", "foo", ["body"], 0.2),
        ("ru", "x:quotes", "foo", "foo", ["body"], 0.2),
        ("ru", "x:url", "foo", "foo", ["body"], 0.2),
        ("ru", "x:proper-seed", "foo", "foo", ["body"], 0.2),
        ("ru", "x:mid-body", "foo", "foo", ["body"], 2.0),
        ("en", "x:mid-body", "foo", "foo", ["body"], 2.0),  # falls to has_body
        ("en", "x:mid-body", "foo", "foo", ["title"], 0.2),
        ("ru", "x:mid-body", "123", "123", ["title"], 0.2),  # no latin letters
        ("ru", "", "Boat", "boat", ["body"], 0.2),  # Title Case brand
        ("ru", "", "boat", "boat", ["body"], 2.0),
        ("ru", "", "boat", "boat", ["bodyMarkdown"], 2.0),
        ("ru", "", "лодка", "лодка", ["body"], 2.0),  # has_body, no latin -> final has_body
        ("ru", "", "лодка", "лодка", ["title"], 0.2),
        ("en", "", "boat", "boat", ["title", "body"], 0.2),  # meta and body -> meta
        ("en", "", "boat", "boat", ["body"], 2.0),
        ("en", "", "boat", "boat", ["bodyMarkdown"], 2.0),
        ("en", "", "boat", "boat", ["other"], 0.2),
        ("en", "", "boat", "boat", [], 0.2),
        ("de", "", "Boat", "boat", ["body"], 2.0),  # brand rule is RU-only
    ],
)
def test_foreign_weight_matrix(
    locale: str,
    reason: str,
    surface: str,
    norm: str,
    scopes: list[str],
    expected: float,
) -> None:
    word = cw(
        norm,
        "foreign",
        reason=reason,
        surface=surface,
        samples=[("a.md", s) for s in scopes] or [],
    )
    word.samples = [VocabSample("a.md", s) for s in scopes]
    assert _foreign_weight_for_word(word, locale, W) == expected
    assert word_rank_weight(word, locale=locale) == expected


def test_raw_ranking_counts_unique_keys_and_sorts() -> None:
    words = [
        cw("alpha", samples=[("p2.md", "body"), ("p1.md", "body")]),
        cw("beta", samples=[("p2.md", "body")]),
        cw("gamma", "ok", samples=[("p3.md", "body")]),  # ignored
        cw("gamma2", "template", samples=[("p3.md", "body")]),  # ignored
    ]
    ranked = rank_pages_by_suspects(words)
    assert [(r.path, r.unique_suspects, r.score) for r in ranked] == [
        ("p2.md", 2, 2.0),
        ("p1.md", 1, 1.0),
    ]
    assert ranked[0].sample_words == ["alpha", "beta"]


def test_raw_ranking_collapses_variants_and_limits_samples() -> None:
    words = [
        cw("orientir", samples=[("a.md", "body")]),
        cw("orientirs", samples=[("a.md", "body")]),
        cw("other1", samples=[("a.md", "body")]),
        cw("other2", samples=[("a.md", "body")]),
    ]
    r = rank_pages_by_suspects(words, needles=["orientir", " ", ""], sample_words=2)[0]
    assert r.unique_suspects == 3  # needle family collapsed
    assert r.sample_words == ["orientir", "other1"]
    ru = rank_pages_by_suspects(
        [cw("абвгам", samples=[("a.md", "body")]), cw("абвгом", samples=[("a.md", "body")])],
        locale="ru",
    )[0]
    assert ru.unique_suspects == 1


def test_raw_ranking_tie_breaks_by_path_and_filters_sources() -> None:
    words = [
        cw("a1", samples=[("docs/b.md", "body")]),
        cw("a2", samples=[("docs/a.md", "body")]),
        cw("a3", samples=[("x.json", "body")]),
    ]
    assert [r.path for r in rank_pages_by_suspects(words)] == ["docs/a.md", "docs/b.md", "x.json"]
    assert [r.path for r in rank_pages_by_suspects(words, source_filter=["docs"])] == [
        "docs/a.md",
        "docs/b.md",
    ]


def test_weighted_scores_dedupe_by_unique_key() -> None:
    words = [
        cw("orientir", "calque", samples=[("a.md", "body")]),
        cw("orientirs", "calque", samples=[("a.md", "body")]),  # same needle key: scored once
        cw("keel", "suspect", tier="confirmed", samples=[("a.md", "body"), ("b.md", "body")]),
    ]
    ranked = rank_pages_weighted(words, needles=["orientir"])
    assert [(r.path, r.score, r.unique_suspects) for r in ranked] == [
        ("a.md", 9.0, 2),
        ("b.md", 3.0, 1),
    ]


def test_weighted_scores_without_needles_count_each_variant() -> None:
    words = [
        cw("alpha", "calque", samples=[("a.md", "body")]),
        cw("beta", "calque", samples=[("a.md", "body")]),
    ]
    assert rank_pages_weighted(words)[0].score == 16.0


def test_weighted_rounding_order_and_samples() -> None:
    words = [
        cw("xaaa", "foreign", reason="x:heading", samples=[("a.md", "title")]),
        cw("xbbb", "foreign", reason="x:heading", samples=[("a.md", "title")]),
        cw("xccc", "foreign", reason="x:heading", samples=[("a.md", "title")]),
    ]
    r = rank_pages_weighted(words, sample_words=2)[0]
    assert r.score == 0.6  # 3 * 0.2 rounded to 4 places, no float noise
    assert r.sample_words == ["xaaa", "xbbb"]
    assert rank_pages_weighted([]) == []


def test_weighted_sorting_ties() -> None:
    words = [
        cw("a1", "calque", samples=[("b.md", "body")]),
        cw("a2", "calque", samples=[("a.md", "body")]),
        cw("a3", "suspect", tier="confirmed", samples=[("b.md", "body")]),
        cw("a4", "suspect", tier="confirmed", samples=[("c.md", "body")]),
        cw("a5", "suspect", tier="likely", samples=[("c.md", "body")]),
        cw("a6", "suspect", tier="likely", samples=[("c.md", "body")]),
    ]
    got = [(r.path, r.score) for r in rank_pages_weighted(words)]
    assert got == [("b.md", 11.0), ("a.md", 8.0), ("c.md", 6.0)]


def test_weighted_equal_score_prefers_more_unique_then_path() -> None:
    words = [
        cw("w1", "suspect", tier="likely", samples=[("z.md", "body")]),
        cw("w2", "suspect", tier="likely", samples=[("z.md", "body")]),
        cw("w3", "suspect", tier="confirmed", samples=[("y.md", "body")]),
        cw("w4", "suspect", tier="confirmed", samples=[("x.md", "body")]),
    ]
    assert [r.path for r in rank_pages_weighted(words)] == ["z.md", "x.md", "y.md"]


def test_weighted_require_needle_and_source_filter() -> None:
    words = [
        cw("orientir", "calque", samples=[("docs/a.md", "body")]),
        cw("other", "calque", samples=[("docs/b.md", "body")]),
        cw("orientirs", "calque", samples=[("x.json", "body")]),
    ]
    got = rank_pages_weighted(words, needles=["orientir"], require_needle=True)
    assert sorted(r.path for r in got) == ["docs/a.md", "x.json"]
    assert len(rank_pages_weighted(words, needles=["orientir"], require_needle=False)) == 3
    assert len(rank_pages_weighted(words, needles=[], require_needle=True)) == 3
    only_docs = rank_pages_weighted(words, source_filter=["docs"])
    assert sorted(r.path for r in only_docs) == ["docs/a.md", "docs/b.md"]
    assert rank_pages_weighted(words, needles=["  "], require_needle=True)[0].score == 8.0


def test_rank_pages_dispatch() -> None:
    words = [cw("alpha", "calque", samples=[("a.md", "body")])]
    assert rank_pages(words, mode="raw")[0].score == 1.0
    assert rank_pages(words, mode="weighted")[0].score == 8.0
    assert rank_pages(words)[0].score == 8.0
    custom = RankWeights(calque=5.0)
    assert rank_pages(words, weights=custom)[0].score == 5.0
    assert rank_pages(words, mode="raw", sample_words=0)[0].sample_words == []
    assert rank_pages(words, locale="ru", needles=["alp"], require_needle=True)[0].score == 6.0
    assert rank_pages(words, source_filter=["academy"]) == []
    assert rank_pages(words, mode="raw", source_filter=["academy"]) == []
