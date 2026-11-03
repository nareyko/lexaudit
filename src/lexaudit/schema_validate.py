"""JSON Schema validators for report and gold records."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def _schema_dir() -> Path:
    """Resolve schema dir for editable checkout and installed wheel."""
    module_file = Path(__file__).resolve()
    here = module_file.parent
    candidates = (
        here / "schema",  # packaged beside this module (wheel)
        module_file.parents[2] / "schema",  # repo root: src/lexaudit/*.py → ../..
    )
    for candidate in candidates:
        if (candidate / "report-v1.schema.json").is_file():
            return candidate
    msg = "lexaudit schema files not found (report-v1.schema.json)"
    raise FileNotFoundError(msg)


@lru_cache(maxsize=4)
def _load_validator(name: str) -> Draft202012Validator:
    path = _schema_dir() / name
    schema = json.loads(path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def validate_report(doc: dict[str, Any]) -> None:
    """Raise jsonschema.ValidationError if report does not match v1 schema."""
    _load_validator("report-v1.schema.json").validate(doc)


def validate_gold_record(doc: dict[str, Any]) -> None:
    """Raise jsonschema.ValidationError if gold record does not match v1 schema."""
    _load_validator("gold-v1.schema.json").validate(doc)
