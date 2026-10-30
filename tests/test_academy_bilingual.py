from __future__ import annotations

import json
from pathlib import Path

from lexaudit.detectors.bilingual import (
    pairs_from_academy,
    pairs_from_config,
    untranslated_latin_in_target,
)


def _write_article(path: Path, *, en: str, ru: str, de: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    translations: dict[str, object] = {
        "en": {"bodyMarkdown": en, "title": "EN"},
        "ru": {"bodyMarkdown": ru, "title": "RU"},
    }
    if de is not None:
        translations["de"] = {"bodyMarkdown": de, "title": "DE"}
    path.write_text(
        json.dumps(
            {
                "slug": path.stem,
                "category": "buying",
                "translations": translations,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_pairs_from_academy_materializes_bodies(tmp_path: Path) -> None:
    academy = tmp_path / "academy"
    _write_article(
        academy / "buying" / "checklist.json",
        en="The denseness of the survey checklist sidebar.",
        ru="Плотность denseness чеклиста sidebar.",
        de="Die denseness der Checklist Sidebar.",
    )
    mat = tmp_path / "mat"
    pairs = pairs_from_academy(academy, "en", "ru", materialize_dir=mat)
    assert len(pairs) == 1
    assert pairs[0].source_locale == "en"
    assert pairs[0].target_locale == "ru"
    src = Path(pairs[0].source_path).read_text(encoding="utf-8")
    tgt = Path(pairs[0].target_path).read_text(encoding="utf-8")
    hits = {w.normalized for w in untranslated_latin_in_target(src, tgt, path="ru/x.md")}
    assert "denseness" in hits
    assert "sidebar" in hits


def test_pairs_from_config_academy_source(tmp_path: Path) -> None:
    academy = tmp_path / "infra" / "corpus-ci" / "pending-academy-articles"
    _write_article(
        academy / "buying" / "a.json",
        en="Pending toast dashboard.",
        ru="Pending toast dashboard остался.",
        de="Pending Toast Dashboard blieb.",
    )
    pairs = pairs_from_config(
        [
            {
                "source": "academy",
                "source_locale": "en",
                "target_locale": "ru",
                "academy_root": "infra/corpus-ci/pending-academy-articles",
                "materialize_dir": "tmp/mat",
            },
            {
                "source": "academy",
                "source_locale": "en",
                "target_locale": "de",
                "academy_root": "infra/corpus-ci/pending-academy-articles",
                "materialize_dir": "tmp/mat",
            },
        ],
        tmp_path,
    )
    assert len(pairs) == 2
    locales = {(p.source_locale, p.target_locale) for p in pairs}
    assert locales == {("en", "ru"), ("en", "de")}
