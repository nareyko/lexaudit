"""CLI entry: audit | rank | diff | expand-needle | explain | label | gold | eval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import click

from lexaudit import __version__
from lexaudit.config import resolve_or_default_config
from lexaudit.core.pipeline import run_locale_audit
from lexaudit.core.rank import rank_pages
from lexaudit.core.types import ClassifiedWord
from lexaudit.curated.queue import append_pending_from_rank, load_curated, save_curated
from lexaudit.report.write import write_reports


@click.group()
@click.version_option(__version__, prog_name="lexaudit")
def main() -> None:
    """Locale vocabulary audit - detection and ranking only."""


@main.command()
def ping() -> None:
    """Smoke command for empty-package green tests."""
    click.echo(f"lexaudit {__version__}")


@main.command("audit")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to lexaudit.config.yaml (auto-discovered or zero-config if omitted)",
)
@click.option(
    "--path",
    "target_paths",
    type=click.Path(exists=True, path_type=Path),
    multiple=True,
    help="Audit specific Markdown/JSON/HTML/PO/XLIFF file(s) or folder(s) directly",
)
@click.option("--locale", default=None, help="Comma-separated locales or omit for config list")
@click.option("--freeze-at", default=None, help="Freeze generated_at for deterministic JSON")
@click.option(
    "--check/--no-check",
    default=False,
    help="Exit 1 when calques/invented (or --fail-on) remain; exit 0 when clean",
)
@click.option(
    "--fail-on",
    default=None,
    help="Statuses that fail --check (default calque,invented; or 'all').",
)
@click.option(
    "--format",
    "out_format",
    type=click.Choice(["text", "json", "sarif"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Stdout machine format (reports are always written under output_dir)",
)
@click.option(
    "--github-annotations",
    is_flag=True,
    help="Emit GitHub Actions ::error/::warning lines",
)
@click.option("--html/--no-html", default=True, help="Write report.html for editors")
@click.option(
    "--no-fetch-dicts",
    is_flag=True,
    help="Do not auto-download missing spelling dictionaries",
)
@click.option(
    "--sarif-file",
    type=click.Path(path_type=Path),
    default=None,
    help="Also write a SARIF file to this path (merged locales)",
)
def audit_cmd(
    config_path: Path | None,
    target_paths: tuple[Path, ...],
    locale: str | None,
    freeze_at: str | None,
    check: bool,
    fail_on: str | None,
    out_format: str,
    github_annotations: bool,
    html: bool,
    no_fetch_dicts: bool,
    sarif_file: Path | None,
) -> None:
    """Run vocabulary audit and write reports (never modifies sources)."""
    from lexaudit.report.ci import parse_fail_on

    try:
        cfg = resolve_or_default_config(config_path)
    except Exception as exc:
        raise SystemExit(2) from exc
    if target_paths:
        cfg.sources = ["files"]
        cfg.files_paths = tuple(p.resolve() for p in target_paths)
    locales = [x.strip() for x in locale.split(",")] if locale else list(cfg.locales)
    fail_set = parse_fail_on("calque,invented" if check and fail_on is None else fail_on)
    if not no_fetch_dicts:
        _ensure_locale_dicts(locales, cfg)
    stamp = freeze_at or "1970-01-01T00:00:00Z"
    all_findings: list[dict[str, Any]] = []
    any_fail = False
    last_paths: dict[str, Path] = {}
    for loc in locales:
        findings, paths, failed = _audit_one_locale(
            cfg,
            loc,
            stamp=stamp,
            html=html,
            want_sarif=(out_format == "sarif" or sarif_file is not None),
            check=check,
            fail_set=fail_set,
            github_annotations=github_annotations,
            text_stdout=(out_format == "text"),
        )
        all_findings.extend(findings)
        last_paths = paths
        any_fail = any_fail or failed
    _emit_machine_output(out_format, all_findings, sarif_file, last_paths)
    if check and any_fail:
        raise SystemExit(1)


def _ensure_locale_dicts(locales: list[str], cfg: Any) -> None:
    from lexaudit.detectors.dictfetch import SOURCES as DICT_SOURCES
    from lexaudit.detectors.dictfetch import cache_dir, fetch_dictionary
    from lexaudit.detectors.hunspell import find_dict

    for loc in locales:
        if loc not in DICT_SOURCES or find_dict(loc, cfg.hunspell) is not None:
            continue
        click.echo(f"dictionary for {loc} missing; downloading to {cache_dir()} …", err=True)
        try:
            fetch_dictionary(loc, cache_dir())
        except OSError as exc:
            click.echo(f"warning: could not fetch dictionary for {loc}: {exc}", err=True)


def _audit_one_locale(
    cfg: Any,
    loc: str,
    *,
    stamp: str,
    html: bool,
    want_sarif: bool,
    check: bool,
    fail_set: frozenset[str],
    github_annotations: bool,
    text_stdout: bool,
) -> tuple[list[dict[str, Any]], dict[str, Path], bool]:
    from lexaudit.report.ci import (
        append_step_summary,
        build_findings,
        emit_github_annotations,
        failing_words,
    )

    stats: dict[str, int] = {}
    words, pages, _ = run_locale_audit(
        cfg, loc, post_detectors=None, freeze_generated_at=stamp, detector_stats=stats
    )
    for w in words:
        for d in w.detectors:
            stats[d] = stats.get(d, 0) + 1
    paths = write_reports(
        out_dir=cfg.output_dir / loc,
        locale=loc,
        words=words,
        pages=pages,
        config_hash=cfg.config_hash(),
        freeze_generated_at=stamp,
        detector_stats=stats,
        repo_root=cfg.repo_root,
        write_html=html,
        write_sarif_file=want_sarif,
    )
    findings = build_findings(words, locale=loc, repo_root=cfg.repo_root)
    bad = failing_words(words, fail_on=fail_set, needles=cfg.needles) if check else []
    if github_annotations:
        emit_github_annotations(
            [f for f in findings if f.get("status") in fail_set] if check else findings
        )
    append_step_summary(pages, loc)
    if text_stdout:
        click.echo(
            f"{loc}: words={len(words)} texts={len(pages)} "
            f"findings={len(findings)} -> {paths['report']}"
        )
        if check and bad:
            click.echo(f"{loc}: CHECK FAIL ({len(bad)} words)", err=True)
    return findings, paths, bool(bad)


def _emit_machine_output(
    out_format: str,
    all_findings: list[dict[str, Any]],
    sarif_file: Path | None,
    last_paths: dict[str, Path],
) -> None:
    from lexaudit.report.ci import build_sarif, write_sarif

    if out_format == "json":
        click.echo(json.dumps(all_findings, ensure_ascii=False, indent=2, sort_keys=True))
    elif out_format == "sarif":
        doc = build_sarif(all_findings)
        click.echo(json.dumps(doc, ensure_ascii=False, indent=2))
        if sarif_file is not None:
            write_sarif(sarif_file, doc)
        elif last_paths.get("sarif"):
            write_sarif(last_paths["sarif"], doc)



def _words_from_report_json(data: dict[str, object]) -> list[ClassifiedWord]:
    from lexaudit.core.types import Tier, VocabSample, VocabStatus

    words: list[ClassifiedWord] = []
    raw_words = data.get("words", [])
    if not isinstance(raw_words, list):
        return words
    for w in raw_words:
        if not isinstance(w, dict):
            continue
        words.append(
            ClassifiedWord(
                normalized=str(w["word"]),
                surface=str(w.get("surface") or w["word"]),
                count=int(w.get("count") or 0),
                status=cast(VocabStatus, str(w.get("status") or "suspect")),
                samples=[
                    VocabSample(
                        str(s["path"]),
                        str(s.get("field") or s.get("scope") or "body"),
                    )
                    for s in (w.get("samples") or [])
                    if isinstance(s, dict)
                ],
                tier=cast(Tier | None, w.get("tier")),
                reason=str(w.get("reason") or ""),
            )
        )
    return words


@main.command("rank")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to lexaudit.config.yaml (auto-discovered or zero-config if omitted)",
)
@click.option("--locale", required=True)
@click.option(
    "--mode",
    type=click.Choice(["raw", "weighted"], case_sensitive=False),
    default=None,
    help="Page ranking mode (default from config: weighted)",
)
@click.option(
    "--needles",
    default=None,
    help="Comma-separated needle lemmas (boost weight 6; merges with config needles)",
)
@click.option(
    "--require-needle",
    is_flag=True,
    help="Only include pages that hit at least one needle",
)
@click.option(
    "--curated",
    "curated_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Read/write curated queue (markdown table or .json)",
)
@click.option(
    "--sources",
    default=None,
    help="Comma-separated page buckets: academy, model_pack (alias: packs), docs (alias: files)",
)
def rank_cmd(
    config_path: Path | None,
    locale: str,
    mode: str | None,
    needles: str | None,
    require_needle: bool,
    curated_path: Path | None,
    sources: str | None,
) -> None:
    """Re-emit queue from an existing words.json report."""
    cfg = resolve_or_default_config(config_path)
    words_path = cfg.output_dir / locale / "words.json"
    data = json.loads(words_path.read_text(encoding="utf-8"))
    words = _words_from_report_json(data)
    rank_mode = (mode or cfg.rank_mode).casefold()
    needle_list = list(cfg.needles)
    if needles:
        needle_list.extend(x.strip() for x in needles.split(",") if x.strip())
    source_filter = [x.strip() for x in sources.split(",") if x.strip()] if sources else None
    pages = rank_pages(
        words,
        mode=rank_mode,  # type: ignore[arg-type]
        weights=cfg.rank_weights,
        needles=needle_list,
        locale=locale,
        require_needle=require_needle,
        source_filter=source_filter,
    )
    write_reports(
        out_dir=cfg.output_dir / locale,
        locale=locale,
        words=words,
        pages=pages,
        config_hash=cfg.config_hash(),
        freeze_generated_at="1970-01-01T00:00:00Z",
    )
    click.echo(f"queue -> {cfg.output_dir / locale / 'queue.md'} (mode={rank_mode})")
    if curated_path is not None:
        rows = load_curated(curated_path)
        rows = append_pending_from_rank(
            rows,
            pages,
            locale=locale,
            needles=needle_list or None,
        )
        save_curated(curated_path, rows)
        click.echo(f"curated -> {curated_path}")


@main.command("diff")
@click.option("--baseline", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--current", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), required=True)
def diff_cmd(baseline: Path, current: Path, out_path: Path) -> None:
    """Diff two report.json files: new / gone / tier-changed words."""
    from lexaudit.report.diff import diff_reports

    result = diff_reports(baseline, current)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    click.echo(f"wrote {out_path}")


def _resolve_locales(cfg_locales: list[str], locale_opt: str) -> list[str]:
    raw = locale_opt.strip().casefold()
    if raw in {"", "all"}:
        return list(cfg_locales)
    parts = [x.strip() for x in locale_opt.split(",") if x.strip()]
    unknown = [p for p in parts if p not in cfg_locales]
    if unknown:
        msg = f"unknown locale(s): {', '.join(unknown)}; config has {cfg_locales}"
        raise click.ClickException(msg)
    return parts


@main.command("expand-needle")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to lexaudit.config.yaml (auto-discovered or zero-config if omitted)",
)
@click.option(
    "--needle",
    required=True,
    help="Stem, exact token, or glob (e.g. orientir, *-orientir)",
)
@click.option(
    "--locale",
    default="all",
    show_default=True,
    help="all or comma-separated locales (en,de,es,pl,ru,sv,uk)",
)
@click.option("--json", "as_json", is_flag=True, help="Emit JSON array on stdout")
@click.option(
    "--write-queue",
    "write_queue",
    type=click.Path(path_type=Path),
    default=None,
    help="Append pending rows to curated markdown queue (no duplicate slugs)",
)
def expand_needle_cmd(
    config_path: Path | None,
    needle: str,
    locale: str,
    as_json: bool,
    write_queue: Path | None,
) -> None:
    """List pages/locales where a needle appears in existing words.json reports."""
    from lexaudit.curated.queue import (
        NeedleQueueHit,
        append_pending_from_needle_hits,
        load_curated,
        save_curated,
    )
    from lexaudit.report.expand_needle import scan_output_dir_for_needle, target_defects_label

    cfg = resolve_or_default_config(config_path)
    locales = _resolve_locales(list(cfg.locales), locale)
    hits = scan_output_dir_for_needle(cfg.output_dir, locales=locales, needle=needle)
    if as_json:
        click.echo(json.dumps([h.to_dict() for h in hits], ensure_ascii=False, indent=2))
    else:
        click.echo("locale\tpath\tcount\tstatus\tnorm\tsurface")
        for h in hits:
            click.echo(f"{h.locale}\t{h.path}\t{h.count}\t{h.status}\t{h.norm}\t{h.surface}")
    if write_queue is not None:
        defect = target_defects_label(needle)
        rows = load_curated(write_queue)
        needle_hits = [NeedleQueueHit(h.path, h.locale, defect) for h in hits]
        rows, added = append_pending_from_needle_hits(rows, needle_hits)
        save_curated(write_queue, rows)
        click.echo(f"queue +{added} pending -> {write_queue}", err=True)


@main.group("pack")
def pack_group() -> None:
    """List, install, and verify rule packs (MIT YAML bundles)."""


@pack_group.command("list")
def pack_list_cmd() -> None:
    from lexaudit.packs import list_packs

    rows = list_packs()
    if not rows:
        click.echo("No packs found.")
        return
    for row in rows:
        loc_raw = row.get("locales") or []
        loc_list = [str(x) for x in loc_raw] if isinstance(loc_raw, list) else []
        click.echo(f"{row['id']}  v{row.get('version')}  locales={','.join(loc_list)}")


@pack_group.command("install")
@click.argument("pack_id")
@click.option("--force", is_flag=True, help="Reinstall over existing cache copy")
@click.option(
    "--dest",
    type=click.Path(path_type=Path),
    default=None,
    help="Install directory (default: user pack cache)",
)
def pack_install_cmd(pack_id: str, force: bool, dest: Path | None) -> None:
    from lexaudit.packs import install_pack

    try:
        rules = install_pack(pack_id, dest=dest, force=force)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"installed {pack_id} -> rules at {rules}")
    click.echo(f"Set calque_rules_dir: {rules} in lexaudit.config.yaml")


@pack_group.command("verify")
@click.argument("pack_id")
def pack_verify_cmd(pack_id: str) -> None:
    from lexaudit.packs import verify_pack

    try:
        rules = verify_pack(pack_id)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"ok: {pack_id} rules at {rules}")


@main.group("eval")
def eval_group() -> None:
    """Product metrics and soft regression (I7)."""


@eval_group.command("product")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
)
@click.option("--k", default=10, show_default=True, help="Top-K for page@K vs rewrite-queue slugs")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON on stdout")
def eval_product_cmd(config_path: Path | None, k: int, as_json: bool) -> None:
    """Needle recall, page@K (weighted rank), and suspect counts from existing reports."""
    from lexaudit.eval.product import compute_product_metrics

    cfg = resolve_or_default_config(config_path)
    metrics = compute_product_metrics(cfg, k=k)
    if as_json:
        click.echo(json.dumps(metrics, ensure_ascii=False, indent=2))
        return
    click.echo(f"page@{k} gold: rewrite-queue #1-#11 slugs")
    for loc, block in metrics["locales"].items():
        nr = block["needle_recall"]
        p = block["page_at_k"]
        click.echo(
            f"{loc}: needle_recall={nr['recall']:.3f} "
            f"(hits {nr['hits']}/{nr['evaluated']}, skipped {nr['skipped_absent']}) "
            f"page@{k}={p['hits']}/{k} ({p['precision']:.2f}) suspect={block['suspect']}"
        )


@eval_group.command("regression")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
)
@click.option("--json", "as_json", is_flag=True, help="Emit JSON on stdout")
def eval_regression_cmd(config_path: Path | None, as_json: bool) -> None:
    """Soft CLEAR check for rewrite-queue #1-#11 (exit 0 always)."""
    from lexaudit.eval.product import run_regression_check

    cfg = resolve_or_default_config(config_path)
    report = run_regression_check(cfg)
    if as_json:
        click.echo(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for row in report["results"]:
            label = "CLEAR" if row["clear"] else "FAIL"
            click.echo(f"{row['slug']}: {label}")
    # Soft job: never fail the process on regression drift.


@main.command("label")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
)
@click.option("--locale", required=True)
@click.option("--top-pages", default=20, show_default=True, type=int)
@click.option("--top-words", default=50, show_default=True, type=int)
@click.option(
    "--tiers",
    default="likely,weak",
    show_default=True,
    help="Comma-separated suspect tiers to label",
)
@click.option(
    "--profile",
    default="gpu",
    show_default=True,
    help="llm_profiles key from config (e.g. gpu, cpu)",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=None,
    help="JSON output path (default: output_dir/<locale>/llm-labels.json)",
)
def label_cmd(
    config_path: Path | None,
    locale: str,
    top_pages: int,
    top_words: int,
    tiers: str,
    profile: str,
    out_path: Path | None,
) -> None:
    """LLM-label weak/likely words on top-ranked pages (cached, no source writes)."""
    from lexaudit.llm.emit import write_llm_labels
    from lexaudit.llm.run_top import run_top_labels

    if top_pages < 1 or top_words < 1:
        raise click.ClickException("--top-pages and --top-words must be >= 1")
    cfg = resolve_or_default_config(config_path)
    if locale not in cfg.locales:
        raise click.ClickException(f"unknown locale {locale!r}; config has {cfg.locales}")
    words_path = cfg.output_dir / locale / "words.json"
    if not words_path.is_file():
        msg = f"missing report {words_path}; run audit first"
        raise click.ClickException(msg)
    data = json.loads(words_path.read_text(encoding="utf-8"))
    words = _words_from_report_json(data)
    try:
        rows, page_paths, stats = run_top_labels(
            cfg,
            locale,
            words,
            top_pages=top_pages,
            top_words=top_words,
            tiers_raw=tiers,
            profile_name=profile,
        )
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    dest = out_path or (cfg.output_dir / locale / "llm-labels.json")
    write_llm_labels(
        dest,
        locale=locale,
        labels=rows,
        page_paths=page_paths,
        profile=profile,
        tiers=tiers,
        stats=stats,
    )
    click.echo(
        f"{locale}: labeled={len(rows)} pages={len(page_paths)} "
        f"calls={stats.get('llm_calls', 0)} cache_hits={stats.get('cache_hits', 0)} -> {dest}"
    )


_STARTER_CONFIG_YAML = """\
# lexaudit configuration (CPU-only by default, no GPU required).
# Run:
#   lexaudit doctor
#   lexaudit audit --locale en

repo_root: .
output_dir: ./tmp/lexaudit
locales: [en]
sources: [files]
files_paths:
  - ./README.md
  - ./docs
min_length: 2

proper_names_path: ./dicts/proper-names.yaml
acronyms_path: ./dicts/acronyms.yaml
allowlist_path: ./dicts/allowlist.yaml

enable_morph: true
enable_compound: true
enable_foreign: true
enable_calque: true
enable_crosslocale: false
enable_llm: false
rank_mode: weighted
needles:
  - orientir
  - denseness
"""

_STARTER_PROPER_YAML = """\
version: 1
brands_and_authors:
  - lexaudit
  - Vadim Nareyko
  - GitHub
  - Python
  - Hunspell
"""

_STARTER_ACRONYMS_YAML = """\
version: 1
items:
  - API
  - CLI
  - CPU
  - CSV
  - GPU
  - HTML
  - JSON
  - JSONL
  - LLM
  - MD
  - SVG
  - TSV
  - URL
  - UTF
  - YAML
"""

_STARTER_ALLOWLIST_YAML = """\
version: 2
section_markers:
  - Overview
  - Contents
  - Install
locale_loans:
  - allowlist
  - monorepo
  - submodule
  - workflow
"""


@main.command("init")
@click.option(
    "--dir",
    "target_dir",
    type=click.Path(path_type=Path),
    default=Path("."),
    show_default=True,
    help="Target directory for lexaudit.config.yaml and dicts/",
)
@click.option("--force", is_flag=True, help="Overwrite existing config and dict files")
def init_cmd(target_dir: Path, force: bool) -> None:
    """Create starter lexaudit.config.yaml and dicts/ for a project (no GPU needed)."""
    root = target_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    dicts_dir = root / "dicts"
    dicts_dir.mkdir(parents=True, exist_ok=True)
    files = [
        (root / "lexaudit.config.yaml", _STARTER_CONFIG_YAML),
        (dicts_dir / "proper-names.yaml", _STARTER_PROPER_YAML),
        (dicts_dir / "acronyms.yaml", _STARTER_ACRONYMS_YAML),
        (dicts_dir / "allowlist.yaml", _STARTER_ALLOWLIST_YAML),
    ]
    created: list[str] = []
    skipped: list[str] = []
    for path, content in files:
        if path.exists() and not force:
            skipped.append(str(path.relative_to(root)))
            continue
        path.write_text(content, encoding="utf-8")
        created.append(str(path.relative_to(root)))
    if created:
        click.echo(f"created: {', '.join(created)}")
    if skipped:
        click.echo(f"skipped existing (use --force to overwrite): {', '.join(skipped)}")
    click.echo("next: run `lexaudit doctor` or `lexaudit audit`")


@main.command("doctor")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Optional lexaudit.config.yaml to inspect",
)
def doctor_cmd(config_path: Path | None) -> None:
    """Check environment readiness (Hunspell dicts, morphology, calque rules; no GPU needed)."""
    from lexaudit.detectors.calque import default_calque_rules_dir, load_calque_rules
    from lexaudit.detectors.hunspell import LOCALE_DICTS, find_dict, resolve_binary

    cfg = resolve_or_default_config(config_path)
    click.echo(f"lexaudit {__version__} environment check")
    click.echo("- Execution mode: CPU-first (GPU required: NO)")
    click.echo(f"- Repo root: {cfg.repo_root}")
    click.echo(f"- Sources: {', '.join(cfg.sources)} | Locales: {', '.join(cfg.locales)}")

    try:
        binary, _ = resolve_binary(cfg.hunspell)
        click.echo(f"- Hunspell binary: OK ({binary})")
    except RuntimeError as exc:
        click.echo(f"- Hunspell binary: not found ({exc}); using the built-in Python checker")
        click.echo(
            "  Optional, faster: sudo apt-get install hunspell (Linux) or brew install hunspell"
        )

    missing_locs: list[str] = []
    for loc in ("en", "de", "ru", "es", "pl", "sv", "uk"):
        found = find_dict(loc, cfg.hunspell)
        if found is not None:
            click.echo(f"  - dict [{loc}]: OK ({found[0]} -> {found[1]})")
        elif loc in cfg.locales:
            missing_locs.append(loc)
            want = "/".join(LOCALE_DICTS.get(loc, []))
            click.echo(f"  - dict [{loc}]: MISSING (expected {want}); run: lexaudit fetch-dicts")

    try:
        import pymorphy3  # type: ignore[import-untyped]

        _ = pymorphy3
        click.echo("- Morphology (pymorphy3 ru/uk): OK")
    except Exception:
        click.echo("- Morphology (pymorphy3 ru/uk): MISSING")

    rules_dir = cfg.calque_rules_dir or default_calque_rules_dir()
    if rules_dir and rules_dir.exists():
        rules = load_calque_rules(rules_dir)
        click.echo(f"- Calque rules: OK ({len(rules)} rules from {rules_dir})")
    else:
        click.echo("- Calque rules: none configured")

    if missing_locs:
        click.echo(
            f"Note: missing Hunspell dictionaries for configured locales {missing_locs}. "
            "Run `lexaudit fetch-dicts` (no admin rights needed) for full accuracy."
        )


@main.command("fetch-dicts")
@click.option(
    "--locale",
    "locales",
    multiple=True,
    help="Locale to download (repeatable). Default: all of en, de, es, pl, ru, sv, uk",
)
@click.option("--force", is_flag=True, help="Download again even if already present")
def fetch_dicts_cmd(locales: tuple[str, ...], force: bool) -> None:
    """Download spelling dictionaries into your user cache (no admin rights, no apt)."""
    from lexaudit.detectors.dictfetch import SOURCES, cache_dir, fetch_dictionary

    dest = cache_dir()
    wanted = list(locales) or sorted(SOURCES)
    for loc in wanted:
        if loc not in SOURCES:
            raise click.ClickException(f"unknown locale {loc!r}; choose from {sorted(SOURCES)}")
        dict_id = SOURCES[loc][1]
        if not force and (dest / f"{dict_id}.dic").is_file():
            click.echo(f"{loc}: already installed ({dest / dict_id})")
            continue
        try:
            stem = fetch_dictionary(loc, dest)
        except OSError as exc:
            raise click.ClickException(f"{loc}: download failed ({exc})") from exc
        click.echo(f"{loc}: downloaded to {stem}")
    click.echo("Dictionaries keep their upstream licenses: see *.license.txt next to each file.")


@main.command("explain")
@click.argument("word")
@click.option(
    "--locale",
    default="en",
    show_default=True,
    help="Locale code (en, de, es, pl, ru, sv, uk)",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Optional lexaudit.config.yaml",
)
@click.option("--json", "as_json", is_flag=True, help="Emit explanation as JSON")
def explain_cmd(word: str, locale: str, config_path: Path | None, as_json: bool) -> None:
    """Explain how a single word is classified and show any editorial hint."""
    from lexaudit.core.classify import classify_occurrences
    from lexaudit.core.tokenize import casefold
    from lexaudit.core.types import VocabOccurrence, VocabSample
    from lexaudit.detectors.calque import (
        default_calque_rules_dir,
        find_matching_rule,
        load_calque_rules,
    )
    from lexaudit.detectors.factory import build_post_detectors
    from lexaudit.detectors.hunspell import resolve_checker
    from lexaudit.dictpacks.loader import build_allowlist, build_compound_known_lemmas

    cfg = resolve_or_default_config(config_path)
    norm = casefold(word, locale)
    occ = {
        norm: VocabOccurrence(
            normalized=norm,
            surface=word,
            count=1,
            samples=[VocabSample(path="<cli>", scope="body")],
        )
    }
    proper, acronyms, templates = build_allowlist(
        locale=locale,
        proper_names_path=cfg.proper_names_path,
        acronyms_path=cfg.acronyms_path,
        allowlist_path=cfg.allowlist_path,
        packs_root=cfg.packs_root,
    )
    seed = build_compound_known_lemmas(proper, acronyms)
    post_dets, _ = build_post_detectors(cfg, locale, seed)
    checker = resolve_checker(locale, cfg.hunspell)
    classified = classify_occurrences(
        occurrences=occ,
        proper=proper,
        acronyms=acronyms,
        templates=templates,
        checker=checker,
        post_detectors=post_dets,
    )[0]

    hint = ""
    rules_dir = cfg.calque_rules_dir or default_calque_rules_dir()
    if rules_dir and rules_dir.exists():
        locale_rules = [r for r in load_calque_rules(rules_dir) if r.locale == locale]
        matched = find_matching_rule(classified, locale_rules, locale)
        if matched is not None:
            hint = matched.hint

    payload = {
        "word": word,
        "normalized": classified.normalized,
        "locale": locale,
        "status": classified.status,
        "tier": classified.tier,
        "reason": classified.reason,
        "detectors": classified.detectors,
        "hint": hint,
    }
    if as_json:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    click.echo(f"word: {word} (normalized: {classified.normalized}, locale: {locale})")
    click.echo(f"status: {classified.status} (tier: {classified.tier or 'none'})")
    click.echo(f"reason: {classified.reason} | detectors: {', '.join(classified.detectors)}")
    if hint:
        click.echo(f"editorial hint: {hint}")


if __name__ == "__main__":
    main()
