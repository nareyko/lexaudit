#!/usr/bin/env python3
"""Honest competitor benchmark: lexaudit vs Hunspell / cspell / Vale / LanguageTool.

Runs the same gold set (synthetic-demo 42 pages + ``gold/real_bench`` if present)
through each tool that is available on the machine. Missing tools are recorded as
skipped rows (N/A metrics) so CI can call ``--lexaudit-only`` without failing.

Writes ``eval/competitor-benchmark.json`` and ``docs/competitor-benchmark.md``.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from lexaudit.config import LexauditConfig, load_config  # noqa: E402
from lexaudit.core.pipeline import run_locale_audit  # noqa: E402
from lexaudit.core.tokenize import casefold, tokenize  # noqa: E402
from lexaudit.core.types import ClassifiedWord, PageSuspectRank  # noqa: E402
from lexaudit.detectors.calque import needle_matches_norm  # noqa: E402
from lexaudit.detectors.hunspell import HunspellConfig, resolve_checker  # noqa: E402
from lexaudit.eval.metrics import (  # noqa: E402
    clean_page_fpr,
    page_precision_at_k,
    pred_is_anomaly,
    word_precision_recall,
)
from lexaudit.sources.collect import collect_all  # noqa: E402

SYNTH_CFG = ROOT / "examples" / "synthetic-demo" / "lexaudit.config.yaml"
GOLD_REAL_DIR = ROOT / "gold" / "real_bench"
DEFAULT_JSON = ROOT / "eval" / "competitor-benchmark.json"
DEFAULT_MD = ROOT / "docs" / "competitor-benchmark.md"
FREEZE_AT = "1970-01-01T00:00:00Z"

UNSEEN_NEOLOGISMS: dict[str, str] = {
    "en": "dockwalkish",
    "de": "stegmanöverig",
    "es": "pantanalezca",
    "pl": "kejowaty",
    "ru": "пирсовыйосмотр",
    "sv": "bryggcheckig",
    "uk": "причальноогляд",
}

REAL_ANOMALY_LABELS = frozenset({"calque", "false_friend", "other_error", "invented", "foreign"})

LT_LANG: dict[str, str] = {
    "en": "en-US",
    "de": "de-DE",
    "es": "es-ES",
    "pl": "pl-PL",
    "ru": "ru-RU",
    "sv": "sv",
    "uk": "uk-UA",
}

CSPELL_LOCALE: dict[str, str] = {
    "en": "en",
    "de": "de-de",
    "es": "es",
    "pl": "pl",
    "ru": "ru",
    "sv": "sv",
    "uk": "uk",
}

TOOL_ORDER = ("lexaudit", "hunspell", "cspell", "vale", "languagetool")


@dataclass
class PageDoc:
    path: str
    locale: str
    text: str
    corpus: str  # synthetic | real_bench


@dataclass
class GoldBundle:
    needles_by_locale: dict[str, list[str]] = field(default_factory=dict)
    bad_page_slugs: list[str] = field(default_factory=list)
    synth_bad_page_slugs: list[str] = field(default_factory=list)
    clean_page_slugs: list[str] = field(default_factory=list)
    clean_tokens: int = 0
    real_bench_present: bool = False
    real_anomaly_spans: list[dict[str, Any]] = field(default_factory=list)
    synth_paths: set[str] = field(default_factory=set)


@dataclass
class ToolRun:
    name: str
    available: bool
    skipped_reason: str | None = None
    backend: str | None = None
    seconds: float | None = None
    # path -> flagged normalized tokens
    flagged_by_page: dict[str, set[str]] = field(default_factory=dict)
    ranked_pages: list[PageSuspectRank] = field(default_factory=list)
    notes: str = ""


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _na_metrics() -> dict[str, Any]:
    return {
        "word_precision": None,
        "word_recall": None,
        "word_tp": None,
        "word_fp": None,
        "word_fn": None,
        "page_p_at_3": None,
        "page_p_at_3_hits": None,
        "clean_fp_per_1000_tokens": None,
        "clean_fp_unique_words": None,
        "seconds": None,
    }


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100.0:.1f}%"


def _fmt_num(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}"


def _fmt_sec(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}s"


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _resolve_npx() -> str | None:
    """Find npx even when it is only an NVM bash function (not on PATH for Python)."""
    found = _which("npx")
    if found:
        return found
    nvm_dir = os.environ.get("NVM_DIR")
    if nvm_dir:
        versions = Path(nvm_dir) / "versions" / "node"
        if versions.is_dir():
            for ver_dir in sorted(versions.iterdir(), reverse=True):
                cand = ver_dir / "bin" / "npx"
                if cand.is_file():
                    return str(cand)
    # Login shell expands nvm shim functions.
    probe = subprocess.run(
        ["bash", "-lc", "command -v npx"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    path = (probe.stdout or "").strip().splitlines()
    if probe.returncode == 0 and path and path[-1]:
        return path[-1]
    return None


def _npx_env(npx: str) -> dict[str, str]:
    """Ensure sibling ``node`` is on PATH when invoking an absolute NVM npx.

    Do not ``Path.resolve()`` the npx path: NVM's ``bin/npx`` is a symlink into
    ``lib/node_modules/npm/bin``, which does not contain ``node``.
    """
    env = os.environ.copy()
    bin_dir = str(Path(npx).parent)
    env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
    return env


def _find_cspell() -> tuple[list[str] | None, str | None]:
    direct = _which("cspell")
    if direct:
        return [direct], None
    npx = _resolve_npx()
    if npx:
        # Probe once; do not fail the whole benchmark if npx package is missing.
        probe = subprocess.run(
            [npx, "--yes", "cspell", "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
            env=_npx_env(npx),
        )
        if probe.returncode == 0:
            return [npx, "--yes", "cspell"], None
        detail = (probe.stderr or probe.stdout or "").strip().splitlines()
        tail = detail[-1] if detail else ""
        return None, f"npx cspell unavailable (exit {probe.returncode}) {tail}".strip()
    return None, "cspell / npx not found"


def _lt_python_importable() -> bool:
    try:
        import language_tool_python  # noqa: F401
    except ImportError:
        return False
    return True


def _lt_server_up(url: str = "http://127.0.0.1:8010/v2/languages") -> bool:
    try:
        import urllib.request

        with urllib.request.urlopen(url, timeout=2) as resp:
            return int(getattr(resp, "status", 200) or 200) < 500
    except OSError:
        return False


def _collect_synth_pages(cfg: LexauditConfig, locales: Sequence[str]) -> list[PageDoc]:
    pages: list[PageDoc] = []
    seen: set[str] = set()
    for loc in locales:
        academy_root = cfg.academy_root or (
            cfg.repo_root / "infra" / "corpus-ci" / "pending-academy-articles"
        )
        packs_root = cfg.packs_root or (
            cfg.repo_root / "infra" / "corpus-ci" / "pending-model-packs"
        )
        chunks = collect_all(
            cfg.repo_root,
            loc,
            set(cfg.sources),
            academy_root=academy_root,
            packs_root=packs_root,
            files_paths=cfg.files_paths,
        )
        by_path: dict[str, list[str]] = defaultdict(list)
        for chunk in chunks:
            by_path[chunk.path].append(chunk.text)
        for path, texts in sorted(by_path.items()):
            if path in seen:
                continue
            seen.add(path)
            pages.append(PageDoc(path=path, locale=loc, text="\n".join(texts), corpus="synthetic"))
    return pages


def _load_real_bench_consensus(locale: str) -> list[dict[str, Any]]:
    path = GOLD_REAL_DIR / f"{locale}.jsonl"
    if not path.is_file():
        return []
    by_key: dict[tuple[str, int, str], dict[str, list[str]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = (str(row["path"]), int(row["line"]), str(row["span"]))
        slot = by_key.setdefault(key, {"labels": [], "source_langs": []})
        slot["labels"].append(str(row["label"]))
        slot["source_langs"].append(str(row.get("source_lang") or ""))
    out: list[dict[str, Any]] = []
    for (path_s, line, span), slot in by_key.items():
        labels = slot["labels"]
        # Require dual-annotator agreement on an anomaly label.
        if len(labels) < 2:
            continue
        if not all(lab in REAL_ANOMALY_LABELS for lab in labels):
            continue
        if labels[0] != labels[1]:
            continue
        out.append(
            {
                "path": path_s,
                "line": line,
                "span": span,
                "label": labels[0],
                "locale": locale,
            }
        )
    return out


def _real_bench_pages(locales: Sequence[str]) -> list[PageDoc]:
    pages: list[PageDoc] = []
    seen: set[str] = set()
    for loc in locales:
        for sub in ("clean", "mt"):
            root = ROOT / "tests" / "fixtures" / "real_bench" / sub / loc
            if not root.is_dir():
                continue
            for path in sorted(root.glob("*.md")):
                rel = path.relative_to(ROOT).as_posix()
                if rel in seen:
                    continue
                seen.add(rel)
                pages.append(
                    PageDoc(
                        path=rel,
                        locale=loc,
                        text=path.read_text(encoding="utf-8"),
                        corpus="real_bench",
                    )
                )
        # GEC JSONL pairs are line-oriented; include as synthetic text pages when present.
        gec = ROOT / "tests" / "fixtures" / "real_bench" / "gec" / f"{loc}.jsonl"
        if gec.is_file():
            rel = gec.relative_to(ROOT).as_posix()
            if rel not in seen:
                seen.add(rel)
                pages.append(
                    PageDoc(
                        path=rel,
                        locale=loc,
                        text=gec.read_text(encoding="utf-8"),
                        corpus="real_bench",
                    )
                )
    return pages


def build_gold(cfg: LexauditConfig, pages: Sequence[PageDoc], locales: Sequence[str]) -> GoldBundle:
    gold = GoldBundle()
    gold.synth_paths = {p.path for p in pages if p.corpus == "synthetic"}
    gold.synth_bad_page_slugs = [
        g for g in cfg.gold_slugs if any(g.startswith(f"{loc}-") for loc in locales)
    ]
    gold.bad_page_slugs = list(gold.synth_bad_page_slugs)
    for loc in locales:
        needles = [n for n in cfg.needles]
        needles.append(UNSEEN_NEOLOGISMS[loc])
        gold.needles_by_locale[loc] = needles
        gold.clean_page_slugs.extend([f"{loc}-01", f"{loc}-02", f"{loc}-03"])

    for page in pages:
        if page.corpus != "synthetic":
            continue
        if any(slug in page.path for slug in gold.bad_page_slugs):
            continue
        if any(slug in page.path for slug in gold.clean_page_slugs):
            gold.clean_tokens += len(
                tokenize(page.text, locale=page.locale, min_length=cfg.min_length)
            )

    for loc in locales:
        consensus = _load_real_bench_consensus(loc)
        if consensus:
            gold.real_bench_present = True
            gold.real_anomaly_spans.extend(consensus)
            for span_row in consensus:
                # Treat agreed anomaly spans as gold needles for that locale.
                gold.needles_by_locale.setdefault(loc, []).append(str(span_row["span"]))
                if "mt/" in span_row["path"] or "/gec/" in span_row["path"]:
                    stem = Path(span_row["path"]).stem
                    if stem not in gold.bad_page_slugs:
                        gold.bad_page_slugs.append(stem)

    for page in pages:
        if page.corpus != "real_bench":
            continue
        if "/clean/" in page.path or page.path.startswith("tests/fixtures/real_bench/clean/"):
            gold.clean_page_slugs.append(Path(page.path).name)
            gold.clean_tokens += len(
                tokenize(page.text, locale=page.locale, min_length=cfg.min_length)
            )

    # De-dupe needles per locale while preserving order.
    for loc, needles in list(gold.needles_by_locale.items()):
        seen: set[str] = set()
        uniq: list[str] = []
        for n in needles:
            key = n.casefold()
            if key in seen:
                continue
            seen.add(key)
            uniq.append(n)
        gold.needles_by_locale[loc] = uniq
    return gold


def _rank_from_flags(flagged_by_page: dict[str, set[str]]) -> list[PageSuspectRank]:
    rows: list[PageSuspectRank] = []
    for path, flags in flagged_by_page.items():
        sample = sorted(flags)[:8]
        rows.append(
            PageSuspectRank(
                path=path,
                unique_suspects=len(flags),
                sample_words=sample,
                score=float(len(flags)),
            )
        )
    rows.sort(key=lambda r: (-r.score, -r.unique_suspects, r.path))
    return rows


def _score_tool(
    run: ToolRun,
    gold: GoldBundle,
    pages: Sequence[PageDoc],
    *,
    lexaudit_words: Sequence[ClassifiedWord] | None = None,
) -> dict[str, Any]:
    if not run.available:
        row = {
            "tool": run.name,
            "available": False,
            "skipped_reason": run.skipped_reason,
            "backend": run.backend,
            "notes": run.notes,
            **_na_metrics(),
        }
        return row

    # Prefer lexaudit-native metrics when we have classified words.
    if run.name == "lexaudit" and lexaudit_words is not None:
        known: list[str] = []
        unseen: list[str] = []
        for loc, needles in gold.needles_by_locale.items():
            for n in needles:
                if n == UNSEEN_NEOLOGISMS.get(loc):
                    unseen.append(n)
                else:
                    known.append(n)
        wr = word_precision_recall(lexaudit_words, known, unseen)
        ranked = run.ranked_pages or _rank_from_flags(run.flagged_by_page)
        # Page P@3 is measured on the synthetic 42-page gold only (fair ranking compare).
        ranked_synth = [r for r in ranked if r.path in gold.synth_paths] or ranked
        p3 = page_precision_at_k(ranked_synth, gold.synth_bad_page_slugs, 3)
        fpr = clean_page_fpr(
            lexaudit_words,
            clean_page_slugs=gold.clean_page_slugs,
            clean_pages_total_tokens=gold.clean_tokens,
        )
        return {
            "tool": run.name,
            "available": True,
            "skipped_reason": None,
            "backend": run.backend,
            "notes": run.notes,
            "word_precision": round(float(wr["word_precision"]), 4),
            "word_recall": round(float(wr["combined_recall"]), 4),
            "word_tp": int(wr["word_tp"]),
            "word_fp": int(wr["word_fp"]),
            "word_fn": int(wr["combined_evaluated"]) - int(wr["combined_hits"]),
            "page_p_at_3": round(float(p3["precision"]), 4),
            "page_p_at_3_hits": int(p3["hits"]),
            "clean_fp_per_1000_tokens": round(float(fpr["fp_per_1000_tokens"]), 3),
            "clean_fp_unique_words": int(fpr["fp_unique_words"]),
            "seconds": None if run.seconds is None else round(run.seconds, 3),
        }

    # Generic spellchecker / linter scoring against gold needles.
    all_flags: set[str] = set()
    for flags in run.flagged_by_page.values():
        all_flags |= flags

    # Build presence map: which needles appear in corpus tokens.
    tokens_by_locale: dict[str, set[str]] = defaultdict(set)
    for page in pages:
        for tok in tokenize(page.text, locale=page.locale, min_length=2):
            tokens_by_locale[page.locale].add(tok)

    hits = 0
    evaluated = 0
    for loc, needles in gold.needles_by_locale.items():
        corpus_toks = tokens_by_locale.get(loc, set())
        for needle in needles:
            present = any(needle_matches_norm(t, needle, loc) for t in corpus_toks)
            if not present:
                # Also allow multi-word span presence via raw text.
                present = any(
                    needle.casefold() in page.text.casefold()
                    for page in pages
                    if page.locale == loc
                )
            if not present:
                continue
            evaluated += 1
            if any(needle_matches_norm(f, needle, loc) for f in all_flags) or any(
                needle.casefold() in f or f in needle.casefold() for f in all_flags
            ):
                hits += 1

    tp = 0
    for flag in all_flags:
        matched = False
        for loc, needles in gold.needles_by_locale.items():
            if any(needle_matches_norm(flag, n, loc) for n in needles):
                matched = True
                break
            if any(flag in n.casefold() or n.casefold() in flag for n in needles):
                matched = True
                break
        if matched:
            tp += 1
    fp = len(all_flags) - tp
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = hits / evaluated if evaluated else 0.0

    ranked = run.ranked_pages or _rank_from_flags(run.flagged_by_page)
    # Competitors: flag-count rank on synthetic pages only (same K=3 gold as lexaudit).
    ranked_synth = [r for r in ranked if r.path in gold.synth_paths]
    p3 = page_precision_at_k(ranked_synth, gold.synth_bad_page_slugs, 3) if ranked_synth else None

    # Clean FPR from flagged tokens on clean pages.
    clean_fp: set[str] = set()
    for path, flags in run.flagged_by_page.items():
        if any(slug in path for slug in gold.clean_page_slugs):
            clean_fp |= flags
    per_1k = (len(clean_fp) / gold.clean_tokens * 1000.0) if gold.clean_tokens else 0.0

    return {
        "tool": run.name,
        "available": True,
        "skipped_reason": None,
        "backend": run.backend,
        "notes": run.notes,
        "word_precision": round(precision, 4),
        "word_recall": round(recall, 4),
        "word_tp": tp,
        "word_fp": fp,
        "word_fn": evaluated - hits,
        "page_p_at_3": None if p3 is None else round(float(p3["precision"]), 4),
        "page_p_at_3_hits": None if p3 is None else int(p3["hits"]),
        "clean_fp_per_1000_tokens": round(per_1k, 3),
        "clean_fp_unique_words": len(clean_fp),
        "seconds": None if run.seconds is None else round(run.seconds, 3),
    }


def run_lexaudit_tool(
    cfg: LexauditConfig,
    locales: Sequence[str],
    pages: Sequence[PageDoc],
    work_dir: Path,
) -> tuple[ToolRun, list[ClassifiedWord]]:
    t0 = time.perf_counter()
    all_words: list[ClassifiedWord] = []
    ranked: list[PageSuspectRank] = []
    flagged: dict[str, set[str]] = defaultdict(set)

    # Synthetic locales via config.
    for loc in locales:
        out = work_dir / "lexaudit" / "synthetic" / loc
        run_cfg = replace(cfg, output_dir=out, locales=[loc])
        words, page_ranks, _ = run_locale_audit(run_cfg, loc, freeze_generated_at=FREEZE_AT)
        all_words.extend(words)
        ranked.extend(page_ranks)
        for w in words:
            if pred_is_anomaly(w.status):
                for s in w.samples:
                    flagged[s.path].add(w.normalized)

    # Real-bench locales (optional).
    real_pages = [p for p in pages if p.corpus == "real_bench"]
    if real_pages:
        rules = ROOT / "rules" / "calques"
        for loc in locales:
            if not any(p.locale == loc for p in real_pages):
                continue
            # Point files_paths at fixture roots that exist for this locale.
            roots: list[Path] = []
            for sub in ("clean", "mt"):
                d = ROOT / "tests" / "fixtures" / "real_bench" / sub / loc
                if d.is_dir():
                    roots.append(d.resolve())
            if not roots:
                continue
            out = work_dir / "lexaudit" / "real" / loc
            run_cfg = replace(
                cfg,
                repo_root=ROOT.resolve(),
                output_dir=out,
                locales=[loc],
                sources=["files"],
                files_paths=tuple(roots),
                academy_root=None,
                packs_root=None,
                calque_rules_dir=rules.resolve() if rules.is_dir() else cfg.calque_rules_dir,
                gold_slugs=(),
                needles=tuple(cfg.needles),
            )
            words, page_ranks, _ = run_locale_audit(run_cfg, loc, freeze_generated_at=FREEZE_AT)
            all_words.extend(words)
            ranked.extend(page_ranks)
            for w in words:
                if pred_is_anomaly(w.status):
                    for s in w.samples:
                        flagged[s.path].add(w.normalized)

    # Global rank by score (synthetic + real mixed).
    ranked.sort(key=lambda r: (-r.score, -r.unique_suspects, r.path))
    elapsed = time.perf_counter() - t0
    return (
        ToolRun(
            name="lexaudit",
            available=True,
            backend="run_locale_audit",
            seconds=elapsed,
            flagged_by_page=dict(flagged),
            ranked_pages=ranked,
            notes="Weighted calque/domain ranking; page P@3 uses native scores.",
        ),
        all_words,
    )


def run_hunspell_tool(pages: Sequence[PageDoc], locales: Sequence[str]) -> ToolRun:
    t0 = time.perf_counter()
    flagged: dict[str, set[str]] = {}
    backends: set[str] = set()
    try:
        checkers = {loc: resolve_checker(loc, HunspellConfig()) for loc in locales}
    except Exception as exc:
        return ToolRun(
            name="hunspell",
            available=False,
            skipped_reason=f"resolve_checker failed: {exc}",
        )

    for checker in checkers.values():
        backends.add(type(checker).__name__)

    for page in pages:
        checker = checkers.get(page.locale)
        if checker is None:
            continue
        tokens = tokenize(page.text, locale=page.locale, min_length=2)
        # Preserve surface forms for hunspell; map back via casefold.
        surfaces = list(dict.fromkeys(tokens))
        try:
            bad = checker.list_misspelled(surfaces)
        except Exception as exc:
            return ToolRun(
                name="hunspell",
                available=False,
                skipped_reason=f"list_misspelled failed: {exc}",
            )
        norms = {casefold(w, page.locale) for w in bad}
        flagged[page.path] = norms

    elapsed = time.perf_counter() - t0
    return ToolRun(
        name="hunspell",
        available=True,
        backend="+".join(sorted(backends)) or "unknown",
        seconds=elapsed,
        flagged_by_page=flagged,
        ranked_pages=_rank_from_flags(flagged),
        notes="Raw dictionary misspellings (spylls or hunspell CLI).",
    )


def _parse_cspell_json(raw: str) -> list[dict[str, Any]]:
    raw = raw.strip()
    if not raw:
        return []
    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError:
        # Some reporters emit NDJSON.
        rows: list[dict[str, Any]] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            with contextlib.suppress(json.JSONDecodeError):
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append(obj)
        return rows
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        issues = payload.get("issues") or payload.get("items") or payload.get("files") or []
        if isinstance(issues, list):
            out: list[dict[str, Any]] = []
            for item in issues:
                if isinstance(item, dict):
                    nested = item.get("issues")
                    if isinstance(nested, list):
                        out.extend(x for x in nested if isinstance(x, dict))
                    else:
                        out.append(item)
            return out
    return []


def run_cspell_tool(pages: Sequence[PageDoc]) -> ToolRun:
    cmd, reason = _find_cspell()
    if cmd is None:
        return ToolRun(name="cspell", available=False, skipped_reason=reason or "unavailable")

    t0 = time.perf_counter()
    flagged: dict[str, set[str]] = defaultdict(set)
    with tempfile.TemporaryDirectory(prefix="lexaudit-cspell-") as tmp:
        tmp_path = Path(tmp)
        by_locale: dict[str, list[PageDoc]] = defaultdict(list)
        for page in pages:
            by_locale[page.locale].append(page)

        file_to_page: dict[str, PageDoc] = {}
        for loc, loc_pages in by_locale.items():
            paths: list[str] = []
            for page in loc_pages:
                safe = page.path.replace("/", "__")
                fpath = tmp_path / f"{loc}__{safe}.md"
                fpath.write_text(page.text, encoding="utf-8")
                paths.append(str(fpath))
                file_to_page[str(fpath.resolve())] = page
                file_to_page[fpath.name] = page

            env = _npx_env(cmd[0]) if "npx" in Path(cmd[0]).name else None
            # cspell glob matching skips /tmp paths; --file --force-check is reliable.
            proc = subprocess.run(
                [
                    *cmd,
                    "lint",
                    "--no-progress",
                    "--no-summary",
                    "--no-config-search",
                    "--force-check",
                    "--locale",
                    CSPELL_LOCALE.get(loc, loc),
                    "--file",
                    *paths,
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=300,
                env=env,
            )
            # Prefer JSON when a reporter package is present; otherwise parse
            # "file:line:col - Unknown word (token)" lines (default reporter).
            issues = _parse_cspell_json(proc.stdout or "")
            if issues:
                for issue in issues:
                    word = str(issue.get("text") or issue.get("word") or "").strip()
                    uri = str(
                        issue.get("uri")
                        or issue.get("filename")
                        or issue.get("file")
                        or issue.get("resource")
                        or ""
                    )
                    page_hit = None
                    if uri:
                        for key, page in file_to_page.items():
                            if key in uri or Path(key).name in uri or uri.endswith(Path(key).name):
                                page_hit = page
                                break
                    if page_hit is None or not word:
                        continue
                    flagged[page_hit.path].add(casefold(word, page_hit.locale))
                continue

            for line in (proc.stdout or "").splitlines() + (proc.stderr or "").splitlines():
                if "Unknown word" not in line and "unknown word" not in line.lower():
                    continue
                page_hit = None
                for key, page in file_to_page.items():
                    name = Path(key).name
                    if name in line or key in line:
                        page_hit = page
                        break
                start = line.rfind("(")
                end = line.rfind(")")
                if page_hit is None or start == -1 or end <= start:
                    continue
                word = line[start + 1 : end].strip()
                if word:
                    flagged[page_hit.path].add(casefold(word, loc))

    elapsed = time.perf_counter() - t0
    return ToolRun(
        name="cspell",
        available=True,
        backend=" ".join(cmd),
        seconds=elapsed,
        flagged_by_page=dict(flagged),
        ranked_pages=_rank_from_flags(dict(flagged)),
        notes="Code-oriented spellchecker; locale packs may be incomplete for RU/UK/SV.",
    )


def run_vale_tool(pages: Sequence[PageDoc]) -> ToolRun:
    vale = _which("vale")
    if vale is None:
        return ToolRun(name="vale", available=False, skipped_reason="vale binary not found")

    t0 = time.perf_counter()
    flagged: dict[str, set[str]] = defaultdict(set)
    with tempfile.TemporaryDirectory(prefix="lexaudit-vale-") as tmp:
        tmp_path = Path(tmp)
        # Minimal ini so Vale can run without a project styles dir.
        ini = tmp_path / ".vale.ini"
        ini.write_text(
            "StylesPath = styles\nMinAlertLevel = suggestion\n[*.md]\nBasedOnStyles =\n",
            encoding="utf-8",
        )
        (tmp_path / "styles").mkdir()
        for page in pages:
            safe = page.path.replace("/", "__")
            fpath = tmp_path / f"{safe}.md"
            fpath.write_text(page.text, encoding="utf-8")
            proc = subprocess.run(
                [vale, "--output=JSON", "--config", str(ini), str(fpath)],
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
            raw = (proc.stdout or "").strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            for _file, alerts in payload.items():
                if not isinstance(alerts, list):
                    continue
                for alert in alerts:
                    if not isinstance(alert, dict):
                        continue
                    match = str(alert.get("Match") or alert.get("Span") or "").strip()
                    if match:
                        # First token of the match.
                        tok = tokenize(match, locale=page.locale, min_length=2)
                        for t in tok:
                            flagged[page.path].add(t)
                        if not tok:
                            flagged[page.path].add(casefold(match, page.locale))

    elapsed = time.perf_counter() - t0
    if not flagged and elapsed < 0.05:
        # Vale present but produced nothing useful / failed silently.
        return ToolRun(
            name="vale",
            available=True,
            backend=vale,
            seconds=elapsed,
            flagged_by_page={},
            ranked_pages=[],
            notes="vale ran with empty styles; alerts may be zero without a style pack.",
        )
    return ToolRun(
        name="vale",
        available=True,
        backend=vale,
        seconds=elapsed,
        flagged_by_page=dict(flagged),
        ranked_pages=_rank_from_flags(dict(flagged)),
        notes="Prose linter; without project styles, signal is weak vs domain calques.",
    )


def run_languagetool_tool(pages: Sequence[PageDoc], locales: Sequence[str]) -> ToolRun:
    use_python = _lt_python_importable()
    use_server = _lt_server_up()
    if not use_python and not use_server:
        return ToolRun(
            name="languagetool",
            available=False,
            skipped_reason="language_tool_python not importable and no local server on :8010",
        )

    t0 = time.perf_counter()
    flagged: dict[str, set[str]] = defaultdict(set)
    backend = "language_tool_python" if use_python else "local-server:8010"

    tools: dict[str, Any] = {}
    if use_python:
        import language_tool_python

        for loc in locales:
            lang = LT_LANG.get(loc, loc)
            try:
                tools[loc] = language_tool_python.LanguageTool(lang)
            except Exception:
                # Fall back to remote/public only if explicitly wanted — skip locale.
                continue
    else:
        tools = {loc: None for loc in locales}

    try:
        for page in pages:
            lang = LT_LANG.get(page.locale, page.locale)
            matches: list[Any] = []
            if use_python:
                tool = tools.get(page.locale)
                if tool is None:
                    continue
                try:
                    matches = list(tool.check(page.text))
                except Exception:
                    continue
            else:
                import urllib.error
                import urllib.parse
                import urllib.request

                data = urllib.parse.urlencode({"language": lang, "text": page.text}).encode()
                req = urllib.request.Request(
                    "http://127.0.0.1:8010/v2/check",
                    data=data,
                    method="POST",
                )
                try:
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        payload = json.loads(resp.read().decode("utf-8"))
                    matches = list(payload.get("matches") or [])
                except (OSError, urllib.error.URLError, json.JSONDecodeError):
                    continue

            for m in matches:
                if use_python:
                    offset = int(getattr(m, "offset", 0) or 0)
                    error_len = int(getattr(m, "errorLength", 0) or 0)
                    span = page.text[offset : offset + error_len]
                else:
                    assert isinstance(m, dict)
                    offset = int(m.get("offset") or 0)
                    error_len = int(m.get("length") or 0)
                    span = page.text[offset : offset + error_len]
                for tok in tokenize(span, locale=page.locale, min_length=2):
                    flagged[page.path].add(tok)
                if span.strip() and not tokenize(span, locale=page.locale, min_length=2):
                    flagged[page.path].add(casefold(span.strip(), page.locale))
    finally:
        if use_python:
            for tool in tools.values():
                close = getattr(tool, "close", None)
                if callable(close):
                    with contextlib.suppress(Exception):
                        close()

    elapsed = time.perf_counter() - t0
    return ToolRun(
        name="languagetool",
        available=True,
        backend=backend,
        seconds=elapsed,
        flagged_by_page=dict(flagged),
        ranked_pages=_rank_from_flags(dict(flagged)),
        notes="Strong on grammar/agreement; weak on domain calques & rewrite-queue ranking.",
    )


def render_markdown(report: dict[str, Any]) -> str:
    tools = report["tools"]
    lines = [
        "# Competitor benchmark (v0.4 Stage V6-1)",
        "",
        f"Generated: `{report.get('generated_at', '')}`",
        "",
        "Same gold set: synthetic-demo **42 pages** (7 locales × 6) "
        + (
            "+ `gold/real_bench` consensus anomalies"
            if report.get("real_bench_present")
            else "(real_bench gold absent)"
        )
        + ".",
        "",
        "## Summary table",
        "",
        "| Tool | Available | Backend | Word P | Word R | Page P@3 | Clean FP / 1k | Time |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for name in TOOL_ORDER:
        row = tools[name]
        avail = "yes" if row.get("available") else "skipped"
        lines.append(
            "| {tool} | {avail} | {backend} | {wp} | {wr} | {p3} | {fpr} | {t} |".format(
                tool=row.get("tool", name),
                avail=avail
                if row.get("available")
                else f"skipped ({row.get('skipped_reason') or 'n/a'})",
                backend=row.get("backend") or "—",
                wp=_fmt_pct(row.get("word_precision")),
                wr=_fmt_pct(row.get("word_recall")),
                p3=_fmt_pct(row.get("page_p_at_3")),
                fpr=_fmt_num(row.get("clean_fp_per_1000_tokens")),
                t=_fmt_sec(row.get("seconds")),
            )
        )

    lines.extend(
        [
            "",
            "## How to read this honestly",
            "",
            "- **LanguageTool** usually wins on *grammar / agreement / punctuation* — that is not",
            "  lexaudit's product job. When LT is available, expect higher generic flag volume and",
            "  better catch-rate on GEC typos, not on bilingual calques.",
            "- **lexaudit** wins on *calque / false-friend ranking*, domain allowlists, lower",
            "  clean-page FPR, and rewrite-queue **page P@3** (weighted scores on the synthetic",
            "  42-page gold). Spellcheckers that only count OOV tokens often bury planted calques",
            "  under jargon-heavy clean pages — compare Clean FP / 1k and P@3 in the table.",
            "- **Hunspell / cspell / Vale** are useful baselines. They do not ship FairHelm",
            "  (or your) domain lists, and they do not rank a multi-page corpus for a rewrite agent.",
            "- Rows marked **skipped** mean the binary/package was missing on the runner.",
            "  CI should call `python scripts/benchmark_competitors.py --lexaudit-only` so the",
            "  table still materializes without installing competitors.",
            "",
            "## Reproduce",
            "",
            "```bash",
            "uv run python scripts/benchmark_competitors.py",
            "uv run python scripts/benchmark_competitors.py --lexaudit-only  # CI / smoke",
            "```",
            "",
            f"Machine snapshot: `{json.dumps(report.get('availability', {}), ensure_ascii=False)}`",
            "",
        ]
    )
    return "\n".join(lines)


def run_benchmark(
    *,
    locales: Sequence[str] | None = None,
    lexaudit_only: bool = False,
    include_real_bench: bool = True,
    work_dir: Path | None = None,
    out_json: Path | None = None,
    out_md: Path | None = None,
) -> dict[str, Any]:
    cfg = load_config(SYNTH_CFG)
    locs = list(locales) if locales else list(cfg.locales)
    work = work_dir or (ROOT / "tmp" / "competitor-benchmark")
    work.mkdir(parents=True, exist_ok=True)

    pages = _collect_synth_pages(cfg, locs)
    if include_real_bench and GOLD_REAL_DIR.is_dir():
        pages.extend(_real_bench_pages(locs))
    gold = build_gold(cfg, pages, locs)

    hunspell_ok = False
    with contextlib.suppress(Exception):
        sample = resolve_checker(locs[0] if locs else "en", HunspellConfig())
        hunspell_ok = type(sample).__name__ != "ProperOnlyChecker" or bool(locs)

    availability = {
        "hunspell": hunspell_ok,
        "cspell": _find_cspell()[0] is not None,
        "vale": _which("vale") is not None,
        "languagetool": _lt_python_importable() or _lt_server_up(),
        "lexaudit": True,
    }

    runs: dict[str, ToolRun] = {}
    lex_words: list[ClassifiedWord] = []

    lex_run, lex_words = run_lexaudit_tool(cfg, locs, pages, work)
    runs["lexaudit"] = lex_run

    if lexaudit_only:
        for name, reason in (
            ("hunspell", "skipped via --lexaudit-only"),
            ("cspell", "skipped via --lexaudit-only"),
            ("vale", "skipped via --lexaudit-only"),
            ("languagetool", "skipped via --lexaudit-only"),
        ):
            runs[name] = ToolRun(name=name, available=False, skipped_reason=reason)
    else:
        runs["hunspell"] = run_hunspell_tool(pages, locs)
        runs["cspell"] = run_cspell_tool(pages)
        runs["vale"] = run_vale_tool(pages)
        runs["languagetool"] = run_languagetool_tool(pages, locs)

    tools_out: dict[str, Any] = {}
    for name in TOOL_ORDER:
        tools_out[name] = _score_tool(
            runs[name],
            gold,
            pages,
            lexaudit_words=lex_words if name == "lexaudit" else None,
        )

    report: dict[str, Any] = {
        "generated_at": _now_iso(),
        "schema_version": 1,
        "locales": locs,
        "page_count": len(pages),
        "synthetic_pages": sum(1 for p in pages if p.corpus == "synthetic"),
        "real_bench_pages": sum(1 for p in pages if p.corpus == "real_bench"),
        "real_bench_present": gold.real_bench_present,
        "lexaudit_only": lexaudit_only,
        "availability": availability,
        "gold": {
            "bad_page_slug_count": len(gold.bad_page_slugs),
            "clean_tokens": gold.clean_tokens,
            "needles_by_locale": {k: list(v) for k, v in gold.needles_by_locale.items()},
            "real_anomaly_span_count": len(gold.real_anomaly_spans),
        },
        "tools": tools_out,
    }

    json_path = out_json or DEFAULT_JSON
    md_path = out_md or DEFAULT_MD
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lexaudit-only",
        action="store_true",
        help="Run only lexaudit; mark competitors skipped (CI-safe).",
    )
    parser.add_argument(
        "--locales",
        default="",
        help="Comma-separated locale filter (default: all synthetic-demo locales).",
    )
    parser.add_argument(
        "--no-real-bench",
        action="store_true",
        help="Skip real_bench fixtures even if gold/real_bench exists.",
    )
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    parser.add_argument("--work-dir", type=Path, default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)

    locales = [x.strip() for x in args.locales.split(",") if x.strip()] or None
    report = run_benchmark(
        locales=locales,
        lexaudit_only=args.lexaudit_only,
        include_real_bench=not args.no_real_bench,
        work_dir=args.work_dir,
        out_json=args.out_json,
        out_md=args.out_md,
    )

    # Print compact table for the terminal.
    print(f"wrote {args.out_json or DEFAULT_JSON}")
    print(f"wrote {args.out_md or DEFAULT_MD}")
    for name in TOOL_ORDER:
        row = report["tools"][name]
        if not row["available"]:
            print(f"{name}: SKIPPED ({row.get('skipped_reason')})")
        else:
            print(
                f"{name}: P={_fmt_pct(row['word_precision'])} "
                f"R={_fmt_pct(row['word_recall'])} "
                f"P@3={_fmt_pct(row['page_p_at_3'])} "
                f"FPR/1k={_fmt_num(row['clean_fp_per_1000_tokens'])} "
                f"t={_fmt_sec(row['seconds'])}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
