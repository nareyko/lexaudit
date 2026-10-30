"""Collect reader-facing text chunks from configured corpus paths (read-only)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from lexaudit.core.types import TextChunk


def _walk_files(root: Path, suffixes: tuple[str, ...]) -> Iterator[Path]:
    if not root.exists():
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part.startswith(".") or part == "node_modules" for part in path.parts):
            continue
        if path.suffix.lower() in suffixes:
            yield path


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _iter_json_strings(node: Any, prefix: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(node, str):
        if node.strip():
            yield prefix or "json", node
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from _iter_json_strings(item, f"{prefix}[{i}]" if prefix else f"[{i}]")
    elif isinstance(node, dict):
        for key, val in sorted(node.items(), key=lambda kv: str(kv[0])):
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from _iter_json_strings(val, next_prefix)


def collect_academy(
    repo_root: Path, locale: str, *, academy_root: Path | None = None
) -> list[TextChunk]:
    root = academy_root or (repo_root / "infra" / "corpus-ci" / "pending-academy-articles")
    chunks: list[TextChunk] = []
    fields = ("title", "excerpt", "metaDescription", "bodyMarkdown")
    for path in _walk_files(root, (".json",)):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        translations = data.get("translations") or {}
        block = translations.get(locale) or {}
        if not isinstance(block, dict):
            continue
        rel = _rel(path, repo_root)
        for field in fields:
            text = block.get(field)
            if isinstance(text, str) and text.strip():
                chunks.append(TextChunk(path=rel, scope=field, text=text, source="academy"))
    return chunks


def collect_packs(
    repo_root: Path, locale: str, *, packs_root: Path | None = None
) -> list[TextChunk]:
    root = packs_root or (repo_root / "infra" / "corpus-ci" / "pending-model-packs")
    chunks: list[TextChunk] = []
    payload_fields = (
        "overview",
        "designHistory",
        "typicalProblems",
        "annualCostsMd",
        "surveyChecklistMd",
    )
    for path in _walk_files(root, (".json",)):
        if path.name != "export.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows = data.get("packRows") or data.get("rows") or []
        if not isinstance(rows, list):
            continue
        rel = _rel(path, repo_root)
        for row in rows:
            if not isinstance(row, dict):
                continue
            if row.get("locale") != locale:
                continue
            payload = row.get("payload") or row
            if not isinstance(payload, dict):
                continue
            for field in payload_fields:
                text = payload.get(field)
                if isinstance(text, str) and text.strip():
                    chunks.append(TextChunk(path=rel, scope=field, text=text, source="packs"))
    return chunks


def collect_md(repo_root: Path, locale: str) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    frontend = repo_root / "frontend"
    if locale == "en":
        roots = [
            frontend / "content" / "blog",
            frontend / "content" / "pages",
            frontend / "content" / "courses",
        ]
        for root in roots:
            for path in _walk_files(root, (".md", ".json")):
                rel = _rel(path, repo_root)
                if path.suffix == ".md":
                    text = path.read_text(encoding="utf-8")
                    chunks.append(TextChunk(path=rel, scope="markdown", text=text, source="md"))
                else:
                    try:
                        data = json.loads(path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        continue
                    for scope, text in _iter_json_strings(data):
                        chunks.append(TextChunk(path=rel, scope=scope, text=text, source="md"))
        for extra, scope in (
            (frontend / "content" / "ui.md", "ui"),
            (frontend / "content" / "home-faq.json", "json"),
        ):
            if not extra.is_file():
                continue
            rel = _rel(extra, repo_root)
            if extra.suffix == ".md":
                chunks.append(
                    TextChunk(
                        path=rel,
                        scope=scope,
                        text=extra.read_text(encoding="utf-8"),
                        source="md",
                    )
                )
            else:
                try:
                    data = json.loads(extra.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                for s, text in _iter_json_strings(data):
                    chunks.append(TextChunk(path=rel, scope=s, text=text, source="md"))
    else:
        root = frontend / "translations" / locale
        for path in _walk_files(root, (".md", ".json")):
            rel = _rel(path, repo_root)
            if path.suffix == ".md":
                chunks.append(
                    TextChunk(
                        path=rel,
                        scope="markdown",
                        text=path.read_text(encoding="utf-8"),
                        source="md",
                    )
                )
            else:
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                for scope, text in _iter_json_strings(data):
                    chunks.append(TextChunk(path=rel, scope=scope, text=text, source="md"))
    return chunks


def _markdown_chunks(path: Path, rel: str, source: str) -> list[TextChunk]:
    """Split a Markdown file into optional H1 title and body chunks."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return []
    if not raw.strip():
        return []
    lines = raw.splitlines()
    title_lines: list[str] = []
    body_lines: list[str] = []
    found_h1 = False
    for line in lines:
        stripped = line.strip()
        if not found_h1 and stripped.startswith("# ") and not stripped.startswith("##"):
            title_lines.append(stripped[2:].strip())
            found_h1 = True
        else:
            body_lines.append(line)
    out: list[TextChunk] = []
    title_text = "\n".join(title_lines).strip()
    body_text = "\n".join(body_lines).strip()
    if title_text:
        out.append(TextChunk(path=rel, scope="title", text=title_text, source=source))
    if body_text:
        out.append(TextChunk(path=rel, scope="body", text=body_text, source=source))
    return out


DEFAULT_ROOT_MD_FILES: tuple[str, ...] = (
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
)


def collect_files(
    repo_root: Path,
    locale: str,
    *,
    files_paths: tuple[Path, ...] = (),
) -> list[TextChunk]:
    """Collect standard Markdown/JSON documentation files."""
    chunks: list[TextChunk] = []
    targets: list[Path] = []
    if files_paths:
        targets.extend(files_paths)
    else:
        for name in DEFAULT_ROOT_MD_FILES:
            candidate = repo_root / name
            if candidate.is_file():
                targets.append(candidate)
        docs_dir = repo_root / "docs"
        if (docs_dir / locale).is_dir():
            targets.append(docs_dir / locale)
        elif docs_dir.is_dir():
            targets.append(docs_dir)

    seen: set[Path] = set()
    for target in targets:
        resolved_target = target if target.is_absolute() else (repo_root / target)
        paths_iter: Iterator[Path]
        if resolved_target.is_file():
            paths_iter = iter((resolved_target,))
        else:
            paths_iter = _walk_files(resolved_target, (".md", ".markdown"))
        for path in paths_iter:
            real = path.resolve()
            if real in seen:
                continue
            seen.add(real)
            rel = _rel(path, repo_root)
            if path.suffix.lower() in (".md", ".markdown"):
                chunks.extend(_markdown_chunks(path, rel, source="files"))
            elif path.suffix.lower() == ".json":
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                for scope, text in _iter_json_strings(data):
                    chunks.append(TextChunk(path=rel, scope=scope, text=text, source="files"))
    return chunks


def collect_jsonl_export(path: Path, locale: str) -> list[TextChunk]:
    """Read JSONL export rows with path/scope/text/locale fields."""
    chunks: list[TextChunk] = []
    if not path.is_file():
        return chunks
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("locale") and row["locale"] != locale:
            continue
        text = row.get("text") or ""
        if not isinstance(text, str) or not text.strip():
            continue
        chunks.append(
            TextChunk(
                path=str(row.get("path") or path.name),
                scope=str(row.get("scope") or "body"),
                text=text,
                source="jsonl_export",
            )
        )
    return chunks


def collect_all(
    repo_root: Path,
    locale: str,
    sources: set[str] | None = None,
    *,
    jsonl_export: Path | None = None,
    academy_root: Path | None = None,
    packs_root: Path | None = None,
    files_paths: tuple[Path, ...] = (),
) -> list[TextChunk]:
    """Collect chunks for selected sources. Never writes."""
    wanted = sources or {"academy", "packs", "md"}
    chunks: list[TextChunk] = []
    if "academy" in wanted:
        chunks.extend(collect_academy(repo_root, locale, academy_root=academy_root))
    if "packs" in wanted:
        chunks.extend(collect_packs(repo_root, locale, packs_root=packs_root))
    if "md" in wanted:
        chunks.extend(collect_md(repo_root, locale))
    if "files" in wanted or "docs" in wanted:
        chunks.extend(collect_files(repo_root, locale, files_paths=files_paths))
    if "jsonl_export" in wanted and jsonl_export is not None:
        chunks.extend(collect_jsonl_export(jsonl_export, locale))
    chunks.sort(key=lambda c: (c.source, c.path, c.scope))
    return chunks
