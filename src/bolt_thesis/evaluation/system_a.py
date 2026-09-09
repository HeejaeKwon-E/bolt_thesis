from __future__ import annotations

from collections import Counter
from typing import Any

from bolt_thesis.extractor.validator import (
    ExtractionValidationError,
    FIELDS,
    validate_extraction,
)
from bolt_thesis.pipelines.system_a import SystemAPipeline


def evaluate_system_a_run(run_data: dict[str, Any]) -> dict[str, Any]:
    pipeline = SystemAPipeline()
    totals = Counter()
    field_correct = Counter()

    for item in run_data["items"]:
        totals["items"] += 1
        raw = item.get("model_output_raw")

        if raw is None:
            item["error"] = "MODEL_OUTPUT_MISSING"
            totals["not_run"] += 1
            continue

        try:
            parsed = validate_extraction(raw)
            item["parsed_attributes"] = parsed
            item["schema_valid"] = True
            totals["schema_valid"] += 1

            ground_truth = item["ground_truth_attributes"]
            all_correct = True

            for field in FIELDS:
                correct = parsed[field] == ground_truth[field]
                item["field_correctness"][field] = correct
                field_correct[field] += int(correct)
                all_correct = all_correct and correct

            item["all_attributes_correct"] = all_correct
            totals["all_attributes_correct"] += int(all_correct)
            item["pipeline_result"] = pipeline.run_from_extraction(parsed)
            item["error"] = None

        except ExtractionValidationError as exc:
            item["schema_valid"] = False
            item["error"] = str(exc)
            totals["schema_invalid"] += 1

    evaluated = totals["items"] - totals["not_run"]

    run_data["summary"] = {
        "total_items": totals["items"],
        "evaluated_items": evaluated,
        "not_run": totals["not_run"],
        "schema_valid_count": totals["schema_valid"],
        "schema_valid_rate": totals["schema_valid"] / evaluated if evaluated else None,
        "all_attributes_correct_count": totals["all_attributes_correct"],
        "all_attributes_correct_rate": (
            totals["all_attributes_correct"] / evaluated if evaluated else None
        ),
        "field_accuracy": {
            field: field_correct[field] / evaluated if evaluated else None
            for field in FIELDS
        },
    }

    return run_data
