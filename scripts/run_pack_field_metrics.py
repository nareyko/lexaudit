#!/usr/bin/env python3
"""Held-out pack field metrics (not the pack's own 04-defect-known fixtures)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lexaudit.config import LexauditConfig  # noqa: E402
from lexaudit.core.pipeline import run_locale_audit  # noqa: E402

FIELD = ROOT / "tests" / "fixtures" / "packs_field"
PACKS = [
    "saas-ui-v0",
    "fintech-v0",
    "developer-docs-v0",
    "ecommerce-ui-v0",
    "healthcare-ui-v0",
    "legal-docs-v0",
    "gaming-ui-v0",
    "edtech-v0",
    "security-docs-v0",
    "hr-ats-v0",
]
LOCALES = ("en", "de", "ru")


def _measure(pack: str, locale: str) -> dict[str, object]:
    pack_dir = ROOT / "packs" / pack
    fixtures = FIELD / pack / locale
    rules = pack_dir / "calques"
    gold_tokens: set[str] = set()
    gold_path = FIELD / "gold.csv"
    with gold_path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["pack"] == pack and row["locale"] == locale and row["label"] == "seeded_calque":
                gold_tokens.add(row["token"].casefold())

    cfg = LexauditConfig(
        repo_root=fixtures,
        locales=[locale],
        sources=["files"],
        files_paths=(fixtures.resolve(),),
        calque_rules_dir=rules.resolve(),
        output_dir=(ROOT / "tmp" / "pack-field" / pack / locale).resolve(),
    )
    words, pages, _ = run_locale_audit(cfg, locale, freeze_generated_at="1970-01-01T00:00:00Z")
    calque_norms = {w.normalized.casefold() for w in words if w.status == "calque"}
    hit = gold_tokens & calque_norms
    recall = (len(hit) / len(gold_tokens)) if gold_tokens else 0.0

    clean_calques = 0
    defect_score = 0.0
    clean_score = 0.0
    for p in pages:
        if "01-clean" in p.path:
            clean_score = max(clean_score, float(p.score))
            # count calques attributed to clean page via samples — approximate by path in words
        if "04-defect" in p.path:
            defect_score = max(defect_score, float(p.score))

    for w in words:
        if w.status != "calque":
            continue
        for s in w.samples:
            if "01-clean" in s.path:
                clean_calques += 1
                break

    return {
        "pack": pack,
        "locale": locale,
        "gold_tokens": len(gold_tokens),
        "gold_hits": len(hit),
        "seeded_recall": round(recall, 4),
        "clean_calque_hits": clean_calques,
        "defect_score": round(defect_score, 3),
        "clean_score": round(clean_score, 3),
        "rank_ok": defect_score > clean_score,
        "recall_ok": recall >= 0.70,
        "clean_ok": clean_calques == 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "tmp" / "pack-field" / "summary.json",
    )
    ap.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "p1-pack-field-eval-2026-10-30.md",
    )
    args = ap.parse_args()

    rows: list[dict[str, object]] = []
    for pack in PACKS:
        for loc in LOCALES:
            rows.append(_measure(pack, loc))

    failed = [r for r in rows if not (r["recall_ok"] and r["clean_ok"] and r["rank_ok"])]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps({"rows": rows, "failed": len(failed)}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    by_pack: dict[str, list[dict[str, object]]] = defaultdict(list)
    for r in rows:
        by_pack[str(r["pack"])].append(r)

    lines = [
        "# Pack field eval · 2026-10-30",
        "",
        "Held-out corpus: `tests/fixtures/packs_field/` (not pack `04-defect-known`).",
        f"Rows: {len(rows)}. Failed gates: **{len(failed)}** "
        "(need seeded_recall≥0.70, clean_calque_hits=0, defect_score>clean_score).",
        "",
        "![Pack field recall](images/pack-field-recall.svg)",
        "",
        "| Pack | en recall | de recall | ru recall | clean FP (sum) | rank OK |",
        "|---|---:|---:|---:|---:|:---:|",
    ]
    for pack in PACKS:
        rs = {str(r["locale"]): r for r in by_pack[pack]}
        clean_fp = sum(int(r["clean_calque_hits"]) for r in by_pack[pack])
        rank_ok = all(bool(r["rank_ok"]) for r in by_pack[pack])
        lines.append(
            f"| `{pack}` | {rs['en']['seeded_recall']:.2f} | {rs['de']['seeded_recall']:.2f} | "
            f"{rs['ru']['seeded_recall']:.2f} | {clean_fp} | {'yes' if rank_ok else 'no'} |"
        )

    mean_rec = sum(float(r["seeded_recall"]) for r in rows) / len(rows)
    lines += [
        "",
        f"Macro mean seeded recall: **{mean_rec:.3f}**.",
        "",
        "## Method",
        "",
        "Each RC pack's rules audit reconstructed clean + seeded pages under "
        "`tests/fixtures/packs_field/<pack>/{en,de,ru}/`. Seeded tokens come from "
        "that pack's YAML (see `gold.csv`). This is still coinage-shaped, but the "
        "**page prose and paths are held out** from the original lab fixtures.",
        "",
        "## Reproduce",
        "",
        "```bash",
        "uv run python scripts/run_pack_field_metrics.py",
        "uv run python scripts/render_field_eval_charts.py",
        "```",
        "",
    ]
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out} rows={len(rows)} failed={len(failed)} mean_recall={mean_rec:.3f}")
    print(f"wrote {args.report}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
