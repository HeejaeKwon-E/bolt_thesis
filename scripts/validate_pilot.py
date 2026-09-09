from __future__ import annotations

import json
from collections import Counter

from bolt_thesis.paths import PILOT_DATASET_PATH
from bolt_thesis.rule_engine import RuleEngine


def main() -> None:
    with PILOT_DATASET_PATH.open("r", encoding="utf-8") as f:
        dataset = json.load(f)

    engine = RuleEngine()
    failures = []

    for item in dataset["items"]:
        attrs = item["ground_truth"]["attributes"]
        expected = item["ground_truth"]["expected_output"]
        actual = engine.run(attrs)

        if actual != expected:
            failures.append(
                {"id": item["id"], "expected": expected, "actual": actual}
            )

    ids = [item["id"] for item in dataset["items"]]
    counts = Counter(item["condition"] for item in dataset["items"])

    print(f"items: {len(ids)}")
    print(f"unique ids: {len(set(ids))}")
    print(f"conditions: {dict(counts)}")
    print(f"rule-engine mismatches: {len(failures)}")

    assert len(ids) == len(set(ids))
    assert not failures


if __name__ == "__main__":
    main()
