"""Load proper-names / acronyms / allowlist YAML from configured paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import regex  # type: ignore[import-untyped]
import yaml

from lexaudit.core.tokenize import TOKEN_RE, casefold

LETTER_PREFIX_RE = regex.compile(r"^[\p{L}]+", regex.VERSION1)


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = f"expected mapping in {path}"
        raise TypeError(msg)
    return data


def _collect_string_lists(node: Any, out: list[str]) -> None:
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, list):
        for item in node:
            _collect_string_lists(item, out)
    elif isinstance(node, dict):
        for key, val in node.items():
            if key == "version":
                continue
            _collect_string_lists(val, out)


def phrase_tokens(phrase: str, locale: str) -> set[str]:
    """Expand a phrase into allowlist tokens (full, parts, compact)."""
    tokens: set[str] = set()
    folded = casefold(phrase, locale)
    tokens.add(folded)
    for match in TOKEN_RE.finditer(phrase):
        tokens.add(casefold(match.group(0), locale))
    if "-" in phrase or " " in phrase:
        compact = regex.sub(r"[-\s]+", "", phrase)
        if compact:
            tokens.add(casefold(compact, locale))
    return {t for t in tokens if t}


def seed_from_slug(slug: str, locale: str) -> set[str]:
    """Seed allowlist tokens from a brand/model folder slug."""
    tokens = phrase_tokens(slug, locale)
    m = LETTER_PREFIX_RE.match(slug)
    if m and len(m.group(0)) >= 2:
        tokens.add(casefold(m.group(0), locale))
    return tokens


def load_proper_names(path: Path, locale: str) -> set[str]:
    data = _read_yaml(path)
    raw: list[str] = []
    _collect_string_lists(data, raw)
    out: set[str] = set()
    for phrase in raw:
        out |= phrase_tokens(phrase, locale)
    return out


def load_acronyms(path: Path, locale: str) -> set[str]:
    data = _read_yaml(path)
    raw: list[str] = []
    if isinstance(data.get("items"), list):
        _collect_string_lists(data["items"], raw)
    else:
        _collect_string_lists(data, raw)
    out: set[str] = set()
    for phrase in raw:
        out |= phrase_tokens(phrase, locale)
    return out


def load_thin_allowlist(path: Path, locale: str) -> tuple[set[str], set[str]]:
    """Return (section_markers, locale_loans) token sets."""
    data = _read_yaml(path)
    markers: set[str] = set()
    loans: set[str] = set()
    for phrase in data.get("section_markers") or []:
        if isinstance(phrase, str):
            markers |= phrase_tokens(phrase, locale)
    for phrase in data.get("locale_loans") or []:
        if isinstance(phrase, str):
            loans |= phrase_tokens(phrase, locale)
    for legacy_key in ("names", "acronyms", "extras"):
        for phrase in data.get(legacy_key) or []:
            if isinstance(phrase, str):
                loans |= phrase_tokens(phrase, locale)
    return markers, loans


def seed_from_pending_packs(packs_root: Path, locale: str) -> set[str]:
    """Seed brand/model folder names under pending-model-packs."""
    out: set[str] = set()
    if not packs_root.is_dir():
        return out
    for brand_dir in sorted(packs_root.iterdir()):
        if not brand_dir.is_dir() or brand_dir.name.startswith("."):
            continue
        out |= seed_from_slug(brand_dir.name, locale)
        for model_dir in sorted(brand_dir.iterdir()):
            if not model_dir.is_dir() or model_dir.name.startswith("."):
                continue
            out |= seed_from_slug(model_dir.name, locale)
    return out


def build_allowlist(
    *,
    locale: str,
    proper_names_path: Path | None = None,
    acronyms_path: Path | None = None,
    allowlist_path: Path | None = None,
    packs_root: Path | None = None,
    extra_slugs: list[str] | None = None,
) -> tuple[set[str], set[str], set[str]]:
    """
    Build (proper_set, acronym_set, template_set).

    proper_set includes proper names + locale loans + pack seeds.
    acronym_set is acronyms only.
    template_set is section markers.
    """
    proper: set[str] = set()
    acronyms: set[str] = set()
    templates: set[str] = set()

    if proper_names_path and proper_names_path.is_file():
        proper |= load_proper_names(proper_names_path, locale)
    if acronyms_path and acronyms_path.is_file():
        acronyms |= load_acronyms(acronyms_path, locale)
    if allowlist_path and allowlist_path.is_file():
        markers, loans = load_thin_allowlist(allowlist_path, locale)
        templates |= markers
        proper |= loans
    if packs_root:
        proper |= seed_from_pending_packs(packs_root, locale)
    if extra_slugs:
        for slug in extra_slugs:
            proper |= seed_from_slug(slug, locale)

    return proper, acronyms, templates


def build_compound_known_lemmas(proper: set[str], acronyms: set[str]) -> set[str]:
    """
    Lemmas available before hunspell ok-words for DE/SV compound splitting.

    Includes configured proper names, locale loans, pack seeds, and acronyms
    (domain glue terms live in proper-names.yaml).
    """
    return set(proper) | set(acronyms)
