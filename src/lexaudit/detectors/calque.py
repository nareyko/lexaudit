"""Calque rule detector - YAML rules, never replaces text.

Supports exact patterns, simple glob (`*`) wildcards, and multi-word phrases.
Rules with ``override_ok: true`` can flip hunspell-``ok`` words to ``calque``
(e.g. denseness as a template-calque even when the English dictionary accepts it).

v0.4 Stage V3 adds ``kind`` (calque | false_friend), ``source_lang``,
sentence-window ``context_require`` / ``context_forbid``, and
``positive_examples`` / ``negative_examples`` for the contract test.
Rules with context filters are applied in the body pass (not the bare
token detector), so dictionary-valid false friends only fire in false
contexts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

import yaml

from lexaudit.core.tokenize import TOKEN_RE, casefold, tokenize
from lexaudit.core.types import ClassifiedWord, TextChunk, VocabSample

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…;:\n])\s+|\n+")


@dataclass(frozen=True)
class CalqueRule:
    pattern: str
    locale: str
    reason: str
    hint: str
    severity: str
    source: str
    override_ok: bool = False
    match: str = "exact"  # exact | glob | prefix | phrase
    kind: str = "calque"  # calque | false_friend
    source_lang: str = ""
    context_require: tuple[str, ...] = ()
    context_forbid: tuple[str, ...] = ()
    positive_examples: tuple[str, ...] = ()
    negative_examples: tuple[str, ...] = ()

    @property
    def needs_context(self) -> bool:
        return bool(self.context_require) or bool(self.context_forbid)


def default_calque_rules_dir() -> Path | None:
    """Locate bundled calque YAML rules in wheel or source checkout."""
    pkg_dir = Path(__file__).resolve().parents[1] / "rules" / "calques"
    if pkg_dir.is_dir():
        return pkg_dir
    repo_dir = Path(__file__).resolve().parents[3] / "rules" / "calques"
    if repo_dir.is_dir():
        return repo_dir
    return None


def _as_str_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                out.append(text)
        return tuple(out)
    return ()


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
            default_mode = (
                "phrase"
                if any(ch.isspace() for ch in pattern)
                else ("glob" if "*" in pattern else "exact")
            )
            match_mode = str(item.get("match") or default_mode)
            if match_mode == "prefix" and not pattern.endswith("*"):
                pattern = pattern + "*"
                match_mode = "glob"
            if any(ch.isspace() for ch in pattern) and match_mode != "phrase":
                match_mode = "phrase"
            kind = str(item.get("kind") or "calque").strip().casefold()
            if kind not in {"calque", "false_friend"}:
                kind = "calque"
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
                    kind=kind,
                    source_lang=str(item.get("source_lang") or "").strip(),
                    context_require=_as_str_tuple(item.get("context_require")),
                    context_forbid=_as_str_tuple(item.get("context_forbid")),
                    positive_examples=_as_str_tuple(item.get("positive_examples")),
                    negative_examples=_as_str_tuple(item.get("negative_examples")),
                )
            )
    rules.sort(key=lambda r: (r.locale, r.pattern, r.source))
    return rules


def split_sentences(text: str) -> list[str]:
    """Split prose into rough sentence windows (punctuation / newlines)."""
    cleaned = text.strip()
    if not cleaned:
        return []
    parts = [p.strip() for p in _SENTENCE_SPLIT_RE.split(cleaned) if p and p.strip()]
    return parts or [cleaned]


def _needle_in_sentence(needle: str, sentence: str, locale: str) -> bool:
    """True if ``needle`` appears as a phrase substring or as a token."""
    n = casefold(needle.strip(), locale)
    if not n:
        return False
    folded = casefold(sentence, locale)
    if any(ch.isspace() for ch in n):
        return n in folded
    tokens = tokenize(sentence, locale=locale, min_length=1)
    if n in tokens:
        return True
    # Allow short morphological tails: stem* match against tokens when needle has no '*'.
    return any(t == n or t.startswith(n) for t in tokens if len(n) >= 4)


def context_allows(rule: CalqueRule, sentence: str, locale: str) -> bool:
    """Sentence-window filter: all require present, no forbid present."""
    if not all(_needle_in_sentence(req, sentence, locale) for req in rule.context_require):
        return False
    return all(not _needle_in_sentence(forbid, sentence, locale) for forbid in rule.context_forbid)


def _pattern_in_sentence(rule: CalqueRule, sentence: str, locale: str) -> bool:
    """Return True if the rule pattern hits inside ``sentence``."""
    folded = casefold(sentence, locale)
    pat = casefold(rule.pattern, locale)
    if not pat:
        return False
    if rule.match == "phrase" or any(ch.isspace() for ch in pat):
        return pat in folded
    tokens = tokenize(sentence, locale=locale, min_length=1)
    if rule.match == "exact" or ("*" not in pat and rule.match != "glob"):
        return pat in tokens
    return any(fnmatchcase(tok, pat) for tok in tokens)


def rule_matches_text(rule: CalqueRule, text: str, locale: str | None = None) -> bool:
    """True if any sentence in ``text`` matches pattern and passes context filters."""
    loc = locale or rule.locale
    for sentence in split_sentences(text):
        if _pattern_in_sentence(rule, sentence, loc) and context_allows(rule, sentence, loc):
            return True
    return False


def _rule_matches(norm: str, rule: CalqueRule, locale: str) -> bool:
    pat = casefold(rule.pattern, locale)
    if rule.match == "exact" or ("*" not in pat and rule.match != "glob"):
        return norm == pat
    # glob / prefix: casefold already applied; fnmatch on folded forms
    return fnmatchcase(norm, pat)


def find_matching_rule(
    word: ClassifiedWord, rules: list[CalqueRule], locale: str
) -> CalqueRule | None:
    """Return the first matching token rule for ``word.normalized`` (stable order).

    Skips phrase rules and rules that require sentence context (those are applied
    in :func:`apply_phrase_calque_pass`).
    """
    for rule in rules:
        if rule.match == "phrase" or rule.needs_context:
            continue
        if _rule_matches(word.normalized, rule, locale):
            return rule
    return None


def phrase_rules_for_locale(rules: list[CalqueRule], locale: str) -> list[CalqueRule]:
    return [r for r in rules if r.locale == locale and r.match == "phrase"]


def contextual_token_rules_for_locale(rules: list[CalqueRule], locale: str) -> list[CalqueRule]:
    """Non-phrase rules that need a sentence window (false friends, gated calques)."""
    return [r for r in rules if r.locale == locale and r.match != "phrase" and r.needs_context]


def _rule_source_id(rule: CalqueRule) -> str:
    if rule.source_lang:
        return f"{rule.source_lang}-origin"
    slug = (rule.source or rule.reason or "calque").strip()
    return slug.replace(" ", "-") or "calque"


def _sample_for_span(chunk: TextChunk, text: str, start: int, end: int) -> VocabSample:
    from lexaudit.core.tokenize import offset_to_line_col

    line, start_col, end_col = offset_to_line_col(text, start, end)
    return VocabSample(
        path=chunk.path,
        scope=chunk.scope,
        line=chunk.line_base + line - 1,
        start_col=start_col,
        end_col=end_col,
    )


def _apply_hit(
    *,
    by_norm: dict[str, ClassifiedWord],
    extra: list[ClassifiedWord],
    seen: set[str],
    key: str,
    surface: str,
    rule: CalqueRule,
    chunk: TextChunk,
    count: int,
    detectors: list[str],
    span_start: int | None = None,
    span_end: int | None = None,
) -> None:
    if key in seen:
        return
    seen.add(key)
    source_id = _rule_source_id(rule)
    sample = VocabSample(path=chunk.path, scope=chunk.scope)
    if span_start is not None and span_end is not None and span_end >= span_start:
        sample = _sample_for_span(chunk, chunk.text, span_start, span_end)
    existing = by_norm.get(key)
    if existing is not None:
        existing.status = "calque"
        existing.reason = rule.reason
        existing.hint = rule.hint
        existing.source_id = source_id
        existing.detectors = sorted({*existing.detectors, *detectors})
        if rule.severity in {"confirmed", "likely", "weak"}:
            existing.tier = rule.severity  # type: ignore[assignment]
        if sample.line is not None and len(existing.samples) < 5:
            dup = any(
                s.path == sample.path
                and s.scope == sample.scope
                and s.line == sample.line
                and s.start_col == sample.start_col
                for s in existing.samples
            )
            if not dup:
                existing.samples.append(sample)
        return
    hit = ClassifiedWord(
        normalized=key,
        surface=surface,
        count=count,
        status="calque",
        samples=[sample],
        reason=rule.reason,
        detectors=list(detectors),
        tier=rule.severity  # type: ignore[arg-type]
        if rule.severity in {"confirmed", "likely", "weak"}
        else "likely",
        hint=rule.hint,
        source_id=source_id,
    )
    extra.append(hit)
    by_norm[key] = hit


def apply_phrase_calque_pass(
    words: list[ClassifiedWord],
    chunks: list[TextChunk],
    rules: list[CalqueRule],
    *,
    locale: str,
) -> list[ClassifiedWord]:
    """Scan body text for multi-word phrases and context-gated token rules."""
    phrases = phrase_rules_for_locale(rules, locale)
    contextual = contextual_token_rules_for_locale(rules, locale)
    if not phrases and not contextual:
        return words
    by_norm = {w.normalized: w for w in words}
    extra: list[ClassifiedWord] = []
    seen: set[str] = set()
    for chunk in chunks:
        scope = chunk.scope.casefold()
        if scope not in {"body", "bodymarkdown"} and not scope.startswith("body"):
            continue
        folded_full = casefold(chunk.text, locale)
        for sentence in split_sentences(chunk.text):
            for rule in phrases:
                if not context_allows(rule, sentence, locale):
                    continue
                pat = casefold(rule.pattern, locale)
                sent_folded = casefold(sentence, locale)
                if not pat or pat not in sent_folded:
                    continue
                key = pat.replace(" ", "_")
                abs_start = folded_full.find(pat)
                abs_end = abs_start + len(pat) if abs_start >= 0 else None
                _apply_hit(
                    by_norm=by_norm,
                    extra=extra,
                    seen=seen,
                    key=key,
                    surface=rule.pattern,
                    rule=rule,
                    chunk=chunk,
                    count=folded_full.count(pat),
                    detectors=["calque", "phrase"],
                    span_start=abs_start if abs_start >= 0 else None,
                    span_end=abs_end,
                )
            for rule in contextual:
                if not context_allows(rule, sentence, locale):
                    continue
                if not _pattern_in_sentence(rule, sentence, locale):
                    continue
                # Prefer the first matching token surface from the sentence.
                pat = casefold(rule.pattern, locale)
                surface = rule.pattern
                key = pat.replace("*", "").replace(" ", "_") or pat
                span_start: int | None = None
                span_end: int | None = None
                # Map sentence-local match to chunk offsets via first occurrence.
                sent_idx = chunk.text.find(sentence)
                for match in TOKEN_RE.finditer(sentence):
                    tok = casefold(match.group(0), locale)
                    if _rule_matches(tok, rule, locale):
                        surface = match.group(0)
                        key = tok
                        if sent_idx >= 0:
                            span_start = sent_idx + match.start()
                            span_end = sent_idx + match.end()
                        break
                else:
                    # Phrase-like glob without a clean token — use pattern key.
                    if "*" in pat:
                        key = pat.replace("*", "").rstrip("-_") or pat
                _apply_hit(
                    by_norm=by_norm,
                    extra=extra,
                    seen=seen,
                    key=key,
                    surface=surface,
                    rule=rule,
                    chunk=chunk,
                    count=1,
                    detectors=["calque", "context"],
                    span_start=span_start,
                    span_end=span_end,
                )
    if not extra:
        return words
    return [*words, *extra]


def make_calque_detector(locale: str, rules: list[CalqueRule]) -> Any:
    locale_rules = [
        r for r in rules if r.locale == locale and r.match != "phrase" and not r.needs_context
    ]
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
        word.hint = rule.hint
        word.source_id = _rule_source_id(rule)
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
