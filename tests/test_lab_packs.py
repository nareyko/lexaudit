from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "packs" / "_lab"

CORE = ("saas-ui-v0", "fintech-v0", "developer-docs-v0")
THIN = ("ecommerce-ui-v0", "healthcare-ui-v0", "legal-docs-v0")


def test_lab_packs_have_pack_yaml_and_calques() -> None:
    for pack_id in CORE + THIN:
        pack = LAB / pack_id
        meta = yaml.safe_load((pack / "pack.yaml").read_text(encoding="utf-8"))
        assert meta["status"] == "lab"
        assert meta["license"] == "MIT"
        assert (pack / "calques" / "en.yaml").is_file()
        rules = yaml.safe_load((pack / "calques" / "en.yaml").read_text(encoding="utf-8"))
        min_rules = 15 if pack_id in CORE else 6
        assert len(rules.get("rules") or []) >= min_rules
        fixtures = pack / "fixtures" / "en"
        assert list(fixtures.glob("01-clean*.md"))
        assert list(fixtures.glob("04-defect-known.md"))


def test_lab_fixtures_stratified() -> None:
    for pack_id in CORE:
        fx = LAB / pack_id / "fixtures" / "en"
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
