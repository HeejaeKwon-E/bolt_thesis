from __future__ import annotations

import json
from typing import Any

from bolt_thesis.paths import ATTRIBUTES_PATH


class SystemBValidationError(ValueError):
    pass


def _load_domains() -> tuple[set[str], set[str], set[str]]:
    with ATTRIBUTES_PATH.open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    return (
        set(cfg["output_domains"]["materials"]),
        set(cfg["output_domains"]["operations"]),
        set(cfg["attributes"].keys()),
    )


def validate_system_b_output(raw: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, str):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SystemBValidationError(f"INVALID_JSON: {exc}") from exc
    else:
        value = raw

    if not isinstance(value, dict):
        raise SystemBValidationError("OUTPUT_MUST_BE_OBJECT")

    expected = {"status", "material", "routing", "required_fields"}
    if set(value) != expected:
        raise SystemBValidationError(
            f"INVALID_KEYS: expected={sorted(expected)}, actual={sorted(value)}"
        )

    materials, operations, fields = _load_domains()

    status = value["status"]
    material = value["material"]
    routing = value["routing"]
    required_fields = value["required_fields"]

    if status not in {"OK", "CLARIFICATION_REQUIRED"}:
        raise SystemBValidationError(f"INVALID_STATUS: {status!r}")

    if material is not None and material not in materials:
        raise SystemBValidationError(f"INVALID_MATERIAL: {material!r}")

    if not isinstance(routing, list) or any(op not in operations for op in routing):
        raise SystemBValidationError("INVALID_ROUTING")

    if len(routing) != len(set(routing)):
        raise SystemBValidationError("DUPLICATE_ROUTING_OPERATION")

    if not isinstance(required_fields, list) or any(
        field not in fields for field in required_fields
    ):
        raise SystemBValidationError("INVALID_REQUIRED_FIELDS")

    if len(required_fields) != len(set(required_fields)):
        raise SystemBValidationError("DUPLICATE_REQUIRED_FIELD")

    # 상태별 의미 제약도 검사한다.
    if status == "OK":
        if material is None:
            raise SystemBValidationError("OK_REQUIRES_MATERIAL")
        if not routing:
            raise SystemBValidationError("OK_REQUIRES_ROUTING")
        if required_fields:
            raise SystemBValidationError("OK_REQUIRES_EMPTY_REQUIRED_FIELDS")
    else:
        if material is not None:
            raise SystemBValidationError("CLARIFICATION_REQUIRES_NULL_MATERIAL")
        if routing:
            raise SystemBValidationError("CLARIFICATION_REQUIRES_EMPTY_ROUTING")
        if not required_fields:
            raise SystemBValidationError("CLARIFICATION_REQUIRES_REQUIRED_FIELDS")

    return {
        "status": status,
        "material": material,
        "routing": routing,
        "required_fields": required_fields,
    }
