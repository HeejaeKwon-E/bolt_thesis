from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any, Literal

from bolt_thesis.extractor.validator import (
    FIELDS,
    ExtractionValidationError,
    validate_extraction,
)
from bolt_thesis.rule_engine import RuleEngine

SystemName = Literal["A", "B", "C"]


def _routing_prf(pred: list[str], gold: list[str]) -> tuple[float, float, float]:
    """Operation-set precision/recall/F1. Routing order is evaluated separately by exact match."""
    p = set(pred)
    g = set(gold)
    tp = len(p & g)
    precision = tp / len(p) if p else (1.0 if not g else 0.0)
    recall = tp / len(g) if g else (1.0 if not p else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def _gold_output(engine: RuleEngine, attrs: dict[str, Any]) -> dict[str, Any]:
    result = engine.run(attrs)
    if result["status"] == "OK":
        return {
            "status": "OK",
            "material": result["material"],
            "routing": result["routing"],
            "required_fields": [],
        }
    if result["status"] == "CLARIFICATION_REQUIRED":
        return {
            "status": "CLARIFICATION_REQUIRED",
            "material": None,
            "routing": [],
            "required_fields": result["required_fields"],
        }
    raise ValueError(f"Unsupported gold status: {result['status']!r}")


def _parse_system_b_structure(
    raw: str, engine: RuleEngine
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate only JSON/output structure and domains, not cross-field semantics.

    This intentionally does NOT enforce rules such as
    `CLARIFICATION_REQUIRED -> routing == []`. Those are counted separately as
    semantic validity so structured-output validity and business consistency do
    not get mixed together.
    """
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"INVALID_JSON: {exc}"

    if not isinstance(value, dict):
        return None, "OUTPUT_MUST_BE_OBJECT"

    expected = {"status", "material", "routing", "required_fields"}
    if set(value) != expected:
        return (
            None,
            f"INVALID_KEYS: expected={sorted(expected)}, actual={sorted(value)}",
        )

    status = value["status"]
    material = value["material"]
    routing = value["routing"]
    required_fields = value["required_fields"]

    if status not in {"OK", "CLARIFICATION_REQUIRED"}:
        return None, f"INVALID_STATUS: {status!r}"
    if material is not None and material not in engine.material_domain:
        return None, f"INVALID_MATERIAL: {material!r}"
    if not isinstance(routing, list) or any(
        op not in engine.operation_domain for op in routing
    ):
        return None, "INVALID_ROUTING"
    if not isinstance(required_fields, list) or any(
        field not in FIELDS for field in required_fields
    ):
        return None, "INVALID_REQUIRED_FIELDS"

    return {
        "status": status,
        "material": material,
        "routing": routing,
        "required_fields": required_fields,
    }, None


def _system_b_semantic_valid(pred: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []

    if len(pred["routing"]) != len(set(pred["routing"])):
        errors.append("DUPLICATE_ROUTING_OPERATION")
    if len(pred["required_fields"]) != len(set(pred["required_fields"])):
        errors.append("DUPLICATE_REQUIRED_FIELD")

    if pred["status"] == "OK":
        if pred["material"] is None:
            errors.append("OK_REQUIRES_MATERIAL")
        if not pred["routing"]:
            errors.append("OK_REQUIRES_ROUTING")
        if pred["required_fields"]:
            errors.append("OK_REQUIRES_EMPTY_REQUIRED_FIELDS")
    else:
        if pred["material"] is not None:
            errors.append("CLARIFICATION_REQUIRES_NULL_MATERIAL")
        if pred["routing"]:
            errors.append("CLARIFICATION_REQUIRES_EMPTY_ROUTING")
        if not pred["required_fields"]:
            errors.append("CLARIFICATION_REQUIRES_REQUIRED_FIELDS")

    return not errors, errors


def _condition_metrics_template() -> dict[str, int]:
    return {
        "total": 0,
        "evaluated": 0,
        "structured_output_valid": 0,
        "semantic_output_valid": 0,
        "attribute_exact": 0,
        "final_task_success": 0,
        "dangerous_guess": 0,
        "over_clarification": 0,
    }


def evaluate_run_common(run_data: dict[str, Any], system: SystemName) -> dict[str, Any]:
    engine = RuleEngine()
    totals = Counter()
    field_correct = Counter()
    by_condition = defaultdict(_condition_metrics_template)

    routing_precision_sum = 0.0
    routing_recall_sum = 0.0
    routing_f1_sum = 0.0

    for item in run_data["items"]:
        totals["total"] += 1
        condition = item.get("condition", "UNKNOWN")
        row = by_condition[condition]
        row["total"] += 1

        raw = item.get("system_output_raw") or item.get("model_output_raw")
        if raw is None:
            item["common_evaluation"] = {
                "evaluated": False,
                "reason": item.get("error") or "MODEL_OUTPUT_MISSING",
            }
            totals["not_run"] += 1
            continue

        totals["evaluated"] += 1
        row["evaluated"] += 1
        gold_attrs = item["ground_truth_attributes"]
        gold = _gold_output(engine, gold_attrs)
        sufficient = gold["status"] == "OK"
        totals["sufficient_cases" if sufficient else "missing_cases"] += 1

        pred: dict[str, Any] | None = None
        structural_valid = False
        semantic_valid = False
        semantic_errors: list[str] = []
        attribute_exact: bool | None = None

        if system in {"A", "C"}:
            try:
                parsed = validate_extraction(raw)
                structural_valid = True
                semantic_valid = True
                pred_result = engine.run(parsed)
                pred = (
                    {
                        "status": "OK",
                        "material": pred_result["material"],
                        "routing": pred_result["routing"],
                        "required_fields": [],
                    }
                    if pred_result["status"] == "OK"
                    else {
                        "status": "CLARIFICATION_REQUIRED",
                        "material": None,
                        "routing": [],
                        "required_fields": pred_result["required_fields"],
                    }
                )

                attribute_exact = all(
                    parsed[field] == gold_attrs[field] for field in FIELDS
                )
                totals["attribute_exact"] += int(attribute_exact)
                row["attribute_exact"] += int(attribute_exact)
                for field in FIELDS:
                    field_correct[field] += int(parsed[field] == gold_attrs[field])
            except ExtractionValidationError as exc:
                semantic_errors = [str(exc)]

        elif system == "B":
            pred, structural_error = _parse_system_b_structure(raw, engine)
            structural_valid = pred is not None
            if structural_error:
                semantic_errors = [structural_error]
            elif pred is not None:
                semantic_valid, semantic_errors = _system_b_semantic_valid(pred)
        else:
            raise ValueError(f"Unsupported system: {system}")

        totals["structured_output_valid"] += int(structural_valid)
        row["structured_output_valid"] += int(structural_valid)
        totals["semantic_output_valid"] += int(semantic_valid)
        row["semantic_output_valid"] += int(semantic_valid)

        if pred is None:
            item["common_evaluation"] = {
                "evaluated": True,
                "structured_output_valid": structural_valid,
                "semantic_output_valid": semantic_valid,
                "semantic_errors": semantic_errors,
                "attribute_exact": attribute_exact,
                "ground_truth_output": gold,
                "final_task_success": False,
            }
            continue

        status_correct = pred["status"] == gold["status"]
        required_fields_correct = set(pred["required_fields"]) == set(
            gold["required_fields"]
        ) and len(pred["required_fields"]) == len(gold["required_fields"])

        if sufficient:
            material_correct = pred["material"] == gold["material"]
            routing_exact = pred["routing"] == gold["routing"]
            over_clarification = pred["status"] == "CLARIFICATION_REQUIRED"
            dangerous_guess = False

            totals["material_correct_sufficient"] += int(material_correct)
            totals["routing_exact_sufficient"] += int(routing_exact)
            totals["over_clarification"] += int(over_clarification)
            row["over_clarification"] += int(over_clarification)

            pr, rc, f1 = _routing_prf(pred["routing"], gold["routing"])
            routing_precision_sum += pr
            routing_recall_sum += rc
            routing_f1_sum += f1
        else:
            material_correct = pred["material"] is None
            routing_exact = pred["routing"] == []
            dangerous_guess = (
                pred["status"] == "OK"
                or pred["material"] is not None
                or bool(pred["routing"])
            )
            over_clarification = False

            totals["missing_status_correct"] += int(status_correct)
            totals["required_fields_correct_missing"] += int(required_fields_correct)
            totals["dangerous_guess"] += int(dangerous_guess)
            row["dangerous_guess"] += int(dangerous_guess)

        final_task_success = (
            status_correct
            and material_correct
            and routing_exact
            and required_fields_correct
        )
        totals["final_task_success"] += int(final_task_success)
        row["final_task_success"] += int(final_task_success)

        item["common_evaluation"] = {
            "evaluated": True,
            "structured_output_valid": structural_valid,
            "semantic_output_valid": semantic_valid,
            "semantic_errors": semantic_errors,
            "attribute_exact": attribute_exact,
            "ground_truth_output": gold,
            "predicted_output": pred,
            "status_correct": status_correct,
            "material_correct": material_correct,
            "routing_exact": routing_exact,
            "required_fields_correct": required_fields_correct,
            "dangerous_guess": dangerous_guess,
            "over_clarification": over_clarification,
            "final_task_success": final_task_success,
        }

    evaluated = totals["evaluated"]
    sufficient = totals["sufficient_cases"]
    missing = totals["missing_cases"]

    def rate(num: int, den: int) -> float | None:
        return num / den if den else None

    summary: dict[str, Any] = {
        "system": system,
        "total_items": totals["total"],
        "evaluated_items": evaluated,
        "not_run": totals["not_run"],
        "structured_output_valid_count": totals["structured_output_valid"],
        "structured_output_valid_rate": rate(
            totals["structured_output_valid"], evaluated
        ),
        "semantic_output_valid_count": totals["semantic_output_valid"],
        "semantic_output_valid_rate": rate(totals["semantic_output_valid"], evaluated),
        "final_task_success_count": totals["final_task_success"],
        "final_task_success_rate": rate(totals["final_task_success"], evaluated),
        "sufficient_case_count": sufficient,
        "material_correct_on_sufficient": totals["material_correct_sufficient"],
        "material_accuracy_on_sufficient": rate(
            totals["material_correct_sufficient"], sufficient
        ),
        "routing_exact_on_sufficient": totals["routing_exact_sufficient"],
        "routing_exact_rate_on_sufficient": rate(
            totals["routing_exact_sufficient"], sufficient
        ),
        "routing_macro_precision_on_sufficient": rate(
            routing_precision_sum, sufficient
        ),
        "routing_macro_recall_on_sufficient": rate(routing_recall_sum, sufficient),
        "routing_macro_f1_on_sufficient": rate(routing_f1_sum, sufficient),
        "over_clarification_count": totals["over_clarification"],
        "over_clarification_rate_on_sufficient": rate(
            totals["over_clarification"], sufficient
        ),
        "missing_case_count": missing,
        "missing_status_correct_count": totals["missing_status_correct"],
        "missing_status_accuracy": rate(totals["missing_status_correct"], missing),
        "required_fields_correct_on_missing": totals["required_fields_correct_missing"],
        "required_fields_accuracy_on_missing": rate(
            totals["required_fields_correct_missing"], missing
        ),
        "dangerous_guess_count": totals["dangerous_guess"],
        "dangerous_guess_rate_on_missing": rate(totals["dangerous_guess"], missing),
    }

    if system in {"A", "C"}:
        summary["attribute_exact_count"] = totals["attribute_exact"]
        summary["attribute_exact_rate"] = rate(totals["attribute_exact"], evaluated)
        summary["field_accuracy"] = {
            field: rate(field_correct[field], evaluated) for field in FIELDS
        }
    else:
        summary["attribute_exact_count"] = None
        summary["attribute_exact_rate"] = None
        summary["field_accuracy"] = None

    condition_summary: dict[str, Any] = {}
    for condition in ("NORMAL", "VARIANT", "MISSING"):
        row = by_condition[condition]
        den = row["evaluated"]
        condition_summary[condition] = {
            **row,
            "structured_output_valid_rate": rate(row["structured_output_valid"], den),
            "semantic_output_valid_rate": rate(row["semantic_output_valid"], den),
            "attribute_exact_rate": rate(row["attribute_exact"], den)
            if system == "A"
            else None,
            "final_task_success_rate": rate(row["final_task_success"], den),
        }

    run_data["common_summary"] = summary
    run_data["common_summary_by_condition"] = condition_summary
    return run_data
