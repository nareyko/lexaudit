"""v0.4.2 W3: JSON non-prose filter + collect_ts_prose."""

from __future__ import annotations

from pathlib import Path

from lexaudit.sources.collect import (
    _iter_json_strings,
    collect_all,
    collect_ts_prose,
)


def test_iter_json_strings_skips_slug_url_icon() -> None:
    data = {
        "slug": "yacht-survey",
        "url": "https://fairhelm.com/en/academy/",
        "href": "/en/yachts/",
        "icon": "anchor",
        "ctaUrl": "/en/services/",
        "title": "Yacht survey guide",
        "body": "Check the chainplates carefully.",
        "nested": {"path": "/tmp/x", "label": "Open report"},
    }
    pairs = list(_iter_json_strings(data))
    texts = {t for _, t in pairs}
    scopes = {s for s, _ in pairs}
    assert "Yacht survey guide" in texts
    assert "Check the chainplates carefully." in texts
    assert "Open report" in texts
    assert "yacht-survey" not in texts
    assert "https://fairhelm.com/en/academy/" not in texts
    assert "anchor" not in texts
    assert not any(s.endswith("slug") or s.endswith("url") or s.endswith("icon") for s in scopes)


def test_collect_ts_prose_reads_locale_object(tmp_path: Path) -> None:
    yachts = tmp_path / "frontend" / "src" / "lib" / "yachts" / "tools"
    yachts.mkdir(parents=True)
    (yachts / "demo-content.ts").write_text(
        """
import type { Locale } from "@/lib/i18n-config";
const PACKS = {
  en: { title: "English title here", lead: "Check the hull carefully." },
  ru: { title: "Русский заголовок здесь", lead: "Проверьте корпус внимательно." },
  de: { title: "Deutscher Titel hier", lead: "Rumpf sorgfältig prüfen." },
};
export function listingReviewPromoDoorLabel(locale: Locale): string {
  switch (locale) {
    case "ru":
      return "Разбор объявления - короткий текст";
    case "de":
      return "Inseratsprüfung - kurzer Text";
    default:
      return "Listing review - short text";
  }
}
""",
        encoding="utf-8",
    )
    ru = collect_ts_prose(tmp_path, "ru")
    assert ru
    blob = "\n".join(c.text for c in ru)
    assert "Русский заголовок здесь" in blob
    assert "Проверьте корпус внимательно." in blob
    assert "Разбор объявления" in blob
    assert "English title here" not in blob
    assert all(c.source == "ts_prose" for c in ru)

    en = collect_ts_prose(tmp_path, "en")
    en_blob = "\n".join(c.text for c in en)
    assert "English title here" in en_blob
    assert "Русский заголовок здесь" not in en_blob


def test_collect_all_includes_ts_prose_flag(tmp_path: Path) -> None:
    yachts = tmp_path / "frontend" / "src" / "lib" / "yachts"
    yachts.mkdir(parents=True)
    (yachts / "x.ts").write_text(
        'const HUB = { en: { title: "Hello reader facing title" } };\n',
        encoding="utf-8",
    )
    chunks = collect_all(tmp_path, "en", sources={"ts_prose"})
    assert chunks and chunks[0].source == "ts_prose"
