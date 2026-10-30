#!/usr/bin/env python3
"""Compute CRAP scores from coverage.json + radon CC.

CRAP(m) = comp(m)^2 * (1 - cov(m)/100)^3 + comp(m)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COV_JSON = ROOT / "coverage.json"
OUT_MD = ROOT / "artifacts" / "crap-report.md"
THRESHOLD = 30.0  # warn above this; common industry soft gate


def _run_coverage() -> None:
    subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "-q",
            "--cov=lexaudit",
            "--cov-report=json:coverage.json",
            "--cov-report=term-missing",
        ],
        cwd=ROOT,
        check=True,
    )


def _radon_cc() -> list[dict]:
    proc = subprocess.run(
        ["uv", "run", "radon", "cc", "-s", "-j", "src/lexaudit"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(proc.stdout)
    rows: list[dict] = []
    for path, items in data.items():
        for item in items:
            if item.get("type") not in {"function", "method"}:
                continue
            rows.append(
                {
                    "path": path,
                    "name": item["name"],
                    "lineno": item["lineno"],
                    "complexity": int(item["complexity"]),
                    "fullname": f"{path}:{item['name']}",
                }
            )
    return rows


def _file_coverage(cov: dict) -> dict[str, float]:
    """Map absolute/relative file path → percent covered (0..100)."""
    out: dict[str, float] = {}
    files = cov.get("files") or {}
    for path, meta in files.items():
        summary = meta.get("summary") or {}
        pct = float(summary.get("percent_covered") or 0.0)
        # normalize to repo-relative
        rel = path
        if "src/lexaudit" in path.replace("\\", "/"):
            rel = "src/lexaudit/" + path.replace("\\", "/").split("src/lexaudit/")[-1]
        out[rel] = pct
        out[Path(path).name] = pct
    return out


def crap(comp: int, cov_pct: float) -> float:
    uncovered = 1.0 - (cov_pct / 100.0)
    return (comp**2) * (uncovered**3) + comp


def main() -> int:
    if "--skip-pytest" not in sys.argv:
        _run_coverage()
    if not COV_JSON.is_file():
        print("missing coverage.json", file=sys.stderr)
        return 2
    cov = json.loads(COV_JSON.read_text(encoding="utf-8"))
    file_cov = _file_coverage(cov)
    rows = _radon_cc()
    scored = []
    for row in rows:
        path = row["path"].replace("\\", "/")
        if (not path.startswith("src/")) and ("src/lexaudit" in path):
            path = "src/lexaudit/" + path.split("src/lexaudit/")[-1]
        pct = file_cov.get(path)
        if pct is None:
            for k, v in file_cov.items():
                if k.endswith(Path(path).name) or path.endswith(k):
                    pct = v
                    break
        pct = float(pct if pct is not None else 0.0)
        score = crap(row["complexity"], pct)
        scored.append({**row, "path": path, "coverage": pct, "crap": score})

    scored.sort(key=lambda r: (-r["crap"], r["path"], r["name"]))
    hot = [r for r in scored if r["crap"] >= THRESHOLD]
    lines = [
        "# CRAP report",
        "",
        f"Threshold: **{THRESHOLD}** (gate: build fails at or above).",
        f"Functions scored: {len(scored)}; above threshold: {len(hot)}.",
        "",
        "| CRAP | CC | cov% | function |",
        "|---:|---:|---:|---|",
    ]
    for r in scored[:40]:
        lines.append(
            f"| {r['crap']:.1f} | {r['complexity']} | {r['coverage']:.1f} "
            f"| `{r['path']}:{r['name']}` |"
        )
    lines.append("")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_MD}")
    print(f"hotspots>={THRESHOLD}: {len(hot)}")
    for r in hot[:15]:
        label = f"{r['path']}:{r['name']}"
        print(f"  {r['crap']:.1f} cc={r['complexity']} cov={r['coverage']:.1f} {label}")
    if hot:
        print(f"FAIL: {len(hot)} function(s) at or above CRAP {THRESHOLD}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
