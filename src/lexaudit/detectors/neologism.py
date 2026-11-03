"""Neologism / invented-coinage detector (Zipf + char n-gram + affix/glue).

Optional ``wordfreq`` Zipf scores with a compact fallback table. Character 3-5gram
language models are trained from Hunspell dictionary tokens (or a bundled seed
list). Catalogue-style codes stay weak; only clear OOV mashups become ``invented``.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable, Iterable
from functools import lru_cache
from pathlib import Path
from typing import Any

from lexaudit.core.types import ClassifiedWord
from lexaudit.detectors.dictfetch import cache_dir
from lexaudit.detectors.hunspell import LOCALE_DICTS, HunspellConfig, find_dict

Detector = Callable[[ClassifiedWord], ClassifiedWord | None]

# Productive coinage / calque-glue suffixes (not benchmark needles).
_COINAGE_SUFFIXES: dict[str, tuple[str, ...]] = {
    "en": ("ization", "fulness", "ishness", "ishly", "ness", "like", "ward", "wise", "ify", "ish"),
    "de": ("mässig", "mäßig", "lichkeit", "igkeit", "heit", "keit", "lich", "ung", "ig"),
    "es": ("alezca", "ezca", "ización", "ismo", "esco", "izar"),
    "pl": ("owaty", "owski", "owość", "anie", "ność"),
    "ru": ("овидный", "ообразн", "ность", "ость", "ение", "овый"),
    "sv": ("mässig", "aktig", "ning", "isk", "ig"),
    "uk": ("оподібн", "ність", "ість", "ення", "овий"),
}

_GREEK_LETTER_TAILS = (
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "zeta",
    "theta",
    "iota",
    "kappa",
    "lambda",
    "sigma",
    "omega",
    "эпсилон",
    "зета",
    "тета",
    "каппа",
    "сигма",
    "омега",
)

_MIXED_ALNUM_RE = re.compile(
    r"^(?=.*\d)(?=.*[A-Za-zА-Яа-яЁёІіЇїЄє])[A-Za-zА-Яа-яЁёІіЇїЄє0-9]+$",
    re.UNICODE,
)

# Compact Zipf-ish priors used when wordfreq is unavailable (common closed-class + stems).
_FALLBACK_ZIPF: dict[str, dict[str, float]] = {
    "en": {
        "the": 7.5,
        "and": 7.2,
        "for": 6.8,
        "with": 6.6,
        "from": 6.4,
        "that": 6.9,
        "this": 6.7,
        "have": 6.5,
        "boat": 4.8,
        "hull": 4.2,
        "check": 5.1,
        "walk": 5.0,
        "dock": 4.5,
        "stringer": 3.1,
        "epoxy": 3.4,
    },
    "de": {"und": 7.4, "der": 7.5, "die": 7.5, "das": 7.2, "mit": 6.8, "boot": 4.6},
    "es": {"de": 7.6, "la": 7.4, "el": 7.3, "que": 7.1, "en": 7.2, "barco": 4.7},
    "pl": {"i": 7.3, "w": 7.2, "na": 7.0, "z": 6.9, "się": 6.8, "jacht": 4.4},
    "ru": {
        "и": 7.5,
        "в": 7.4,
        "на": 7.2,
        "с": 7.0,
        "не": 7.1,
        "лодка": 4.5,
        "осмотр": 4.0,
    },
    "sv": {"och": 7.4, "att": 7.2, "det": 7.1, "en": 7.0, "på": 6.9, "båt": 4.6},
    "uk": {
        "і": 7.4,
        "в": 7.3,
        "на": 7.2,
        "з": 7.0,
        "не": 7.1,
        "човен": 4.4,
        "огляд": 4.0,
    },
}

# Seed tokens for char-LM when no Hunspell word list is reachable.
_SEED_WORDS: dict[str, tuple[str, ...]] = {
    "en": (
        "the",
        "and",
        "boat",
        "hull",
        "harbour",
        "harbor",
        "check",
        "walk",
        "dock",
        "stringer",
        "laminate",
        "epoxy",
        "primer",
        "rudder",
        "anchor",
        "battery",
        "charger",
        "maintenance",
        "inspection",
        "protocol",
        "composite",
        "bulkhead",
        "keel",
        "bilge",
        "pump",
        "hose",
        "clamp",
        "orientation",
        "checklist",
        "survey",
        "yacht",
        "vessel",
        "marine",
        "sailing",
        "engine",
        "cooling",
        "water",
        "system",
    ),
    "de": (
        "und",
        "der",
        "die",
        "boot",
        "rumpf",
        "hafen",
        "leine",
        "steuer",
        "manöver",
        "steg",
        "prüfung",
        "sicherheit",
        "ausrüstung",
        "ladung",
        "batterie",
        "epoxid",
        "grundierung",
        "wasserpass",
        "winterlager",
        "ruderblatt",
    ),
    "es": (
        "de",
        "la",
        "el",
        "barco",
        "casco",
        "puerto",
        "revisión",
        "bomba",
        "agua",
        "salada",
        "laminado",
        "resina",
        "fibra",
        "varada",
        "sentina",
        "batería",
        "cargador",
        "fondeo",
    ),
    "pl": (
        "i",
        "w",
        "na",
        "jacht",
        "pokład",
        "pompa",
        "marina",
        "cumowanie",
        "keja",
        "ogląd",
        "uszczelnienie",
        "wał",
        "dławica",
        "wodowanie",
        "bezpiecznik",
        "ładowarka",
        "akumulator",
    ),
    "ru": (
        "и",
        "в",
        "на",
        "лодка",
        "палуба",
        "осмотр",
        "причал",
        "корпус",
        "смола",
        "ламинат",
        "переборка",
        "трюм",
        "лебёдка",
        "якорь",
        "навигация",
        "радиосвязь",
        "предохранитель",
        "пирс",
        "осмотр",
        "причальный",
    ),
    "sv": (
        "och",
        "att",
        "båt",
        "hamn",
        "brygga",
        "genomgång",
        "pump",
        "laminat",
        "epoxi",
        "primer",
        "batteri",
        "laddare",
        "motor",
        "kylvatten",
        "roder",
    ),
    "uk": (
        "і",
        "в",
        "на",
        "човен",
        "палуба",
        "огляд",
        "причал",
        "корпус",
        "смола",
        "ламінат",
        "перебірка",
        "трюм",
        "лебідка",
        "якір",
        "навігація",
        "радіозв",
        "запобіжник",
    ),
}

_VOWELS_LATIN = set("aeiouyäöüáéíóúàèìòùâêîôûãõæøå")
_VOWELS_CYR = set("аеёиоуыэюяіїє")


def _has_wordfreq() -> bool:
    try:
        import wordfreq  # noqa: F401

        return True
    except ImportError:
        return False


def zipf_frequency(token: str, locale: str) -> float:
    """Zipf frequency in ``[0, 8]``-ish; ``0`` means unseen / extremely rare."""
    word = token.casefold().strip()
    if not word:
        return 0.0
    lang = locale.casefold()
    if _has_wordfreq():
        try:
            from wordfreq import zipf_frequency as _zf

            # wordfreq uses ISO 639-1; our locales already match.
            return float(_zf(word, lang))
        except Exception:
            pass
    table = _FALLBACK_ZIPF.get(lang, {})
    if word in table:
        return table[word]
    # Mild length prior so very short closed-class-looking tokens are not zero.
    if len(word) <= 3 and word.isalpha():
        return 2.0
    return 0.0


def _is_catalog_code(normalized: str) -> bool:
    """True for SKU / part-number style tokens that should stay weak."""
    n = normalized.casefold()
    if len(n) < 4:
        return True
    if _MIXED_ALNUM_RE.match(n):
        return True
    if any(ch.isdigit() for ch in n) and any(ch.isalpha() for ch in n):
        return True
    for tail in _GREEK_LETTER_TAILS:
        if n.endswith(tail) and len(n) - len(tail) <= 6:
            prefix = n[: -len(tail)]
            if prefix and _consonant_heavy(prefix):
                return True
    # Consonant-run catalogue blobs (no vowel in a 5+ letter stretch of Latin).
    if re.search(r"[bcdfghjklmnpqrstvwxz]{5,}", n):
        return True
    return bool(re.search(r"[бвгджзйклмнпрстфхцчшщ]{5,}", n))


def _consonant_heavy(text: str) -> bool:
    letters = [c for c in text.casefold() if c.isalpha()]
    if len(letters) < 2:
        return True
    vowels = _VOWELS_LATIN | _VOWELS_CYR
    v = sum(1 for c in letters if c in vowels)
    return (v / len(letters)) <= 0.25


def _load_dic_tokens(dic_path: Path, *, limit: int = 25000) -> list[str]:
    tokens: list[str] = []
    try:
        lines = dic_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return tokens
    for i, line in enumerate(lines):
        if i == 0 and line.strip().isdigit():
            continue
        raw = line.split("/")[0].split("\t")[0].strip()
        if not raw:
            continue
        w = raw.casefold()
        if not any(ch.isalpha() for ch in w):
            continue
        if not all(ch.isalpha() or ch in "'’-." for ch in w):
            continue
        pure = "".join(ch for ch in w if ch.isalpha())
        if 2 <= len(pure) <= 28:
            tokens.append(pure)
        if len(tokens) >= limit:
            break
    return tokens


def _dictionary_tokens(locale: str, hunspell: HunspellConfig | None = None) -> list[str]:
    cfg = hunspell or HunspellConfig()
    found = find_dict(locale, cfg)
    tokens: list[str] = []
    if found is not None:
        _dict_id, base = found
        tokens = _load_dic_tokens(Path(f"{base}.dic"))
    if not tokens:
        # Also probe cache dir for any matching locale id.
        for dict_id in LOCALE_DICTS.get(locale, []):
            candidate = cache_dir() / f"{dict_id}.dic"
            if candidate.is_file():
                tokens = _load_dic_tokens(candidate)
                if tokens:
                    break
    seed = list(_SEED_WORDS.get(locale.casefold(), _SEED_WORDS["en"]))
    # Strip accidental spaces from seed typos.
    seed = [s.replace(" ", "") for s in seed if s.strip()]
    if not tokens:
        return seed
    # Blend a few seeds so maritime stems exist even in sparse dicts.
    return tokens + seed


class CharNgramLM:
    """Smoothed character n-gram model (orders 3-5) over dictionary tokens."""

    def __init__(self, words: Iterable[str], orders: tuple[int, ...] = (3, 4, 5)) -> None:
        self.orders = orders
        self._counts: dict[int, Counter[str]] = {n: Counter() for n in orders}
        self._totals: dict[int, int] = {n: 0 for n in orders}
        self._vocab: set[str] = set()
        for raw in words:
            w = "".join(ch for ch in raw.casefold() if ch.isalpha())
            if len(w) < 2:
                continue
            self._vocab.add(w)
            padded = f"^{w}$"
            for n in orders:
                for i in range(0, len(padded) - n + 1):
                    gram = padded[i : i + n]
                    self._counts[n][gram] += 1
                    self._totals[n] += 1

    def __contains__(self, word: str) -> bool:
        pure = "".join(ch for ch in word.casefold() if ch.isalpha())
        return pure in self._vocab

    def mean_log_prob(self, word: str) -> float:
        pure = "".join(ch for ch in word.casefold() if ch.isalpha())
        if len(pure) < 2:
            return -20.0
        scores: list[float] = []
        for n in self.orders:
            padded = f"^{pure}$"
            if len(padded) < n:
                continue
            total = self._totals[n] + 1
            vocab_extra = len(self._counts[n]) + 1
            lp = 0.0
            steps = 0
            for i in range(0, len(padded) - n + 1):
                gram = padded[i : i + n]
                c = self._counts[n].get(gram, 0)
                p = (c + 0.05) / (total + 0.05 * vocab_extra)
                lp += math.log(p)
                steps += 1
            if steps:
                scores.append(lp / steps)
        return sum(scores) / len(scores) if scores else -20.0

    def join_boundary_surprise(self, left: str, right: str) -> float:
        """Higher = more surprising character join (calque-glue cue)."""
        if not left or not right:
            return 0.0
        pure_l = "".join(ch for ch in left.casefold() if ch.isalpha())
        pure_r = "".join(ch for ch in right.casefold() if ch.isalpha())
        if not pure_l or not pure_r:
            return 0.0
        # Compare P(boundary 4-gram) vs average of each side's internal 4-grams.
        boundary = (pure_l[-2:] + pure_r[:2]) if len(pure_l) >= 2 and len(pure_r) >= 2 else ""
        if len(boundary) < 4:
            return 0.0
        counts, total = self._counts.get(4, Counter()), self._totals.get(4, 1)
        vocab_extra = len(counts) + 1
        p_b = (counts.get(boundary, 0) + 0.05) / (total + 0.05 * vocab_extra)
        # Internal reference: last 4-gram of left if available.
        ref = pure_l[-4:] if len(pure_l) >= 4 else pure_l
        p_ref = (counts.get(ref, 0) + 0.05) / (total + 0.05 * vocab_extra)
        if p_ref <= 0:
            return 0.0
        return math.log(p_ref) - math.log(p_b)


@lru_cache(maxsize=16)
def _locale_lm(locale: str) -> CharNgramLM:
    return CharNgramLM(_dictionary_tokens(locale))


def _strip_coinage_suffix(word: str, locale: str) -> tuple[str, str]:
    n = word.casefold()
    for suf in sorted(_COINAGE_SUFFIXES.get(locale.casefold(), ()), key=len, reverse=True):
        if n.endswith(suf) and len(n) - len(suf) >= 3:
            return n[: -len(suf)], suf
    return n, ""


def _known_stem(part: str, lm: CharNgramLM, *, min_len: int = 3) -> bool:
    p = "".join(ch for ch in part.casefold() if ch.isalpha())
    if len(p) < min_len:
        return False
    if p in lm:
        return True
    # Mild morphological peel for Latin stems.
    for tail in ("ing", "ed", "er", "ers", "ly", "al", "ic", "ous", "ive", "tion", "sion"):
        if len(p) > len(tail) + 2 and p.endswith(tail) and p[: -len(tail)] in lm:
            return True
    for tail in ("ый", "ой", "ий", "ая", "ое", "ые", "ов", "ам", "ах", "ий", "ій", "ої", "их"):
        if len(p) > len(tail) + 2 and p.endswith(tail) and p[: -len(tail)] in lm:
            return True
    return False


def _glue_splits(word: str, lm: CharNgramLM, *, min_part: int = 4) -> list[tuple[str, str]]:
    n = "".join(ch for ch in word.casefold() if ch.isalpha())
    out: list[tuple[str, str]] = []
    if len(n) < min_part * 2:
        return out
    for i in range(min_part, len(n) - min_part + 1):
        left, right = n[:i], n[i:]
        both_known = _known_stem(left, lm) and _known_stem(right, lm)
        left_ok = _known_stem(left, lm) and len(right) >= 5 and lm.mean_log_prob(right) > -12.5
        right_ok = _known_stem(right, lm) and len(left) >= 5 and lm.mean_log_prob(left) > -12.5
        if both_known or left_ok or right_ok:
            out.append((left, right))
    return out


def _looks_affix_mash(word: str, locale: str, lm: CharNgramLM) -> bool:
    stem, suf = _strip_coinage_suffix(word, locale)
    if not suf:
        return False
    if len(stem) < 3:
        return False
    # Suffix on a glued stem (dock+walk+ish) or on a long OOV stem.
    splits = _glue_splits(stem, lm, min_part=3)
    if splits:
        return True
    # Long foreign stem + coinage suffix (surveyness-like / Stegmanöver+ig).
    if len(stem) >= 6 and stem not in lm:
        return True
    # Short OOV stem + *marked* coinage suffix (kej+owaty, pantanal+ezca).
    # Do NOT treat every productive denominal (-овий/-owy/-ish alone on a short
    # loan stem) as invented — those are often editorial domain adjectives.
    marked = {
        "en": {"ish", "ness", "like", "ify", "ization"},
        "de": {"ig", "heit", "keit", "mässig", "mäßig"},
        "es": {"ezca", "alezca", "ismo", "izar"},
        "pl": {"owaty", "owski"},
        "ru": {"ность", "ость"},
        "sv": {"ig", "aktig", "mässig"},
        "uk": {"ність", "ість"},
    }
    if suf in marked.get(locale.casefold(), set()) and len(stem) >= 3 and stem not in lm:
        # Require the stem itself to look multi-morphemic or fairly long.
        if len(stem) >= 5 or _glue_splits(stem, lm, min_part=3):
            return True
        if locale in {"pl", "es"} and len(word) >= 8:
            return True
    return False


def _looks_calque_glue(word: str, locale: str, lm: CharNgramLM) -> bool:
    """Concatenated native-looking parts without a space (esp. Cyrillic mashups)."""
    pure = "".join(ch for ch in word.casefold() if ch.isalpha())
    if len(pure) < 10:
        return False
    # German/Swedish closed compounds are productive and handled by compound.py;
    # do not promote ordinary X+Y dictionary compounds to invented.
    if locale in {"de", "sv"}:
        return False
    splits = _glue_splits(pure, lm, min_part=4)
    if not splits:
        # Cyrillic locales: also accept split where both sides score as native-ish.
        if locale in {"ru", "uk"} and len(pure) >= 11:
            for i in range(4, len(pure) - 3):
                left, right = pure[:i], pure[i:]
                if (
                    lm.mean_log_prob(left) > -12.0
                    and lm.mean_log_prob(right) > -12.0
                    and lm.join_boundary_surprise(left, right) > 0.8
                ):
                    return True
        return False
    # Prefer splits with a surprising join; avoid flagging every technical X+Y.
    for left, right in splits[:8]:
        surprise = lm.join_boundary_surprise(left, right)
        if surprise >= 0.6:
            return True
        # Slavic-style adjective stem glued to a noun stem (пирсовый|осмотр).
        if locale in {"ru", "uk"} and left.endswith(
            ("ый", "ой", "ий", "о", "но", "льно", "ний", "ній", "ий")
        ):
            return True
    return False


def score_neologism(
    token: str,
    locale: str,
    *,
    lm: CharNgramLM | None = None,
) -> dict[str, Any]:
    """Return diagnostic scores; ``invented`` recommendation is a boolean."""
    n = token.casefold().strip()
    model = lm or _locale_lm(locale.casefold())
    zipf = zipf_frequency(n, locale)
    catalog = _is_catalog_code(n)
    native = model.mean_log_prob(n)
    affix = _looks_affix_mash(n, locale, model)
    glue = _looks_calque_glue(n, locale, model)
    invented = False
    if not catalog and zipf < 1.5 and len(n) >= 7:
        if affix or glue:
            invented = True
        elif native < -12.8 and len(n) >= 11 and zipf < 0.5:
            # Extremely unnatural long hapax without catalogue shape.
            invented = True
    return {
        "zipf": zipf,
        "catalog_code": catalog,
        "native_logprob": native,
        "affix_mash": affix,
        "calque_glue": glue,
        "invented": invented,
    }


def make_neologism_detector(
    locale: str,
    *,
    hunspell: HunspellConfig | None = None,
) -> Detector:
    """Post-detector: promote clear inventeds; leave catalogue codes / plain hapaxes."""

    loc = locale.casefold()
    # Warm LM with optional hunspell override (tests may inject).
    lm = CharNgramLM(_dictionary_tokens(loc, hunspell)) if hunspell is not None else _locale_lm(loc)

    def detect(word: ClassifiedWord) -> ClassifiedWord | None:
        if word.status not in {"suspect", "morph-miss", "unsure"}:
            return None
        # Domain repeats are handled elsewhere; still skip obvious catalogue noise early.
        info = score_neologism(word.normalized, loc, lm=lm)
        if info["catalog_code"]:
            # Keep weak / non-invented; annotate lightly for debugging.
            if word.reason in {"", "unknown"}:
                word.reason = "catalog-code"
                word.detectors = sorted({*word.detectors, "neologism"})
                return word
            return None
        if not info["invented"]:
            return None
        word.status = "invented"
        reason = "neologism-affix-mash" if info["affix_mash"] else "neologism-calque-glue"
        if info["native_logprob"] < -12.8 and not info["affix_mash"] and not info["calque_glue"]:
            reason = "neologism-unnatural-ngram"
        word.reason = reason
        word.detectors = sorted({*word.detectors, "neologism"})
        word.tier = "likely"
        return word

    return detect
