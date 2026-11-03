"""Collect reader-facing text chunks from configured corpus paths (read-only)."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from lexaudit.core.types import TextChunk

# Non-prose JSON keys (ids, URLs, paths, icons) — skip in collect_md / UI JSON.
_JSON_NON_PROSE_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "slug",
        "url",
        "href",
        "icon",
        "image",
        "avatar",
        "date",
        "publishedat",
        "updatedat",
        "code",
        "locale",
        "category",
        "path",
        "ctaurl",
        "videourl",
        "src",
        "srcset",
        "thumbnail",
        "ogimage",
        "canonical",
        "key",
        "uid",
        "uuid",
        "filename",
        "filetype",
        "mimetype",
        "extension",
    }
)

_URL_OR_PATH_RE = re.compile(
    r"^(?:https?://|/|\./|\.\./|[A-Za-z0-9_.-]+/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]*)$"
)
_TS_STRING_RE = re.compile(
    r""""((?:\\.|[^"\\])*)"|'((?:\\.|[^'\\])*)'|`((?:\\.|[^`\\]|\$\{[^}]*\})*)`""",
    re.MULTILINE,
)
_TS_LOCALE_OBJECT_RE = re.compile(
    r"""(?P<loc>\b(?:en|de|es|pl|ru|sv|uk|ar|zh|he)\b)\s*:\s*\{""",
    re.MULTILINE,
)
_TS_CASE_RETURN_RE = re.compile(
    r"""case\s+["'](?P<loc>en|de|es|pl|ru|sv|uk|ar|zh|he)["']\s*:\s*return\s+"""
    r"""(?P<q>["'`])(?P<body>(?:\\.|(?!\2).)*)(?P=q)""",
    re.MULTILINE,
)


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


def _leaf_key(prefix: str) -> str:
    if not prefix:
        return ""
    # Strip list indices: faqItems[0].question → question
    cleaned = re.sub(r"\[\d+\]", "", prefix)
    return cleaned.rsplit(".", 1)[-1].casefold()


def _is_non_prose_json_string(prefix: str, value: str) -> bool:
    key = _leaf_key(prefix)
    if key in _JSON_NON_PROSE_KEYS:
        return True
    stripped = value.strip()
    if not stripped:
        return True
    if _URL_OR_PATH_RE.match(stripped):
        return True
    return bool(
        stripped.startswith(("http://", "https://", "mailto:", "/")) and " " not in stripped
    )


def _iter_json_strings(node: Any, prefix: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(node, str):
        if node.strip() and not _is_non_prose_json_string(prefix, node):
            yield prefix or "json", node
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from _iter_json_strings(item, f"{prefix}[{i}]" if prefix else f"[{i}]")
    elif isinstance(node, dict):
        for key, val in sorted(node.items(), key=lambda kv: str(kv[0])):
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(val, str) and _is_non_prose_json_string(next_prefix, val):
                continue
            if str(key).casefold() in _JSON_NON_PROSE_KEYS and not isinstance(val, (dict, list)):
                continue
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


def _unescape_ts_string(raw: str) -> str:
    """Unescape common TS/JS string escapes without breaking UTF-8 prose."""
    return (
        raw.replace(r"\\", "\0")
        .replace(r"\n", "\n")
        .replace(r"\t", "\t")
        .replace(r"\'", "'")
        .replace(r"\"", '"')
        .replace(r"\`", "`")
        .replace("\0", "\\")
    )


def _extract_balanced_object(src: str, open_brace_index: int) -> str | None:
    """Return substring of `{...}` starting at ``open_brace_index``, or None."""
    if open_brace_index < 0 or open_brace_index >= len(src) or src[open_brace_index] != "{":
        return None
    depth = 0
    in_str: str | None = None
    escape = False
    for i in range(open_brace_index, len(src)):
        ch = src[i]
        if in_str:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == in_str:
                in_str = None
            continue
        if ch in {'"', "'", "`"}:
            in_str = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[open_brace_index : i + 1]
    return None


def _strings_from_ts_fragment(fragment: str) -> list[str]:
    out: list[str] = []
    for m in _TS_STRING_RE.finditer(fragment):
        raw = (
            m.group(1)
            if m.group(1) is not None
            else m.group(2)
            if m.group(2) is not None
            else m.group(3)
        )
        if raw is None:
            continue
        # Skip template interpolations / code-like tokens.
        if "${" in raw:
            continue
        text = _unescape_ts_string(raw).strip()
        if len(text) < 4:
            continue
        if _URL_OR_PATH_RE.match(text) or text.startswith(("http://", "https://", "@/", "./")):
            continue
        # Skip pure identifiers / CSS-ish tokens.
        if re.fullmatch(r"[A-Za-z0-9_./:-]+", text) and " " not in text:
            continue
        out.append(text)
    return out


def collect_ts_prose(repo_root: Path, locale: str) -> list[TextChunk]:
    """Read-only extract of locale-scoped reader strings from ``frontend/src/lib/yachts/``."""
    root = repo_root / "frontend" / "src" / "lib" / "yachts"
    chunks: list[TextChunk] = []
    loc = locale.casefold()
    if not root.is_dir():
        return chunks
    for path in _walk_files(root, (".ts", ".tsx")):
        if (
            "__tests__" in path.parts
            or path.name.endswith(".test.ts")
            or path.name.endswith(".test.tsx")
        ):
            continue
        try:
            src = path.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = _rel(path, repo_root)
        collected: list[str] = []
        # Pattern A: `case "ru": return "..."`
        for m in _TS_CASE_RETURN_RE.finditer(src):
            if m.group("loc").casefold() != loc:
                continue
            body = _unescape_ts_string(m.group("body")).strip()
            if len(body) >= 4:
                collected.append(body)
        # Pattern B: `ru: { ... }` locale object literals
        for m in _TS_LOCALE_OBJECT_RE.finditer(src):
            if m.group("loc").casefold() != loc:
                continue
            brace_at = src.find("{", m.start())
            block = _extract_balanced_object(src, brace_at)
            if not block:
                continue
            collected.extend(_strings_from_ts_fragment(block))
        if not collected:
            continue
        # Deduplicate while preserving order.
        seen: set[str] = set()
        unique: list[str] = []
        for t in collected:
            if t in seen:
                continue
            seen.add(t)
            unique.append(t)
        chunks.append(
            TextChunk(
                path=rel,
                scope=f"ts:{loc}",
                text="\n\n".join(unique),
                source="ts_prose",
            )
        )
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
    title_line_no: int | None = None
    body_lines: list[str] = []
    body_first_line: int | None = None
    found_h1 = False
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not found_h1 and stripped.startswith("# ") and not stripped.startswith("##"):
            title_lines.append(stripped[2:].strip())
            title_line_no = idx
            found_h1 = True
        else:
            if body_first_line is None:
                body_first_line = idx
            body_lines.append(line)
    out: list[TextChunk] = []
    title_text = "\n".join(title_lines).strip()
    raw_body = "\n".join(body_lines)
    # Preserve leading content for offsets; only drop fully empty bodies.
    body_text = raw_body.strip("\n")
    if title_text:
        out.append(
            TextChunk(
                path=rel,
                scope="title",
                text=title_text,
                source=source,
                line_base=title_line_no or 1,
            )
        )
    if body_text.strip():
        # Adjust line_base for leading blank lines removed by strip("\n").
        leading_nl = len(raw_body) - len(raw_body.lstrip("\n"))
        base = (body_first_line or 1) + leading_nl
        out.append(
            TextChunk(
                path=rel,
                scope="body",
                text=body_text,
                source=source,
                line_base=base,
            )
        )
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
            dir_walk = False
        else:
            # Directory walks skip .json (explicit file targets still load JSON).
            paths_iter = _walk_files(
                resolved_target,
                (".md", ".markdown", ".html", ".htm", ".po", ".xliff", ".xlf", ".rst"),
            )
            dir_walk = True
        for path in paths_iter:
            real = path.resolve()
            if real in seen:
                continue
            seen.add(real)
            rel = _rel(path, repo_root)
            suf = path.suffix.lower()
            if suf in (".md", ".markdown"):
                chunks.extend(_markdown_chunks(path, rel, source="files"))
            elif suf in (".html", ".htm"):
                from lexaudit.sources.formats import collect_html_file

                chunks.extend(collect_html_file(path, rel, source="files"))
            elif suf == ".po":
                from lexaudit.sources.formats import collect_po_file

                chunks.extend(collect_po_file(path, rel))
            elif suf in (".xliff", ".xlf"):
                from lexaudit.sources.formats import collect_xliff_file

                chunks.extend(collect_xliff_file(path, rel))
            elif suf == ".rst":
                from lexaudit.sources.formats import collect_rst_file

                chunks.extend(collect_rst_file(path, rel, source="files"))
            elif suf in {".json", ".yaml", ".yml"} and not dir_walk:
                from lexaudit.sources.formats import collect_i18n_file

                chunks.extend(collect_i18n_file(path, rel, source="files"))
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
    if "ts_prose" in wanted:
        chunks.extend(collect_ts_prose(repo_root, locale))
    if "files" in wanted or "docs" in wanted:
        chunks.extend(collect_files(repo_root, locale, files_paths=files_paths))
    if "jsonl_export" in wanted and jsonl_export is not None:
        chunks.extend(collect_jsonl_export(jsonl_export, locale))
    if wanted & {"gettext", "po", "xliff", "html", "l10n"}:
        from lexaudit.sources.formats import collect_l10n_tree

        chunks.extend(collect_l10n_tree(repo_root, locale, files_paths=files_paths))
    if "mkdocs" in wanted:
        from lexaudit.sources.formats import collect_mkdocs

        chunks.extend(collect_mkdocs(repo_root, locale))
    if "docusaurus" in wanted:
        from lexaudit.sources.formats import collect_docusaurus

        chunks.extend(collect_docusaurus(repo_root, locale))
    if "vitepress" in wanted:
        from lexaudit.sources.formats import collect_vitepress

        chunks.extend(collect_vitepress(repo_root, locale))
    chunks.sort(key=lambda c: (c.source, c.path, c.scope))
    return chunks
