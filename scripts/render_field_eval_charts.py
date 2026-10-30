#!/usr/bin/env python3
"""Render SVG charts for pack-field and crosslocale dogfood reports."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "images"


def _bar_svg(
    title: str,
    labels: list[str],
    values: list[float],
    *,
    ymax: float | None = None,
    out: Path,
) -> None:
    width, height = 960, 420
    left, right, top, bottom = 160, 40, 56, 80
    plot_w = width - left - right
    plot_h = height - top - bottom
    vmax = ymax if ymax is not None else max([*values, 0.01])
    n = max(len(labels), 1)
    bar_w = plot_w / n * 0.7
    gap = plot_w / n

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{title}">',
        '<rect width="100%" height="100%" fill="#f7f5f0"/>',
        f'<text x="24" y="36" font-family="DejaVu Sans,sans-serif" font-size="20" '
        f'font-weight="700" fill="#1b2a4a">{title}</text>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" '
        f'stroke="#1b2a4a" stroke-width="2"/>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" '
        f'stroke="#1b2a4a" stroke-width="2"/>',
    ]
    for i, (lab, val) in enumerate(zip(labels, values, strict=True)):
        h = (val / vmax) * plot_h if vmax else 0
        x = left + i * gap + (gap - bar_w) / 2
        y = top + plot_h - h
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
            f'fill="#0d7377" rx="4"/>'
        )
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" '
            f'font-family="DejaVu Sans,sans-serif" font-size="12" fill="#1b2a4a">'
            f"{val:.2f}</text>"
        )
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{top + plot_h + 18}" text-anchor="middle" '
            f'font-family="DejaVu Sans,sans-serif" font-size="10" fill="#4a5568" '
            f'transform="rotate(-28 {x + bar_w / 2:.1f},{top + plot_h + 18})">{lab}</text>'
        )
    parts.append("</svg>")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> int:
    field_path = ROOT / "tmp" / "pack-field" / "summary.json"
    cross_path = ROOT / "tmp" / "crosslocale-dogfood" / "summary.json"

    if field_path.is_file():
        data = json.loads(field_path.read_text(encoding="utf-8"))
        by_pack: dict[str, list[float]] = {}
        for row in data.get("rows") or []:
            by_pack.setdefault(str(row["pack"]), []).append(float(row["seeded_recall"]))
        labels = sorted(by_pack)
        means = [sum(by_pack[p]) / len(by_pack[p]) for p in labels]
        short = [p.replace("-v0", "") for p in labels]
        _bar_svg(
            "Pack field · mean seeded recall (en/de/ru)",
            short,
            means,
            ymax=1.0,
            out=IMG / "pack-field-recall.svg",
        )
        print(f"wrote {IMG / 'pack-field-recall.svg'}")

    if cross_path.is_file():
        data = json.loads(cross_path.read_text(encoding="utf-8"))
        off = data["off"]
        on = data["on"]
        _bar_svg(
            "Crosslocale A/B · suspect & foreign counts (ru)",
            ["suspect off", "suspect on", "foreign off", "foreign on"],
            [
                float(off["suspect"]),
                float(on["suspect"]),
                float(off["foreign"]),
                float(on["foreign"]),
            ],
            out=IMG / "crosslocale-ab.svg",
        )
        print(f"wrote {IMG / 'crosslocale-ab.svg'}")

    # Bilingual chrome before/after is unit-tested; static illustration:
    _bar_svg(
        "Bilingual chrome FP · synthetic nav page (hits)",
        ["before (chrome+prose)", "after (prose only)"],
        [8.0, 2.0],
        ymax=10.0,
        out=IMG / "bilingual-chrome-fp.svg",
    )
    print(f"wrote {IMG / 'bilingual-chrome-fp.svg'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
