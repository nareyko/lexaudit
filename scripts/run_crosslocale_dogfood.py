#!/usr/bin/env python3
"""A/B dogfood: enable_crosslocale off vs on on pack-field RU (+ EN reference)."""

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
PACKS = [
    "saas-ui-v0",
    "fintech-v0",
    "developer-docs-v0",
    "ecommerce-ui-v0",
    "healthcare-ui-v0",
]


def _run(*, cross: bool, out_tag: str) -> dict[str, object]:
    # EN+RU trees under several packs share terminology; reference locale = en.
    paths = []
    for pack in PACKS:
        for loc in ("en", "ru"):
            paths.append((FIELD / pack / loc).resolve())
    rules = ROOT / "packs" / "saas-ui-v0" / "calques"
    cfg = LexauditConfig(
        repo_root=FIELD,
        locales=["ru"],
        sources=["files"],
        files_paths=tuple(paths),
        calque_rules_dir=rules.resolve(),
        enable_crosslocale=cross,
        crosslocale_reference_locale="en",
        output_dir=(ROOT / "tmp" / "crosslocale-dogfood" / out_tag).resolve(),
    )
    words, pages, _ = run_locale_audit(cfg, "ru", freeze_generated_at="1970-01-01T00:00:00Z")
    by_status: dict[str, int] = {}
    by_tier: dict[str, int] = {}
    cross_hits = 0
    for w in words:
        by_status[w.status] = by_status.get(w.status, 0) + 1
        if w.tier:
            by_tier[w.tier] = by_tier.get(w.tier, 0) + 1
        if "crosslocale" in (w.detectors or []):
            cross_hits += 1
    top = sorted(pages, key=lambda p: p.score, reverse=True)[:8]
    return {
        "enable_crosslocale": cross,
        "words": len(words),
        "pages": len(pages),
        "status": by_status,
        "tier": by_tier,
        "crosslocale_hits": cross_hits,
        "likely": by_tier.get("likely", 0),
        "top_pages": [{"path": p.path, "score": round(p.score, 3)} for p in top],
        "suspect": by_status.get("suspect", 0),
        "foreign": by_status.get("foreign", 0),
        "calque": by_status.get("calque", 0),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "tmp" / "crosslocale-dogfood" / "summary.json",
    )
    ap.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "p1-crosslocale-dogfood-2026-10-30.md",
    )
    args = ap.parse_args()

    off = _run(cross=False, out_tag="off")
    on = _run(cross=True, out_tag="on")
    delta_suspect = int(on["suspect"]) - int(off["suspect"])
    delta_foreign = int(on["foreign"]) - int(off["foreign"])
    delta_likely = int(on["likely"]) - int(off["likely"])
    cross_hits = int(on["crosslocale_hits"])

    # Verdict: useful if on changes ranking or tiers without exploding FP.
    useful = cross_hits > 0 or abs(delta_likely) > 0 or abs(delta_suspect) + abs(delta_foreign) > 0
    explode = int(on["suspect"]) > int(off["suspect"]) * 1.5 + 20
    if explode:
        verdict = (
            "KEEP DEFAULT OFF — crosslocale inflated suspects sharply on this "
            "corpus; treat as experimental opt-in only."
        )
    elif useful:
        verdict = (
            "KEEP DEFAULT OFF — opt-in OK: ref_present mode boosts tiers "
            f"(crosslocale_hits={cross_hits}, delta_likely={delta_likely:+d}); "
            "not a default-on feature."
        )
    else:
        verdict = (
            "KEEP DEFAULT OFF — no meaningful tier/status delta on this corpus; "
            "flag stays available for consumers with aligned EN reference docs."
        )

    payload = {
        "off": off,
        "on": on,
        "delta_suspect": delta_suspect,
        "delta_foreign": delta_foreign,
        "delta_likely": delta_likely,
        "crosslocale_hits": cross_hits,
        "verdict": verdict,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    off_row = (
        f"| off | {off['words']} | {off['pages']} | {off['suspect']} | "
        f"{off['foreign']} | {off['likely']} | {off['crosslocale_hits']} |"
    )
    on_row = (
        f"| on | {on['words']} | {on['pages']} | {on['suspect']} | "
        f"{on['foreign']} | {on['likely']} | {on['crosslocale_hits']} |"
    )
    deltas = (
        f"Delta suspect: {delta_suspect:+d}. "
        f"Delta foreign: {delta_foreign:+d}. "
        f"Delta likely: {delta_likely:+d}."
    )
    report = "\n".join(
        [
            "# Crosslocale dogfood · 2026-10-30",
            "",
            "Corpus: `tests/fixtures/packs_field/` (EN+RU trees for five packs),",
            "audit locale `ru`, reference locale `en`.",
            "Package default stays `enable_crosslocale: false`.",
            "",
            "![Crosslocale A/B](images/crosslocale-ab.svg)",
            "",
            "## Results",
            "",
            "| Mode | words | pages | suspect | foreign | likely | xl hits |",
            "|---|---:|---:|---:|---:|---:|---:|",
            off_row,
            on_row,
            "",
            deltas,
            "",
            "## Verdict",
            "",
            verdict,
            "",
            "Opt-in recipe: `examples/lexaudit.config.crosslocale.yaml`.",
            "",
            "## Reproduce",
            "",
            "```bash",
            "uv run python scripts/run_crosslocale_dogfood.py",
            "uv run python scripts/render_field_eval_charts.py",
            "```",
            "",
        ]
    )
    args.report.write_text(report, encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"wrote {args.report}")
    print(verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
