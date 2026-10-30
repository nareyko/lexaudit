"""Schema fixture validation."""

from __future__ import annotations

import json
from pathlib import Path

from lexaudit.schema_validate import validate_gold_record, validate_report

FIXTURES = Path(__file__).parent / "fixtures"


def test_report_minimal_validates() -> None:
    doc = json.loads((FIXTURES / "report-minimal.json").read_text(encoding="utf-8"))
    validate_report(doc)


def test_gold_minimal_validates() -> None:
    doc = json.loads((FIXTURES / "gold-minimal.json").read_text(encoding="utf-8"))
    validate_gold_record(doc)
