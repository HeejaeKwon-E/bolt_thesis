from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bolt_thesis.paths import FINAL_TEST_DATASET_PATH

FIELDS = ("diameter_mm", "length_mm", "strength_grade", "surface_treatment")


def load_final_test_dataset(path: Path = FINAL_TEST_DATASET_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_system_a_run(dataset: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_metadata": {
            "system": "A",
            "component": "LLM_ATTRIBUTE_EXTRACTOR_PLUS_RULE_ENGINE",
            "dataset": dataset["dataset_name"],
            "split": "final_test",
            "final_test": True,
        },
        "items": [
            {
                "id": item["id"],
                "condition": item["condition"],
                "variation_tags": item.get("variation_tags", []),
                "text": item["text"],
                "ground_truth_attributes": item["ground_truth"]["attributes"],
                "model_output_raw": None,
                "parsed_attributes": None,
                "schema_valid": None,
                "field_correctness": {field: None for field in FIELDS},
                "all_attributes_correct": None,
                "pipeline_result": None,
                "error": None,
            }
            for item in dataset["items"]
        ],
    }


def build_system_b_run(dataset: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_metadata": {
            "system": "B",
            "component": "DIRECT_LLM_GENERATION",
            "dataset": dataset["dataset_name"],
            "split": "final_test",
            "final_test": True,
            "rules_source": "config/rules.json",
        },
        "items": [
            {
                "id": item["id"],
                "condition": item["condition"],
                "variation_tags": item.get("variation_tags", []),
                "text": item["text"],
                "ground_truth_attributes": item["ground_truth"]["attributes"],
                "model_output_raw": None,
                "parsed_output": None,
                "schema_valid": None,
                "ground_truth_output": None,
                "correctness": None,
                "error": None,
            }
            for item in dataset["items"]
        ],
    }
