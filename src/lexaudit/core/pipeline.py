"""End-to-end audit pipeline for one locale."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from lexaudit.config import LexauditConfig
from lexaudit.core.aggregate import add_tokens
from lexaudit.core.classify import DetectorFn, classify_occurrences
from lexaudit.core.rank import rank_pages
from lexaudit.core.tokenize import tokenize_with_surface
from lexaudit.core.types import ClassifiedWord, PageSuspectRank, VocabOccurrence
from lexaudit.detectors.compound import SUPPORTED as COMPOUND_LOCALES
from lexaudit.detectors.compound import make_compound_detector
from lexaudit.detectors.factory import build_post_detectors
from lexaudit.detectors.hunspell import resolve_checker
from lexaudit.dictpacks.loader import build_allowlist, build_compound_known_lemmas
from lexaudit.report.write import write_reports
from lexaudit.sources.collect import collect_all


def apply_crosslocale_pass(
    words: list[ClassifiedWord],
    cfg: LexauditConfig,
    locale: str,
    *,
    academy_root: Path,
    packs_root: Path,
    stats: dict[str, int],
) -> list[ClassifiedWord]:
    """Boost suspect tiers when a token has no counterpart in the reference locale."""
    ref = (cfg.crosslocale_reference_locale or "en").casefold()
    if locale.casefold() == ref:
        stats.setdefault("crosslocale", 0)
        return words
    from lexaudit.detectors.crosslocale import (
        aggregate_norms_from_chunks,
        make_crosslocale_detector,
    )

    ref_chunks = collect_all(
        cfg.repo_root,
        ref,
        set(cfg.sources),
        academy_root=academy_root,
        packs_root=packs_root,
        files_paths=cfg.files_paths,
    )
    norms = aggregate_norms_from_chunks(ref_chunks, ref)
    detect = make_crosslocale_detector(norms)
    hits = 0
    for w in words:
        updated = detect(w)  # type: ignore[operator]
        if updated is not None:
            hits += 1
    stats["crosslocale"] = hits
    return words


def apply_compound_second_pass(
    words: list[ClassifiedWord],
    locale: str,
    compound_seed: set[str],
) -> None:
    """Re-run compound split on suspects using seed lemmas plus hunspell-ok parts."""
    known = compound_seed | {w.normalized for w in words if w.status == "ok"}
    compound = make_compound_detector(locale, known)
    for w in words:
        if w.status != "suspect":
            continue
        updated = compound(w)
        if updated is None:
            continue
        w.status = updated.status
        w.reason = updated.reason
        w.detectors = updated.detectors
        w.tier = updated.tier
    words.sort(key=lambda x: (-x.count, x.normalized))


def run_locale_audit(
    cfg: LexauditConfig,
    locale: str,
    *,
    post_detectors: list[DetectorFn] | None = None,
    freeze_generated_at: str | None = None,
    detector_stats: dict[str, int] | None = None,
) -> tuple[list[ClassifiedWord], list[PageSuspectRank], dict[str, Path]]:
    """Collect → tokenize → classify → rank → write reports."""
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
    occ_map: dict[str, VocabOccurrence] = {}
    for chunk in chunks:
        tokens = tokenize_with_surface(chunk.text, locale=locale, min_length=cfg.min_length)
        add_tokens(occ_map, tokens, path=chunk.path, scope=chunk.scope)

    proper, acronyms, templates = build_allowlist(
        locale=locale,
        proper_names_path=cfg.proper_names_path,
        acronyms_path=cfg.acronyms_path,
        allowlist_path=cfg.allowlist_path,
        packs_root=cfg.packs_root or (cfg.repo_root / "infra/corpus-ci/pending-model-packs"),
    )
    compound_seed = build_compound_known_lemmas(proper, acronyms)
    checker = resolve_checker(locale, cfg.hunspell)

    stats = detector_stats if detector_stats is not None else {}
    if post_detectors is None:
        post_detectors, built_stats = build_post_detectors(cfg, locale, compound_seed)
        for key, val in built_stats.items():
            stats.setdefault(key, val)

    words = classify_occurrences(
        occurrences=occ_map,
        proper=proper,
        acronyms=acronyms,
        templates=templates,
        checker=checker,
        post_detectors=post_detectors,
    )
    if cfg.enable_calque:
        from lexaudit.detectors.calque import (
            apply_phrase_calque_pass,
            default_calque_rules_dir,
            load_calque_rules,
        )

        rules_dir = cfg.calque_rules_dir or default_calque_rules_dir()
        if rules_dir is not None:
            words = apply_phrase_calque_pass(
                words, chunks, load_calque_rules(rules_dir), locale=locale
            )
    if cfg.enable_compound and locale in COMPOUND_LOCALES:
        apply_compound_second_pass(words, locale, compound_seed)
    if cfg.enable_crosslocale:
        words = apply_crosslocale_pass(
            words,
            cfg,
            locale,
            academy_root=academy_root,
            packs_root=packs_root,
            stats=stats,
        )
    if cfg.enable_bilingual:
        from lexaudit.detectors.bilingual import (
            apply_bilingual_pass,
            load_extra_loans,
            pairs_from_config,
        )

        pairs = [
            p
            for p in pairs_from_config(list(cfg.bilingual_pairs), cfg.repo_root)
            if p.target_locale.casefold() == locale.casefold()
        ]
        words = apply_bilingual_pass(
            words,
            pairs,
            enabled=True,
            extra_loans=load_extra_loans(cfg.bilingual_extra_loans_path),
            extra_loans_locales=frozenset(cfg.bilingual_extra_loans_locales),
        )
    pages = rank_pages(
        words,
        mode=cfg.rank_mode,  # type: ignore[arg-type]
        weights=cfg.rank_weights,
        needles=cfg.needles,
        locale=locale,
    )
    out_dir = cfg.output_dir / locale
    paths = write_reports(
        out_dir=out_dir,
        locale=locale,
        words=words,
        pages=pages,
        config_hash=cfg.config_hash(),
        freeze_generated_at=freeze_generated_at,
        detector_stats=stats,
    )
    return words, pages, paths


DetectorBuilder = Callable[[LexauditConfig, str], list[DetectorFn]]
