"""Aggregate + page rank mutation coverage."""

from __future__ import annotations

from lexaudit.core.aggregate import add_tokens
from lexaudit.core.rank import (
    SUSPECT_STATUSES,
    filter_pages_by_sources,
    page_source_bucket,
    rank_pages,
    rank_pages_by_suspects,
    rank_pages_weighted,
    rank_unique_key,
)
from lexaudit.core.types import ClassifiedWord, PageSuspectRank, VocabOccurrence, VocabSample
from lexaudit.curated.queue import append_pending_from_rank, load_curated, save_curated


def test_add_tokens_count_samples_and_dedupe() -> None:
    occ: dict[str, VocabOccurrence] = {}
    add_tokens(
        occ,
        [{"normalized": "boat", "surface": "Boat"}],
        path="a.md",
        scope="body",
        max_samples=2,
    )
    add_tokens(
        occ,
        [{"normalized": "boat", "surface": "boat"}],
        path="a.md",
        scope="body",
        max_samples=2,
    )
    add_tokens(
        occ,
        [{"normalized": "boat", "surface": "boat"}],
        path="b.md",
        scope="title",
        max_samples=2,
    )
    add_tokens(
        occ,
        [{"normalized": "boat", "surface": "boat"}],
        path="c.md",
        scope="body",
        max_samples=2,
    )
    assert occ["boat"].count == 4
    assert len(occ["boat"].samples) == 2  # capped
    assert occ["boat"].samples[0].path == "a.md"
    assert occ["boat"].samples[1].path == "b.md"


def test_add_tokens_default_max_samples_is_five() -> None:
    """Default max_samples=5 (mutmut number +1 must fail)."""
    occ: dict[str, VocabOccurrence] = {}
    for i in range(6):
        add_tokens(
            occ,
            [{"normalized": "keel", "surface": "keel"}],
            path=f"p{i}.md",
            scope="body",
        )
    assert occ["keel"].count == 6
    assert len(occ["keel"].samples) == 5


def test_add_tokens_dedupe_requires_path_and_scope() -> None:
    """Same path + different scope is a new sample (and≠or)."""
    occ: dict[str, VocabOccurrence] = {}
    add_tokens(
        occ,
        [{"normalized": "mast", "surface": "mast"}],
        path="same.md",
        scope="body",
        max_samples=5,
    )
    add_tokens(
        occ,
        [{"normalized": "mast", "surface": "mast"}],
        path="same.md",
        scope="title",
        max_samples=5,
    )
    assert len(occ["mast"].samples) == 2
    assert {s.scope for s in occ["mast"].samples} == {"body", "title"}


def test_rank_pages_filters_and_sorts() -> None:
    assert "suspect" in SUSPECT_STATUSES
    assert "foreign" in SUSPECT_STATUSES
    assert "ok" not in SUSPECT_STATUSES
    words = [
        ClassifiedWord(
            normalized="okword",
            surface="okword",
            count=9,
            status="ok",
            samples=[VocabSample("p1.md", "body")],
        ),
        ClassifiedWord(
            normalized="bad1",
            surface="bad1",
            count=1,
            status="suspect",
            samples=[VocabSample("p2.md", "body"), VocabSample("p1.md", "body")],
        ),
        ClassifiedWord(
            normalized="bad2",
            surface="bad2",
            count=1,
            status="foreign",
            samples=[VocabSample("p2.md", "body")],
        ),
        ClassifiedWord(
            normalized="bad3",
            surface="bad3",
            count=1,
            status="calque",
            samples=[VocabSample("p2.md", "title")],
        ),
    ]
    ranked = rank_pages_by_suspects(words, sample_words=2)
    assert ranked[0].path == "p2.md"
    assert ranked[0].unique_suspects == 3
    assert ranked[0].score == 3.0
    assert len(ranked[0].sample_words) == 2
    assert ranked[1].path == "p1.md"
    assert ranked[1].unique_suspects == 1


def test_rank_empty() -> None:
    assert rank_pages_by_suspects([]) == []
    assert rank_pages_weighted([]) == []


def test_weighted_score_differs_from_unique_count() -> None:
    """One calque page should beat many weak hapax suspects under weighted rank."""
    weak_page = "weak.json"
    calque_page = "calque.json"
    words = [
        ClassifiedWord(
            normalized=f"w{i}",
            surface=f"w{i}",
            count=1,
            status="suspect",
            tier="weak",
            samples=[VocabSample(weak_page, "body")],
        )
        for i in range(5)
    ] + [
        ClassifiedWord(
            normalized="orientir",
            surface="orientir",
            count=2,
            status="calque",
            tier="likely",
            samples=[VocabSample(calque_page, "body")],
        ),
    ]
    raw = rank_pages_by_suspects(words)
    weighted = rank_pages_weighted(words)
    raw_weak = next(r for r in raw if r.path == weak_page)
    raw_calque = next(r for r in raw if r.path == calque_page)
    assert raw_weak.unique_suspects == 5
    assert raw_weak.score == 5.0
    assert raw_calque.unique_suspects == 1
    assert raw_calque.score == 1.0
    assert raw[0].path == weak_page

    w_weak = next(r for r in weighted if r.path == weak_page)
    w_calque = next(r for r in weighted if r.path == calque_page)
    assert w_weak.score == 0.5  # 5 * 0.1
    assert w_calque.score == 8.0
    assert weighted[0].path == calque_page
    assert w_calque.score != float(w_calque.unique_suspects)


def test_template_excluded_from_rank() -> None:
    words = [
        ClassifiedWord(
            normalized="anchor",
            surface="Anchor",
            count=3,
            status="template",
            samples=[VocabSample("p.json", "body")],
        ),
        ClassifiedWord(
            normalized="bad",
            surface="bad",
            count=1,
            status="suspect",
            samples=[VocabSample("p.json", "body")],
        ),
    ]
    ranked = rank_pages_weighted(words)
    assert len(ranked) == 1
    assert ranked[0].unique_suspects == 1
    assert ranked[0].score == 0.1


def test_needle_boost_and_require(tmp_path) -> None:
    words = [
        ClassifiedWord(
            normalized="orientir",
            surface="orientir",
            count=1,
            status="suspect",
            samples=[VocabSample("a.json", "body")],
        ),
        ClassifiedWord(
            normalized="zzz",
            surface="zzz",
            count=1,
            status="suspect",
            samples=[VocabSample("b.json", "body")],
        ),
    ]
    all_pages = rank_pages_weighted(words, needles=["orientir"])
    assert all_pages[0].path == "a.json"
    assert all_pages[0].score == 6.0
    only = rank_pages_weighted(words, needles=["orientir"], require_needle=True)
    assert len(only) == 1
    assert only[0].path == "a.json"


def test_curated_roundtrip(tmp_path) -> None:
    md = tmp_path / "queue.md"
    rows = append_pending_from_rank(
        [],
        [
            PageSuspectRank(
                path="infra/corpus-ci/pending-academy-articles/foo/bar.json",
                unique_suspects=2,
                sample_words=["orientir", "bad"],
                score=8.0,
            )
        ],
        locale="en",
        needles=["orientir"],
    )
    save_curated(md, rows)
    loaded = load_curated(md)
    assert len(loaded) == 1
    assert loaded[0].status == "pending"
    assert loaded[0].path == "foo/bar"


def test_rank_unique_key_needle_and_ru_stem() -> None:
    assert rank_unique_key("чеклисте", locale="ru", needles=["чеклист"]) == rank_unique_key(
        "чеклист", locale="ru", needles=["чеклист"]
    )
    assert rank_unique_key("чеклисте", locale="ru", needles=[]) == rank_unique_key(
        "чеклист", locale="ru", needles=[]
    )


def test_rank_collapses_ru_inflections_on_page() -> None:
    path = "infra/corpus-ci/pending-academy-articles/x.json"
    words = [
        ClassifiedWord(
            normalized="чеклист",
            surface="чеклист",
            count=1,
            status="calque",
            samples=[VocabSample(path, "body")],
        ),
        ClassifiedWord(
            normalized="чеклисте",
            surface="чеклисте",
            count=1,
            status="calque",
            samples=[VocabSample(path, "body")],
        ),
    ]
    ranked = rank_pages_by_suspects(words, locale="ru", needles=["чеклист"])
    assert ranked[0].unique_suspects == 1
    assert len(ranked[0].sample_words) == 1


def test_source_bucket_and_filter() -> None:
    assert page_source_bucket("infra/corpus-ci/pending-academy-articles/a.json") == "academy"
    assert page_source_bucket("infra/corpus-ci/pending-model-packs/b/export.json") == "model_pack"
    pages = [
        PageSuspectRank("infra/corpus-ci/pending-academy-articles/a.json", 1, ["x"], 1.0),
        PageSuspectRank("infra/corpus-ci/pending-model-packs/b/export.json", 2, ["y"], 2.0),
    ]
    academy_only = filter_pages_by_sources(pages, ["academy"])
    assert len(academy_only) == 1
    assert academy_only[0].path.endswith("a.json")
    via_rank = rank_pages(
        [
            ClassifiedWord(
                normalized="bad",
                surface="bad",
                count=1,
                status="suspect",
                samples=[
                    VocabSample(
                        "infra/corpus-ci/pending-academy-articles/a.json",
                        "body",
                    ),
                ],
            ),
            ClassifiedWord(
                normalized="worse",
                surface="worse",
                count=1,
                status="suspect",
                samples=[
                    VocabSample(
                        "infra/corpus-ci/pending-model-packs/b/export.json",
                        "body",
                    ),
                ],
            ),
        ],
        source_filter=["academy"],
    )
    assert len(via_rank) == 1
