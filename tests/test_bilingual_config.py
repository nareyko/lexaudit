from __future__ import annotations

from pathlib import Path

from lexaudit.config import load_config
from lexaudit.detectors.bilingual import (
    DEFAULT_INTENTIONAL_LOANS,
    intentional_loans_for_target,
    load_extra_loans,
    untranslated_latin_in_target,
)

ROOT = Path(__file__).resolve().parents[1]


def test_bilingual_example_config_loads_opt_in() -> None:
    path = ROOT / "examples" / "lexaudit.config.bilingual.yaml"
    assert path.is_file()
    cfg = load_config(path)
    assert cfg.enable_bilingual is True
    assert len(cfg.bilingual_pairs) >= 2
    assert cfg.bilingual_extra_loans_path is not None
    assert cfg.bilingual_extra_loans_path.is_file()
    assert list(cfg.bilingual_extra_loans_locales) == ["de"]
    extras = load_extra_loans(cfg.bilingual_extra_loans_path)
    assert "dashboard" in extras
    assert "toast" in extras
    assert "dashboard" not in DEFAULT_INTENTIONAL_LOANS


def test_default_example_config_keeps_bilingual_off() -> None:
    default_cfg = load_config(ROOT / "examples" / "lexaudit.config.example.yaml")
    assert default_cfg.enable_bilingual is False
    assert default_cfg.bilingual_extra_loans_path is None


def test_de_ui_extras_clear_leftover_only_for_de() -> None:
    src = "Open the Dashboard and dismiss the Toast.\n"
    de_tgt = "Öffnen Sie das Dashboard und schließen Sie den Toast.\n"
    ru_tgt = "Откройте Dashboard и закройте Toast.\n"
    extras = frozenset({"dashboard", "toast"})
    de_loans = intentional_loans_for_target(
        "de", extra=extras, extra_locales=frozenset({"de"})
    )
    ru_loans = intentional_loans_for_target(
        "ru", extra=extras, extra_locales=frozenset({"de"})
    )
    de_hits = {
        w.normalized
        for w in untranslated_latin_in_target(
            src, de_tgt, path="de/x.md", intentional_loans=de_loans
        )
    }
    ru_hits = {
        w.normalized
        for w in untranslated_latin_in_target(
            src, ru_tgt, path="ru/x.md", intentional_loans=ru_loans
        )
    }
    assert "dashboard" not in de_hits
    assert "toast" not in de_hits
    assert "dashboard" in ru_hits
    assert "toast" in ru_hits
