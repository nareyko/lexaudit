#!/usr/bin/env python3
"""Harvest a few CX leftover-like pairs from a local dump (never commit the dump).

Expects ``dumps/cx-corpora.ru2en.text.json.gz`` (or ``--dump``). Writes:
- ``docs/p1-cx-sample-ids-2026-10-30.md`` (ids only)
- optional short fixtures under ``tests/fixtures/bilingual/cx_samples/``

Download first (gitignored):

  curl -L -o dumps/cx-corpora.ru2en.text.json.gz \\
    https://dumps.wikimedia.org/other/contenttranslation/20261016/cx-corpora.ru2en.text.json.gz
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DUMP = ROOT / "dumps" / "cx-corpora.ru2en.text.json.gz"
IDS_DOC = ROOT / "docs" / "p1-cx-sample-ids-2026-10-30.md"
OUT_FIX = ROOT / "tests" / "fixtures" / "bilingual" / "cx_samples"

_LATIN = re.compile(r"[A-Za-z]{5,}")
_CYR = re.compile(r"[\u0400-\u04FF]{4,}")


def _content(block: object) -> str:
    if isinstance(block, dict):
        return str(block.get("content") or "").strip()
    return str(block or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dump", type=Path, default=DEFAULT_DUMP)
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--write-fixtures", action="store_true")
    ap.add_argument("--scan-cap", type=int, default=5000, help="Max records to scan")
    args = ap.parse_args()

    if not args.dump.is_file():
        print(f"missing dump: {args.dump}")
        print("See docs/p1-cx-corpora-notes-2026-10-30.md — download into dumps/ first.")
        IDS_DOC.write_text(
            "\n".join(
                [
                    "# CX sample ids · 2026-10-30",
                    "",
                    "No dump present locally. Download `cx-corpora.ru2en.text.json.gz`",
                    "into `dumps/` (gitignored), then re-run:",
                    "",
                    "```bash",
                    "uv run python scripts/harvest_cx_leftover_samples.py --write-fixtures",
                    "```",
                    "",
                    "Do not commit the dump.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return 0

    with gzip.open(args.dump, "rt", encoding="utf-8", errors="replace") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        print("unexpected dump shape")
        return 1

    picks: list[tuple[str, str, str, str]] = []
    for rec in data[: args.scan_cap]:
        if not isinstance(rec, dict):
            continue
        source = _content(rec.get("source"))
        target = _content(rec.get("target"))
        if len(source) < 40 or len(target) < 40:
            continue
        # Prefer true leftovers: Cyrillic still in EN target.
        cyr_in_en = bool(_CYR.search(target))
        identical = source.casefold() == target.casefold()
        if not (cyr_in_en or identical):
            continue
        kind = "identical" if identical else "cyrillic-in-en"
        sid = str(rec.get("id") or f"row-{len(picks)}")
        picks.append((sid, kind, source[:500], target[:500]))
        if len(picks) >= args.limit:
            break

    lines = [
        "# CX sample ids · 2026-10-30",
        "",
        f"Dump: `{args.dump.name}` (local only; not in git).",
        f"Scanned {min(len(data), args.scan_cap)} / {len(data)} records; "
        f"kept {len(picks)} leftover-like segments.",
        "",
        "| id | kind |",
        "|---|---|",
        *[f"| `{sid}` | {kind} |" for sid, kind, _, _ in picks],
        "",
        "Short fixtures (if `--write-fixtures`) are trimmed + attributed; dump stays out.",
        "",
    ]
    IDS_DOC.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {IDS_DOC.relative_to(ROOT)} ({len(picks)} ids)")

    if args.write_fixtures and picks:
        OUT_FIX.mkdir(parents=True, exist_ok=True)
        (OUT_FIX / "SOURCES.md").write_text(
            "\n".join(
                [
                    "# CX leftover samples (trimmed)",
                    "",
                    "Source dump: Wikimedia Content Translation `ru2en` text JSON.",
                    "License: treat as CC BY-SA Wikipedia-derived; short extracts only.",
                    "Full dump must stay in `dumps/` (gitignored).",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        for i, (sid, kind, source, target) in enumerate(picks[:5], start=1):
            (OUT_FIX / "ru").mkdir(parents=True, exist_ok=True)
            (OUT_FIX / "en").mkdir(parents=True, exist_ok=True)
            (OUT_FIX / "ru" / f"{i:02d}.md").write_text(
                f"# CX sample {sid}\n\n> kind: {kind}\n\n{source}\n",
                encoding="utf-8",
            )
            (OUT_FIX / "en" / f"{i:02d}.md").write_text(
                f"# CX sample {sid}\n\n> kind: {kind}\n\n{target}\n",
                encoding="utf-8",
            )
        print(f"wrote fixtures under {OUT_FIX.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
