"""Stage V2: real-bench fixtures exist and IAA κ script runs."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("en", "de", "es", "pl", "ru", "sv", "uk")
GEC_MIN = ("uk", "en", "ru")


def test_clean_fixtures_exist_per_locale() -> None:
    root = ROOT / "tests" / "fixtures" / "real_bench" / "clean"
    for locale in LOCALES:
        pages = sorted((root / locale).glob("*.md"))
        assert len(pages) >= 8, f"{locale}: expected ≥8 clean pages, got {len(pages)}"


def test_gec_fixtures_cover_required_locales() -> None:
    root = ROOT / "tests" / "fixtures" / "real_bench" / "gec"
    for locale in GEC_MIN:
        path = root / f"{locale}.jsonl"
        assert path.is_file(), f"missing gec fixture {path}"
        lines = path.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(line) for line in lines if line.strip()]
        assert len(rows) >= 3, f"{locale}: expected ≥3 gec pairs"
        for row in rows:
            assert "source" in row and "target" in row and "provenance" in row


def test_mt_fixtures_total_pages() -> None:
    root = ROOT / "tests" / "fixtures" / "real_bench" / "mt"
    total = 0
    for locale in LOCALES:
        loc = root / locale
        if loc.is_dir():
            total += len(list(loc.glob("*.md")))
    assert total >= 15, f"expected ≥15 mt pages across locales, got {total}"


def test_manifest_and_third_party_license() -> None:
    manifest = ROOT / "eval" / "corpora" / "manifest.json"
    assert manifest.is_file()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data.get("entries"), "manifest entries empty"
    allowed = set(data.get("allowed_licenses", []))
    assert "CC0-1.0" in allowed
    assert "CC-BY-4.0" in allowed
    third = ROOT / "LICENSE-THIRD-PARTY.md"
    assert third.is_file()
    text = third.read_text(encoding="utf-8")
    assert "ua-gec" in text
    assert "github-typo-corpus" in text


def test_gold_real_bench_schema_and_dual_annotators() -> None:
    gold_dir = ROOT / "gold" / "real_bench"
    required = {"path", "line", "span", "label", "source_lang", "suggestion", "annotator"}
    found = 0
    for locale in LOCALES:
        path = gold_dir / f"{locale}.jsonl"
        if not path.is_file():
            continue
        found += 1
        lines = path.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(line) for line in lines if line.strip()]
        anns = {r["annotator"] for r in rows}
        assert "A1" in anns and "A2" in anns, f"{locale}: need A1 and A2"
        for row in rows:
            assert required <= set(row.keys())
    assert found >= 3, "need gold for ≥3 locales"


def test_compute_iaa_kappa_script_runs() -> None:
    script = ROOT / "scripts" / "compute_iaa_kappa.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--write-docs", "--min-kappa", "0.70"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "OVERALL:" in proc.stdout
    assert (ROOT / "docs" / "real-benchmark.md").is_file()
    assert "κ" in (ROOT / "docs" / "real-benchmark.md").read_text(encoding="utf-8")
