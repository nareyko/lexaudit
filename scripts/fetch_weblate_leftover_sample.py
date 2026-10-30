#!/usr/bin/env python3
"""Time-boxed sample of public hosted.weblate.org units with Latin overlap (lab).

Network required. Unauthenticated API is throttled — keep queries small.
Does not write fixtures; prints JSON for manual curation into live_weblate/.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_LATIN = re.compile(r"\b[A-Za-z][A-Za-z']{3,}\b")

DEFAULT_QUERIES: list[tuple[str, str]] = [
    ("ru", 'target:"Onboarding complete"'),
    ("ru", "target:Toast source:Toast"),
    ("ru", "target:Inbox source:Inbox state:translated"),
    ("de", "target:Toast source:Toast"),
    ("de", "target:Dashboard source:Dashboard state:translated"),
    ("ru", 'target:"Sign in" state:translated'),
    ("de", 'target:"Sign in" state:translated'),
]


def _fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("/tmp/lexaudit-live-units.json"))
    p.add_argument("--sleep", type=float, default=0.25)
    args = p.parse_args()

    rows: list[dict[str, object]] = []
    for lang, q in DEFAULT_QUERIES:
        query = f"language:{lang} {q}"
        url = (
            "https://hosted.weblate.org/api/units/?"
            + urllib.parse.urlencode({"q": query, "page_size": 20})
        )
        try:
            data = _fetch(url)
        except urllib.error.HTTPError as exc:
            print(f"HTTP {exc.code} for {query}")
            continue
        print(f"{query}: count={data.get('count')}")
        for unit in data.get("results") or []:
            src = unit.get("source")
            tgt = unit.get("target")
            if isinstance(src, list):
                src = " ".join(map(str, src))
            if isinstance(tgt, list):
                tgt = " ".join(map(str, tgt))
            if not src or not tgt:
                continue
            src_l = {m.group(0).casefold() for m in _LATIN.finditer(str(src))}
            overlap = sorted(
                {
                    m.group(0).casefold()
                    for m in _LATIN.finditer(str(tgt))
                    if m.group(0).casefold() in src_l
                }
            )
            if not overlap:
                continue
            rows.append(
                {
                    "lang": lang,
                    "source": src,
                    "target": tgt,
                    "overlap": overlap,
                    "web_url": unit.get("web_url"),
                }
            )
        time.sleep(args.sleep)

    args.out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
