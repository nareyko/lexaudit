from __future__ import annotations

from pathlib import Path

from lexaudit.detectors.bilingual import (
    pair_paths,
    untranslated_latin_in_target,
)


def test_pair_paths_and_untranslated(tmp_path: Path) -> None:
    en = tmp_path / "en"
    ru = tmp_path / "ru"
    en.mkdir()
    ru.mkdir()
    (en / "a.md").write_text("The denseness of the survey checklist.\n", encoding="utf-8")
    (ru / "a.md").write_text("Плотность denseness чеклиста.\n", encoding="utf-8")
    pairs = pair_paths(en, ru, source_locale="en", target_locale="ru")
    assert len(pairs) == 1
    hits = untranslated_latin_in_target(
        (en / "a.md").read_text(encoding="utf-8"),
        (ru / "a.md").read_text(encoding="utf-8"),
        path="ru/a.md",
    )
    assert any(w.normalized == "denseness" for w in hits)
