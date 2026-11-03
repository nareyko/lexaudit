"""``.lexaudit-baseline.json`` — suppress known findings for ``--check``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lexaudit.core.types import ClassifiedWord


def baseline_key(locale: str, path: str, normalized: str, status: str) -> tuple[str, str, str, str]:
    return (
        locale.casefold(),
        path,
        normalized.casefold(),
        status.casefold(),
    )


def finding_key(finding: dict[str, Any]) -> tuple[str, str, str, str]:
    return baseline_key(
        str(finding.get("locale") or ""),
        str(finding.get("path") or ""),
        str(finding.get("normalized") or finding.get("word") or ""),
        str(finding.get("status") or ""),
    )


def word_keys(word: ClassifiedWord, locale: str) -> list[tuple[str, str, str, str]]:
    samples = word.samples or []
    if not samples:
        return [baseline_key(locale, "", word.normalized, word.status)]
    return [baseline_key(locale, s.path, word.normalized, word.status) for s in samples]


def load_baseline(path: Path) -> set[tuple[str, str, str, str]]:
    """Load suppression keys from a baseline JSON file."""
    if not path.is_file():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    items: list[Any]
    if isinstance(data, dict):
        raw = data.get("findings") or data.get("entries") or data.get("suppressions") or []
        items = raw if isinstance(raw, list) else []
    elif isinstance(data, list):
        items = data
    else:
        return set()
    out: set[tuple[str, str, str, str]] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        out.add(
            baseline_key(
                str(item.get("locale") or ""),
                str(item.get("path") or ""),
                str(item.get("normalized") or item.get("word") or ""),
                str(item.get("status") or ""),
            )
        )
    return out


def write_baseline(
    path: Path,
    findings: list[dict[str, Any]],
    *,
    schema_version: str = "1",
) -> None:
    """Write unique (locale, path, normalized, status) entries for accepted findings."""
    seen: set[tuple[str, str, str, str]] = set()
    entries: list[dict[str, str]] = []
    for f in findings:
        key = finding_key(f)
        if key in seen:
            continue
        seen.add(key)
        entries.append(
            {
                "locale": key[0],
                "path": key[1],
                "normalized": key[2],
                "status": key[3],
            }
        )
    entries.sort(key=lambda e: (e["locale"], e["path"], e["normalized"], e["status"]))
    doc = {"schema_version": schema_version, "findings": entries}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def apply_baseline_to_findings(
    findings: list[dict[str, Any]],
    baseline: set[tuple[str, str, str, str]],
) -> list[dict[str, Any]]:
    """Mark findings covered by the baseline as ``suppressed: true``."""
    out: list[dict[str, Any]] = []
    for f in findings:
        row = dict(f)
        row["suppressed"] = finding_key(f) in baseline if baseline else False
        out.append(row)
    return out


def filter_unsuppressed_words(
    words: list[ClassifiedWord],
    *,
    locale: str,
    baseline: set[tuple[str, str, str, str]],
) -> list[ClassifiedWord]:
    """Drop words whose every sample key is covered by the baseline."""
    if not baseline:
        return list(words)
    kept: list[ClassifiedWord] = []
    for w in words:
        keys = word_keys(w, locale)
        if keys and all(k in baseline for k in keys):
            continue
        kept.append(w)
    return kept
