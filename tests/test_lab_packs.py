from __future__ import annotations

from pathlib import Path

import yaml

from lexaudit.packs import pack_content_dir

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "packs" / "_lab"

CORE = ("saas-ui-v0", "fintech-v0", "developer-docs-v0")
THIN = ("ecommerce-ui-v0", "healthcare-ui-v0", "legal-docs-v0")


def test_lab_registry_stubs_and_promoted_content() -> None:
    for pack_id in CORE + THIN:
        stub = LAB / pack_id
        meta = yaml.safe_load((stub / "pack.yaml").read_text(encoding="utf-8"))
        assert meta["status"] == "lab"
        assert meta["license"] == "MIT"
        # No twin calques/fixtures under _lab after dedupe.
        assert not (stub / "calques").is_dir()
        assert not (stub / "fixtures").is_dir()
        content = pack_content_dir(pack_id, prefer_lab=True)
        assert content == ROOT / "packs" / pack_id
        assert (content / "calques" / "en.yaml").is_file()
        rules = yaml.safe_load((content / "calques" / "en.yaml").read_text(encoding="utf-8"))
        min_rules = 15 if pack_id in CORE else 6
        assert len(rules.get("rules") or []) >= min_rules
        fixtures = content / "fixtures" / "en"
        assert list(fixtures.glob("01-clean*.md"))
        assert list(fixtures.glob("04-defect-known.md"))


def test_lab_fixtures_stratified() -> None:
    for pack_id in CORE:
        fx = pack_content_dir(pack_id) / "fixtures" / "en"
        names = {p.name for p in fx.glob("*.md")}
        assert any(n.startswith("01-clean") for n in names)
        assert "04-defect-known.md" in names
        assert "06-defect-open.md" in names


def test_lab_pack_metrics_recall_bar() -> None:
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from lab_pack_metrics import measure

    for pack_id in CORE + THIN:
        report = measure(pack_id, "en")
        assert report["lab_rank_ok"] is True
        assert float(report["known_rule_recall"]) >= 0.85
