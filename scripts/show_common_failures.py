from __future__ import annotations

import argparse
import json

from bolt_thesis.evaluation.common import evaluate_run_common
from bolt_thesis.paths import (
    DEFAULT_SYSTEM_A_RESULT_PATH,
    DEFAULT_SYSTEM_A_VALIDATION_RESULT_PATH,
    DEFAULT_SYSTEM_B_PILOT_RESULT_PATH,
    DEFAULT_SYSTEM_B_VALIDATION_RESULT_PATH,
    DEFAULT_SYSTEM_C_PILOT_RESULT_PATH,
    DEFAULT_SYSTEM_C_VALIDATION_RESULT_PATH,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", choices=["A", "B", "C"], required=True)
    parser.add_argument(
        "--split", choices=["pilot", "validation"], default="validation"
    )
    args = parser.parse_args()

    if args.system == "A":
        path = (
            DEFAULT_SYSTEM_A_RESULT_PATH
            if args.split == "pilot"
            else DEFAULT_SYSTEM_A_VALIDATION_RESULT_PATH
        )
    elif args.system == "B":
        path = (
            DEFAULT_SYSTEM_B_PILOT_RESULT_PATH
            if args.split == "pilot"
            else DEFAULT_SYSTEM_B_VALIDATION_RESULT_PATH
        )
    else:
        path = (
            DEFAULT_SYSTEM_C_PILOT_RESULT_PATH
            if args.split == "pilot"
            else DEFAULT_SYSTEM_C_VALIDATION_RESULT_PATH
        )

    data = evaluate_run_common(
        json.loads(path.read_text(encoding="utf-8")), args.system
    )

    for item in data["items"]:
        ev = item.get("common_evaluation") or {}
        if not ev.get("evaluated") or ev.get("final_task_success") is True:
            continue

        print("=" * 88)
        print("ID:", item["id"])
        print("CONDITION:", item.get("condition"))
        print("TEXT:", item["text"])
        print("GT ATTR:", item["ground_truth_attributes"])
        print("GT OUTPUT:", ev.get("ground_truth_output"))
        print("PRED OUTPUT:", ev.get("predicted_output"))
        if args.system == "A":
            print("PRED ATTR:", item.get("parsed_attributes"))
            print("ATTRIBUTE EXACT:", ev.get("attribute_exact"))
        print("STRUCTURED VALID:", ev.get("structured_output_valid"))
        print("SEMANTIC VALID:", ev.get("semantic_output_valid"))
        print("SEMANTIC ERRORS:", ev.get("semantic_errors"))
        print("DANGEROUS GUESS:", ev.get("dangerous_guess"))
        print("OVER CLARIFICATION:", ev.get("over_clarification"))


if __name__ == "__main__":
    main()
