"""Config loader tests."""

from __future__ import annotations

from pathlib import Path

from lexaudit.config import load_config


def test_load_config_minimal(tmp_path: Path) -> None:
    cfg_path = tmp_path / "lexaudit.config.yaml"
    cfg_path.write_text(
        "\n".join(
            [
                "repo_root: .",
                "output_dir: out",
                "locales: [ru, en]",
                "sources: [academy]",
                "min_length: 3",
                "enable_morph: false",
                "enable_llm: true",
                "llm_profiles:",
                "  gpu:",
                "    model: phi4-14b",
                "    base_url: http://127.0.0.1:8501/v1",
            ]
        ),
        encoding="utf-8",
    )
    cfg = load_config(cfg_path)
    assert cfg.locales == ["ru", "en"]
    assert cfg.sources == ["academy"]
    assert cfg.min_length == 3
    assert cfg.enable_morph is False
    assert cfg.enable_llm is True
    assert "gpu" in cfg.llm_profiles
    assert cfg.llm_profiles["gpu"].model == "phi4-14b"
    assert len(cfg.config_hash()) == 16
    assert cfg.output_dir == (tmp_path / "out").resolve()
