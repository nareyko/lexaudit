"""Calque rule detector - YAML rules, never replaces text.

Supports exact patterns and simple glob (`*`) wildcards.
Rules with ``override_ok: true`` can flip hunspell-``ok`` words to ``calque``
(e.g. denseness as a template-calque even when the English dictionary accepts it).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

import yaml

from lexaudit.core.tokenize import casefold
from lexaudit.core.types import ClassifiedWord


@dataclass(frozen=True)
class CalqueRule:
    pattern: str
    locale: str
    reason: str
    hint: str
    severity: str
    source: str
    override_ok: bool = False
    match: str = "exact"  # exact | glob | prefix


def default_calque_rules_dir() -> Path | None:
    """Locate bundled calque YAML rules in wheel or source checkout."""
    pkg_dir = Path(__file__).resolve().parents[1] / "rules" / "calques"
    if pkg_dir.is_dir():
        return pkg_dir
    repo_dir = Path(__file__).resolve().parents[3] / "rules" / "calques"
    if repo_dir.is_dir():
        return repo_dir
    return None


def load_calque_rules(path: Path) -> list[CalqueRule]:
    if not path.exists():
        return []
    rules: list[CalqueRule] = []
    files = sorted(path.glob("*.yaml")) + sorted(path.glob("*.yml")) if path.is_dir() else [path]
    for f in files:
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        items = data.get("rules") if isinstance(data, dict) else data
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            pattern = str(item["pattern"])
            match_mode = str(item.get("match") or ("glob" if "*" in pattern else "exact"))
            if match_mode == "prefix" and not pattern.endswith("*"):
                pattern = pattern + "*"
                match_mode = "glob"
            rules.append(
                CalqueRule(
                    pattern=pattern,
                    locale=str(item["locale"]),
                    reason=str(item.get("reason") or "calque"),
                    hint=str(item.get("hint") or ""),
                    severity=str(item.get("severity") or "likely"),
                    source=str(item.get("source") or f.name),
                    override_ok=bool(item.get("override_ok") or False),
                    match=match_mode,
                )
            )
    rules.sort(key=lambda r: (r.locale, r.pattern, r.source))
    return rules


def _rule_matches(norm: str, rule: CalqueRule, locale: str) -> bool:
    pat = casefold(rule.pattern, locale)
    if rule.match == "exact" or ("*" not in pat and rule.match != "glob"):
        return norm == pat
    # glob / prefix: casefold already applied; fnmatch on folded forms
    return fnmatchcase(norm, pat)


def find_matching_rule(
    word: ClassifiedWord, rules: list[CalqueRule], locale: str
) -> CalqueRule | None:
    """Return the first matching rule for ``word.normalized`` (stable rule order)."""
    for rule in rules:
        if _rule_matches(word.normalized, rule, locale):
            return rule
    return None


def make_calque_detector(locale: str, rules: list[CalqueRule]) -> Any:
    locale_rules = [r for r in rules if r.locale == locale]
    # Longer / more specific globs first among equals - keep load sort, but
    # prefer exact over glob when both could match by checking exact first.
    exact = [r for r in locale_rules if r.match == "exact" or "*" not in r.pattern]
    globbed = [r for r in locale_rules if r not in exact]
    ordered = exact + globbed

    def detect(word: ClassifiedWord) -> ClassifiedWord | None:
        rule = find_matching_rule(word, ordered, locale)
        if rule is None:
            return None
        if word.status == "ok" and not rule.override_ok and word.reason != "pymorphy3":
            return None
        if word.status not in {"suspect", "ok", "foreign", "unsure", "morph-miss"}:
            return None
        word.status = "calque"
        word.reason = rule.reason
        word.detectors = sorted({*word.detectors, "calque"})
        if rule.severity in {"confirmed", "likely", "weak"}:
            word.tier = rule.severity  # type: ignore[assignment]
        return word

    return detect


def compile_prefix_re(prefix: str) -> re.Pattern[str]:
    """Helper for tests / expand-needle family matching."""
    return re.compile("^" + re.escape(prefix) + ".*$", re.IGNORECASE)


def needle_matches_norm(normalized: str, needle: str, locale: str) -> bool:
    """Return True if ``normalized`` hits a needle (exact, glob, or stem family).

    Bare stems (no ``*``) match: exact token, prefix extensions (``orientirs``), and
    hyphen suffixes (``*-orientir``).
    """
    nd = casefold(needle.strip(), locale)
    if not nd:
        return False
    norm = casefold(normalized, locale)
    if "*" in nd:
        return fnmatchcase(norm, nd)
    if norm == nd:
        return True
    if norm.startswith(nd):
        return True
    return fnmatchcase(norm, f"*-{nd}")
