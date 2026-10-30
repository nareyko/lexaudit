"""Additional corpus formats: HTML, gettext PO, XLIFF, MkDocs, Docusaurus, VitePress."""

from __future__ import annotations

import re
from collections.abc import Iterator
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

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


def _markdown_chunks(path: Path, rel: str, source: str) -> list[TextChunk]:
    from lexaudit.sources.collect import _markdown_chunks as md_chunks

    return md_chunks(path, rel, source)


_PO_MSGSTR_RE = re.compile(
    r'^msgstr(?:\[\d+\])?\s+"(.*)"\s*$',
    re.MULTILINE,
)
_PO_CONT_RE = re.compile(r'^"(.*)"\s*$', re.MULTILINE)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        text = data.strip()
        if text:
            self._chunks.append(text)

    def text(self) -> str:
        return "\n".join(self._chunks)


def html_to_text(raw: str) -> str:
    parser = _HTMLTextExtractor()
    try:
        parser.feed(raw)
        parser.close()
    except Exception:
        return re.sub(r"<[^>]+>", " ", raw)
    return parser.text()


def collect_html_file(path: Path, rel: str, source: str = "html") -> list[TextChunk]:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    text = html_to_text(raw).strip()
    if not text:
        return []
    return [TextChunk(path=rel, scope="body", text=text, source=source)]


def _unescape_po(s: str) -> str:
    return s.replace(r"\\", "\\").replace(r"\"", '"').replace(r"\n", "\n").replace(r"\t", "\t")


def collect_po_file(path: Path, rel: str, source: str = "gettext") -> list[TextChunk]:
    """Extract non-empty msgstr strings from a gettext .po file (stdlib only)."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    chunks: list[TextChunk] = []
    lines = raw.splitlines()
    i = 0
    idx = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^msgstr(?:\[(\d+)\])?\s+"(.*)"\s*$', line)
        if not m:
            i += 1
            continue
        parts = [m.group(2)]
        i += 1
        while i < len(lines):
            cm = re.match(r'^"(.*)"\s*$', lines[i])
            if not cm:
                break
            parts.append(cm.group(1))
            i += 1
        text = _unescape_po("".join(parts)).strip()
        if text:
            chunks.append(TextChunk(path=rel, scope=f"msgstr[{idx}]", text=text, source=source))
            idx += 1
    return chunks


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def collect_xliff_file(path: Path, rel: str, source: str = "xliff") -> list[TextChunk]:
    """Collect target (or source) text nodes from XLIFF 1.2 / 2.0."""
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError):
        return []
    root = tree.getroot()
    chunks: list[TextChunk] = []
    idx = 0
    for el in root.iter():
        name = _local_name(el.tag).lower()
        if name not in {"target", "source"}:
            continue
        # Prefer target; keep source only when no sibling target with text
        if name == "source":
            # ElementTree has no parent pointer; accept source as fallback via later filter
            pass
        text = "".join(el.itertext()).strip()
        if not text:
            continue
        if name == "source":
            continue  # target-only for QA of translations
        chunks.append(TextChunk(path=rel, scope=f"target[{idx}]", text=text, source=source))
        idx += 1
    if not chunks:
        # monolingual / unfinished: fall back to source
        idx = 0
        for el in root.iter():
            if _local_name(el.tag).lower() != "source":
                continue
            text = "".join(el.itertext()).strip()
            if not text:
                continue
            chunks.append(TextChunk(path=rel, scope=f"source[{idx}]", text=text, source=source))
            idx += 1
    return chunks


def collect_mkdocs(repo_root: Path, locale: str) -> list[TextChunk]:
    """MkDocs: docs_dir or docs/<locale>/ i18n layout."""
    chunks: list[TextChunk] = []
    docs_dir = repo_root / "docs"
    cfg = repo_root / "mkdocs.yml"
    if not cfg.is_file() and not (docs_dir / locale).is_dir() and not docs_dir.is_dir():
        return chunks
    roots: list[Path] = []
    if (docs_dir / locale).is_dir():
        roots.append(docs_dir / locale)
    elif docs_dir.is_dir():
        roots.append(docs_dir)
    for root in roots:
        for path in _walk_files(root, (".md", ".markdown", ".html", ".htm")):
            rel = _rel(path, repo_root)
            suf = path.suffix.lower()
            if suf in {".md", ".markdown"}:
                chunks.extend(_markdown_chunks(path, rel, source="mkdocs"))
            else:
                chunks.extend(collect_html_file(path, rel, source="mkdocs"))
    return chunks


def collect_docusaurus(repo_root: Path, locale: str) -> list[TextChunk]:
    """Docusaurus i18n docs + blog."""
    chunks: list[TextChunk] = []
    roots = [
        repo_root / "i18n" / locale / "docusaurus-plugin-content-docs",
        repo_root / "i18n" / locale / "docusaurus-plugin-content-blog",
        repo_root / "blog",
        repo_root / "docs",
    ]
    # Prefer i18n tree when present; else default docs/blog only for locale match heuristics
    i18n_hit = False
    for root in roots[:2]:
        if root.is_dir():
            i18n_hit = True
            for path in _walk_files(root, (".md", ".markdown", ".mdx")):
                rel = _rel(path, repo_root)
                chunks.extend(_markdown_chunks(path, rel, source="docusaurus"))
    if i18n_hit:
        return chunks
    for root in roots[2:]:
        if not root.is_dir():
            continue
        for path in _walk_files(root, (".md", ".markdown", ".mdx")):
            rel = _rel(path, repo_root)
            chunks.extend(_markdown_chunks(path, rel, source="docusaurus"))
    return chunks


def collect_vitepress(repo_root: Path, locale: str) -> list[TextChunk]:
    """VitePress docs tree and locale subfolders."""
    chunks: list[TextChunk] = []
    candidates = [
        repo_root / "docs" / locale,
        repo_root / locale,
        repo_root / "docs",
    ]
    seen: set[Path] = set()
    has_vp = (
        (repo_root / ".vitepress").is_dir()
        or (repo_root / "docs" / ".vitepress").is_dir()
        or any((c / ".vitepress").is_dir() for c in candidates if c.is_dir())
    )
    for root in candidates:
        if not root.is_dir():
            continue
        if not has_vp and root.name != locale:
            continue
        for path in _walk_files(root, (".md", ".markdown")):
            real = path.resolve()
            if real in seen:
                continue
            seen.add(real)
            rel = _rel(path, repo_root)
            chunks.extend(_markdown_chunks(path, rel, source="vitepress"))
        if chunks and root.name == locale:
            break
    return chunks


def collect_l10n_tree(
    repo_root: Path, locale: str, files_paths: tuple[Path, ...] = ()
) -> list[TextChunk]:
    """Walk .po / .xliff / .html under explicit paths or common locale folders."""
    chunks: list[TextChunk] = []
    roots: list[Path] = []
    if files_paths:
        roots.extend(files_paths)
    else:
        for name in ("locale", "locales", "i18n", "translations", "po"):
            candidate = repo_root / name
            if candidate.is_dir():
                roots.append(candidate)
            loc_dir = candidate / locale if candidate.is_dir() else repo_root / name / locale
            if loc_dir.is_dir():
                roots.append(loc_dir)
    seen: set[Path] = set()
    for root in roots:
        resolved = root if root.is_absolute() else (repo_root / root)
        paths: list[Path]
        if resolved.is_file():
            paths = [resolved]
        elif resolved.is_dir():
            paths = list(_walk_files(resolved, (".po", ".xliff", ".xlf", ".html", ".htm")))
        else:
            continue
        for path in paths:
            real = path.resolve()
            if real in seen:
                continue
            seen.add(real)
            rel = _rel(path, repo_root)
            suf = path.suffix.lower()
            if suf == ".po":
                chunks.extend(collect_po_file(path, rel))
            elif suf in {".xliff", ".xlf"}:
                chunks.extend(collect_xliff_file(path, rel))
            elif suf in {".html", ".htm"}:
                chunks.extend(collect_html_file(path, rel))
    return chunks
