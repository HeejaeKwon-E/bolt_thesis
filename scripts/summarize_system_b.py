from __future__ import annotations

import argparse
import json
from collections import defaultdict

from bolt_thesis.paths import (
    DEFAULT_SYSTEM_B_PILOT_RESULT_PATH,
    DEFAULT_SYSTEM_B_VALIDATION_RESULT_PATH,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["pilot", "validation"], required=True)
    args = parser.parse_args()

    path = (
        DEFAULT_SYSTEM_B_PILOT_RESULT_PATH
        if args.split == "pilot"
        else DEFAULT_SYSTEM_B_VALIDATION_RESULT_PATH
    )
    result = json.loads(path.read_text(encoding="utf-8"))

    rows = defaultdict(
        lambda: {
            "total": 0,
            "schema_valid": 0,
            "task_success": 0,
            "dangerous_guess": 0,
            "over_clarification": 0,
        }
    )

    for item in result["items"]:
        if item.get("model_output_raw") is None:
            continue

        row = rows[item["condition"]]
        row["total"] += 1
        row["schema_valid"] += int(item.get("schema_valid") is True)

        c = item.get("correctness") or {}
        row["task_success"] += int(c.get("task_success") is True)
        row["dangerous_guess"] += int(c.get("dangerous_guess") is True)
        row["over_clarification"] += int(c.get("over_clarification") is True)

    print(
        "condition,total,schema_valid,task_success,accuracy,"
        "dangerous_guess,over_clarification"
    )
    for condition in ("NORMAL", "VARIANT", "MISSING"):
        row = rows[condition]
        accuracy = row["task_success"] / row["total"] if row["total"] else 0.0
        print(
            f"{condition},{row['total']},{row['schema_valid']},"
            f"{row['task_success']},{accuracy:.4f},"
            f"{row['dangerous_guess']},{row['over_clarification']}"
        )


if __name__ == "__main__":
    main()
