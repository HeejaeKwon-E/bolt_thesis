from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from bolt_thesis.paths import DEFAULT_SYSTEM_A_RESULT_PATH, PILOT_DATASET_PATH


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", default=str(DEFAULT_SYSTEM_A_RESULT_PATH))
    args = parser.parse_args()

    with PILOT_DATASET_PATH.open("r", encoding="utf-8") as f:
        pilot = json.load(f)

    with Path(args.result).open("r", encoding="utf-8") as f:
        result = json.load(f)

    condition_by_id = {item["id"]: item["condition"] for item in pilot["items"]}
    rows = defaultdict(lambda: {"total": 0, "correct": 0, "schema_valid": 0})

    for item in result["items"]:
        if item.get("model_output_raw") is None:
            continue

        condition = condition_by_id[item["id"]]
        rows[condition]["total"] += 1
        rows[condition]["schema_valid"] += int(item.get("schema_valid") is True)
        rows[condition]["correct"] += int(item.get("all_attributes_correct") is True)

    print("condition,total,schema_valid,all_attributes_correct,accuracy")

    for condition in ("NORMAL", "VARIANT", "MISSING"):
        row = rows[condition]
        accuracy = row["correct"] / row["total"] if row["total"] else 0.0
        print(
            f"{condition},{row['total']},{row['schema_valid']},"
            f"{row['correct']},{accuracy:.4f}"
        )


if __name__ == "__main__":
    main()
