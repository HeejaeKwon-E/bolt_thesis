from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bolt_thesis.paths import ATTRIBUTES_PATH, RULES_PATH


@dataclass(frozen=True)
class RuleEngineConfig:
    attributes: dict[str, Any]
    rules: dict[str, Any]


class RuleEngine:
    def __init__(
        self,
        attributes_path: str | Path = ATTRIBUTES_PATH,
        rules_path: str | Path = RULES_PATH,
    ) -> None:
        self.config = RuleEngineConfig(
            attributes=self._load_json(attributes_path),
            rules=self._load_json(rules_path),
        )

        self.attribute_defs: dict[str, dict[str, Any]] = self.config.attributes["attributes"]
        self.material_domain = set(self.config.attributes["output_domains"]["materials"])
        self.operation_domain = set(self.config.attributes["output_domains"]["operations"])
        self.routing_order: list[str] = self.config.rules["routing_order"]
        self.routing_rank = {
            operation: index for index, operation in enumerate(self.routing_order)
        }

    @staticmethod
    def _load_json(path: str | Path) -> dict[str, Any]:
        with Path(path).open("r", encoding="utf-8") as f:
            return json.load(f)

    def run(self, attrs: dict[str, Any]) -> dict[str, Any]:
        missing_fields = self._find_missing_required_fields(attrs)
        if missing_fields:
            return {
                "status": "CLARIFICATION_REQUIRED",
                "material": None,
                "routing": None,
                "required_fields": missing_fields,
                "applied_rules": [],
            }

        validation_errors = self._validate_attribute_values(attrs)
        if validation_errors:
            return {
                "status": "INVALID_INPUT",
                "material": None,
                "routing": None,
                "required_fields": [],
                "errors": validation_errors,
                "applied_rules": [],
            }

        material: str | None = None
        operations: set[str] = set()
        applied_rules: list[str] = []

        for rule in self.config.rules["rules"]:
            if not self._matches(rule["condition"], attrs):
                continue

            applied_rules.append(rule["id"])

            for action in rule["actions"]:
                action_type = action["type"]
                value = action["value"]

                if action_type == "SET_MATERIAL":
                    if material is not None and material != value:
                        raise ValueError(
                            f"Material conflict: {material!r} vs {value!r} "
                            f"(rule={rule['id']})"
                        )
                    if value not in self.material_domain:
                        raise ValueError(
                            f"Unknown material {value!r} in rule {rule['id']}"
                        )
                    material = value

                elif action_type == "ADD_OPERATION":
                    if value not in self.operation_domain:
                        raise ValueError(
                            f"Unknown operation {value!r} in rule {rule['id']}"
                        )
                    operations.add(value)

                else:
                    raise ValueError(
                        f"Unsupported action type {action_type!r} in rule {rule['id']}"
                    )

        if material is None:
            raise ValueError(f"No material selected for input: {attrs}")

        forming = {"COLD_FORMING", "HOT_FORMING"} & operations
        if len(forming) != 1:
            raise ValueError(
                "Exactly one forming process must be selected, "
                f"but got {sorted(forming)} for input {attrs}"
            )

        routing = sorted(operations, key=lambda op: self.routing_rank[op])

        return {
            "status": "OK",
            "material": material,
            "routing": routing,
            "required_fields": [],
            "applied_rules": applied_rules,
        }

    def _find_missing_required_fields(self, attrs: dict[str, Any]) -> list[str]:
        return [
            name
            for name, definition in self.attribute_defs.items()
            if definition.get("required", False)
            and (name not in attrs or attrs[name] is None)
        ]

    def _validate_attribute_values(self, attrs: dict[str, Any]) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []

        for name, definition in self.attribute_defs.items():
            if name not in attrs or attrs[name] is None:
                continue

            value = attrs[name]
            allowed_values = definition.get("values")

            if allowed_values is not None and value not in allowed_values:
                errors.append(
                    {
                        "field": name,
                        "value": value,
                        "reason": "VALUE_NOT_ALLOWED",
                        "allowed_values": allowed_values,
                    }
                )

        return errors

    def _matches(self, condition: dict[str, Any], attrs: dict[str, Any]) -> bool:
        if condition.get("always") is True:
            return True

        if "all" in condition:
            return all(self._matches(item, attrs) for item in condition["all"])

        if "any" in condition:
            return any(self._matches(item, attrs) for item in condition["any"])

        actual = attrs[condition["field"]]
        operator = condition["op"]
        expected = condition["value"]

        operators = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "in": lambda a, b: a in b,
        }

        try:
            return operators[operator](actual, expected)
        except KeyError as exc:
            raise ValueError(f"Unsupported operator: {operator!r}") from exc
