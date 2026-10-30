#!/usr/bin/env python3
"""A4/E: clean-domain + packs_wild must not explode pack calque FPs.

Writes ``docs/p1-clean-wild-sanity-2026-10-30.md`` and ``tmp/clean-wild/summary.json``.
tmp/ is gitignored.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lexaudit.config import LexauditConfig  # noqa: E402
from lexaudit.core.pipeline import run_locale_audit  # noqa: E402

FIELD = ROOT / "tests" / "fixtures" / "packs_field"
WILD = ROOT / "tests" / "fixtures" / "packs_wild"


def _audit(pack: str, loc: str, tree: Path) -> dict[str, object]:
    rules = ROOT / "packs" / pack / "calques"
    if not rules.is_dir() or not tree.is_dir():
        return {"skip": True}
    cfg = LexauditConfig(
        repo_root=tree,
        locales=[loc],
        sources=["files"],
        files_paths=(tree.resolve(),),
        calque_rules_dir=rules.resolve(),
        output_dir=(ROOT / "tmp" / "clean-wild" / pack / loc).resolve(),
    )
    words, pages, _ = run_locale_audit(
        cfg, loc, freeze_generated_at="1970-01-01T00:00:00Z"
    )
    calques = sorted({w.normalized for w in words if w.status == "calque"})
    return {
        "pages": len(pages),
        "calque_unique": len(calques),
        "calques_sample": calques[:8],
        "top_score": round(max((p.score for p in pages), default=0.0), 3),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "tmp" / "clean-wild" / "summary.json",
    )
    ap.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "p1-clean-wild-sanity-2026-10-30.md",
    )
    args = ap.parse_args()

    rows: list[dict[str, object]] = []
    clean_fp = 0
    for pack_dir in sorted(p for p in FIELD.iterdir() if p.is_dir()):
        pack = pack_dir.name
        if not (ROOT / "packs" / pack / "calques").is_dir():
            continue
        for loc in ("en", "de", "ru"):
            # Clean-domain only (no defect seeds).
            clean_dir = pack_dir / loc
            if not clean_dir.is_dir():
                continue
            # Point files_paths at the locale dir but pipeline walks all md —
            # copy filter: audit via a temp list by setting files_paths to specific files.
            files = sorted(clean_dir.glob("0*-clean*.md"))
            if not files:
                continue
            rules = ROOT / "packs" / pack / "calques"
            cfg = LexauditConfig(
                repo_root=clean_dir,
                locales=[loc],
                sources=["files"],
                files_paths=tuple(f.resolve() for f in files),
                calque_rules_dir=rules.resolve(),
                output_dir=(ROOT / "tmp" / "clean-wild" / "clean" / pack / loc).resolve(),
            )
            words, pages, _ = run_locale_audit(
                cfg, loc, freeze_generated_at="1970-01-01T00:00:00Z"
            )
            calques = sorted({w.normalized for w in words if w.status == "calque"})
            clean_fp += len(calques)
            rows.append(
                {
                    "kind": "clean-domain",
                    "pack": pack,
                    "locale": loc,
                    "pages": len(pages),
                    "calque_unique": len(calques),
                    "calques_sample": calques[:8],
                }
            )

    wild_hits = 0
    for pack_dir in sorted(p for p in WILD.iterdir() if p.is_dir()):
        pack = pack_dir.name
        if not (ROOT / "packs" / pack / "calques").is_dir():
            continue
        for loc_dir in sorted(p for p in pack_dir.iterdir() if p.is_dir()):
            loc = loc_dir.name
            r = _audit(pack, loc, loc_dir)
            if r.get("skip"):
                continue
            wild_hits += int(r["calque_unique"])  # type: ignore[arg-type]
            rows.append({"kind": "wild", "pack": pack, "locale": loc, **r})

    payload = {
        "rows": rows,
        "clean_calque_fp_total": clean_fp,
        "wild_calque_unique_sum": wild_hits,
        "verdict": (
            "OK — clean-domain calque FP=0; wild calque sum is exploratory"
            if clean_fp == 0
            else f"FAIL — clean-domain calque FP={clean_fp}"
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Clean-domain + wild sanity · 2026-10-30",
        "",
        "Track A4/E: pack rules on ordinary domain prose and Wikipedia wild extracts.",
        "Clean pages must not raise calques. Wild hits stay exploratory (often 0).",
        "",
        f"Clean-domain calque FP total: **{clean_fp}**.",
        f"Wild calque unique sum: **{wild_hits}**.",
        "",
        f"Verdict: {payload['verdict']}",
        "",
        "| kind | pack | locale | pages | calque unique | sample |",
        "|---|---|---|---:|---:|---|",
    ]
    for r in rows:
        sample = ", ".join(r.get("calques_sample") or []) or "—"  # type: ignore[arg-type]
        lines.append(
            f"| {r['kind']} | `{r['pack']}` | {r['locale']} | {r['pages']} | "
            f"{r['calque_unique']} | {sample} |"
        )
    lines += [
        "",
        "## Reproduce",
        "",
        "```bash",
        "uv run python scripts/run_clean_wild_sanity.py",
        "uv run python scripts/check_pack_density.py",
        "```",
        "",
        "Do not commit `tmp/clean-wild/`.",
        "",
    ]
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(payload["verdict"])
    print(f"wrote {args.report}")
    return 1 if clean_fp else 0


if __name__ == "__main__":
    raise SystemExit(main())
