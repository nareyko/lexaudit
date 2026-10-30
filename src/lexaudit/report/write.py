"""Deterministic report writers - no timestamps in CSV/MD bodies."""

from __future__ import annotations

import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lexaudit import __version__
from lexaudit.core.types import ClassifiedWord, PageSuspectRank
from lexaudit.report.ci import ANOMALY_STATUSES, build_findings, build_sarif, write_sarif
from lexaudit.schema_validate import validate_report


def _stats(words: list[ClassifiedWord]) -> dict[str, int]:
    counts: dict[str, int] = {
        "ok": 0,
        "proper": 0,
        "acronym": 0,
        "foreign": 0,
        "calque": 0,
        "invented": 0,
        "morph-miss": 0,
        "template": 0,
        "unsure": 0,
        "suspect": 0,
        "all": 0,
    }
    for w in words:
        counts["all"] += 1
        if w.status in counts:
            counts[w.status] += 1
        else:
            counts["suspect"] += 1
    return counts


def build_report_doc(
    *,
    locale: str,
    words: list[ClassifiedWord],
    pages: list[PageSuspectRank],
    config_hash: str,
    generated_at: str | None = None,
    detector_stats: dict[str, int] | None = None,
) -> dict[str, Any]:
    word_rows = []
    for w in sorted(words, key=lambda x: (-x.count, x.normalized)):
        word_rows.append(
            {
                "word": w.surface,
                "norm": w.normalized,
                "status": w.status,
                "tier": w.tier,
                "reason": w.reason,
                "detectors": sorted(w.detectors),
                "count": w.count,
                "samples": [
                    {"path": s.path, "scope": s.scope}
                    for s in sorted(w.samples, key=lambda s: (s.path, s.scope))
                ],
                "occurrences": [
                    {"path": s.path, "scope": s.scope, "line": None}
                    for s in sorted(w.samples, key=lambda s: (s.path, s.scope))
                ],
            }
        )
    page_rows = [
        {
            "path": p.path,
            "score": p.score,
            "unique_suspects": p.unique_suspects,
            "top_words": list(p.sample_words),
        }
        for p in pages
    ]
    doc: dict[str, Any] = {
        "schema_version": "1",
        "generated_at": generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lexaudit_version": __version__,
        "config_hash": config_hash,
        "locales": [
            {
                "locale": locale,
                "stats": _stats(words),
                "words": word_rows,
                "pages": page_rows,
            }
        ],
    }
    if detector_stats is not None:
        doc["detector_stats"] = dict(sorted(detector_stats.items()))
    validate_report(doc)
    return doc


def _write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)


def _html_escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def write_html_report(
    path: Path,
    *,
    locale: str,
    pages: list[PageSuspectRank],
    findings: list[dict[str, Any]],
) -> None:
    """Self-contained HTML report for editors (no CDN)."""
    rows = []
    for p in pages:
        rows.append(
            "<tr>"
            f"<td>{_html_escape(p.score)}</td>"
            f"<td>{_html_escape(p.unique_suspects)}</td>"
            f"<td><a href='#text-{_html_escape(p.path)}'>{_html_escape(p.path)}</a></td>"
            f"<td>{_html_escape(' '.join(p.sample_words[:8]))}</td>"
            "</tr>"
        )
    finding_blocks = []
    for i, f in enumerate(findings[:200]):
        finding_blocks.append(
            "<details open>"
            f"<summary><code>{_html_escape(f.get('word'))}</code> "
            f"({_html_escape(f.get('status'))}) in "
            f"<code>{_html_escape(f.get('path'))}</code></summary>"
            f"<p>{_html_escape(f.get('excerpt') or f.get('reason') or '')}</p>"
            f"<p id='f-{i}'><small>tier={_html_escape(f.get('tier'))} "
            f"reason={_html_escape(f.get('reason'))}</small></p>"
            "</details>"
        )
    body = f"""<!DOCTYPE html>
<html lang="{_html_escape(locale)}">
<head>
<meta charset="utf-8"/>
<title>lexaudit {_html_escape(locale)}</title>
<style>
body {{ font-family: Georgia, 'Times New Roman', serif; color: #1a1a1a; background: #f7f5f0;
  margin: 2rem auto; max-width: 960px; line-height: 1.45; }}
h1,h2 {{ font-family: system-ui, sans-serif; font-weight: 600; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th,td {{ border-bottom: 1px solid #ccc; padding: 0.4rem 0.5rem; text-align: left;
  vertical-align: top; font-size: 0.95rem; }}
th {{ font-family: system-ui, sans-serif; }}
a {{ color: #0b3d5c; }}
code {{ font-size: 0.9em; }}
details {{ margin: 0.6rem 0; padding: 0.4rem 0.6rem; background: #fff; border: 1px solid #ddd; }}
</style>
</head>
<body>
<h1>lexaudit report / {_html_escape(locale)}</h1>
<p>Detection only. Passages below are excerpts around flagged words.</p>
<h2>Top texts</h2>
<table>
<thead><tr><th>score</th><th>unique</th><th>path</th><th>top words</th></tr></thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
<h2>Findings</h2>
{"".join(finding_blocks) if finding_blocks else "<p>No anomalies.</p>"}
</body>
</html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def write_reports(
    *,
    out_dir: Path,
    locale: str,
    words: list[ClassifiedWord],
    pages: list[PageSuspectRank],
    config_hash: str,
    generated_at: str | None = None,
    detector_stats: dict[str, int] | None = None,
    freeze_generated_at: str | None = None,
    repo_root: Path | None = None,
    write_html: bool = True,
    write_sarif_file: bool = False,
) -> dict[str, Path]:
    """
    Write JSON/CSV/MD/HTML reports.

    For determinism tests, pass freeze_generated_at so JSON header is stable.
    CSV/MD bodies never contain timestamps.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = freeze_generated_at or generated_at
    doc = build_report_doc(
        locale=locale,
        words=words,
        pages=pages,
        config_hash=config_hash,
        generated_at=stamp,
        detector_stats=detector_stats,
    )

    # Deterministic JSON body for words/pages: rewrite generated_at only in header.
    # For byte-identical runs, caller should pass the same freeze_generated_at.
    json_path = out_dir / "report.json"
    json_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # Also words.json compatible-ish map for parity tooling
    words_path = out_dir / "words.json"
    words_doc = {
        "meta": {
            "locale": locale,
            "config_hash": config_hash,
            "lexaudit_version": __version__,
        },
        "words": [
            {
                "word": w.normalized,
                "surface": w.surface,
                "status": w.status,
                "tier": w.tier,
                "count": w.count,
                "samples": [{"path": s.path, "field": s.scope} for s in w.samples],
            }
            for w in sorted(words, key=lambda x: (-x.count, x.normalized))
        ],
    }
    words_path.write_text(
        json.dumps(words_doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    suspect_rows: list[list[str]] = []
    for w in sorted(words, key=lambda x: (-x.count, x.normalized)):
        if w.status in {"ok", "proper", "acronym", "template"}:
            continue
        sample_paths = "; ".join(f"{s.path}#{s.scope}" for s in w.samples)
        suspect_rows.append([w.normalized, w.surface, str(w.count), sample_paths])
    suspect_path = out_dir / "suspect.csv"
    _write_csv(suspect_path, ["word", "surface", "count", "sample_paths"], suspect_rows)

    page_rows = [
        [p.path, str(p.score), str(p.unique_suspects), " ".join(p.sample_words)] for p in pages
    ]
    pages_path = out_dir / "pages.csv"
    _write_csv(pages_path, ["path", "score", "unique_suspects", "sample_words"], page_rows)

    stats = _stats(words)
    md_lines = [
        f"# lexaudit summary / {locale}",
        "",
        "## Totals",
        "",
        "| status | count |",
        "|---|---|",
    ]
    for key in sorted(stats):
        md_lines.append(f"| {key} | {stats[key]} |")
    md_lines += ["", "## Worst texts", ""]
    md_lines += ["| path | score | unique_suspects | top |", "|---|---|---|---|"]
    for p in pages[:25]:
        top = " ".join(p.sample_words[:8])
        md_lines.append(f"| {p.path} | {p.score} | {p.unique_suspects} | {top} |")
    md_lines += ["", "## Top suspects", ""]
    md_lines += ["| word | count | status | tier |", "|---|---|---|---|"]
    anomalies = [
        w
        for w in sorted(words, key=lambda x: (-x.count, x.normalized))
        if w.status not in {"ok", "proper", "acronym", "template"}
    ]
    for w in anomalies[:40]:
        md_lines.append(f"| {w.normalized} | {w.count} | {w.status} | {w.tier or ''} |")
    md_lines.append("")
    summary_path = out_dir / "summary.md"
    summary_path.write_text("\n".join(md_lines), encoding="utf-8")

    queue_rows = [
        {
            "locale": locale,
            "path": p.path,
            "score": p.score,
            "unique_suspects": p.unique_suspects,
            "top_words": p.sample_words,
        }
        for p in pages
    ]
    queue_json = out_dir / "queue.json"
    queue_json.write_text(
        json.dumps(queue_rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    queue_md_lines = [
        f"# Rewrite queue / {locale}",
        "",
        "| score | unique_suspects | path | top_words |",
        "|---|---|---|---|",
    ]
    for p in pages:
        queue_md_lines.append(
            f"| {p.score} | {p.unique_suspects} | {p.path} | {' '.join(p.sample_words[:8])} |"
        )
    queue_md_lines.append("")
    queue_md = out_dir / "queue.md"
    queue_md.write_text("\n".join(queue_md_lines), encoding="utf-8")

    findings = build_findings(words, locale=locale, repo_root=repo_root)
    findings_path = out_dir / "findings.json"
    findings_path.write_text(
        json.dumps(findings, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    paths: dict[str, Path] = {
        "report": json_path,
        "words": words_path,
        "suspect": suspect_path,
        "pages": pages_path,
        "summary": summary_path,
        "queue_json": queue_json,
        "queue_md": queue_md,
        "findings": findings_path,
    }
    if write_html:
        html_path = out_dir / "report.html"
        write_html_report(html_path, locale=locale, pages=pages, findings=findings)
        paths["html"] = html_path
    if write_sarif_file:
        sarif_path = out_dir / "results.sarif"
        write_sarif(
            sarif_path,
            build_sarif([f for f in findings if f.get("status") in ANOMALY_STATUSES]),
        )
        paths["sarif"] = sarif_path
    return paths
