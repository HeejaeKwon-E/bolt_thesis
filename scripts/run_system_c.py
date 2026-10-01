from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from bolt_thesis.evaluation.common import evaluate_run_common
from bolt_thesis.paths import (
    DEFAULT_SYSTEM_C_PILOT_RESULT_PATH,
    DEFAULT_SYSTEM_C_VALIDATION_RESULT_PATH,
    PILOT_DATASET_PATH,
    VALIDATION_DATASET_PATH,
)
from bolt_thesis.rule_engine import RuleEngine
from bolt_thesis.system_c import RegexDictionaryExtractor


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _gold_attrs(item: dict[str, Any]) -> dict[str, Any]:
    return item["ground_truth"]["attributes"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run System C regex/dictionary baseline"
    )
    parser.add_argument("--split", choices=["pilot", "validation"], required=True)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.split == "pilot":
        dataset_path = PILOT_DATASET_PATH
        default_output = DEFAULT_SYSTEM_C_PILOT_RESULT_PATH
    else:
        dataset_path = VALIDATION_DATASET_PATH
        default_output = DEFAULT_SYSTEM_C_VALIDATION_RESULT_PATH

    output_path = Path(args.output) if args.output else default_output
    dataset = load_json(dataset_path)

    extractor = RegexDictionaryExtractor()
    engine = RuleEngine()

    run_data: dict[str, Any] = {
        "run_metadata": {
            "system": "C",
            "component": "REGEX_DICTIONARY_EXTRACTOR_PLUS_RULE_ENGINE",
            "dataset": dataset["dataset_name"],
            "split": args.split,
            "config_version": extractor.config["version"],
            "deterministic": True,
            "uses_llm": False,
            "rules_source": "config/rules.json",
        },
        "items": [],
    }

    started_all = time.perf_counter()

    for item in dataset["items"]:
        started = time.perf_counter()
        attrs = extractor.extract(item["text"])
        result = engine.run(attrs)
        latency = time.perf_counter() - started

        # `system_output_raw` is the generic field used by the new common
        # evaluator. `model_output_raw` is also written for backwards
        # compatibility with earlier A/B tooling.
        raw = json.dumps(attrs, ensure_ascii=False, separators=(",", ":"))

        run_data["items"].append(
            {
                "id": item["id"],
                "condition": item["condition"],
                "text": item["text"],
                "ground_truth_attributes": _gold_attrs(item),
                "system_output_raw": raw,
                "model_output_raw": raw,
                "parsed_attributes": attrs,
                "pipeline_result": {
                    "attributes": attrs,
                    "result": result,
                },
                "latency_sec": latency,
                "error": None,
            }
        )

    run_data["run_metadata"]["wall_time_sec"] = time.perf_counter() - started_all
    evaluated = evaluate_run_common(run_data, "C")
    save_json(output_path, evaluated)

    summary = evaluated["common_summary"]
    print(
        "system,task_success,attribute_exact,material_acc_sufficient,"
        "routing_exact_sufficient,required_fields_acc_missing,"
        "dangerous_guess_rate,over_clarification_rate"
    )
    print(
        "C,"
        f"{summary['final_task_success_rate']:.4f},"
        f"{summary['attribute_exact_rate']:.4f},"
        f"{summary['material_accuracy_on_sufficient']:.4f},"
        f"{summary['routing_exact_rate_on_sufficient']:.4f},"
        f"{summary['required_fields_accuracy_on_missing']:.4f},"
        f"{summary['dangerous_guess_rate_on_missing']:.4f},"
        f"{summary['over_clarification_rate_on_sufficient']:.4f}"
    )

    print("\ncondition,total,task_success,accuracy")
    for condition in ("NORMAL", "VARIANT", "MISSING"):
        row = evaluated["common_summary_by_condition"][condition]
        print(
            f"{condition},{row['evaluated']},{row['final_task_success']},"
            f"{row['final_task_success_rate']:.4f}"
        )

    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
