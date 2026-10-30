from __future__ import annotations

import csv
from pathlib import Path

from lexaudit.detectors.bilingual import (
    DEFAULT_FUNCTION_STOP,
    DEFAULT_INTENTIONAL_LOANS,
    DEFAULT_TEMPLATE_CHROME,
    detect_pair_leftovers,
    length_ratio_leftovers,
    length_ratio_signal,
    matrix_pairs,
    pair_paths,
    pairs_from_config,
    strip_urls_emails_code,
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
    hits = length_ratio_leftovers("short", "x" * 80, path="ru/x.md")
    assert hits and hits[0].reason.startswith("bilingual-length-ratio:")
    assert hits[0].tier == "weak"


def test_urls_and_code_not_counted_as_leftovers() -> None:
    cleaned = strip_urls_emails_code(
        "See https://example.com/path and `schemaize` plus a@b.co denseness here."
    )
    assert "https" not in cleaned
    assert "schemaize" not in cleaned
    assert "denseness" in cleaned
    src = "Visit https://example.com/dashboard denseness docs."
    tgt = "См. https://example.com/dashboard denseness в документации."
    hits = untranslated_latin_in_target(src, tgt, path="ru/x.md")
    norms = {w.normalized for w in hits}
    assert "denseness" in norms
    assert "example" not in norms


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


def test_template_chrome_skipped_but_prose_leftover_kept() -> None:
    assert "definition" in DEFAULT_TEMPLATE_CHROME
    assert "fairhelm" in DEFAULT_TEMPLATE_CHROME
    assert "sidebar" not in DEFAULT_TEMPLATE_CHROME
    src = (
        "FairHelm academy wiki definition related limits services courses "
        "yachts and a denseness leftover sidebar note.\n"
    )
    tgt = (
        "FairHelm academy wiki definition related limits services courses "
        "yachts и leftover denseness sidebar.\n"
    )
    hits = {w.normalized for w in untranslated_latin_in_target(src, tgt, path="ru/x.md")}
    assert "definition" not in hits
    assert "fairhelm" not in hits
    assert "academy" not in hits
    assert "denseness" in hits
    assert "sidebar" in hits


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


def test_live_v1_others_fixtures() -> None:
    root = FIXTURES / "live_v1_others"
    assert (root / "SOURCES.md").is_file()
    assert (root / "gold-leftovers.csv").is_file()
    for loc in ("en", "es", "pl", "sv", "uk"):
        assert (root / loc / "dicio-toast.md").is_file()
    src = (root / "en" / "soapbox-onboarding.md").read_text(encoding="utf-8")
    tgt = (root / "es" / "soapbox-onboarding.md").read_text(encoding="utf-8")
    hits = {
        w.normalized
        for w in untranslated_latin_in_target(src, tgt, path="es/onboarding.md")
    }
    assert "onboarding" in hits
    assert "complete" in hits


def test_matrix_pairs_v1_directions() -> None:
    assert len(matrix_pairs(mode="anchors")) == 6
    assert len(matrix_pairs(mode="anchors_x_others")) == 30
    pairs = matrix_pairs(mode="all")
    assert len(pairs) == 42  # 7 locales x 6
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


def test_cyrillic_to_latin_thin_fixture() -> None:
    root = FIXTURES / "cyrillic_to_latin"
    assert (root / "SOURCES.md").is_file()
    src = (root / "ru" / "settings.md").read_text(encoding="utf-8")
    tgt = (root / "en" / "settings.md").read_text(encoding="utf-8")
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
