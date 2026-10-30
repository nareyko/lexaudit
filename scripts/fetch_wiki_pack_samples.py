#!/usr/bin/env python3
"""Fetch short Wikipedia REST summaries into tests/fixtures/packs_wild/ (CC BY-SA).

Reproducible local research corpus. Does not commit dumps; extracts are short.
Respect rate limits; identify with a descriptive User-Agent.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "packs_wild"

# Topic → pack affinity. Titles are Wikipedia page titles per language.
CATALOG: list[tuple[str, str, str, str]] = [
    # pack, lang, title, slug hint
    ("developer-docs-v0", "en", "Application programming interface", "api"),
    ("developer-docs-v0", "ru", "Программный интерфейс приложения", "api"),
    ("developer-docs-v0", "de", "Programmierschnittstelle", "api"),
    ("developer-docs-v0", "en", "OpenAPI Specification", "openapi"),
    ("developer-docs-v0", "ru", "OpenAPI", "openapi"),
    ("developer-docs-v0", "de", "OpenAPI", "openapi"),
    ("saas-ui-v0", "en", "Software as a service", "saas"),
    ("saas-ui-v0", "ru", "Программное обеспечение как услуга", "saas"),
    ("saas-ui-v0", "de", "Software as a Service", "saas"),
    ("saas-ui-v0", "en", "Dashboard", "dashboard"),
    ("saas-ui-v0", "de", "Dashboard", "dashboard"),
    ("ecommerce-ui-v0", "en", "Electronic commerce", "ecommerce"),
    ("ecommerce-ui-v0", "ru", "Электронная коммерция", "ecommerce"),
    ("ecommerce-ui-v0", "de", "Elektronischer Handel", "ecommerce"),
    ("ecommerce-ui-v0", "en", "Shopping cart", "cart"),
    ("fintech-v0", "en", "Payment", "payment"),
    ("fintech-v0", "ru", "Платёж", "payment"),
    ("fintech-v0", "de", "Zahlung", "payment"),
    ("fintech-v0", "en", "Know your customer", "kyc"),
    ("healthcare-ui-v0", "en", "Electronic health record", "ehr"),
    ("healthcare-ui-v0", "de", "Elektronische Patientenakte", "ehr"),
    ("healthcare-ui-v0", "ru", "Электронная история болезни", "ehr"),
    ("legal-docs-v0", "en", "Contract", "contract"),
    ("legal-docs-v0", "ru", "Договор", "contract"),
    ("legal-docs-v0", "de", "Vertrag", "contract"),
    ("gaming-ui-v0", "en", "Heads-up display", "hud"),
    ("gaming-ui-v0", "de", "Head-up-Display", "hud"),
    ("edtech-v0", "en", "Learning management system", "lms"),
    ("edtech-v0", "ru", "Система управления обучением", "lms"),
    ("edtech-v0", "de", "Lernplattform", "lms"),
    ("security-docs-v0", "en", "Vulnerability (computing)", "vuln"),
    ("security-docs-v0", "ru", "Уязвимость (компьютерная безопасность)", "vuln"),
    ("security-docs-v0", "de", "Sicherheitslücke", "vuln"),
    ("hr-ats-v0", "en", "Applicant tracking system", "ats"),
    ("hr-ats-v0", "de", "Bewerbermanagementsystem", "ats"),
]

UA = "lexaudit-research/0.3 (+https://github.com/nareyko/lexaudit; educational pack eval)"


def fetch_summary(lang: str, title: str) -> dict[str, str]:
    q = urllib.parse.quote(title.replace(" ", "_"), safe="")
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{q}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    extract = (data.get("extract") or "").strip()
    if len(extract) > 1200:
        extract = extract[:1200].rsplit(" ", 1)[0] + "…"
    page = ""
    try:
        page = data["content_urls"]["desktop"]["page"]
    except (KeyError, TypeError):
        page = f"https://{lang}.wikipedia.org/wiki/{q}"
    return {
        "title": str(data.get("title") or title),
        "extract": extract,
        "url": page,
    }


def write_page(pack: str, lang: str, slug: str, meta: dict[str, str]) -> Path:
    dest_dir = OUT / pack / lang
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe = slug.replace("/", "-")
    path = dest_dir / f"wiki-{safe}.md"
    body = (
        f"# {meta['title']}\n\n"
        f"> Source: [{meta['url']}]({meta['url']})  \n"
        f"> License: CC BY-SA 4.0 (Wikipedia)\n\n"
        f"{meta['extract']}\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def prune_stale(keep: set[Path]) -> list[str]:
    """Remove wiki-*.md not produced by this run (title-named leftovers)."""
    removed: list[str] = []
    if not OUT.is_dir():
        return removed
    for path in OUT.rglob("wiki-*.md"):
        if path.resolve() not in keep:
            removed.append(str(path.relative_to(ROOT)))
            path.unlink(missing_ok=True)
    return removed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sleep", type=float, default=0.35, help="Delay between requests")
    ap.add_argument("--limit", type=int, default=0, help="Max pages (0=all)")
    args = ap.parse_args()

    written_paths: list[Path] = []
    written: list[str] = []
    errors: list[str] = []
    catalog = CATALOG if not args.limit else CATALOG[: args.limit]
    for pack, lang, title, slug in catalog:
        try:
            meta = fetch_summary(lang, title)
            if not meta["extract"]:
                errors.append(f"empty:{lang}:{title}")
                continue
            path = write_page(pack, lang, slug, meta)
            written_paths.append(path.resolve())
            written.append(str(path.relative_to(ROOT)))
            print(f"OK {pack}/{lang}/{slug}")
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            json.JSONDecodeError,
        ) as exc:
            errors.append(f"{lang}:{title}:{exc}")
            print(f"FAIL {lang} {title}: {exc}")
        time.sleep(args.sleep)

    removed = prune_stale(set(written_paths)) if not args.limit else []
    for rel in removed:
        print(f"PRUNE {rel}")

    sources = [
        "# Pack wild corpus (Wikipedia)",
        "",
        "Short summaries via Wikipedia REST page/summary.",
        "License: CC BY-SA 4.0 — Wikipedia contributors.",
        "Refresh: `uv run python scripts/fetch_wiki_pack_samples.py`",
        "Do not commit full dumps, CX corpora, or title-named duplicates here.",
        "Keep slug filenames (`wiki-{slug}.md`) only; prune stale on refresh.",
        "",
        "## Files",
        "",
        *[f"- `{p}`" for p in written],
        "",
    ]
    if errors:
        sources += ["## Fetch errors", "", *[f"- `{e}`" for e in errors], ""]
    if removed:
        sources += ["## Pruned this run", "", *[f"- `{p}`" for p in removed], ""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SOURCES.md").write_text("\n".join(sources), encoding="utf-8")
    print(f"wrote {len(written)} pages; pruned={len(removed)}; errors={len(errors)}")
    return 0 if written else 1


if __name__ == "__main__":
    raise SystemExit(main())
