from __future__ import annotations

from collections import Counter
from typing import Any

from bolt_thesis.rule_engine import RuleEngine
from bolt_thesis.system_b.validator import (
    SystemBValidationError,
    validate_system_b_output,
)


def _routing_prf(pred: list[str], gold: list[str]) -> tuple[float, float, float]:
    p = set(pred)
    g = set(gold)

    tp = len(p & g)
    precision = tp / len(p) if p else (1.0 if not g else 0.0)
    recall = tp / len(g) if g else (1.0 if not p else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def evaluate_system_b_run(run_data: dict[str, Any]) -> dict[str, Any]:
    engine = RuleEngine()
    totals = Counter()
    routing_precision_sum = 0.0
    routing_recall_sum = 0.0
    routing_f1_sum = 0.0
    routing_count = 0

    for item in run_data["items"]:
        totals["items"] += 1
        raw = item.get("model_output_raw")

        if raw is None:
            item["error"] = item.get("error") or "MODEL_OUTPUT_MISSING"
            totals["not_run"] += 1
            continue

        try:
            pred = validate_system_b_output(raw)
            item["parsed_output"] = pred
            item["schema_valid"] = True
            totals["schema_valid"] += 1

            attrs = item["ground_truth_attributes"]
            gold = engine.run(attrs)

            if gold["status"] == "OK":
                gold_output = {
                    "status": "OK",
                    "material": gold["material"],
                    "routing": gold["routing"],
                    "required_fields": [],
                }

                status_correct = pred["status"] == "OK"
                material_correct = pred["material"] == gold["material"]
                routing_exact = pred["routing"] == gold["routing"]
                required_fields_correct = pred["required_fields"] == []
                over_clarification = pred["status"] == "CLARIFICATION_REQUIRED"
                dangerous_guess = False

                pr, rc, f1 = _routing_prf(pred["routing"], gold["routing"])
                routing_precision_sum += pr
                routing_recall_sum += rc
                routing_f1_sum += f1
                routing_count += 1

                totals["material_correct"] += int(material_correct)
                totals["routing_exact"] += int(routing_exact)
                totals["over_clarification"] += int(over_clarification)

            else:
                gold_output = {
                    "status": "CLARIFICATION_REQUIRED",
                    "material": None,
                    "routing": [],
                    "required_fields": gold["required_fields"],
                }

                status_correct = pred["status"] == "CLARIFICATION_REQUIRED"
                material_correct = pred["material"] is None
                routing_exact = pred["routing"] == []
                required_fields_correct = set(pred["required_fields"]) == set(
                    gold["required_fields"]
                ) and len(pred["required_fields"]) == len(gold["required_fields"])
                over_clarification = False
                dangerous_guess = (
                    pred["status"] == "OK"
                    or pred["material"] is not None
                    or bool(pred["routing"])
                )

                totals["missing_cases"] += 1
                totals["required_fields_correct"] += int(required_fields_correct)
                totals["dangerous_guess"] += int(dangerous_guess)

            task_success = (
                status_correct
                and material_correct
                and routing_exact
                and required_fields_correct
            )

            item["ground_truth_output"] = gold_output
            item["correctness"] = {
                "status_correct": status_correct,
                "material_correct": material_correct,
                "routing_exact": routing_exact,
                "required_fields_correct": required_fields_correct,
                "task_success": task_success,
                "dangerous_guess": dangerous_guess,
                "over_clarification": over_clarification,
            }

            totals["task_success"] += int(task_success)
            item["error"] = None

        except SystemBValidationError as exc:
            item["schema_valid"] = False
            item["error"] = str(exc)
            totals["schema_invalid"] += 1

    evaluated = totals["items"] - totals["not_run"]

    run_data["summary"] = {
        "total_items": totals["items"],
        "evaluated_items": evaluated,
        "not_run": totals["not_run"],
        "schema_valid_rate": totals["schema_valid"] / evaluated if evaluated else None,
        "task_success_count": totals["task_success"],
        "task_success_rate": totals["task_success"] / evaluated if evaluated else None,
        "material_accuracy_on_all_evaluated": (
            totals["material_correct"] / evaluated if evaluated else None
        ),
        "routing_exact_count": totals["routing_exact"],
        "routing_macro_precision_on_sufficient": (
            routing_precision_sum / routing_count if routing_count else None
        ),
        "routing_macro_recall_on_sufficient": (
            routing_recall_sum / routing_count if routing_count else None
        ),
        "routing_macro_f1_on_sufficient": (
            routing_f1_sum / routing_count if routing_count else None
        ),
        "missing_case_count": totals["missing_cases"],
        "missing_required_fields_correct_count": totals["required_fields_correct"],
        "dangerous_guess_count": totals["dangerous_guess"],
        "over_clarification_count": totals["over_clarification"],
    }
    return run_data
