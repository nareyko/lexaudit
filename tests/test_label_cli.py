"""CLI label command and run_top_labels (mocked LLM)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from lexaudit.cli.main import main
from lexaudit.config import load_config
from lexaudit.core.types import ClassifiedWord, VocabSample
from lexaudit.llm.client import LlmClient
from lexaudit.llm.run_top import localai_is_up, run_top_labels


def _write_words_json(out_dir: Path, locale: str, words: list[dict[str, object]]) -> None:
    loc_dir = out_dir / locale
    loc_dir.mkdir(parents=True, exist_ok=True)
    doc = {"words": words}
    (loc_dir / "words.json").write_text(json.dumps(doc), encoding="utf-8")


def test_label_cli_mocked(tmp_path: Path) -> None:
    cfg_path = tmp_path / "cfg.yaml"
    out_dir = tmp_path / "out"
    cfg_path.write_text(
        "\n".join(
            [
                f"repo_root: {tmp_path}",
                f"output_dir: {out_dir}",
                "locales: [en]",
                f"llm_cache_dir: {tmp_path / 'cache'}",
                "llm_profiles:",
                "  gpu:",
                "    model: mock-model",
                "    base_url: http://127.0.0.1:8501/v1",
            ]
        ),
        encoding="utf-8",
    )
    _write_words_json(
        out_dir,
        "en",
        [
            {
                "word": "orientir",
                "norm": "orientir",
                "status": "suspect",
                "tier": "weak",
                "count": 1,
                "samples": [
                    {
                        "path": "infra/corpus-ci/pending-academy-articles/x.json",
                        "scope": "bodyMarkdown",
                    }
                ],
            }
        ],
    )
    academy = tmp_path / "infra" / "corpus-ci" / "pending-academy-articles"
    academy.mkdir(parents=True)
    (academy / "x.json").write_text(
        json.dumps({"translations": {"en": {"bodyMarkdown": "bad orientir here"}}}),
        encoding="utf-8",
    )

    def fake_label_word(client: LlmClient, **kwargs: object) -> dict[str, object]:
        return {
            "label": "calque",
            "confidence": 0.9,
            "rationale": "false friend",
            "model": "mock-model",
            "prompt_version": "label-v1",
        }

    runner = CliRunner()
    with patch("lexaudit.llm.run_top.label_word", side_effect=fake_label_word):
        result = runner.invoke(
            main,
            [
                "label",
                "--config",
                str(cfg_path),
                "--locale",
                "en",
                "--top-pages",
                "5",
                "--top-words",
                "3",
                "--tiers",
                "likely,weak",
            ],
        )
    assert result.exit_code == 0, result.output
    out_file = out_dir / "en" / "llm-labels.json"
    assert out_file.is_file()
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["labels"][0]["class"] == "calque"
    assert payload["labels"][0]["hint"] == "false friend"
    assert "orientir" in payload["labels"][0]["word"]


def test_run_top_labels_empty_slice(tmp_path: Path) -> None:
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(
        f"repo_root: {tmp_path}\noutput_dir: {tmp_path / 'out'}\nlocales: [en]\n",
        encoding="utf-8",
    )
    cfg = load_config(cfg_path)
    rows, _pages, stats = run_top_labels(
        cfg,
        "en",
        [],
        top_pages=5,
        top_words=10,
        tiers_raw="likely,weak",
        profile_name="gpu",
    )
    assert rows == []
    assert stats["targets"] == 0


def test_localai_smoke_ten_words(tmp_path: Path) -> None:
    """Live LocalAI smoke on 10 words when 127.0.0.1:8501 is up; else skip."""
    if not localai_is_up():
        import pytest

        pytest.skip("LocalAI not running at 127.0.0.1:8501 - see eval/llm-dev.md")

    cfg_path = tmp_path / "cfg.yaml"
    cache = tmp_path / "cache"
    cfg_path.write_text(
        "\n".join(
            [
                f"repo_root: {tmp_path}",
                f"output_dir: {tmp_path / 'out'}",
                "locales: [en]",
                f"llm_cache_dir: {cache}",
                "llm_profiles:",
                "  gpu:",
                "    model: phi4-14b",
                "    base_url: http://127.0.0.1:8501/v1",
                "    timeout_s: 120",
            ]
        ),
        encoding="utf-8",
    )
    cfg = load_config(cfg_path)
    profile = cfg.llm_profiles["gpu"]
    client = LlmClient(profile, cache_dir=cache)
    words: list[ClassifiedWord] = []
    academy = tmp_path / "infra" / "corpus-ci" / "pending-academy-articles" / "smoke"
    academy.mkdir(parents=True)
    for i in range(10):
        slug = f"page{i}.json"
        rel = f"infra/corpus-ci/pending-academy-articles/smoke/{slug}"
        token = f"smokeword{i}"
        (academy / slug).write_text(
            json.dumps({"translations": {"en": {"bodyMarkdown": f"Text with {token} inside."}}}),
            encoding="utf-8",
        )
        words.append(
            ClassifiedWord(
                normalized=token,
                surface=token,
                count=1,
                status="suspect",
                samples=[VocabSample(rel, "bodyMarkdown")],
                tier="weak" if i % 2 == 0 else "likely",
                reason="hunspell",
            )
        )
    rows, _pages, stats = run_top_labels(
        cfg,
        "en",
        words,
        top_pages=10,
        top_words=10,
        tiers_raw="likely,weak",
        profile_name="gpu",
        client=client,
    )
    assert len(rows) == 10
    assert stats["llm_calls"] >= 1 or stats["cache_hits"] >= 1
    for row in rows:
        assert row["class"]
        assert "hint" in row
