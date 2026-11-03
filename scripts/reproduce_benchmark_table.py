#!/usr/bin/env python3
"""Reproduce synthetic 42-page ablation metrics and keep README/docs in sync.

Writes ``eval/synthetic-benchmark-metrics.json``, prints Markdown tables, and
supports ``--check`` / ``--write-docs``.

Note: ``scripts/render_diagrams.py`` embeds benchmark numbers in a hardcoded
``BENCHMARK_SVG`` string (it does not read this JSON). After metric changes,
update that SVG template and re-run ``uv run python scripts/render_diagrams.py``
if the diagram must match; this script does not regenerate the SVG from metrics.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from lexaudit.config import LexauditConfig, load_config  # noqa: E402
from lexaudit.core.pipeline import run_locale_audit  # noqa: E402
from lexaudit.core.tokenize import tokenize  # noqa: E402
from lexaudit.core.types import ClassifiedWord, PageSuspectRank  # noqa: E402
from lexaudit.eval.metrics import (  # noqa: E402
    clean_page_fpr,
    needle_recall,
    page_precision_at_k,
    page_recall_at_k,
)
from lexaudit.sources.collect import collect_all  # noqa: E402

SYNTH_CFG = ROOT / "examples" / "synthetic-demo" / "lexaudit.config.yaml"
METRICS_JSON = ROOT / "eval" / "synthetic-benchmark-metrics.json"
README_PATH = ROOT / "README.md"
DOCS_BENCH_PATH = ROOT / "docs" / "synthetic-benchmark.md"
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

LOCALE_NAMES: dict[str, str] = {
    "en": "English",
    "de": "German",
    "es": "Spanish",
    "pl": "Polish",
    "ru": "Russian",
    "sv": "Swedish",
    "uk": "Ukrainian",
}

ABLATION_ORDER = ("A", "B", "C")

README_TABLE_START = "| Setup | Bad page in top 2 |"
DOCS_MACRO_START = "| Configuration | `Precision@2` |"


def fmt_pct(value: float) -> str:
    return f"{value * 100.0:.1f}%"


def fmt_map(value: float) -> str:
    return f"{value:.3f}"


def fmt_seconds(value: float) -> str:
    return f"{value:.2f} s"


def fmt_fraction(hits: int, evaluated: int) -> str:
    return f"{hits}/{evaluated}"


def average_precision(ranked: list[PageSuspectRank], gold_slugs: list[str]) -> float:
    """AP with denominator = |gold| (3 defective pages per locale)."""
    n_bad = len(gold_slugs)
    if n_bad == 0:
        return 0.0
    hits = 0
    sum_prec = 0.0
    for idx, page in enumerate(ranked, 1):
        if any(slug in page.path for slug in gold_slugs):
            hits += 1
            sum_prec += hits / idx
    return sum_prec / float(n_bad)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _ablation_config(cfg: LexauditConfig, name: str, out_dir: Path) -> LexauditConfig:
    if name == "A":
        return replace(
            cfg,
            output_dir=out_dir,
            proper_names_path=None,
            acronyms_path=None,
            allowlist_path=None,
            enable_morph=False,
            enable_compound=False,
            enable_neologism=False,
            enable_calque=False,
            rank_mode="raw",
            needles=[],
        )
    if name == "B":
        return replace(
            cfg,
            output_dir=out_dir,
            enable_neologism=False,
            enable_calque=False,
            rank_mode="raw",
            needles=[],
        )
    if name == "C":
        return replace(cfg, output_dir=out_dir)
    msg = f"unknown ablation {name!r}"
    raise ValueError(msg)


def _count_clean_tokens(cfg: LexauditConfig, locale: str) -> tuple[list[str], int]:
    academy_root = cfg.academy_root or (
        cfg.repo_root / "infra" / "corpus-ci" / "pending-academy-articles"
    )
    packs_root = cfg.packs_root or (cfg.repo_root / "infra" / "corpus-ci" / "pending-model-packs")
    chunks = collect_all(
        cfg.repo_root,
        locale,
        set(cfg.sources),
        academy_root=academy_root,
        packs_root=packs_root,
        files_paths=cfg.files_paths,
    )
    clean_slugs: list[str] = []
    total = 0
    for chunk in chunks:
        if any(slug in chunk.path for slug in cfg.gold_slugs):
            continue
        stem = Path(chunk.path).stem
        clean_slugs.append(stem)
        total += len(tokenize(chunk.text, locale=locale, min_length=cfg.min_length))
    # Prefer short prefixes used by clean_page_fpr / gold matching.
    prefixes = [f"{locale}-01", f"{locale}-02", f"{locale}-03"]
    return prefixes, total


def _locale_metrics(
    words: list[ClassifiedWord],
    pages: list[PageSuspectRank],
    *,
    cfg: LexauditConfig,
    locale: str,
) -> dict[str, Any]:
    gold_loc = [g for g in cfg.gold_slugs if g.startswith(f"{locale}-")]
    p2 = page_precision_at_k(pages, gold_loc, 2)
    p3 = page_precision_at_k(pages, gold_loc, 3)
    r2 = page_recall_at_k(pages, gold_loc, 2)
    r3 = page_recall_at_k(pages, gold_loc, 3)
    known = needle_recall(cfg.needles, words, locale=locale)
    unseen = needle_recall([UNSEEN_NEOLOGISMS[locale]], words, locale=locale)
    return {
        "locale": locale,
        "p_at_2": float(p2["precision"]),
        "p_at_2_hits": int(p2["hits"]),
        "p_at_3": float(p3["precision"]),
        "p_at_3_hits": int(p3["hits"]),
        "r_at_2": float(r2["recall"]),
        "r_at_2_hits": int(r2["hits"]),
        "r_at_3": float(r3["recall"]),
        "r_at_3_hits": int(r3["hits"]),
        "map": average_precision(pages, gold_loc),
        "known_hits": int(known["hits"]),
        "known_evaluated": int(known["evaluated"]),
        "unseen_hits": int(unseen["hits"]),
        "unseen_evaluated": int(unseen["evaluated"]),
        "n_bad": len(gold_loc),
        "top_paths": [p.path for p in pages[:6]],
    }


def compute_benchmark_metrics(
    *,
    config_path: Path = SYNTH_CFG,
    work_dir: Path | None = None,
) -> dict[str, Any]:
    """Run ablations A/B/C across all configured locales and aggregate metrics."""
    cfg = load_config(config_path)
    base_out = work_dir or (ROOT / "tmp" / "reproduce-benchmark")
    ablations: dict[str, Any] = {}
    per_locale_c: dict[str, Any] = {}

    for name in ABLATION_ORDER:
        t0 = time.perf_counter()
        locale_rows: list[dict[str, Any]] = []
        all_words: list[ClassifiedWord] = []
        clean_slugs: list[str] = []
        clean_tokens = 0
        for loc in cfg.locales:
            run_cfg = _ablation_config(cfg, name, base_out / name / loc)
            # Keep gold needles for recall measurement even when ranking disables them.
            words, pages, _ = run_locale_audit(run_cfg, loc, freeze_generated_at=FREEZE_AT)
            row = _locale_metrics(words, pages, cfg=cfg, locale=loc)
            locale_rows.append(row)
            all_words.extend(words)
            prefixes, tok = _count_clean_tokens(cfg, loc)
            clean_slugs.extend(prefixes)
            clean_tokens += tok
            if name == "C":
                per_locale_c[loc] = row
        elapsed = time.perf_counter() - t0
        known_hits = sum(r["known_hits"] for r in locale_rows)
        known_eval = sum(r["known_evaluated"] for r in locale_rows)
        unseen_hits = sum(r["unseen_hits"] for r in locale_rows)
        unseen_eval = sum(r["unseen_evaluated"] for r in locale_rows)
        comb_hits = known_hits + unseen_hits
        comb_eval = known_eval + unseen_eval
        fpr = clean_page_fpr(
            all_words,
            clean_page_slugs=sorted(set(clean_slugs)),
            clean_pages_total_tokens=clean_tokens,
        )
        ablations[name] = {
            "p_at_2": _mean([r["p_at_2"] for r in locale_rows]),
            "p_at_3": _mean([r["p_at_3"] for r in locale_rows]),
            "r_at_2": _mean([r["r_at_2"] for r in locale_rows]),
            "r_at_3": _mean([r["r_at_3"] for r in locale_rows]),
            "map": _mean([r["map"] for r in locale_rows]),
            "known_hits": known_hits,
            "known_evaluated": known_eval,
            "known_recall": (known_hits / known_eval) if known_eval else 0.0,
            "unseen_hits": unseen_hits,
            "unseen_evaluated": unseen_eval,
            "unseen_recall": (unseen_hits / unseen_eval) if unseen_eval else 0.0,
            "combined_hits": comb_hits,
            "combined_evaluated": comb_eval,
            "combined_recall": (comb_hits / comb_eval) if comb_eval else 0.0,
            "seconds": elapsed,
            "clean_page_fpr": {
                "fp_unique_words": fpr["fp_unique_words"],
                "clean_pages_total_tokens": fpr["clean_pages_total_tokens"],
                "fp_per_1000_tokens": fpr["fp_per_1000_tokens"],
                "unique_word_fpr": fpr["unique_word_fpr"],
            },
            "locales": {r["locale"]: r for r in locale_rows},
        }

    return {
        "freeze_generated_at": FREEZE_AT,
        "config": str(config_path.relative_to(ROOT)),
        "locales": list(cfg.locales),
        "ablations": ablations,
        "per_locale_full": per_locale_c,
        "unseen_neologisms": dict(UNSEEN_NEOLOGISMS),
    }


def _ablation_label_readme(name: str) -> str:
    return {
        "A": "A. Plain spellchecker",
        "B": "B. Plus your word lists",
        "C": "C. Full lexaudit",
    }[name]


def _ablation_label_docs(name: str) -> str:
    return {
        "A": "A. Naive Hunspell (`raw`)",
        "B": "B. Dictionaries + Morph/Compound (`raw`)",
        "C": "C. Full `lexaudit` (`weighted`)",
    }[name]


def render_readme_table(metrics: dict[str, Any]) -> str:
    lines = [
        "| Setup | Bad page in top 2 | Bad page in top 3 | "
        "Recall@2 | Recall@3 | MAP (0 to 1, higher is better) | "
        "Known problems found | Brand-new neologisms found | Combined planted problems | "
        "Clean-page FP / 1k tokens | Time |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ABLATION_ORDER:
        a = metrics["ablations"][name]
        lines.append(
            "| {setup} | {p2} | {p3} | {r2} | {r3} | {mp} | {known} | {unseen} | {comb} | {fpr} | {t} |".format(
                setup=_ablation_label_readme(name),
                p2=fmt_pct(a["p_at_2"]),
                p3=fmt_pct(a["p_at_3"]),
                r2=fmt_pct(a["r_at_2"]),
                r3=fmt_pct(a["r_at_3"]),
                mp=fmt_map(a["map"]),
                known=f"{fmt_pct(a['known_recall'])} ({fmt_fraction(a['known_hits'], a['known_evaluated'])})",
                unseen=f"{fmt_pct(a['unseen_recall'])} ({fmt_fraction(a['unseen_hits'], a['unseen_evaluated'])})",
                comb=f"{fmt_pct(a['combined_recall'])} ({fmt_fraction(a['combined_hits'], a['combined_evaluated'])})",
                fpr=f"{a['clean_page_fpr']['fp_per_1000_tokens']:.1f}",
                t=fmt_seconds(a["seconds"]),
            )
        )
    return "\n".join(lines)


def render_docs_macro_table(metrics: dict[str, Any]) -> str:
    lines = [
        "| Configuration | `Precision@2` | `Precision@3` | `Recall@2` | `Recall@3` | "
        "`MAP` (Mean Average Precision) | Known-Rule Calque Recall | Unseen Neologism Recall | "
        "Combined Calque Recall | Clean-Page FP / 1000 tokens | Total CPU Time (42 pages) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ABLATION_ORDER:
        a = metrics["ablations"][name]
        lines.append(
            "| {setup} | {p2} | {p3} | {r2} | {r3} | {mp} | {known} | {unseen} | {comb} | {fpr} | {t} |".format(
                setup=_ablation_label_docs(name),
                p2=fmt_pct(a["p_at_2"]),
                p3=fmt_pct(a["p_at_3"]),
                r2=fmt_pct(a["r_at_2"]),
                r3=fmt_pct(a["r_at_3"]),
                mp=fmt_map(a["map"]),
                known=f"{fmt_pct(a['known_recall'])} ({fmt_fraction(a['known_hits'], a['known_evaluated'])})",
                unseen=f"{fmt_pct(a['unseen_recall'])} ({fmt_fraction(a['unseen_hits'], a['unseen_evaluated'])})",
                comb=f"{fmt_pct(a['combined_recall'])} ({fmt_fraction(a['combined_hits'], a['combined_evaluated'])})",
                fpr=f"{a['clean_page_fpr']['fp_per_1000_tokens']:.1f}",
                t=fmt_seconds(a["seconds"]),
            )
        )
    return "\n".join(lines)


def render_docs_per_locale_table(metrics: dict[str, Any]) -> str:
    a_map = metrics["ablations"]["A"]["locales"]
    lines = [
        "| Locale | Language | Ablation A `P@3` | `lexaudit` `P@2` | `lexaudit` `P@3` | "
        "`lexaudit` `R@2` | `lexaudit` `R@3` | Ablation A `MAP` | `lexaudit` `MAP` | "
        "Known Recall | Unseen Recall | Combined Recall |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for loc in metrics["locales"]:
        a = a_map[loc]
        c = metrics["per_locale_full"][loc]
        known_s = f"{fmt_pct(c['known_hits'] / c['known_evaluated'] if c['known_evaluated'] else 0.0)} ({fmt_fraction(c['known_hits'], c['known_evaluated'])})"
        unseen_s = f"{fmt_pct(c['unseen_hits'] / c['unseen_evaluated'] if c['unseen_evaluated'] else 0.0)} ({fmt_fraction(c['unseen_hits'], c['unseen_evaluated'])})"
        comb_h = c["known_hits"] + c["unseen_hits"]
        comb_e = c["known_evaluated"] + c["unseen_evaluated"]
        comb_s = f"{fmt_pct(comb_h / comb_e if comb_e else 0.0)} ({fmt_fraction(comb_h, comb_e)})"
        lines.append(
            "| **`{loc}`** | {lang} | {ap3} | {cp2} | {cp3} | {cr2} | {cr3} | {amap} | {cmap} | "
            "{known} | {unseen} | {comb} |".format(
                loc=loc,
                lang=LOCALE_NAMES.get(loc, loc),
                ap3=f"{fmt_pct(a['p_at_3'])} ({fmt_fraction(a['p_at_3_hits'], 3)})",
                cp2=f"{fmt_pct(c['p_at_2'])} ({fmt_fraction(c['p_at_2_hits'], 2)})",
                cp3=f"**{fmt_pct(c['p_at_3'])} ({fmt_fraction(c['p_at_3_hits'], 3)})**",
                cr2=fmt_pct(c["r_at_2"]),
                cr3=fmt_pct(c["r_at_3"]),
                amap=fmt_map(a["map"]),
                cmap=f"**{fmt_map(c['map'])}**",
                known=known_s,
                unseen=unseen_s,
                comb=comb_s,
            )
        )
    return "\n".join(lines)


def render_readme_bullets(metrics: dict[str, Any]) -> str:
    c = metrics["ablations"]["C"]
    return "\n".join(
        [
            "What this means:",
            "",
            "- Pages with known problems come first in every language. The plain spellchecker puts clean pages first.",
            f"- Known-rule problems: **{fmt_pct(c['known_recall'])}** "
            f"({fmt_fraction(c['known_hits'], c['known_evaluated'])}). "
            f"Unseen single-occurrence neologisms (Zipf + char n-gram / affix-glue): "
            f"**{fmt_pct(c['unseen_recall'])}** "
            f"({fmt_fraction(c['unseen_hits'], c['unseen_evaluated'])}). "
            f"Combined planted problems (honest fraction): **{fmt_pct(c['combined_recall'])}** "
            f"({fmt_fraction(c['combined_hits'], c['combined_evaluated'])}).",
            f"- With exactly 3 defective pages per locale, `Recall@2` is "
            f"**{fmt_pct(c['r_at_2'])}** when the top-2 slots are both bad (`Precision@2` = "
            f"**{fmt_pct(c['p_at_2'])}**). `Precision@3` / `Recall@3` are "
            f"**{fmt_pct(c['p_at_3'])}** (singleton inventeds outrank repeated domain jargon).",
            f"- Clean-page false positives: **{c['clean_page_fpr']['fp_per_1000_tokens']:.1f}** "
            f"unique flagged words per 1000 tokens "
            f"({c['clean_page_fpr']['fp_unique_words']} unique FP / "
            f"{c['clean_page_fpr']['clean_pages_total_tokens']} tokens).",
            "- Domain terms that recur on a page (or sit in H1/title) are tagged "
            "`domain-term-candidate`, nearly zero-weighted in ranking, and listed under "
            "Suggested glossary additions.",
        ]
    )


def _replace_markdown_table(text: str, start_marker: str, new_table: str) -> str:
    lines = text.splitlines(keepends=True)
    start = None
    for i, line in enumerate(lines):
        if line.startswith(start_marker):
            start = i
            break
    if start is None:
        msg = f"table start marker not found: {start_marker!r}"
        raise ValueError(msg)
    end = start + 1
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    replacement = new_table if new_table.endswith("\n") else new_table + "\n"
    return "".join(lines[:start]) + replacement + "".join(lines[end:])


def write_docs(metrics: dict[str, Any]) -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    readme = _replace_markdown_table(readme, README_TABLE_START, render_readme_table(metrics))
    # Replace the "What this means:" bullet block through the blank line before Documentation.
    m = re.search(
        r"What this means:\n\n(?:- .+\n)+",
        readme,
    )
    if not m:
        msg = "README 'What this means' block not found"
        raise ValueError(msg)
    readme = readme[: m.start()] + render_readme_bullets(metrics) + "\n\n" + readme[m.end() :]
    README_PATH.write_text(readme, encoding="utf-8")

    docs = DOCS_BENCH_PATH.read_text(encoding="utf-8")
    docs = _replace_markdown_table(docs, DOCS_MACRO_START, render_docs_macro_table(metrics))
    # Per-language table
    per_start = "| Locale | Language | Ablation A `P@3` |"
    docs = _replace_markdown_table(docs, per_start, render_docs_per_locale_table(metrics))

    c = metrics["ablations"]["C"]
    # Refresh section 3 heading numbers to current C metrics.
    docs = re.sub(
        r"## 3\. Error Analysis & Honest Limitations \(Why `P@3 = [^`]+` and `MAP = [^`]+`\)",
        f"## 3. Error Analysis & Honest Limitations "
        f"(Why `P@3 = {fmt_pct(c['p_at_3'])}` and `MAP = {fmt_map(c['map'])}`)",
        docs,
        count=1,
    )
    # Insert / refresh R@k explanation after the ablation list if missing.
    explain = (
        "\n"
        f"Per locale there are exactly **3 defective** and **3 clean** pages. "
        f"Macro-averaged full `lexaudit` currently reports "
        f"`Precision@2` = **{fmt_pct(c['p_at_2'])}**, "
        f"`Recall@2` = **{fmt_pct(c['r_at_2'])}** (two of three bad pages in the top two), "
        f"`Precision@3` / `Recall@3` = **{fmt_pct(c['p_at_3'])}**, "
        f"`MAP` = **{fmt_map(c['map'])}**. "
        f"Known-rule calque recall is **{fmt_pct(c['known_recall'])}** "
        f"({fmt_fraction(c['known_hits'], c['known_evaluated'])}); "
        f"unseen singleton neologisms are "
        f"**{fmt_pct(c['unseen_recall'])}** "
        f"({fmt_fraction(c['unseen_hits'], c['unseen_evaluated'])}); "
        f"combined planted-problem recall is the honest fraction "
        f"**{fmt_pct(c['combined_recall'])}** "
        f"({fmt_fraction(c['combined_hits'], c['combined_evaluated'])}). "
        f"Clean-page FPR is "
        f"**{c['clean_page_fpr']['fp_per_1000_tokens']:.1f}** unique FP words / 1000 tokens.\n"
    )
    marker = "### Macro-Averaged Summary Across All 7 Languages"
    if marker in docs:
        # Replace any previous auto-summary paragraph immediately before the marker.
        docs = re.sub(
            r"\nPer locale there are exactly \*\*3 defective\*\*.*?\n(?=### Macro-Averaged Summary Across All 7 Languages)",
            explain + "\n",
            docs,
            count=1,
            flags=re.S,
        )
        if "Per locale there are exactly **3 defective**" not in docs:
            docs = docs.replace(marker, explain.lstrip("\n") + "\n" + marker)

    # Reproduce section: point at this script.
    repro = (
        "## 4. Reproduce the Study Locally\n"
        "\n"
        "```bash\n"
        "uv run lexaudit audit --config examples/synthetic-demo/lexaudit.config.yaml\n"
        "uv run python scripts/reproduce_benchmark_table.py --write-docs\n"
        "uv run python scripts/reproduce_benchmark_table.py --check\n"
        "uv run pytest tests/test_synthetic_benchmark.py tests/test_benchmark_docs_sync.py\n"
        "```\n"
    )
    docs = re.sub(
        r"## 4\. Reproduce the Study Locally\n\n```bash\n.*?```\n",
        repro,
        docs,
        count=1,
        flags=re.S,
    )
    DOCS_BENCH_PATH.write_text(docs, encoding="utf-8")


def _is_separator_row(cells: list[str]) -> bool:
    if not cells:
        return True
    return all(re.fullmatch(r":?-{3,}:?", c or "") is not None for c in cells)


def _extract_table_rows(text: str, start_marker: str) -> list[list[str]]:
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.startswith(start_marker)), None)
    if start is None:
        msg = f"missing table starting with {start_marker!r}"
        raise ValueError(msg)
    rows: list[list[str]] = []
    for ln in lines[start:]:
        if not ln.startswith("|"):
            break
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if _is_separator_row(cells):
            continue
        rows.append(cells)
    return rows


def _expected_readme_cells(metrics: dict[str, Any]) -> list[list[str]]:
    out: list[list[str]] = []
    for name in ABLATION_ORDER:
        a = metrics["ablations"][name]
        out.append(
            [
                fmt_pct(a["p_at_2"]),
                fmt_pct(a["p_at_3"]),
                fmt_pct(a["r_at_2"]),
                fmt_pct(a["r_at_3"]),
                fmt_map(a["map"]),
                fmt_pct(a["known_recall"]),
                fmt_fraction(a["known_hits"], a["known_evaluated"]),
                fmt_pct(a["unseen_recall"]),
                fmt_fraction(a["unseen_hits"], a["unseen_evaluated"]),
                fmt_pct(a["combined_recall"]),
                fmt_fraction(a["combined_hits"], a["combined_evaluated"]),
                f"{a['clean_page_fpr']['fp_per_1000_tokens']:.1f}",
            ]
        )
    return out


def _expected_docs_macro_cells(metrics: dict[str, Any]) -> list[list[str]]:
    # Same core numeric set as README (time excluded from strict check).
    return _expected_readme_cells(metrics)


def check_docs_sync(metrics: dict[str, Any] | None = None) -> list[str]:
    """Return a list of human-readable mismatches (empty ⇒ OK)."""
    data = metrics if metrics is not None else compute_benchmark_metrics()
    errors: list[str] = []

    readme = README_PATH.read_text(encoding="utf-8")
    docs = DOCS_BENCH_PATH.read_text(encoding="utf-8")
    readme_rows = _extract_table_rows(readme, README_TABLE_START)
    docs_rows = _extract_table_rows(docs, DOCS_MACRO_START)

    # Skip header row; expect 3 ablation rows.
    readme_body = [r for r in readme_rows[1:] if r and not r[0].startswith("---")]
    docs_body = [r for r in docs_rows[1:] if r and not r[0].startswith("---")]
    if len(readme_body) != 3:
        errors.append(f"README honest-answer table: expected 3 data rows, got {len(readme_body)}")
    if len(docs_body) != 3:
        errors.append(f"docs macro table: expected 3 data rows, got {len(docs_body)}")

    expected = _expected_readme_cells(data)
    for idx, (row, exp) in enumerate(zip(readme_body, expected, strict=False)):
        joined = " | ".join(row)
        for token in exp:
            if token not in joined:
                errors.append(
                    f"README row {ABLATION_ORDER[idx]}: missing expected token {token!r} in {joined!r}"
                )

    expected_docs = _expected_docs_macro_cells(data)
    for idx, (row, exp) in enumerate(zip(docs_body, expected_docs, strict=False)):
        joined = " | ".join(row)
        for token in exp:
            if token not in joined:
                errors.append(
                    f"docs macro row {ABLATION_ORDER[idx]}: missing expected token {token!r} in {joined!r}"
                )

    # Guard against the old vague claim.
    if re.search(r"About 78%\s+of all planted problems", readme):
        errors.append("README still contains vague 'About 78%' wording")

    return errors


def write_metrics_json(metrics: dict[str, Any], path: Path = METRICS_JSON) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(metrics, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Recompute metrics and verify README/docs table numbers (exit 1 on mismatch).",
    )
    parser.add_argument(
        "--write-docs",
        action="store_true",
        help="Update README.md and docs/synthetic-benchmark.md tables from recomputed metrics.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=METRICS_JSON,
        help=f"Path for metrics JSON (default: {METRICS_JSON})",
    )
    args = parser.parse_args(argv)

    metrics = compute_benchmark_metrics()
    write_metrics_json(metrics, args.json_out)

    print(render_readme_table(metrics))
    print()
    print(render_docs_macro_table(metrics))
    print()
    print(render_docs_per_locale_table(metrics))
    print()
    c = metrics["ablations"]["C"]
    print(
        "Summary C: "
        f"P@2={fmt_pct(c['p_at_2'])} P@3={fmt_pct(c['p_at_3'])} "
        f"R@2={fmt_pct(c['r_at_2'])} R@3={fmt_pct(c['r_at_3'])} "
        f"MAP={fmt_map(c['map'])} "
        f"known={fmt_fraction(c['known_hits'], c['known_evaluated'])} "
        f"unseen={fmt_fraction(c['unseen_hits'], c['unseen_evaluated'])} "
        f"combined={fmt_fraction(c['combined_hits'], c['combined_evaluated'])} "
        f"clean_fpr_per_1k={c['clean_page_fpr']['fp_per_1000_tokens']:.1f}"
    )
    print(f"Wrote {args.json_out.relative_to(ROOT)}")

    if args.write_docs:
        write_docs(metrics)
        print(f"Updated {README_PATH.relative_to(ROOT)} and {DOCS_BENCH_PATH.relative_to(ROOT)}")

    if args.check:
        errs = check_docs_sync(metrics)
        if errs:
            print("CHECK FAILED:", file=sys.stderr)
            for e in errs:
                print(f"  - {e}", file=sys.stderr)
            return 1
        print("CHECK OK: README.md and docs/synthetic-benchmark.md match recomputed metrics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
