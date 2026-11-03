"""German/Swedish compound splitter using dictionary word set.

Handles closed compounds, hyphenated X-Y(/-Z) developer-docs terms,
Fugen elements (-s-/-n-/-en-/-es-/-er-), and productive suffixes
(-ung/-heit/-keit/-barkeit/-ning/-het/-barhet). Detection-only: never
rewrites the audited text.
"""

from __future__ import annotations

from collections.abc import Callable

from lexaudit.core.types import ClassifiedWord

SUPPORTED = frozenset({"de", "sv"})

# Productive nominal / adjectival suffixes (longest first).
_DE_SUFFIXES: tuple[str, ...] = (
    "barkeit",
    "schaft",
    "ierung",
    "heiten",
    "keiten",
    "ungen",
    "heit",
    "keit",
    "ung",
    "chen",
    "lein",
    "lich",
    "isch",
    "bar",
)
_SV_SUFFIXES: tuple[str, ...] = (
    "barhet",
    "ningar",
    "heter",
    "elser",
    "ering",
    "ning",
    "het",
    "else",
    "ande",
    "ende",
    "isk",
    "lig",
    "bar",
)

# Fugen / linking elements between closed-compound parts (longest first).
_DE_FUGEN: tuple[str, ...] = ("en", "es", "er", "n", "s")
_SV_FUGEN: tuple[str, ...] = ("o", "e", "u", "s")

# English / shared IT tokens that appear as hyphen parts or standalone loans
# in DE/SV developer documentation (Kubernetes, FastAPI, CI prose).
# Keep protocol-/tool-shaped — do not add generic prose leftovers.
DEVELOPER_DOCS_TECH_PARTS: frozenset[str] = frozenset(
    {
        "access",
        "age",
        "and",
        "api",
        "apis",
        "async",
        "await",
        "backend",
        "backends",
        "backfill",
        "backfills",
        "body",
        "bodys",
        "branch",
        "build",
        "cache",
        "caching",
        "commit",
        "commits",
        "contract",
        "control",
        "coroutine",
        "coroutines",
        "cors",
        "dead",
        "deploy",
        "deploys",
        "deprecation",
        "docker",
        "endpoint",
        "endpoints",
        "etag",
        "etags",
        "expand",
        "failover",
        "feature",
        "features",
        "flag",
        "flags",
        "gateway",
        "git",
        "handler",
        "handlers",
        "header",
        "headers",
        "hop",
        "hops",
        "http",
        "https",
        "idempotent",
        "json",
        "jwt",
        "kubernetes",
        "letter",
        "load",
        "log",
        "logs",
        "max",
        "oauth",
        "only",
        "openapi",
        "parameter",
        "parameters",
        "payload",
        "proxy",
        "pydantic",
        "query",
        "queue",
        "queues",
        "refresh",
        "registry",
        "release",
        "replay",
        "request",
        "requestbody",
        "requestbodys",
        "response",
        "responses",
        "reverse",
        "rolling",
        "rollout",
        "rollouts",
        "schema",
        "server",
        "servers",
        "session",
        "sessions",
        "span",
        "spans",
        "sticky",
        "swagger",
        "test",
        "tests",
        "token",
        "tokens",
        "trace",
        "traces",
        "ui",
        "unit",
        "webhook",
        "webhooks",
        "worker",
        "workers",
        "yaml",
    }
)

# German / Swedish stems frequently glued to the tech parts above.
_NATIVE_TECH_STEMS: frozenset[str] = frozenset(
    {
        # de
        "anfrage",
        "beobacht",
        "bzw",
        "coroutinen",
        "fenster",
        "idempotente",
        "kennung",
        "kennungen",
        "konsument",
        "konsumenten",
        "kontrolle",
        "körper",
        "lebens",
        "lebenszyklus",
        "meist",
        "modell",
        "modelle",
        "optimierung",
        "optimierungen",
        "parameter",
        "parametern",
        "performanz",
        "regel",
        "regeln",
        "risiko",
        "schlüssel",
        "signier",
        "span",
        "spans",
        "test",
        "tests",
        "tracken",
        "usw",
        "verwendet",
        "version",
        "versionierung",
        "wert",
        "werte",
        "zyklus",
        # sv
        "autentisering",
        "hopp",
        "huvud",
        "huvuden",
        "idempotenta",
        "kaka",
        "kakor",
        "kö",
        "köer",
        "observerbar",
        "sökväg",
        "sökvägs",
        "token",
        "uppdatering",
        "uppdaterings",
        "versioner",
        "åtkomst",
    }
)


def _suffixes_for(locale: str) -> tuple[str, ...]:
    return _DE_SUFFIXES if locale == "de" else _SV_SUFFIXES


def _fugen_for(locale: str) -> tuple[str, ...]:
    return _DE_FUGEN if locale == "de" else _SV_FUGEN


def _strip_inflection(part: str, locale: str) -> str:
    """Drop light plural / case endings for hyphen-part matching."""
    p = part
    if locale == "de":
        for ending in ("ungen", "en", "er", "e", "n", "s"):
            if len(p) - len(ending) >= 3 and p.endswith(ending):
                return p[: -len(ending)]
    else:
        for ending in ("erna", "orna", "ar", "or", "er", "en", "et", "n", "s"):
            if len(p) - len(ending) >= 3 and p.endswith(ending):
                return p[: -len(ending)]
    return p


def _part_known(part: str, known: set[str], locale: str) -> bool:
    if not part or len(part) < 2:
        return False
    if part in known:
        return True
    stem = _strip_inflection(part, locale)
    if stem in known:
        return True
    for suf in _suffixes_for(locale):
        if len(part) > len(suf) + 2 and part.endswith(suf):
            base = part[: -len(suf)]
            if base in known or _strip_inflection(base, locale) in known:
                return True
            # beobachten → beobacht + barkeit style: drop trailing vowel before suffix
            if base.endswith(("e", "en")) and base[:-1] in known:
                return True
            if base.endswith("en") and base[:-2] in known:
                return True
    return False


def _can_split_closed(
    word: str,
    known: set[str],
    locale: str,
    *,
    min_part: int = 3,
    depth: int = 0,
) -> bool:
    """True when ``word`` is a closed compound of known parts (+ optional Fugen)."""
    w = word.casefold()
    if depth > 4 or len(w) < min_part * 2:
        return False
    fugen = _fugen_for(locale)
    for i in range(min_part, len(w) - min_part + 1):
        left, right = w[:i], w[i:]
        left_ok = _part_known(left, known, locale)
        if not left_ok:
            # left + fugen consumed into left slice (arbeitszeit → arbeit + s + zeit)
            for fug in fugen:
                if left.endswith(fug) and len(left) - len(fug) >= min_part:
                    stem = left[: -len(fug)]
                    if _part_known(stem, known, locale):
                        left_ok = True
                        break
        if not left_ok:
            continue
        if _part_known(right, known, locale):
            return True
        # right itself may be a further compound
        if _can_split_closed(right, known, locale, min_part=min_part, depth=depth + 1):
            return True
        # fugen glued onto the start of right (arbeit + s + zeit already covered;
        # also try explicit split with fugen between parts)
        for fug in fugen:
            if right.startswith(fug) and len(right) - len(fug) >= min_part:
                rest = right[len(fug) :]
                if _part_known(rest, known, locale) or _can_split_closed(
                    rest, known, locale, min_part=min_part, depth=depth + 1
                ):
                    return True
    return False


def _can_split_hyphenated(word: str, known: set[str], locale: str) -> bool:
    """True when every hyphen segment is a known / tech / suffix-stripped part."""
    if "-" not in word:
        return False
    parts = [p for p in word.casefold().split("-") if p]
    if len(parts) < 2:
        return False
    return all(_part_known(p, known, locale) or _can_split_closed(p, known, locale) for p in parts)


def _can_split(word: str, known: set[str], *, min_part: int = 3, locale: str = "de") -> bool:
    """Public helper used by tests; locale defaults to German fugen/suffixes."""
    w = word.casefold()
    if "-" in w:
        return _can_split_hyphenated(w, known, locale)
    return _can_split_closed(w, known, locale, min_part=min_part)


def _is_standalone_tech_loan(word: str, known: set[str], locale: str) -> bool:
    w = word.casefold()
    if w in known:
        return True
    return _part_known(w, known, locale) and (
        w in DEVELOPER_DOCS_TECH_PARTS or _strip_inflection(w, locale) in DEVELOPER_DOCS_TECH_PARTS
    )


def make_compound_detector(
    locale: str, known_words: set[str]
) -> Callable[[ClassifiedWord], ClassifiedWord | None]:
    if locale not in SUPPORTED:

        def _noop(word: ClassifiedWord) -> ClassifiedWord | None:
            return None

        return _noop

    known = {k.casefold() for k in known_words}
    known |= {p.casefold() for p in DEVELOPER_DOCS_TECH_PARTS}
    known |= {p.casefold() for p in _NATIVE_TECH_STEMS}

    def detect(word: ClassifiedWord) -> ClassifiedWord | None:
        if word.status != "suspect":
            return None
        norm = word.normalized.casefold()
        reason: str | None = None
        if _can_split_hyphenated(norm, known, locale):
            reason = "compound-hyphen"
        elif _can_split_closed(norm, known, locale):
            reason = "compound-split"
        elif _is_standalone_tech_loan(norm, known, locale):
            reason = "tech-term"
        elif _part_known(norm, known, locale) and any(
            norm.endswith(suf) and len(norm) > len(suf) + 2 for suf in _suffixes_for(locale)
        ):
            # Productive derivation from a known stem (Beobachtbarkeit, Observerbarhet).
            reason = "compound-suffix"
        if reason is None:
            return None
        word.status = "ok"
        word.reason = reason
        word.detectors = sorted({*word.detectors, "compound"})
        word.tier = None
        return word

    return detect
