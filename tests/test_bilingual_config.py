from __future__ import annotations

from pathlib import Path

from lexaudit.config import load_config

ROOT = Path(__file__).resolve().parents[1]


def test_bilingual_example_config_loads_opt_in() -> None:
    path = ROOT / "examples" / "lexaudit.config.bilingual.yaml"
    assert path.is_file()
    cfg = load_config(path)
    assert cfg.enable_bilingual is True
    assert len(cfg.bilingual_pairs) >= 2


def test_default_example_config_keeps_bilingual_off() -> None:
    default_cfg = load_config(ROOT / "examples" / "lexaudit.config.example.yaml")
    assert default_cfg.enable_bilingual is False
