from __future__ import annotations

import argparse
import json
from pathlib import Path

from bolt_thesis.evaluation.common import evaluate_run_common
from bolt_thesis.paths import (
    DEFAULT_SYSTEM_A_RESULT_PATH,
    DEFAULT_SYSTEM_A_VALIDATION_RESULT_PATH,
    DEFAULT_SYSTEM_B_PILOT_RESULT_PATH,
    DEFAULT_SYSTEM_B_VALIDATION_RESULT_PATH,
    PILOT_DATASET_PATH,
    RESULTS_DIR,
    VALIDATION_DATASET_PATH,
)


def _paths(split: str) -> tuple[Path, Path, Path]:
    if split == "pilot":
        return (
            DEFAULT_SYSTEM_A_RESULT_PATH,
            DEFAULT_SYSTEM_B_PILOT_RESULT_PATH,
            RESULTS_DIR / "unified_evaluation_pilot.json",
        )
    return (
        DEFAULT_SYSTEM_A_VALIDATION_RESULT_PATH,
        DEFAULT_SYSTEM_B_VALIDATION_RESULT_PATH,
        RESULTS_DIR / "unified_evaluation_validation.json",
    )


def _attach_conditions(run_data: dict, split: str) -> dict:
    """Attach canonical dataset condition to result items by id.

    System A result files created by the earlier runner do not store `condition`,
    while System B result files do. Condition must therefore come from the
    dataset rather than from the result-file shape.
    """
    dataset_path = PILOT_DATASET_PATH if split == "pilot" else VALIDATION_DATASET_PATH
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    condition_by_id = {item["id"]: item["condition"] for item in dataset["items"]}

    missing_ids = []
    for item in run_data["items"]:
        item_id = item["id"]
        condition = condition_by_id.get(item_id)
        if condition is None:
            missing_ids.append(item_id)
            continue
        item["condition"] = condition

    if missing_ids:
        raise ValueError(
            "Result item id(s) not found in canonical dataset: "
            + ", ".join(missing_ids)
        )

    return run_data


def _fmt(value: float | None) -> str:
    return "-" if value is None else f"{value:.4f}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-evaluate existing A/B result JSONs with common metrics"
    )
    parser.add_argument(
        "--split", choices=["pilot", "validation"], default="validation"
    )
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    a_path, b_path, default_output = _paths(args.split)
    output = Path(args.output) if args.output else default_output

    missing = [str(path) for path in (a_path, b_path) if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing result file(s): " + ", ".join(missing))

    a_run = _attach_conditions(
        json.loads(a_path.read_text(encoding="utf-8")),
        args.split,
    )
    b_run = _attach_conditions(
        json.loads(b_path.read_text(encoding="utf-8")),
        args.split,
    )

    a = evaluate_run_common(a_run, "A")
    b = evaluate_run_common(b_run, "B")

    report = {
        "split": args.split,
        "systems": {
            "A": a["common_summary"],
            "B": b["common_summary"],
        },
        "by_condition": {
            "A": a["common_summary_by_condition"],
            "B": b["common_summary_by_condition"],
        },
    }
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        "system,task_success,attribute_exact,material_acc_sufficient,routing_exact_sufficient,required_fields_acc_missing,dangerous_guess_rate,over_clarification_rate"
    )
    for name, data in report["systems"].items():
        print(
            f"{name},"
            f"{_fmt(data['final_task_success_rate'])},"
            f"{_fmt(data['attribute_exact_rate'])},"
            f"{_fmt(data['material_accuracy_on_sufficient'])},"
            f"{_fmt(data['routing_exact_rate_on_sufficient'])},"
            f"{_fmt(data['required_fields_accuracy_on_missing'])},"
            f"{_fmt(data['dangerous_guess_rate_on_missing'])},"
            f"{_fmt(data['over_clarification_rate_on_sufficient'])}"
        )

    print("\ncondition,system,total,task_success,accuracy")
    for condition in ("NORMAL", "VARIANT", "MISSING"):
        for system in ("A", "B"):
            row = report["by_condition"][system][condition]
            print(
                f"{condition},{system},{row['evaluated']},"
                f"{row['final_task_success']},{_fmt(row['final_task_success_rate'])}"
            )

    print(f"\nSaved: {output}")


if __name__ == "__main__":
    main()
