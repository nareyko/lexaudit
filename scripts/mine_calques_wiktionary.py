#!/usr/bin/env python3
"""Mine calque / false-friend candidates from Kaikki or Wiktionary API.

Detection-research helper for lexaudit v0.4 Stage V3-3. Writes a ranked
candidate list under ``tmp/mined-calques/`` (gitignored). Raw dumps are never
committed. Network is optional: ``--fixture`` or offline fallback uses
``tests/fixtures/mined_calques_sample.json``.

Examples
--------
  uv run python scripts/mine_calques_wiktionary.py
  uv run python scripts/mine_calques_wiktionary.py --fixture
  uv run python scripts/mine_calques_wiktionary.py --locale es --limit 40
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tmp" / "mined-calques"
FIXTURE = ROOT / "tests" / "fixtures" / "mined_calques_sample.json"
UA = "lexaudit-mine-calques/0.4 (+https://github.com/nareyko/lexaudit; research)"

# Compact seed queries per locale (false-friend / calque research pages).
WIKT_QUERIES: dict[str, list[str]] = {
    "en": ["false friend", "calque", "loan translation"],
    "de": ["Falscher Freund", "Lehnübersetzung", "realisieren"],
    "es": ["falso amigo", "calco", "actualmente", "librería"],
    "pl": ["fałszywi przyjaciele", "kalka językowa", "ewentualnie", "aktualnie"],
    "ru": ["ложные друзья переводчика", "калька", "имеет смысл"],
    "sv": ["falska vänner", "översättningslån", "eventuellt"],
    "uk": ["фальшиві друзі перекладача", "калька", "брати участь"],
}

# Hand-curated offline seed (also mirrored in the fixture file).
OFFLINE_SEEDS: list[dict[str, Any]] = [
    {
        "lemma": "actualmente",
        "locale": "es",
        "kind": "false_friend",
        "source_lang": "en",
        "hint": "currently OK; not English 'actually' → en realidad",
        "score": 90,
        "origin": "fixture",
    },
    {
        "lemma": "librería",
        "locale": "es",
        "kind": "false_friend",
        "source_lang": "en",
        "hint": "bookstore OK; not English 'library' → biblioteca",
        "score": 88,
        "origin": "fixture",
    },
    {
        "lemma": "realisieren",
        "locale": "de",
        "kind": "false_friend",
        "source_lang": "en",
        "hint": "implement OK; not English 'realize/understand' → merken",
        "score": 86,
        "origin": "fixture",
    },
    {
        "lemma": "ewentualnie",
        "locale": "pl",
        "kind": "false_friend",
        "source_lang": "en",
        "hint": "optionally OK; not English 'eventually' → ostatecznie",
        "score": 84,
        "origin": "fixture",
    },
    {
        "lemma": "aktualnie",
        "locale": "pl",
        "kind": "false_friend",
        "source_lang": "en",
        "hint": "currently OK; not English 'actually' → właściwie",
        "score": 84,
        "origin": "fixture",
    },
    {
        "lemma": "eventuellt",
        "locale": "sv",
        "kind": "false_friend",
        "source_lang": "en",
        "hint": "possibly OK; not English 'eventually' → så småningom",
        "score": 82,
        "origin": "fixture",
    },
    {
        "lemma": "приймати участь",
        "locale": "uk",
        "kind": "calque",
        "source_lang": "ru",
        "hint": "брати участь (not RU принимать участие)",
        "score": 95,
        "origin": "fixture",
    },
    {
        "lemma": "в залежності від",
        "locale": "uk",
        "kind": "calque",
        "source_lang": "ru",
        "hint": "залежно від (not RU в зависимости от)",
        "score": 94,
        "origin": "fixture",
    },
    {
        "lemma": "делает смысл",
        "locale": "ru",
        "kind": "calque",
        "source_lang": "en",
        "hint": "имеет смысл (not EN makes sense)",
        "score": 96,
        "origin": "fixture",
    },
    {
        "lemma": "orientir",
        "locale": "en",
        "kind": "calque",
        "source_lang": "ru",
        "hint": "working rule / ballpark — not RU ориентир",
        "score": 92,
        "origin": "fixture",
    },
]


def _http_get_json(url: str, timeout: float = 20.0) -> dict[str, Any] | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def fetch_wikt_opensearch(locale: str, query: str, limit: int = 8) -> list[str]:
    """MediaWiki opensearch on the locale Wiktionary."""
    lang = "en" if locale == "en" else locale
    # Ukrainian / Russian Wiktionaries use same language codes.
    host = f"{lang}.wiktionary.org"
    q = urllib.parse.urlencode(
        {
            "action": "opensearch",
            "search": query,
            "limit": str(limit),
            "namespace": "0",
            "format": "json",
        }
    )
    data = _http_get_json(f"https://{host}/w/api.php?{q}")
    if not isinstance(data, list) or len(data) < 2:
        return []
    titles = data[1]
    return [str(t) for t in titles if isinstance(t, str)]


def fetch_kaikki_lexeme(locale: str, lemma: str) -> dict[str, Any] | None:
    """Best-effort Kaikki JSON lookup (network optional)."""
    # Kaikki hosts per-language dumps; word endpoint is unofficial/CDN-ish.
    # We only probe a lightweight raw page; failures fall back silently.
    lang_map = {
        "en": "en",
        "de": "de",
        "es": "es",
        "pl": "pl",
        "ru": "ru",
        "sv": "sv",
        "uk": "uk",
    }
    lang = lang_map.get(locale)
    if not lang:
        return None
    enc = urllib.parse.quote(lemma)
    url = f"https://kaikki.org/dictionary/{lang}/meaning/{enc[0:1].lower()}/{enc}.json"
    return _http_get_json(url)


def score_candidate(lemma: str, kind: str, origin: str) -> int:
    base = 50
    if kind == "false_friend":
        base += 15
    if kind == "calque":
        base += 20
    if origin == "fixture":
        base += 10
    if " " in lemma:
        base += 8
    return min(99, base + max(0, 12 - len(lemma) // 4))


def load_fixture() -> list[dict[str, Any]]:
    if FIXTURE.is_file():
        raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        items = raw.get("candidates") or [] if isinstance(raw, dict) else raw
        return [c for c in items if isinstance(c, dict)]
    return list(OFFLINE_SEEDS)


def mine(
    *,
    locales: list[str],
    limit: int,
    use_network: bool,
) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}

    def add(row: dict[str, Any]) -> None:
        lemma = str(row.get("lemma") or "").strip()
        locale = str(row.get("locale") or "").strip()
        if not lemma or not locale:
            return
        key = (locale, lemma.casefold())
        score = int(
            row.get("score")
            or score_candidate(lemma, str(row.get("kind") or ""), str(row.get("origin") or ""))
        )
        prev = by_key.get(key)
        if prev is None or score > int(prev.get("score") or 0):
            by_key[key] = {
                "lemma": lemma,
                "locale": locale,
                "kind": str(row.get("kind") or "calque"),
                "source_lang": str(row.get("source_lang") or ""),
                "hint": str(row.get("hint") or ""),
                "score": score,
                "origin": str(row.get("origin") or "unknown"),
            }

    for row in load_fixture():
        if row.get("locale") in locales:
            add(row)

    if use_network:
        for locale in locales:
            for query in WIKT_QUERIES.get(locale, []):
                titles = fetch_wikt_opensearch(locale, query, limit=min(8, limit))
                for title in titles:
                    kind = (
                        "false_friend"
                        if "friend" in query.casefold()
                        or "amigo" in query.casefold()
                        or "vriend" in query.casefold()
                        or "друж" in query.casefold()
                        else "calque"
                    )
                    add(
                        {
                            "lemma": title,
                            "locale": locale,
                            "kind": kind,
                            "source_lang": "",
                            "hint": f"Wiktionary hit for query {query!r}",
                            "score": score_candidate(title, kind, "wiktionary"),
                            "origin": "wiktionary-opensearch",
                        }
                    )
                    kaikki = fetch_kaikki_lexeme(locale, title)
                    if isinstance(kaikki, dict) and kaikki:
                        add(
                            {
                                "lemma": title,
                                "locale": locale,
                                "kind": kind,
                                "source_lang": "",
                                "hint": "Kaikki lexeme present",
                                "score": score_candidate(title, kind, "kaikki") + 5,
                                "origin": "kaikki",
                            }
                        )

    ranked = sorted(by_key.values(), key=lambda r: (-int(r["score"]), r["locale"], r["lemma"]))
    return ranked[:limit]


def write_outputs(rows: list[dict[str, Any]]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_path = OUT_DIR / "candidates.json"
    all_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    by_locale: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_locale[str(row["locale"])].append(row)
    for locale, items in by_locale.items():
        (OUT_DIR / f"{locale}.json").write_text(
            json.dumps(items, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    summary = OUT_DIR / "summary.md"
    lines = [
        "# Mined calque / false-friend candidates",
        "",
        f"Total: **{len(rows)}**",
        "",
        "| Locale | Count | Top lemmas |",
        "|---|---:|---|",
    ]
    for locale in sorted(by_locale):
        items = by_locale[locale]
        top = ", ".join(i["lemma"] for i in items[:5])
        lines.append(f"| {locale} | {len(items)} | {top} |")
    lines.append("")
    lines.append("Generated by `scripts/mine_calques_wiktionary.py`. Do not commit raw dumps.")
    lines.append("")
    summary.write_text("\n".join(lines), encoding="utf-8")
    return all_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--locale",
        action="append",
        dest="locales",
        help="Locale to mine (repeatable). Default: all seven.",
    )
    parser.add_argument("--limit", type=int, default=120, help="Max candidates to keep.")
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="Force offline fixture/sample only (no network).",
    )
    parser.add_argument(
        "--network",
        action="store_true",
        help="Attempt Wiktionary/Kaikki network fetch (default unless --fixture).",
    )
    args = parser.parse_args(argv)
    locales = args.locales or ["en", "de", "es", "pl", "ru", "sv", "uk"]
    use_network = (not args.fixture) or bool(args.network)
    rows = mine(locales=locales, limit=args.limit, use_network=use_network)
    if not rows:
        # Hard fallback so the script always produces tmp output.
        rows = [r for r in OFFLINE_SEEDS if r["locale"] in locales][: args.limit]
    path = write_outputs(rows)
    print(f"Wrote {len(rows)} candidates → {path}")
    print(f"Summary → {OUT_DIR / 'summary.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
