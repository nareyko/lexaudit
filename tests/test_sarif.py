"""V5-2: SARIF 2.1.0 hierarchical ruleId, hint message, region columns."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from lexaudit.report.ci import build_sarif, sarif_message, sarif_rule_id

SCHEMA = Path(__file__).parent / "fixtures" / "sarif-2.1.0-minimal.schema.json"


def test_sarif_rule_id_hierarchical() -> None:
    assert (
        sarif_rule_id(
            {"status": "calque", "locale": "uk", "source_id": "ru-origin", "word": "x"}
        )
        == "calque.uk.ru-origin"
    )


def test_sarif_message_span_to_hint() -> None:
    msg = sarif_message({"word": "orientir", "hint": "ballpark figure", "status": "calque"})
    assert msg == "«orientir» → «ballpark figure»"


def test_build_sarif_validates_against_minimal_schema() -> None:
    findings = [
        {
            "path": "docs/a.md",
            "line": 3,
            "start_col": 5,
            "end_col": 13,
            "word": "orientir",
            "normalized": "orientir",
            "status": "calque",
            "reason": "loan-calque-orientir",
            "hint": "working rule",
            "source_id": "ru-origin",
            "excerpt": "…orientir…",
            "locale": "uk",
            "suppressed": False,
        },
        {
            "path": "docs/b.md",
            "line": 1,
            "start_col": 1,
            "end_col": 8,
            "word": "denseness",
            "normalized": "denseness",
            "status": "calque",
            "hint": "",
            "source_id": "editorial-calque-bank",
            "locale": "en",
            "suppressed": False,
        },
    ]
    doc = build_sarif(findings)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(doc)

    result = doc["runs"][0]["results"][0]
    assert result["ruleId"] == "calque.uk.ru-origin"
    assert result["message"]["text"] == "«orientir» → «working rule»"
    region = result["locations"][0]["physicalLocation"]["region"]
    assert region == {"startLine": 3, "startColumn": 5, "endColumn": 13}

    # Suppressed findings are omitted from SARIF results
    findings[0]["suppressed"] = True
    doc2 = build_sarif(findings)
    assert len(doc2["runs"][0]["results"]) == 1
