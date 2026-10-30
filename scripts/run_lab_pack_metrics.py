#!/usr/bin/env python3
"""Run lab_pack_metrics for every packs/_lab/* with EN/RU/DE fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lab_pack_metrics import measure  # noqa: E402

LAB = ROOT / "packs" / "_lab"
LOCALES = ("en", "ru", "de")


def main() -> int:
    rows: list[dict[str, object]] = []
    failed = 0
    for pack_dir in sorted(p for p in LAB.iterdir() if p.is_dir()):
        for loc in LOCALES:
            if not (pack_dir / "fixtures" / loc).is_dir():
                continue
            report = measure(pack_dir.name, loc)
            rows.append(report)
            status = "ok" if report["lab_rank_ok"] else "FAIL"
            if not report["lab_rank_ok"]:
                failed += 1
            print(
                f"{status} {pack_dir.name}/{loc} "
                f"recall={report['known_rule_recall']} "
                f"calques={report['calque_words']}"
            )
    out = ROOT / "tmp" / "lab-packs" / "summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out} ({len(rows)} rows, failed={failed})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
