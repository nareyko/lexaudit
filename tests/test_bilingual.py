from __future__ import annotations

import csv
from pathlib import Path

from lexaudit.detectors.bilingual import (
    DEFAULT_FUNCTION_STOP,
    DEFAULT_INTENTIONAL_LOANS,
    detect_pair_leftovers,
    length_ratio_signal,
    matrix_pairs,
    pair_paths,
    pairs_from_config,
    untranslated_cyrillic_in_target,
    untranslated_latin_in_target,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "bilingual"


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


def test_intentional_loans_not_flagged() -> None:
    src = "Call the API with JSON and OpenAPI examples."
    tgt = "Вызовите API с примерами JSON и OpenAPI."  # noqa: RUF001
    hits = untranslated_latin_in_target(src, tgt, path="ru/x.md")
    assert hits == []
    assert "api" in DEFAULT_INTENTIONAL_LOANS


def test_heldout_fixtures_exist() -> None:
    gold = FIXTURES / "heldout" / "gold-leftovers.csv"
    assert gold.is_file()
    rows = list(csv.DictReader(gold.open(encoding="utf-8")))
    assert len(rows) >= 20
    assert any(r["label"] == "leftover" for r in rows)
    assert any(r["label"] == "intentional" for r in rows)
    for loc in ("en", "ru", "de"):
        assert (FIXTURES / "heldout" / loc / "payments.md").is_file()


def test_pairs_from_config_heldout() -> None:
    root = FIXTURES / "heldout"
    pairs = pairs_from_config(
        [
            {
                "source_locale": "en",
                "target_locale": "ru",
                "source_root": "en",
                "target_root": "ru",
            }
        ],
        root,
    )
    assert len(pairs) >= 3
    assert all(p.target_locale == "ru" for p in pairs)


def test_length_ratio_soft_signal() -> None:
    ratio = length_ratio_signal("abcd", "abcdefgh")
    assert 1.9 < ratio < 2.1


def test_heldout_metrics_script_importable() -> None:
    # Ensure gold labels cover tokens the detector can see on payments EN→RU.
    src = (FIXTURES / "heldout" / "en" / "settings.md").read_text(encoding="utf-8")
    tgt = (FIXTURES / "heldout" / "ru" / "settings.md").read_text(encoding="utf-8")
    hits = {w.normalized for w in untranslated_latin_in_target(src, tgt, path="ru/settings.md")}
    assert "sidebar" in hits
    assert "toast" in hits


def test_kebab_anchor_slugs_skipped() -> None:
    src = "See why-you-need-kubernetes-and-what-can-it-do in the overview.\n"
    tgt = "См. why-you-need-kubernetes-and-what-can-it-do в обзоре.\n"
    hits = untranslated_latin_in_target(src, tgt, path="ru/x.md")
    assert hits == []


def test_real_public_fixtures_and_seeded_leak() -> None:
    root = FIXTURES / "real_public"
    assert (root / "SOURCES.md").is_file()
    assert (root / "gold-leftovers.csv").is_file()
    assert (root / "en" / "seeded-leak.md").is_file()
    assert (root / "ru" / "fastapi-first-steps.md").is_file()
    assert (root / "de" / "k8s-pods.md").is_file()
    src = (root / "en" / "seeded-leak.md").read_text(encoding="utf-8")
    tgt = (root / "ru" / "seeded-leak.md").read_text(encoding="utf-8")
    hits = {w.normalized for w in untranslated_latin_in_target(src, tgt, path="ru/seeded-leak.md")}
    assert "pending" in hits
    assert "sidebar" in hits
    assert "api" not in hits


def test_function_stop_skips_glue_words() -> None:
    assert "this" in DEFAULT_FUNCTION_STOP
    src = "In this scene Available fonts are listed.\n"
    tgt = "В разделе In this scene показаны Available fonts.\n"  # noqa: RUF001
    hits = {w.normalized for w in untranslated_latin_in_target(src, tgt, path="ru/x.md")}
    assert "this" not in hits
    assert "scene" in hits
    assert "available" in hits
    assert "fonts" in hits


def test_community_imperfect_fixtures() -> None:
    root = FIXTURES / "community"
    assert (root / "SOURCES.md").is_file()
    gold = root / "gold-leftovers.csv"
    assert gold.is_file()
    rows = list(csv.DictReader(gold.open(encoding="utf-8")))
    assert len(rows) >= 40
    src = (root / "en" / "ever-sidebar.md").read_text(encoding="utf-8")
    tgt = (root / "ru" / "ever-sidebar.md").read_text(encoding="utf-8")
    hits = {w.normalized for w in untranslated_latin_in_target(src, tgt, path="ru/ever-sidebar.md")}
    assert "inbox" in hits
    assert "platform" in hits
    assert "home" in hits


def test_live_weblate_fixtures() -> None:
    root = FIXTURES / "live_weblate"
    assert (root / "SOURCES.md").is_file()
    assert (root / "gold-leftovers.csv").is_file()
    assert (root / "intentional-extra-de.txt").is_file()
    src = (root / "en" / "soapbox-onboarding.md").read_text(encoding="utf-8")
    tgt = (root / "ru" / "soapbox-onboarding.md").read_text(encoding="utf-8")
    hits = {
        w.normalized
        for w in untranslated_latin_in_target(src, tgt, path="ru/onboarding.md")
    }
    assert "onboarding" in hits
    assert "complete" in hits


def test_live_crowdin_fixtures() -> None:
    root = FIXTURES / "live_crowdin"
    assert (root / "SOURCES.md").is_file()
    assert (root / "gold-leftovers.csv").is_file()
    src = (root / "en" / "jellyfin-dashboard.md").read_text(encoding="utf-8")
    tgt = (root / "ru" / "jellyfin-dashboard.md").read_text(encoding="utf-8")
    hits = {
        w.normalized
        for w in untranslated_latin_in_target(src, tgt, path="ru/jellyfin.md")
    }
    assert "dashboard" in hits
    assert "libraries" in hits


def test_matrix_pairs_v1_directions() -> None:
    assert len(matrix_pairs(mode="anchors")) == 6
    assert len(matrix_pairs(mode="anchors_x_others")) == 30
    pairs = matrix_pairs(mode="all")
    assert len(pairs) == 42  # 7 locales × 6
    assert ("en", "es") in pairs and ("es", "ru") in pairs
    assert ("uk", "pl") in pairs and ("sv", "de") in pairs


def test_cyrillic_overlap_ru_to_en() -> None:
    src = (FIXTURES / "heldout" / "ru" / "settings.md").read_text(encoding="utf-8")
    tgt = (FIXTURES / "heldout" / "en" / "settings.md").read_text(encoding="utf-8")
    hits = {
        w.normalized
        for w in untranslated_cyrillic_in_target(src, tgt, path="en/settings.md")
    }
    assert "откройте" in hits
    assert "закройте" in hits


def test_detect_pair_leftovers_routes_by_locale() -> None:
    src = (FIXTURES / "heldout" / "de" / "german-leak.md").read_text(encoding="utf-8")
    tgt = (FIXTURES / "heldout" / "en" / "german-leak.md").read_text(encoding="utf-8")
    hits = {
        w.normalized
        for w in detect_pair_leftovers(
            src, tgt, source_locale="de", target_locale="en", path="en/german-leak.md"
        )
    }
    assert "überweisungen" in hits
    assert "auszahlungen" in hits
