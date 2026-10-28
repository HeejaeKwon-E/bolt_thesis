from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bolt_thesis.evaluation.common import evaluate_run_common
from bolt_thesis.final_test import load_final_test_dataset
from bolt_thesis.paths import (
    DEFAULT_SYSTEM_A_FINAL_TEST_RESULT_PATH,
    DEFAULT_SYSTEM_B_FINAL_TEST_RESULT_PATH,
    DEFAULT_SYSTEM_C_FINAL_TEST_RESULT_PATH,
    FINAL_TEST_UNIFIED_RESULT_PATH,
)

SYSTEM_PATHS = {
    "A": DEFAULT_SYSTEM_A_FINAL_TEST_RESULT_PATH,
    "B": DEFAULT_SYSTEM_B_FINAL_TEST_RESULT_PATH,
    "C": DEFAULT_SYSTEM_C_FINAL_TEST_RESULT_PATH,
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    missing = [str(path) for path in SYSTEM_PATHS.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing Final Test result file(s): " + ", ".join(missing)
        )

    dataset = load_final_test_dataset()
    metadata_by_id = {
        item["id"]: {
            "condition": item["condition"],
            "variation_tags": item.get("variation_tags", []),
        }
        for item in dataset["items"]
    }

    evaluated: dict[str, dict[str, Any]] = {}
    for system, path in SYSTEM_PATHS.items():
        run = load_json(path)
        evaluated[system] = evaluate_run_common(run, system)  # type: ignore[arg-type]

    report: dict[str, Any] = {
        "dataset": dataset["dataset_name"],
        "split": "final_test",
        "systems": {system: run["common_summary"] for system, run in evaluated.items()},
        "by_condition": {
            system: run["common_summary_by_condition"]
            for system, run in evaluated.items()
        },
        "items": [],
    }

    item_maps = {
        system: {item["id"]: item for item in run["items"]}
        for system, run in evaluated.items()
    }

    for item_id, meta in metadata_by_id.items():
        row: dict[str, Any] = {"id": item_id, **meta, "systems": {}}
        for system in ("A", "B", "C"):
            ce = item_maps[system][item_id].get("common_evaluation", {})
            row["systems"][system] = {
                "final_task_success": ce.get("final_task_success"),
                "attribute_exact": ce.get("attribute_exact"),
                "routing_exact": ce.get("routing_exact"),
                "required_fields_correct": ce.get("required_fields_correct"),
                "dangerous_guess": ce.get("dangerous_guess"),
                "over_clarification": ce.get("over_clarification"),
            }
        report["items"].append(row)

    FINAL_TEST_UNIFIED_RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FINAL_TEST_UNIFIED_RESULT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        "system,task_success,attribute_exact,material_acc_sufficient,"
        "routing_exact_sufficient,required_fields_acc_missing,"
        "dangerous_guess_rate,over_clarification_rate"
    )
    for system in ("A", "B", "C"):
        s = report["systems"][system]
        fmt = lambda v: "-" if v is None else f"{v:.4f}"
        print(
            f"{system},"
            f"{fmt(s['final_task_success_rate'])},"
            f"{fmt(s.get('attribute_exact_rate'))},"
            f"{fmt(s['material_accuracy_on_sufficient'])},"
            f"{fmt(s['routing_exact_rate_on_sufficient'])},"
            f"{fmt(s['required_fields_accuracy_on_missing'])},"
            f"{fmt(s['dangerous_guess_rate_on_missing'])},"
            f"{fmt(s['over_clarification_rate_on_sufficient'])}"
        )

    print("\ncondition,system,total,task_success,accuracy")
    for condition in ("NORMAL", "VARIANT", "MISSING"):
        for system in ("A", "B", "C"):
            row = report["by_condition"][system][condition]
            rate = row["final_task_success_rate"]
            print(
                f"{condition},{system},{row['evaluated']},"
                f"{row['final_task_success']},"
                f"{'-' if rate is None else f'{rate:.4f}'}"
            )

    print(f"\nSaved: {FINAL_TEST_UNIFIED_RESULT_PATH}")


if __name__ == "__main__":
    main()
