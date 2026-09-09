from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bolt_thesis.paths import ATTRIBUTES_PATH


FIELDS = (
    "diameter_mm",
    "length_mm",
    "strength_grade",
    "surface_treatment",
)


class ExtractionValidationError(ValueError):
    pass


def validate_extraction(
    raw: str | dict[str, Any],
    attributes_path: str | Path = ATTRIBUTES_PATH,
) -> dict[str, Any]:
    value = _parse_json_object(raw)

    with Path(attributes_path).open("r", encoding="utf-8") as f:
        definitions = json.load(f)["attributes"]

    expected_fields = set(FIELDS)
    actual_fields = set(value)

    missing_keys = expected_fields - actual_fields
    extra_keys = actual_fields - expected_fields

    if missing_keys:
        raise ExtractionValidationError(f"MISSING_KEYS: {sorted(missing_keys)}")
    if extra_keys:
        raise ExtractionValidationError(f"EXTRA_KEYS: {sorted(extra_keys)}")

    normalized: dict[str, Any] = {}

    for field in FIELDS:
        field_value = value[field]

        if field_value is None:
            normalized[field] = None
            continue

        allowed_values = definitions[field]["values"]
        if field_value not in allowed_values:
            raise ExtractionValidationError(
                f"VALUE_NOT_ALLOWED: field={field}, value={field_value!r}, "
                f"allowed={allowed_values!r}"
            )

        normalized[field] = field_value

    return normalized


def _parse_json_object(raw: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw

    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ExtractionValidationError(f"INVALID_JSON: {exc}") from exc

    if not isinstance(value, dict):
        raise ExtractionValidationError("OUTPUT_MUST_BE_JSON_OBJECT")

    return value
