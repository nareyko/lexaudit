"""Tests for non-technical user CLI commands: init, doctor, zero-config, and API key header."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from lexaudit.cli.main import main
from lexaudit.config import LlmProfile, resolve_or_default_config
from lexaudit.llm.client import LlmClient


def test_cli_init_creates_and_skips(tmp_path: Path) -> None:
    runner = CliRunner()
    res = runner.invoke(main, ["init", "--dir", str(tmp_path)])
    assert res.exit_code == 0
    assert "created:" in res.output
    assert (tmp_path / "lexaudit.config.yaml").is_file()
    assert (tmp_path / "dicts" / "proper-names.yaml").is_file()
    assert (tmp_path / "dicts" / "acronyms.yaml").is_file()
    assert (tmp_path / "dicts" / "allowlist.yaml").is_file()

    # Second run without --force skips existing files
    res2 = runner.invoke(main, ["init", "--dir", str(tmp_path)])
    assert res2.exit_code == 0
    assert "skipped existing" in res2.output

    # With --force overwrites
    res3 = runner.invoke(main, ["init", "--dir", str(tmp_path), "--force"])
    assert res3.exit_code == 0
    assert "created:" in res3.output


def test_cli_doctor_runs_without_config(tmp_path: Path) -> None:
    runner = CliRunner()
    res = runner.invoke(main, ["doctor"])
    assert res.exit_code == 0
    assert "CPU-first (GPU required: NO)" in res.output
    assert "Calque rules: OK" in res.output


def test_resolve_or_default_config_zero_config_and_autodiscover(tmp_path: Path) -> None:
    # Zero-config when no lexaudit.config.yaml is present
    cfg = resolve_or_default_config(None, cwd=tmp_path)
    assert cfg.repo_root == tmp_path.resolve()
    assert cfg.sources == ["files"]
    assert cfg.locales == ["en"]
    assert cfg.calque_rules_dir is not None

    # Auto-discover when lexaudit.config.yaml exists in cwd
    Runner = CliRunner
    _ = Runner
    (tmp_path / "lexaudit.config.yaml").write_text(
        "repo_root: .\noutput_dir: ./out\nlocales: [de]\nsources: [files]\n",
        encoding="utf-8",
    )
    cfg2 = resolve_or_default_config(None, cwd=tmp_path)
    assert cfg2.locales == ["de"]


def test_llm_client_passes_bearer_api_key(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CUSTOM_LLM_KEY", "sk-test-12345")
    profile = LlmProfile(
        name="cloud",
        base_url="https://api.example.com/v1",
        model="gpt-4o-mini",
        timeout_s=5,
        max_retries=0,
        api_key_env="CUSTOM_LLM_KEY",
    )
    client = LlmClient(profile, cache_dir=tmp_path)
    payload = {
        "choices": [{"message": {"content": json.dumps({"label": "ok", "confidence": 0.9})}}]
    }

    class Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return payload

    with patch("lexaudit.llm.client.httpx.Client") as mock_http:
        inst = MagicMock()
        inst.__enter__.return_value = inst
        inst.__exit__.return_value = None
        inst.post.return_value = Resp()
        mock_http.return_value = inst
        out = client.chat_json(
            system="sys",
            user="usr",
            prompt_version="v1",
            word="boat",
            context="ctx",
        )
        assert out["label"] == "ok"
        _, kwargs = mock_http.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer sk-test-12345"
