"""Source collectors - fixture-based, read-only."""

from __future__ import annotations

import json
from pathlib import Path

from lexaudit.sources.collect import collect_academy, collect_jsonl_export, collect_packs


def test_collect_academy_fixture(tmp_path: Path) -> None:
    root = tmp_path / "infra" / "corpus-ci" / "pending-academy-articles" / "systems"
    root.mkdir(parents=True)
    doc = {
        "translations": {
            "ru": {
                "title": "Заголовок",
                "excerpt": "Кратко",
                "metaDescription": "Мета",
                "bodyMarkdown": "Текст корпуса",
            }
        }
    }
    (root / "demo.json").write_text(json.dumps(doc), encoding="utf-8")
    chunks = collect_academy(tmp_path, "ru")
    assert len(chunks) == 4
    assert chunks[0].source == "academy"
    assert "pending-academy-articles" in chunks[0].path


def test_collect_packs_fixture(tmp_path: Path) -> None:
    root = tmp_path / "infra" / "corpus-ci" / "pending-model-packs" / "hallberg-rassy" / "hr40"
    root.mkdir(parents=True)
    export = {
        "packRows": [
            {
                "locale": "en",
                "payload": {"overview": "A solid offshore cruiser.", "designHistory": ""},
            }
        ]
    }
    (root / "export.json").write_text(json.dumps(export), encoding="utf-8")
    chunks = collect_packs(tmp_path, "en")
    assert any(c.scope == "overview" for c in chunks)


def test_collect_jsonl_export(tmp_path: Path) -> None:
    path = tmp_path / "export.jsonl"
    path.write_text(
        json.dumps({"locale": "de", "path": "a.md", "scope": "body", "text": "Rumpf und Deck"})
        + "\n",
        encoding="utf-8",
    )
    chunks = collect_jsonl_export(path, "de")
    assert len(chunks) == 1
    assert "Rumpf" in chunks[0].text
