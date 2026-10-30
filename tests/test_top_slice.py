"""Top-page / tier slice selection for LLM label (I6-1)."""

from __future__ import annotations

import json
from pathlib import Path

from lexaudit.config import load_config
from lexaudit.core.types import ClassifiedWord, Tier, VocabSample
from lexaudit.llm.context_snippet import format_context_snippet, load_scope_text
from lexaudit.llm.top_slice import parse_tier_filter, select_label_targets


def _word(
    norm: str,
    *,
    tier: Tier | None,
    path: str,
    status: str = "suspect",
) -> ClassifiedWord:
    return ClassifiedWord(
        normalized=norm,
        surface=norm,
        count=1,
        status=status,  # type: ignore[arg-type]
        samples=[VocabSample(path, "bodyMarkdown")],
        tier=tier,
        reason="hunspell",
    )


def test_parse_tier_filter() -> None:
    assert parse_tier_filter("likely,weak") == frozenset({"likely", "weak"})
    assert parse_tier_filter("confirmed") == frozenset({"confirmed"})


def test_select_label_targets_respects_tiers_and_limits(tmp_path: Path) -> None:
    academy = tmp_path / "infra" / "corpus-ci" / "pending-academy-articles" / "a"
    academy.mkdir(parents=True)
    doc = {
        "translations": {
            "en": {
                "bodyMarkdown": "The orientir denseness token appears here.",
            }
        }
    }
    (academy / "one.json").write_text(json.dumps(doc), encoding="utf-8")
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(
        f"repo_root: {tmp_path}\noutput_dir: {tmp_path / 'out'}\nlocales: [en]\n",
        encoding="utf-8",
    )
    cfg = load_config(cfg_path)
    p1 = "infra/corpus-ci/pending-academy-articles/a/one.json"
    p2 = "infra/corpus-ci/pending-academy-articles/a/two.json"
    words = [
        _word("orientir", tier="likely", path=p1),
        _word("denseness", tier="weak", path=p1),
        _word("confirmed-only", tier="confirmed", path=p1),
        _word("otherpage", tier="likely", path=p2),
    ]
    targets, pages = select_label_targets(
        words,
        locale="en",
        top_pages=1,
        top_words=2,
        tiers=frozenset({"likely", "weak"}),
        cfg=cfg,
    )
    norms = {t.normalized for t in targets}
    assert "confirmed-only" not in norms
    assert len(targets) <= 2
    assert pages


def test_load_scope_text_branches_and_format_snippet(tmp_path: Path) -> None:
    assert load_scope_text(tmp_path, "missing.json", "body", "en") is None
    (tmp_path / "doc.md").write_text("# Heading\n\nMarkdown body text.\n", encoding="utf-8")
    assert "Markdown body" in (load_scope_text(tmp_path, "doc.md", "body", "en") or "")

    (tmp_path / "bad.json").write_text("{not-json", encoding="utf-8")
    assert load_scope_text(tmp_path, "bad.json", "body", "en") is None

    (tmp_path / "list.json").write_text("[1, 2]", encoding="utf-8")
    assert load_scope_text(tmp_path, "list.json", "body", "en") is None

    pack = {"packRows": [{"locale": "en", "payload": {"overview": "Pack overview text"}}]}
    (tmp_path / "pack.json").write_text(json.dumps(pack), encoding="utf-8")
    assert load_scope_text(tmp_path, "pack.json", "overview", "en") == "Pack overview text"

    direct = {"body": "Direct body text"}
    (tmp_path / "direct.json").write_text(json.dumps(direct), encoding="utf-8")
    assert load_scope_text(tmp_path, "direct.json", "body", "en") == "Direct body text"

    snip = format_context_snippet(
        path="doc.md",
        scope="body",
        text="Some text without target",
        word="absent",
        surface="absent",
    )
    assert snip.startswith("doc.md#body: ...")
