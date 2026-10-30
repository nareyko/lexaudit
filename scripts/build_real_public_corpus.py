#!/usr/bin/env python3
"""Build prose-only real_public bilingual fixtures from a staging download dir.

Lab only. Does not fetch the network — pass a pre-downloaded staging tree.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "bilingual" / "real_public"

_FENCE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]+`")
_HTML = re.compile(r"<[^>]+>")
_FRONT = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
_MKDOCS_INC = re.compile(r"\{\*.*?\*\}", re.DOTALL)
_ANCHOR = re.compile(r"\{ #\S+ \}")
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_URL = re.compile(r"https?://\S+")
_ADMONITION = re.compile(r"^///\s*\w+.*$", re.MULTILINE)
_ADMONITION_END = re.compile(r"^///\s*$", re.MULTILINE)
_MULTI_NL = re.compile(r"\n{3,}")


def prose_excerpt(raw: str, *, max_chars: int = 2800) -> str:
    text = _FRONT.sub("", raw)
    text = _FENCE.sub(" ", text)
    text = _MKDOCS_INC.sub(" ", text)
    text = _ANCHOR.sub(" ", text)
    text = _ADMONITION.sub(" ", text)
    text = _ADMONITION_END.sub(" ", text)
    text = _MD_IMAGE.sub(" ", text)
    text = _MD_LINK.sub(r"\1", text)
    text = _URL.sub(" ", text)
    text = _HTML.sub(" ", text)
    text = _INLINE_CODE.sub(" ", text)
    text = _MULTI_NL.sub("\n\n", text).strip()
    if len(text) > max_chars:
        cut = text[:max_chars]
        # Prefer breaking on paragraph
        if "\n\n" in cut:
            cut = cut.rsplit("\n\n", 1)[0]
        text = cut.strip() + "\n"
    return text + "\n"


def _copy_pair(
    staging: Path,
    rel_en: str,
    rel_ru: str,
    rel_de: str | None,
    slug: str,
) -> None:
    en_raw = (staging / rel_en).read_text(encoding="utf-8")
    ru_raw = (staging / rel_ru).read_text(encoding="utf-8")
    (OUT / "en" / f"{slug}.md").write_text(prose_excerpt(en_raw), encoding="utf-8")
    (OUT / "ru" / f"{slug}.md").write_text(prose_excerpt(ru_raw), encoding="utf-8")
    if rel_de and (staging / rel_de).is_file():
        de_raw = (staging / rel_de).read_text(encoding="utf-8")
        # Skip near-empty stubs
        if len(de_raw.strip()) > 500:
            (OUT / "de" / f"{slug}.md").write_text(prose_excerpt(de_raw), encoding="utf-8")


def write_seeded_overlays() -> None:
    """Real EN prose + deliberately leaky RU/DE for leftover recall (documented overlay)."""
    en = """# Payments overview

Check the available balance before you mark a transfer as pending.
Configure the webhook setup for settlement events.
Open the sidebar toast after authentication method onboarding.
Use query parameters and path parameters when reading status codes.
"""
    ru = """# Обзор платежей

Проверьте available balance, прежде чем пометить перевод как pending.
Настройте webhook setup для событий settlement.
Откройте sidebar toast после authentication method onboarding.
Используйте query parameters и path parameters при чтении status codes.
Оставьте SEPA и API без перевода.
"""
    de = """# Zahlungsübersicht

Prüfen Sie available balance, bevor Sie eine Überweisung als pending markieren.
Konfigurieren Sie webhook setup für Settlement-Ereignisse.
Öffnen Sie sidebar toast nach authentication method onboarding.
Nutzen Sie query parameters und path parameters beim Lesen von status codes.
SEPA und API bleiben stehen.
"""
    (OUT / "en" / "seeded-leak.md").write_text(en, encoding="utf-8")
    (OUT / "ru" / "seeded-leak.md").write_text(ru, encoding="utf-8")
    (OUT / "de" / "seeded-leak.md").write_text(de, encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--staging",
        type=Path,
        default=Path("/tmp/lexaudit-corpus"),
        help="Directory with pre-downloaded FastAPI/k8s trees",
    )
    args = p.parse_args()
    staging: Path = args.staging
    for loc in ("en", "ru", "de"):
        (OUT / loc).mkdir(parents=True, exist_ok=True)

    fastapi_slugs = [
        "first-steps",
        "path-params",
        "query-params",
        "body",
        "features",
        "async",
    ]
    for slug in fastapi_slugs:
        base = staging / "fastapi" / slug
        if not (base / "en.md").is_file():
            print(f"skip missing {slug}")
            continue
        _copy_pair(
            staging,
            f"fastapi/{slug}/en.md",
            f"fastapi/{slug}/ru.md",
            f"fastapi/{slug}/de.md",
            f"fastapi-{slug}",
        )

    # Kubernetes pods (full translations)
    if (staging / "k8s" / "pods" / "en.md").is_file():
        _copy_pair(
            staging,
            "k8s/pods/en.md",
            "k8s/pods/ru.md",
            "k8s/pods/de.md",
            "k8s-pods",
        )
    # overview EN+RU (DE is short description — still usable if >500 after frontmatter strip)
    if (staging / "k8s-overview-en.md").is_file():
        _copy_pair(
            staging,
            "k8s-overview-en.md",
            "k8s-overview-ru.md",
            "k8s-overview-de.md",
            "k8s-overview",
        )

    write_seeded_overlays()
    n = len(list((OUT / "en").glob("*.md")))
    print(f"wrote {n} EN slugs under {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
