"""CI-native helpers: fail criteria, SARIF, GitHub annotations, step summary."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from lexaudit import __version__
from lexaudit.core.types import ClassifiedWord, PageSuspectRank, VocabSample

FAIL_STATUSES = frozenset({"calque", "invented"})
ANOMALY_STATUSES = frozenset({"suspect", "foreign", "calque", "invented", "morph-miss", "unsure"})


def parse_fail_on(raw: str | None) -> frozenset[str]:
    """Parse ``--fail-on`` / ``--check`` status list. Empty → default calque+invented."""
    if raw is None or not str(raw).strip() or str(raw).strip().lower() in {"1", "true", "yes"}:
        return FAIL_STATUSES
    parts = {p.strip().casefold() for p in str(raw).split(",") if p.strip()}
    if "all" in parts:
        return ANOMALY_STATUSES
    return frozenset(parts)


def failing_words(
    words: Iterable[ClassifiedWord],
    *,
    fail_on: frozenset[str],
    needles: Iterable[str] = (),
) -> list[ClassifiedWord]:
    """Words that should fail ``--check`` (status match or needle hit)."""
    needle_list = [n.strip().casefold() for n in needles if n and n.strip()]
    out: list[ClassifiedWord] = []
    for w in words:
        if w.status in fail_on:
            out.append(w)
            continue
        if needle_list and w.status in ANOMALY_STATUSES:
            norm = w.normalized.casefold()
            if any(norm == n or norm.startswith(n) or n in norm for n in needle_list):
                out.append(w)
    return out


def excerpt_around(text: str, needle: str, *, width: int = 200) -> str:
    """Return a short passage around the first case-insensitive hit of ``needle``."""
    if not text or not needle:
        return ""
    lower = text.casefold()
    key = needle.casefold()
    idx = lower.find(key)
    if idx < 0:
        # try first alphanumeric token of surface
        m = re.search(r"[\w\u0400-\u04FF'-]+", needle, re.UNICODE)
        if m:
            idx = lower.find(m.group(0).casefold())
    if idx < 0:
        snippet = " ".join(text.split())
        return snippet[:width]
    half = max(20, width // 2)
    start = max(0, idx - half)
    end = min(len(text), idx + len(needle) + half)
    snippet = text[start:end]
    snippet = " ".join(snippet.split())
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet[: width + 5]


def locate_in_file(repo_root: Path | None, path: str, surface: str) -> tuple[str, int | None]:
    """Return (excerpt, 1-based line) for the first hit of ``surface`` in the file."""
    if not path:
        return "", None
    candidate = Path(path)
    if not candidate.is_file() and repo_root is not None:
        candidate = repo_root / path
    if not candidate.is_file():
        return "", None
    try:
        text = candidate.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "", None
    excerpt = excerpt_around(text, surface)
    line: int | None = None
    key = surface.casefold()
    for i, raw in enumerate(text.splitlines(), start=1):
        if key and key in raw.casefold():
            line = i
            break
    return excerpt, line


def load_excerpt(repo_root: Path | None, path: str, surface: str) -> str:
    return locate_in_file(repo_root, path, surface)[0]


def build_findings(
    words: list[ClassifiedWord],
    *,
    locale: str,
    repo_root: Path | None = None,
    fail_on: frozenset[str] | None = None,
) -> list[dict[str, Any]]:
    """Flat findings list for editors and SARIF."""
    interesting = fail_on or ANOMALY_STATUSES
    rows: list[dict[str, Any]] = []
    for w in sorted(words, key=lambda x: (-x.count, x.normalized)):
        if w.status in {"ok", "proper", "acronym", "template"}:
            continue
        if w.status not in interesting and w.status not in ANOMALY_STATUSES:
            continue
        samples = list(w.samples) if w.samples else [VocabSample(path="", scope="body")]
        for sample in samples:
            path = sample.path
            scope = sample.scope
            excerpt, found_line = locate_in_file(repo_root, path, w.surface)
            line = sample.line if sample.line is not None else found_line
            rows.append(
                {
                    "locale": locale,
                    "path": path,
                    "scope": scope,
                    "line": line,
                    "word": w.surface,
                    "normalized": w.normalized,
                    "status": w.status,
                    "tier": w.tier,
                    "reason": w.reason,
                    "hint": "",
                    "count": w.count,
                    "excerpt": excerpt,
                }
            )
    return rows


def build_sarif(
    findings: list[dict[str, Any]],
    *,
    tool_name: str = "lexaudit",
) -> dict[str, Any]:
    """SARIF 2.1.0 document with one result per finding."""
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    for f in findings:
        rule_id = str(f.get("status") or "suspect")
        if rule_id not in rules:
            rules[rule_id] = {
                "id": rule_id,
                "shortDescription": {"text": f"lexaudit status: {rule_id}"},
                "fullDescription": {
                    "text": "Flagged vocabulary issue (calque, invented word, or related anomaly)."
                },
                "defaultConfiguration": {
                    "level": "error" if rule_id in FAIL_STATUSES else "warning"
                },
            }
        level = "error" if rule_id in FAIL_STATUSES else "warning"
        loc: dict[str, Any] = {
            "physicalLocation": {
                "artifactLocation": {"uri": str(f.get("path") or "unknown")},
            }
        }
        if f.get("line") is not None:
            loc["physicalLocation"]["region"] = {"startLine": int(f["line"])}
        msg = f.get("excerpt") or f.get("reason") or f.get("word") or rule_id
        results.append(
            {
                "ruleId": rule_id,
                "level": level,
                "message": {
                    "text": f"{f.get('word')} ({rule_id}): {msg}",
                },
                "locations": [loc],
                "properties": {
                    "normalized": f.get("normalized"),
                    "tier": f.get("tier"),
                    "reason": f.get("reason"),
                    "locale": f.get("locale"),
                },
            }
        )
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "version": __version__,
                        "informationUri": "https://github.com/nareyko/lexaudit",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }


def emit_github_annotations(findings: list[dict[str, Any]]) -> None:
    for f in findings:
        path = str(f.get("path") or "unknown")
        line = f.get("line")
        level = "error" if f.get("status") in FAIL_STATUSES else "warning"
        msg = f"{f.get('word')} ({f.get('status')}): {f.get('reason') or f.get('excerpt') or ''}"
        msg = msg.replace("\n", " ").replace("%", "%25")
        if line is not None:
            print(f"::{level} file={path},line={int(line)}::{msg}")
        else:
            print(f"::{level} file={path}::{msg}")


def append_step_summary(pages: list[PageSuspectRank], locale: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    lines = [
        f"### lexaudit / {locale}",
        "",
        "| score | unique | path | top words |",
        "|---:|---:|---|---|",
    ]
    for p in pages[:20]:
        top = " ".join(p.sample_words[:6])
        lines.append(f"| {p.score} | {p.unique_suspects} | `{p.path}` | {top} |")
    lines.append("")
    # Append to the Actions step summary file (never to corpus sources).
    summary = Path(path)
    existing = summary.read_text(encoding="utf-8") if summary.is_file() else ""
    summary.write_text(existing + "\n".join(lines), encoding="utf-8")


def write_sarif(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
