from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "packs" / "_lab"


def test_lab_packs_have_pack_yaml_and_calques() -> None:
    ids = ["saas-ui-v0", "fintech-v0", "developer-docs-v0"]
    for pack_id in ids:
        pack = LAB / pack_id
        meta = yaml.safe_load((pack / "pack.yaml").read_text(encoding="utf-8"))
        assert meta["status"] == "lab"
        assert meta["license"] == "MIT"
        assert (pack / "calques" / "en.yaml").is_file()
        rules = yaml.safe_load((pack / "calques" / "en.yaml").read_text(encoding="utf-8"))
        assert len(rules.get("rules") or []) >= 15
        fixtures = pack / "fixtures" / "en"
        assert (fixtures / "01-clean-settings.md").is_file() or list(fixtures.glob("01-clean*.md"))
        assert list(fixtures.glob("04-defect-known.md"))


def test_lab_fixtures_stratified() -> None:
    for pack_id in ("saas-ui-v0", "fintech-v0", "developer-docs-v0"):
        fx = LAB / pack_id / "fixtures" / "en"
        names = {p.name for p in fx.glob("*.md")}
        assert any(n.startswith("01-clean") for n in names)
        assert "04-defect-known.md" in names
        assert "06-defect-open.md" in names
