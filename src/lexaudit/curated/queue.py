"""Curated rewrite queue - markdown table or JSON (I2-4)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from lexaudit.core.types import PageSuspectRank

CURATED_STATUSES = frozenset({"pending", "in_progress", "done", "skipped"})


@dataclass
class CuratedRow:
    number: int
    status: str
    path: str
    locales: str
    target_defects: str
    note: str


def _slug_from_report_path(path: str) -> str:
    """Strip corpus file prefix to slug-like path."""
    p = path.replace("\\", "/")
    for marker in (
        "pending-academy-articles/",
        "pending-model-packs/",
        "infra/corpus-ci/",
    ):
        if marker in p:
            p = p.split(marker, 1)[1]
    if p.endswith(".json"):
        p = p[: -len(".json")]
    return p


def load_curated(path: Path) -> list[CuratedRow]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return _load_json(text)
    return _load_markdown(text)


def _load_json(text: str) -> list[CuratedRow]:
    data = json.loads(text)
    if isinstance(data, dict) and "rows" in data:
        items = data["rows"]
    elif isinstance(data, list):
        items = data
    else:
        msg = "curated JSON must be a list or {rows: [...]}"
        raise ValueError(msg)
    rows: list[CuratedRow] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        rows.append(
            CuratedRow(
                number=int(item.get("#") or item.get("number") or len(rows) + 1),
                status=str(item.get("status") or "pending"),
                path=str(item.get("path") or item.get("slug") or ""),
                locales=str(item.get("locales") or ""),
                target_defects=str(item.get("target_defects") or item.get("target defects") or ""),
                note=str(item.get("note") or ""),
            )
        )
    return rows


_MD_ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*(\w+)\s*\|\s*`?([^`|]+)`?\s*\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|"
)


def _load_markdown(text: str) -> list[CuratedRow]:
    rows: list[CuratedRow] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        if re.match(r"^\|\s*#?\s*\|", line) or "---" in line:
            continue
        m = _MD_ROW_RE.match(line.strip())
        if not m:
            continue
        num, status, path, locales, defects, note = m.groups()
        path = path.strip().strip("`")
        rows.append(
            CuratedRow(
                number=int(num),
                status=status.strip(),
                path=path,
                locales=locales.strip(),
                target_defects=defects.strip(),
                note=note.strip(),
            )
        )
    return rows


def save_curated(path: Path, rows: list[CuratedRow], *, title: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        doc = {
            "schema_version": "1",
            "rows": [
                {
                    "#": r.number,
                    "status": r.status,
                    "path": r.path,
                    "locales": r.locales,
                    "target_defects": r.target_defects,
                    "note": r.note,
                }
                for r in rows
            ],
        }
        path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return
    header = title or "# lexaudit curated rewrite queue"
    lines = [
        header,
        "",
        "Статусы: `pending` / `in_progress` / `done` / `skipped`.",
        "",
        "| # | status | slug / path | locales | target defects | note |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r.number} | {r.status} | `{r.path}` | {r.locales} | "
            f"{r.target_defects} | {r.note} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def append_pending_from_rank(
    rows: list[CuratedRow],
    pages: list[PageSuspectRank],
    *,
    locale: str,
    needles: list[str] | None = None,
    max_new: int = 50,
) -> list[CuratedRow]:
    """Append pending rows for ranked pages not already listed (by path slug)."""
    existing = {_normalize_path(r.path) for r in rows}
    next_num = max((r.number for r in rows), default=0) + 1
    added = 0
    out = list(rows)
    needle_hint = ", ".join(needles) if needles else ""
    for p in pages:
        if added >= max_new:
            break
        slug = _normalize_path(_slug_from_report_path(p.path))
        if not slug or slug in existing:
            continue
        defects = needle_hint or " ".join(p.sample_words[:6])
        out.append(
            CuratedRow(
                number=next_num,
                status="pending",
                path=slug,
                locales=locale,
                target_defects=defects,
                note=f"score={p.score} unique={p.unique_suspects}",
            )
        )
        existing.add(slug)
        next_num += 1
        added += 1
    return out


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip().strip("`").casefold()


def first_pending(rows: list[CuratedRow]) -> CuratedRow | None:
    for r in rows:
        if r.status == "pending":
            return r
    return None


@dataclass(frozen=True)
class NeedleQueueHit:
    report_path: str
    locale: str
    target_defects: str


def append_pending_from_needle_hits(
    rows: list[CuratedRow],
    hits: list[NeedleQueueHit],
) -> tuple[list[CuratedRow], int]:
    """Append ``pending`` rows for needle scan hits; skip duplicate slugs."""
    existing = {_normalize_path(r.path) for r in rows}
    next_num = max((r.number for r in rows), default=0) + 1
    out = list(rows)
    added = 0
    for h in hits:
        slug = _slug_from_report_path(h.report_path)
        key = _normalize_path(slug)
        if not key or key in existing:
            continue
        out.append(
            CuratedRow(
                number=next_num,
                status="pending",
                path=slug,
                locales=h.locale.upper(),
                target_defects=h.target_defects,
                note="",
            )
        )
        existing.add(key)
        next_num += 1
        added += 1
    return out, added
