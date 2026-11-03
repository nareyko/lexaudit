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


def locate_in_file(
    repo_root: Path | None, path: str, surface: str
) -> tuple[str, int | None, int | None, int | None]:
    """Return (excerpt, 1-based line, start_col, end_col) for the first hit of ``surface``."""
    if not path:
        return "", None, None, None
    candidate = Path(path)
    if not candidate.is_file() and repo_root is not None:
        candidate = repo_root / path
    if not candidate.is_file():
        return "", None, None, None
    try:
        text = candidate.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "", None, None, None
    excerpt = excerpt_around(text, surface)
    line: int | None = None
    start_col: int | None = None
    end_col: int | None = None
    key = surface.casefold()
    for i, raw in enumerate(text.splitlines(), start=1):
        pos = raw.casefold().find(key) if key else -1
        if pos >= 0:
            line = i
            start_col = pos + 1
            end_col = pos + len(surface) + 1
            break
    return excerpt, line, start_col, end_col


def load_excerpt(repo_root: Path | None, path: str, surface: str) -> str:
    return locate_in_file(repo_root, path, surface)[0]


def format_location(path: str, line: int | None, start_col: int | None = None) -> str:
    """Format ``path:line:col`` (omit missing trailing parts)."""
    if line is None:
        return path or "unknown"
    if start_col is None:
        return f"{path}:{line}"
    return f"{path}:{line}:{start_col}"


def _sanitize_rule_part(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip())
    return cleaned.strip("-._") or "unknown"


def sarif_rule_id(finding: dict[str, Any]) -> str:
    """Hierarchical rule id: ``calque.<locale>.<source_lang_or_id>``."""
    status = _sanitize_rule_part(str(finding.get("status") or "suspect")).casefold()
    locale = _sanitize_rule_part(str(finding.get("locale") or "und")).casefold()
    source = (
        finding.get("source_id")
        or finding.get("source_lang")
        or finding.get("reason")
        or status
    )
    source_part = _sanitize_rule_part(str(source)).casefold()
    return f"{status}.{locale}.{source_part}"


def sarif_message(finding: dict[str, Any]) -> str:
    """Message with «span» → «hint» when a hint is present."""
    span = str(finding.get("word") or finding.get("normalized") or "")
    hint = str(finding.get("hint") or "").strip()
    status = str(finding.get("status") or "suspect")
    if hint:
        return f"«{span}» → «{hint}»"
    excerpt = str(finding.get("excerpt") or finding.get("reason") or "")
    if excerpt:
        return f"{span} ({status}): {excerpt}"
    return f"{span} ({status})"


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
            excerpt, found_line, found_sc, found_ec = locate_in_file(repo_root, path, w.surface)
            line = sample.line if sample.line is not None else found_line
            start_col = sample.start_col if sample.start_col is not None else found_sc
            end_col = sample.end_col if sample.end_col is not None else found_ec
            rows.append(
                {
                    "locale": locale,
                    "path": path,
                    "scope": scope,
                    "line": line,
                    "start_col": start_col,
                    "end_col": end_col,
                    "word": w.surface,
                    "normalized": w.normalized,
                    "status": w.status,
                    "tier": w.tier,
                    "reason": w.reason,
                    "hint": w.hint,
                    "source_id": w.source_id,
                    "count": w.count,
                    "excerpt": excerpt,
                    "suppressed": False,
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
        if f.get("suppressed"):
            continue
        rule_id = sarif_rule_id(f)
        status = str(f.get("status") or "suspect")
        if rule_id not in rules:
            rules[rule_id] = {
                "id": rule_id,
                "shortDescription": {"text": f"lexaudit status: {status}"},
                "fullDescription": {
                    "text": "Flagged vocabulary issue (calque, invented word, or related anomaly)."
                },
                "defaultConfiguration": {
                    "level": "error" if status in FAIL_STATUSES else "warning"
                },
            }
        level = "error" if status in FAIL_STATUSES else "warning"
        region: dict[str, Any] = {}
        if f.get("line") is not None:
            region["startLine"] = int(f["line"])
        if f.get("start_col") is not None:
            region["startColumn"] = int(f["start_col"])
        if f.get("end_col") is not None:
            region["endColumn"] = int(f["end_col"])
        loc: dict[str, Any] = {
            "physicalLocation": {
                "artifactLocation": {"uri": str(f.get("path") or "unknown")},
            }
        }
        if region:
            loc["physicalLocation"]["region"] = region
        results.append(
            {
                "ruleId": rule_id,
                "level": level,
                "message": {"text": sarif_message(f)},
                "locations": [loc],
                "properties": {
                    "normalized": f.get("normalized"),
                    "tier": f.get("tier"),
                    "reason": f.get("reason"),
                    "hint": f.get("hint"),
                    "locale": f.get("locale"),
                    "source_id": f.get("source_id"),
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
        if f.get("suppressed"):
            continue
        path = str(f.get("path") or "unknown")
        line = f.get("line")
        col = f.get("start_col")
        level = "error" if f.get("status") in FAIL_STATUSES else "warning"
        msg = sarif_message(f).replace("\n", " ").replace("%", "%25")
        if line is not None and col is not None:
            print(f"::{level} file={path},line={int(line)},col={int(col)}::{msg}")
        elif line is not None:
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
