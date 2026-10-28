from __future__ import annotations

import json
import math
import random
from collections.abc import Callable
from pathlib import Path
from typing import Any

from bolt_thesis.paths import FINAL_TEST_STATISTICS_PATH, FINAL_TEST_UNIFIED_RESULT_PATH

BOOTSTRAP_ITERATIONS = 10_000
BOOTSTRAP_SEED = 42


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def exact_mcnemar_p(left_only: int, right_only: int) -> float:
    """Two-sided exact McNemar p-value via Binomial(n, 0.5)."""
    n = left_only + right_only
    if n == 0:
        return 1.0
    k = min(left_only, right_only)
    cumulative = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2.0 * cumulative)


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise ValueError("percentile requires at least one value")
    position = (len(sorted_values) - 1) * q
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return sorted_values[low]
    fraction = position - low
    return sorted_values[low] * (1 - fraction) + sorted_values[high] * fraction


def paired_bootstrap_ci(
    left: list[bool],
    right: list[bool],
    *,
    iterations: int = BOOTSTRAP_ITERATIONS,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    if len(left) != len(right) or not left:
        raise ValueError("paired bootstrap requires equal non-empty vectors")
    rng = random.Random(seed)
    n = len(left)
    diffs: list[float] = []
    for _ in range(iterations):
        delta_sum = 0
        for _ in range(n):
            index = rng.randrange(n)
            delta_sum += int(left[index]) - int(right[index])
        diffs.append(delta_sum / n)
    diffs.sort()
    return percentile(diffs, 0.025), percentile(diffs, 0.975)


def compare_vectors(
    left_name: str,
    right_name: str,
    left: list[bool],
    right: list[bool],
) -> dict[str, Any]:
    if len(left) != len(right) or not left:
        raise ValueError("paired comparison requires equal non-empty vectors")

    both_correct = sum(a and b for a, b in zip(left, right))
    left_only = sum(a and not b for a, b in zip(left, right))
    right_only = sum((not a) and b for a, b in zip(left, right))
    both_wrong = len(left) - both_correct - left_only - right_only
    left_rate = sum(left) / len(left)
    right_rate = sum(right) / len(right)
    ci_low, ci_high = paired_bootstrap_ci(left, right)

    return {
        "left": left_name,
        "right": right_name,
        "n": len(left),
        "left_rate": left_rate,
        "right_rate": right_rate,
        "difference_left_minus_right": left_rate - right_rate,
        "bootstrap_95_ci_difference": [ci_low, ci_high],
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "mcnemar": {
            "both_success": both_correct,
            "left_only_success": left_only,
            "right_only_success": right_only,
            "both_failure": both_wrong,
            "discordant_pairs": left_only + right_only,
            "exact_two_sided_p": exact_mcnemar_p(left_only, right_only),
        },
    }


def select_items(
    report: dict[str, Any], condition: str | None = None
) -> list[dict[str, Any]]:
    if condition is None:
        return report["items"]
    return [item for item in report["items"] if item["condition"] == condition]


def bool_metric(
    items: list[dict[str, Any]],
    system: str,
    key: str,
    transform: Callable[[Any], bool] | None = None,
) -> list[bool]:
    values: list[bool] = []
    for item in items:
        value = item["systems"][system].get(key)
        if value is None:
            raise ValueError(f"Missing metric {key} for {system} on {item['id']}")
        values.append(transform(value) if transform else bool(value))
    return values


def add_pairwise(
    target: dict[str, Any],
    items: list[dict[str, Any]],
    metric: str,
    pairs: tuple[tuple[str, str], ...],
    *,
    transform: Callable[[Any], bool] | None = None,
) -> None:
    target[metric] = {}
    for left, right in pairs:
        lv = bool_metric(items, left, metric, transform)
        rv = bool_metric(items, right, metric, transform)
        target[metric][f"{left}_vs_{right}"] = compare_vectors(left, right, lv, rv)


def main() -> None:
    if not FINAL_TEST_UNIFIED_RESULT_PATH.exists():
        raise FileNotFoundError(
            f"Run scripts/evaluate_final_test.py first: {FINAL_TEST_UNIFIED_RESULT_PATH}"
        )
    report = load_json(FINAL_TEST_UNIFIED_RESULT_PATH)

    stats: dict[str, Any] = {
        "dataset": report["dataset"],
        "method": {
            "mcnemar": "two-sided exact McNemar test on paired binary outcomes",
            "bootstrap": "paired nonparametric bootstrap of accuracy difference",
            "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "ci": 0.95,
        },
        "primary": {},
        "secondary": {},
    }

    all_items = select_items(report)
    pairs = (("A", "B"), ("A", "C"), ("B", "C"))
    add_pairwise(stats["primary"], all_items, "final_task_success", pairs)

    # RQ1: deterministic rule-engine hybrid vs direct LLM on complete inputs.
    sufficient = [
        item for item in all_items if item["condition"] in {"NORMAL", "VARIANT"}
    ]
    stats["secondary"]["routing_exact_sufficient"] = {
        "A_vs_B": compare_vectors(
            "A",
            "B",
            bool_metric(sufficient, "A", "routing_exact"),
            bool_metric(sufficient, "B", "routing_exact"),
        )
    }

    # RQ2: missing-information behavior. "safe" means no dangerous guess.
    missing = select_items(report, "MISSING")
    safe_transform = lambda value: not bool(value)
    stats["secondary"]["no_dangerous_guess_missing"] = {}
    for left, right in pairs:
        stats["secondary"]["no_dangerous_guess_missing"][f"{left}_vs_{right}"] = (
            compare_vectors(
                left,
                right,
                bool_metric(missing, left, "dangerous_guess", safe_transform),
                bool_metric(missing, right, "dangerous_guess", safe_transform),
            )
        )

    stats["secondary"]["required_fields_correct_missing"] = {
        "A_vs_B": compare_vectors(
            "A",
            "B",
            bool_metric(missing, "A", "required_fields_correct"),
            bool_metric(missing, "B", "required_fields_correct"),
        ),
        "A_vs_C": compare_vectors(
            "A",
            "C",
            bool_metric(missing, "A", "required_fields_correct"),
            bool_metric(missing, "C", "required_fields_correct"),
        ),
    }

    # RQ3: LLM extraction vs Regex/Dictionary extraction, especially variants.
    stats["secondary"]["attribute_exact_A_vs_C"] = {}
    for condition in (None, "NORMAL", "VARIANT", "MISSING"):
        subset = select_items(report, condition)
        label = "ALL" if condition is None else condition
        stats["secondary"]["attribute_exact_A_vs_C"][label] = compare_vectors(
            "A",
            "C",
            bool_metric(subset, "A", "attribute_exact"),
            bool_metric(subset, "C", "attribute_exact"),
        )

    # Condition-specific primary outcome for interpretation; treat as secondary analyses.
    stats["secondary"]["final_task_success_by_condition"] = {}
    for condition in ("NORMAL", "VARIANT", "MISSING"):
        subset = select_items(report, condition)
        condition_report: dict[str, Any] = {}
        for left, right in pairs:
            condition_report[f"{left}_vs_{right}"] = compare_vectors(
                left,
                right,
                bool_metric(subset, left, "final_task_success"),
                bool_metric(subset, right, "final_task_success"),
            )
        stats["secondary"]["final_task_success_by_condition"][condition] = (
            condition_report
        )

    FINAL_TEST_STATISTICS_PATH.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("PRIMARY: final_task_success")
    for label, result in stats["primary"]["final_task_success"].items():
        ci = result["bootstrap_95_ci_difference"]
        print(
            f"{label}: n={result['n']} "
            f"left={result['left_rate']:.4f} right={result['right_rate']:.4f} "
            f"diff={result['difference_left_minus_right']:+.4f} "
            f"95%CI=[{ci[0]:+.4f}, {ci[1]:+.4f}] "
            f"McNemar p={result['mcnemar']['exact_two_sided_p']:.6g}"
        )

    print("\nRQ1: routing_exact_sufficient A_vs_B")
    r = stats["secondary"]["routing_exact_sufficient"]["A_vs_B"]
    ci = r["bootstrap_95_ci_difference"]
    print(
        f"A={r['left_rate']:.4f} B={r['right_rate']:.4f} "
        f"diff={r['difference_left_minus_right']:+.4f} "
        f"95%CI=[{ci[0]:+.4f}, {ci[1]:+.4f}] "
        f"p={r['mcnemar']['exact_two_sided_p']:.6g}"
    )

    print("\nRQ2: missing-information behavior A_vs_B")
    for metric in ("required_fields_correct_missing", "no_dangerous_guess_missing"):
        r = stats["secondary"][metric]["A_vs_B"]
        ci = r["bootstrap_95_ci_difference"]
        print(
            f"{metric}: A={r['left_rate']:.4f} B={r['right_rate']:.4f} "
            f"diff={r['difference_left_minus_right']:+.4f} "
            f"95%CI=[{ci[0]:+.4f}, {ci[1]:+.4f}] "
            f"p={r['mcnemar']['exact_two_sided_p']:.6g}"
        )

    print("\nRQ3: attribute_exact A_vs_C")
    for label, result in stats["secondary"]["attribute_exact_A_vs_C"].items():
        ci = result["bootstrap_95_ci_difference"]
        print(
            f"{label}: A={result['left_rate']:.4f} C={result['right_rate']:.4f} "
            f"diff={result['difference_left_minus_right']:+.4f} "
            f"95%CI=[{ci[0]:+.4f}, {ci[1]:+.4f}] "
            f"p={result['mcnemar']['exact_two_sided_p']:.6g}"
        )

    print(f"\nSaved: {FINAL_TEST_STATISTICS_PATH}")


if __name__ == "__main__":
    main()
