#!/usr/bin/env python3
"""Exploratory metrics: pack rules vs Wikipedia packs_wild extracts (no fail gate)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lexaudit.config import LexauditConfig  # noqa: E402
from lexaudit.core.pipeline import run_locale_audit  # noqa: E402

WILD = ROOT / "tests" / "fixtures" / "packs_wild"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "tmp" / "pack-wild" / "summary.json",
    )
    ap.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "p1-pack-wild-eval-2026-10-30.md",
    )
    args = ap.parse_args()

    rows: list[dict[str, object]] = []
    for pack_dir in sorted(p for p in WILD.iterdir() if p.is_dir()):
        pack = pack_dir.name
        rules = ROOT / "packs" / pack / "calques"
        if not rules.is_dir():
            continue
        for loc_dir in sorted(p for p in pack_dir.iterdir() if p.is_dir()):
            loc = loc_dir.name
            md = list(loc_dir.glob("*.md"))
            if not md:
                continue
            cfg = LexauditConfig(
                repo_root=loc_dir,
                locales=[loc],
                sources=["files"],
                files_paths=(loc_dir.resolve(),),
                calque_rules_dir=rules.resolve(),
                output_dir=(ROOT / "tmp" / "pack-wild" / pack / loc).resolve(),
            )
            words, pages, _ = run_locale_audit(cfg, loc, freeze_generated_at="1970-01-01T00:00:00Z")
            calques = sorted({w.normalized for w in words if w.status == "calque"})
            rows.append(
                {
                    "pack": pack,
                    "locale": loc,
                    "pages": len(pages),
                    "calque_unique": len(calques),
                    "calques_sample": calques[:12],
                    "top_score": round(max((p.score for p in pages), default=0.0), 3),
                }
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps({"rows": rows}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Pack wild eval (Wikipedia) · 2026-10-30",
        "",
        "Exploratory: RC pack rules against CC BY-SA Wikipedia summaries in",
        "`tests/fixtures/packs_wild/`. Not a precision gold — hits need human review.",
        "",
        f"Rows: {len(rows)}. Refresh corpus: `uv run python scripts/fetch_wiki_pack_samples.py`.",
        "",
        "| Pack | Locale | pages | calque unique | sample |",
        "|---|---|---:|---:|---|",
    ]
    for r in rows:
        sample = ", ".join(str(x) for x in (r["calques_sample"] or [])[:5]) or "—"
        lines.append(
            f"| `{r['pack']}` | {r['locale']} | {r['pages']} | {r['calque_unique']} | {sample} |"
        )
    lines += [
        "",
        "## Note",
        "",
        "Encyclopedic prose rarely contains SaaS coinages; low calque counts are expected.",
        "Use this to catch accidental over-matching (brands/common words), not for recall.",
        "",
    ]
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out} rows={len(rows)}")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
