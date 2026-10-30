"""P1 lab: bilingual MD pair signals (feature-flagged, off by default)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import regex  # type: ignore[import-untyped]

from lexaudit.core.types import ClassifiedWord, VocabSample

_LATIN_WORD = regex.compile(r"\b[\p{Latin}][\p{Latin}'-]{2,}\b", regex.VERSION1)
_CYRILLIC_WORD = regex.compile(r"\b[\p{Cyrillic}][\p{Cyrillic}'-]{2,}\b", regex.VERSION1)
_URL_EMAIL_RE = re.compile(
    r"https?://\S+|www\.\S+|\b\S+@\S+\.\S+\b|`[^`]+`",
    re.IGNORECASE,
)

# Cyrillic tokens often kept intentionally (thin; expand carefully).
DEFAULT_CYRILLIC_LOANS: frozenset[str] = frozenset()

# Full V1 locale set (calque packs + hunspell). Matrix = all directed pairs.
MATRIX_LOCALES: tuple[str, ...] = ("en", "de", "pl", "ru", "es", "sv", "uk")
ANCHOR_LOCALES: tuple[str, ...] = ("en", "de", "ru")
OTHER_LOCALES: tuple[str, ...] = ("es", "pl", "sv", "uk")
CYRILLIC_LOCALES: frozenset[str] = frozenset({"ru", "uk"})

# Soft cognates / shared Latin UI nouns: still flag, but demote tier (anti-FP rank).
# Keep narrow — do not swallow real leftovers like sidebar/toast/onboarding.
SOFT_COGNATE_DEMOTE: frozenset[str] = frozenset(
    {
        "system",
        "systems",
        "version",
        "versions",
        "normal",
        "standard",
        "global",
        "local",
        "social",
        "digital",
        "mobile",
        "portal",
        "service",
        "services",
        "product",
        "products",
        "model",
        "models",
        "client",
        "server",
        "format",
        "formats",
        "region",
        "regions",
        "address",
        "message",
        "messages",
        "number",
        "numbers",
        "password",
        "profile",
        "profiles",
        "contact",
        "contacts",
        "support",
        "export",
        "import",
        "report",
        "reports",
        "filter",
        "filters",
        "group",
        "groups",
        "role",
        "roles",
        "session",
        "sessions",
        "event",
        "events",
        "action",
        "actions",
        "error",
        "errors",
        "warning",
        "warnings",
        "option",
        "options",
        "default",
        "defaults",
        "public",
        "private",
        "secure",
        "security",
        "privacy",
        "policy",
        "policies",
        "license",
        "licence",
        "copyright",
        "index",
        "total",
        "video",
        "audio",
        "online",
        "offline",
        "email",
        "admin",
        "user",
        "users",
        "file",
        "files",
        "page",
        "type",
        "types",
        "mode",
        "date",
        "list",
        "test",
        "form",
        "name",
        "info",
        "debug",
        "level",
        "levels",
        "limit",
        "limits",
        "value",
        "values",
        "range",
        "ranges",
        "token",
        "tokens",
        "cache",
        "queue",
        "queues",
        "sort",
        "trace",
        "offset",
        "custom",
        "terms",
        "conditions",
    }
)

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

# CMS / site-shell chrome often shared EN↔locale (nav labels, not prose leftovers).
# Do not put real UI leftovers here (sidebar, toast, dashboard, inbox, …) — those
# belong in corpus extras / gold. This set is for template shells and brand crumbs.
DEFAULT_TEMPLATE_CHROME: frozenset[str] = frozenset(
    {
        "definition",
        "related",
        "limits",
        "academy",
        "wiki",
        "blog",
        "courses",
        "services",
        "yachts",
        "models",
        "buying",
        "cruising",
        "ownership",
        "systems",
        "fairhelm",
        "judgment",
        "permalink",
        "slug",
        "toc",
        "breadcrumb",
        "breadcrumbs",
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
    extra_chrome: frozenset[str] | None = None,
) -> list[ClassifiedWord]:
    """Flag Latin tokens that appear in both source and target (likely leftover)."""
    allow = intentional_loans if intentional_loans is not None else DEFAULT_INTENTIONAL_LOANS
    stop = function_stop if function_stop is not None else DEFAULT_FUNCTION_STOP
    chrome = DEFAULT_TEMPLATE_CHROME | (extra_chrome or frozenset())
    source_text = strip_urls_emails_code(source_text)
    target_text = strip_urls_emails_code(target_text)
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
        if key not in src or key in seen or key in allow or key in stop or key in chrome:
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
    source_text = strip_urls_emails_code(source_text)
    target_text = strip_urls_emails_code(target_text)
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


def identical_segment_leftovers(
    source_text: str,
    target_text: str,
    *,
    path: str,
    min_chars: int = 24,
    intentional_loans: frozenset[str] | None = None,
    chrome: frozenset[str] | None = None,
) -> list[ClassifiedWord]:
    """Flag near-identical Latin segments copied from source into target (soft)."""
    allow = intentional_loans if intentional_loans is not None else DEFAULT_INTENTIONAL_LOANS
    stop = DEFAULT_FUNCTION_STOP | DEFAULT_TEMPLATE_CHROME | (chrome or frozenset())
    src_lines = {ln.strip().casefold() for ln in source_text.splitlines() if ln.strip()}
    out: list[ClassifiedWord] = []
    seen: set[str] = set()
    for raw in target_text.splitlines():
        line = raw.strip()
        if len(line) < min_chars:
            continue
        key = line.casefold()
        if key not in src_lines or key in seen:
            continue
        # Prefer a representative Latin token from the segment for ranking.
        tokens = [m.group(0) for m in _LATIN_WORD.finditer(line)]
        pick = next(
            (
                t
                for t in tokens
                if len(t) >= 4 and t.casefold() not in allow and t.casefold() not in stop
            ),
            None,
        )
        if pick is None:
            continue
        seen.add(key)
        norm = pick.casefold()
        out.append(
            ClassifiedWord(
                normalized=norm,
                surface=pick,
                count=1,
                status="foreign",
                samples=[VocabSample(path=path, scope="body")],
                reason="bilingual-identical-segment",
                detectors=["bilingual"],
                tier="likely",
            )
        )
    return out


def demote_soft_cognates(hits: list[ClassifiedWord]) -> list[ClassifiedWord]:
    """C3: demote likely→weak for shared Latin cognates (ranking only)."""
    for w in hits:
        if w.normalized not in SOFT_COGNATE_DEMOTE:
            continue
        if w.tier == "likely":
            w.tier = "weak"
            w.reason = (w.reason or "bilingual") + "+cognate-soft"
    return hits


def detect_pair_leftovers(
    source_text: str,
    target_text: str,
    *,
    source_locale: str,
    target_locale: str,
    path: str,
    intentional_loans: frozenset[str] | None = None,
    extra_chrome: frozenset[str] | None = None,
) -> list[ClassifiedWord]:
    """Choose Latin vs Cyrillic leftover detector from locale pair."""
    src_l = source_locale.casefold()
    # RU/UK source → Cyrillic overlap (into Latin or other Cyrillic targets)
    if src_l in CYRILLIC_LOCALES:
        hits = untranslated_cyrillic_in_target(
            source_text,
            target_text,
            path=path,
            intentional_loans=intentional_loans,
        )
    else:
        # Default: Latin overlap (EN/DE/ES/PL/SV → *)
        hits = untranslated_latin_in_target(
            source_text,
            target_text,
            path=path,
            intentional_loans=intentional_loans,
            extra_chrome=extra_chrome,
        )
        hits.extend(
            identical_segment_leftovers(
                source_text,
                target_text,
                path=path,
                intentional_loans=intentional_loans,
                chrome=extra_chrome,
            )
        )
    hits.extend(
        length_ratio_leftovers(
            source_text,
            target_text,
            path=path,
        )
    )
    return demote_soft_cognates(hits)


def matrix_pairs(*, mode: str = "all") -> list[tuple[str, str]]:
    """Directed locale pairs.

    mode:
      - ``all`` — every directed pair among MATRIX_LOCALES (7x6=42)
      - ``anchors`` — only among en/de/ru (6)
      - ``anchors_x_others`` — en/de/ru ↔ es/pl/sv/uk both ways (24) + anchors (6) = 30
    """
    out: list[tuple[str, str]] = []
    if mode == "anchors":
        locales = ANCHOR_LOCALES
        for src in locales:
            for tgt in locales:
                if src != tgt:
                    out.append((src, tgt))
        return out
    if mode == "anchors_x_others":
        for src in ANCHOR_LOCALES:
            for tgt in ANCHOR_LOCALES:
                if src != tgt:
                    out.append((src, tgt))
        for a in ANCHOR_LOCALES:
            for o in OTHER_LOCALES:
                out.append((a, o))
                out.append((o, a))
        return out
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


def strip_urls_emails_code(text: str) -> str:
    """Drop URLs, emails, and inline code spans before leftover scans."""
    return _URL_EMAIL_RE.sub(" ", text)


def length_ratio_leftovers(
    source_text: str,
    target_text: str,
    *,
    path: str,
    low: float = 0.55,
    high: float = 1.85,
) -> list[ClassifiedWord]:
    """Soft page signal when target length diverges sharply from source.

    Uses a synthetic token so the alarm is not mistaken for a real leftover
    word from the source (which would pollute precision gold).
    """
    ratio = length_ratio_signal(source_text, target_text)
    if low <= ratio <= high:
        return []
    return [
        ClassifiedWord(
            normalized="length-ratio",
            surface="(length-ratio)",
            count=1,
            status="foreign",
            samples=[VocabSample(path=path, scope="body")],
            reason=f"bilingual-length-ratio:{ratio:.2f}",
            detectors=["bilingual"],
            tier="weak",
        )
    ]


def load_extra_loans(path: Path | None) -> frozenset[str]:
    """Load one-token-per-line extras (# comments allowed). Casefolded."""
    if path is None or not path.is_file():
        return frozenset()
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip().casefold()
        if not s or s.startswith("#"):
            continue
        out.add(s)
    return frozenset(out)


def intentional_loans_for_target(
    target_locale: str,
    *,
    extra: frozenset[str] = frozenset(),
    extra_locales: frozenset[str] = frozenset(),
    base: frozenset[str] | None = None,
) -> frozenset[str]:
    """DEFAULT loans, plus extras only when target_locale is in extra_locales.

    DE UI nouns (dashboard, toast, …) must stay out of DEFAULT — pass them via
    ``extra`` + ``extra_locales={"de"}``. See docs/p1-de-loan-policy.md.
    """
    loans = DEFAULT_INTENTIONAL_LOANS if base is None else base
    if not extra:
        return loans
    allowed = {x.casefold() for x in extra_locales}
    if not allowed or target_locale.casefold() not in allowed:
        return loans
    return frozenset(loans | extra)


def apply_bilingual_pass(
    words: list[ClassifiedWord],
    pairs: list[BilingualPair],
    *,
    enabled: bool,
    extra_loans: frozenset[str] = frozenset(),
    extra_loans_locales: frozenset[str] = frozenset(),
    extra_chrome: frozenset[str] = frozenset(),
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
        loans = intentional_loans_for_target(
            pair.target_locale,
            extra=extra_loans,
            extra_locales=extra_loans_locales,
        )
        extra.extend(
            detect_pair_leftovers(
                src,
                tgt,
                source_locale=pair.source_locale,
                target_locale=pair.target_locale,
                path=pair.target_path,
                intentional_loans=loans,
                extra_chrome=extra_chrome or None,
            )
        )
    return [*words, *extra]


def _academy_body(translations: dict[str, Any], locale: str) -> str:
    block = translations.get(locale)
    if not isinstance(block, dict):
        return ""
    body = block.get("bodyMarkdown")
    return body if isinstance(body, str) else ""


def pairs_from_academy(
    academy_root: Path,
    source_locale: str,
    target_locale: str,
    *,
    materialize_dir: Path,
) -> list[BilingualPair]:
    """Pair academy JSON articles by slug; write bodyMarkdown to materialize_dir.

    ``apply_bilingual_pass`` reads plain-text paths, so each locale body is
    materialized as ``{materialize_dir}/{locale}/{rel}.md`` (rel mirrors the
    JSON path under academy_root without the ``.json`` suffix).
    """
    pairs: list[BilingualPair] = []
    if not academy_root.is_dir():
        return pairs

    for src_json in sorted(academy_root.rglob("*.json")):
        try:
            data = json.loads(src_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        translations = data.get("translations")
        if not isinstance(translations, dict):
            continue
        src_body = _academy_body(translations, source_locale)
        tgt_body = _academy_body(translations, target_locale)
        if not src_body.strip() or not tgt_body.strip():
            continue
        rel = src_json.relative_to(academy_root).with_suffix("").as_posix()
        src_md = materialize_dir / source_locale / f"{rel}.md"
        tgt_md = materialize_dir / target_locale / f"{rel}.md"
        try:
            src_md.parent.mkdir(parents=True, exist_ok=True)
            tgt_md.parent.mkdir(parents=True, exist_ok=True)
            src_md.write_text(src_body, encoding="utf-8")
            tgt_md.write_text(tgt_body, encoding="utf-8")
        except OSError:
            continue
        pairs.append(
            BilingualPair(
                source_locale=source_locale,
                target_locale=target_locale,
                source_path=str(src_md),
                target_path=str(tgt_md),
            )
        )
    return pairs


def pairs_from_config(raw: list[dict[str, Any]] | None, repo_root: Path) -> list[BilingualPair]:
    if not raw:
        return []
    out: list[BilingualPair] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        source_locale = str(row.get("source_locale") or "en")
        target_locale = str(row.get("target_locale") or "ru")
        if str(row.get("source") or "").casefold() == "academy":
            academy_root = repo_root / str(
                row.get("academy_root") or "infra/corpus-ci/pending-academy-articles"
            )
            materialize_dir = repo_root / str(
                row.get("materialize_dir") or "frontend/tmp/lexaudit-bilingual-pairs"
            )
            out.extend(
                pairs_from_academy(
                    academy_root,
                    source_locale,
                    target_locale,
                    materialize_dir=materialize_dir,
                )
            )
            continue
        src_root = repo_root / str(row.get("source_root") or "")
        tgt_root = repo_root / str(row.get("target_root") or "")
        out.extend(
            pair_paths(
                src_root,
                tgt_root,
                source_locale=source_locale,
                target_locale=target_locale,
            )
        )
    return out
