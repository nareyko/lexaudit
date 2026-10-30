"""P1 lab: bilingual MD pair signals (feature-flagged, off by default)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import regex  # type: ignore[import-untyped]

from lexaudit.core.types import ClassifiedWord, VocabSample

_LATIN_WORD = regex.compile(r"\b[\p{Latin}][\p{Latin}'-]{2,}\b", regex.VERSION1)
_CYRILLIC_WORD = regex.compile(r"\b[\p{Cyrillic}][\p{Cyrillic}'-]{2,}\b", regex.VERSION1)

# Cyrillic tokens often kept intentionally (thin; expand carefully).
DEFAULT_CYRILLIC_LOANS: frozenset[str] = frozenset()

MATRIX_LOCALES: tuple[str, ...] = ("en", "de", "ru")
CYRILLIC_LOCALES: frozenset[str] = frozenset({"ru", "uk"})

# Function / glue words — weak leftover signal when a whole English clause is pasted.
DEFAULT_FUNCTION_STOP: frozenset[str] = frozenset(
    {
        "this",
        "that",
        "these",
        "those",
        "with",
        "from",
        "into",
        "onto",
        "over",
        "under",
        "about",
        "after",
        "before",
        "between",
        "through",
        "during",
        "without",
        "within",
        "than",
        "then",
        "when",
        "where",
        "while",
        "whom",
        "which",
        "what",
        "only",
        "even",
        "still",
        "already",
        "very",
        "more",
        "most",
        "less",
        "least",
        "such",
        "same",
        "other",
        "another",
        "each",
        "every",
        "both",
        "many",
        "much",
        "some",
        "your",
        "our",
        "their",
        "also",
        "just",
        "been",
        "being",
        "have",
        "will",
        "would",
        "could",
        "should",
        "might",
        "must",
        "shall",
        "does",
        "were",
    }
)

# Intentional English tokens often kept in RU/DE technical prose.
# Keep this set brand/protocol-shaped — do not add generic prose leftovers
# (pending, sidebar, query, parameters, …) or held-out recall collapses.
DEFAULT_INTENTIONAL_LOANS: frozenset[str] = frozenset(
    {
        "api",
        "apis",
        "http",
        "https",
        "json",
        "yaml",
        "url",
        "uri",
        "html",
        "css",
        "sql",
        "oauth",
        "oauth2",
        "jwt",
        "uuid",
        "id",
        "ids",
        "sdk",
        "cli",
        "cpu",
        "gpu",
        "ok",
        "okey",
        "null",
        "true",
        "false",
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "options",
        "trace",
        "github",
        "gitlab",
        "docker",
        "kubernetes",
        "linux",
        "macos",
        "windows",
        "python",
        "fastapi",
        "openapi",
        "markdown",
        "mermaid",
        "todo",
        "fix",
        "wip",
        "mvp",
        "saas",
        "b2b",
        "b2c",
        "sepa",
        "iban",
        "kyc",
        "aml",
        "pci",
        "ssl",
        "tls",
        "dns",
        "cdn",
        "aws",
        "gcp",
        "azure",
        # Brands / runtimes kept in FastAPI & Kubernetes i18n
        "async",
        "await",
        "pydantic",
        "starlette",
        "uvicorn",
        "swagger",
        "redoc",
        "redocly",
        "graphql",
        "orm",
        "orms",
        "iot",
        "cors",
        "websocket",
        "websockets",
        "vscode",
        "codelens",
        "jetbrains",
        "pycharm",
        "basemodel",
        "cgroups",
        "dict",
        "list",
    }
)


@dataclass(frozen=True)
class BilingualPair:
    source_locale: str
    target_locale: str
    source_path: str
    target_path: str


def pair_paths(
    source_root: Path,
    target_root: Path,
    *,
    source_locale: str,
    target_locale: str,
) -> list[BilingualPair]:
    """Match files with the same relative path under two locale roots."""
    pairs: list[BilingualPair] = []
    if not source_root.is_dir() or not target_root.is_dir():
        return pairs
    for src in sorted(source_root.rglob("*.md")):
        rel = src.relative_to(source_root).as_posix()
        tgt = target_root / rel
        if tgt.is_file():
            pairs.append(
                BilingualPair(
                    source_locale=source_locale,
                    target_locale=target_locale,
                    source_path=str(src),
                    target_path=str(tgt),
                )
            )
    return pairs


def untranslated_latin_in_target(
    source_text: str,
    target_text: str,
    *,
    path: str,
    min_len: int = 4,
    intentional_loans: frozenset[str] | None = None,
    function_stop: frozenset[str] | None = None,
) -> list[ClassifiedWord]:
    """Flag Latin tokens that appear in both source and target (likely leftover)."""
    allow = intentional_loans if intentional_loans is not None else DEFAULT_INTENTIONAL_LOANS
    stop = function_stop if function_stop is not None else DEFAULT_FUNCTION_STOP
    src = {m.group(0).casefold() for m in _LATIN_WORD.finditer(source_text)}
    out: list[ClassifiedWord] = []
    seen: set[str] = set()
    for m in _LATIN_WORD.finditer(target_text):
        surface = m.group(0)
        if len(surface) < min_len:
            continue
        key = surface.casefold()
        # Kebab heading/anchor leftovers (why-you-need-…, path-parameters-with-types)
        if key.count("-") >= 2:
            continue
        if key not in src or key in seen or key in allow or key in stop:
            continue
        seen.add(key)
        out.append(
            ClassifiedWord(
                normalized=key,
                surface=surface,
                count=1,
                status="foreign",
                samples=[VocabSample(path=path, scope="body")],
                reason="bilingual-untranslated",
                detectors=["bilingual"],
                tier="likely",
            )
        )
    return out


def untranslated_cyrillic_in_target(
    source_text: str,
    target_text: str,
    *,
    path: str,
    min_len: int = 4,
    intentional_loans: frozenset[str] | None = None,
) -> list[ClassifiedWord]:
    """Flag Cyrillic tokens that appear in both source and target (RU→EN/DE leak)."""
    allow = intentional_loans if intentional_loans is not None else DEFAULT_CYRILLIC_LOANS
    src = {m.group(0).casefold() for m in _CYRILLIC_WORD.finditer(source_text)}
    out: list[ClassifiedWord] = []
    seen: set[str] = set()
    for m in _CYRILLIC_WORD.finditer(target_text):
        surface = m.group(0)
        if len(surface) < min_len:
            continue
        key = surface.casefold()
        if key not in src or key in seen or key in allow:
            continue
        seen.add(key)
        out.append(
            ClassifiedWord(
                normalized=key,
                surface=surface,
                count=1,
                status="foreign",
                samples=[VocabSample(path=path, scope="body")],
                reason="bilingual-untranslated-cyrillic",
                detectors=["bilingual"],
                tier="likely",
            )
        )
    return out


def detect_pair_leftovers(
    source_text: str,
    target_text: str,
    *,
    source_locale: str,
    target_locale: str,
    path: str,
    intentional_loans: frozenset[str] | None = None,
) -> list[ClassifiedWord]:
    """Choose Latin vs Cyrillic leftover detector from locale pair."""
    src_l = source_locale.casefold()
    tgt_l = target_locale.casefold()
    if src_l in CYRILLIC_LOCALES and tgt_l not in CYRILLIC_LOCALES:
        return untranslated_cyrillic_in_target(
            source_text,
            target_text,
            path=path,
            intentional_loans=intentional_loans,
        )
    # Default: Latin overlap (EN/DE → RU, EN → DE, DE → EN, DE → RU)
    return untranslated_latin_in_target(
        source_text,
        target_text,
        path=path,
        intentional_loans=intentional_loans,
    )


def matrix_pairs() -> list[tuple[str, str]]:
    """All directed pairs among en/de/ru (6)."""
    out: list[tuple[str, str]] = []
    for src in MATRIX_LOCALES:
        for tgt in MATRIX_LOCALES:
            if src != tgt:
                out.append((src, tgt))
    return out


def length_ratio_signal(source_text: str, target_text: str) -> float:
    """Soft ratio target/source character length (1.0 = equal)."""
    a = max(1, len(source_text.strip()))
    b = len(target_text.strip())
    return b / a


def apply_bilingual_pass(
    words: list[ClassifiedWord],
    pairs: list[BilingualPair],
    *,
    enabled: bool,
) -> list[ClassifiedWord]:
    if not enabled:
        return words
    extra: list[ClassifiedWord] = []
    for pair in pairs:
        try:
            src = Path(pair.source_path).read_text(encoding="utf-8")
            tgt = Path(pair.target_path).read_text(encoding="utf-8")
        except OSError:
            continue
        extra.extend(
            detect_pair_leftovers(
                src,
                tgt,
                source_locale=pair.source_locale,
                target_locale=pair.target_locale,
                path=pair.target_path,
            )
        )
    return [*words, *extra]


def pairs_from_config(raw: list[dict[str, Any]] | None, repo_root: Path) -> list[BilingualPair]:
    if not raw:
        return []
    out: list[BilingualPair] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        src_root = repo_root / str(row.get("source_root") or "")
        tgt_root = repo_root / str(row.get("target_root") or "")
        out.extend(
            pair_paths(
                src_root,
                tgt_root,
                source_locale=str(row.get("source_locale") or "en"),
                target_locale=str(row.get("target_locale") or "ru"),
            )
        )
    return out
