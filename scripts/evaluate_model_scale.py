from __future__ import annotations

import json
import math
import random
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable

from bolt_thesis.paths import (
    MODEL_SCALE_4B_DIR,
    MODEL_SCALE_9B_DIR,
    MODEL_SCALE_COMPARISON_JSON_PATH,
    MODEL_SCALE_COMPARISON_MD_PATH,
)

BOOTSTRAP_ITERATIONS = 10_000
BOOTSTRAP_SEED = 42


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def exact_mcnemar_p(left_only: int, right_only: int) -> float:
    n = left_only + right_only
    if n == 0:
        return 1.0
    k = min(left_only, right_only)
    cumulative = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2.0 * cumulative)


def percentile(values: list[float], q: float) -> float:
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return values[lo]
    frac = pos - lo
    return values[lo] * (1 - frac) + values[hi] * frac


def paired_bootstrap_ci(left: list[bool], right: list[bool]) -> tuple[float, float]:
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(left)
    diffs: list[float] = []
    for _ in range(BOOTSTRAP_ITERATIONS):
        delta = 0
        for _ in range(n):
            i = rng.randrange(n)
            delta += int(right[i]) - int(left[i])
        diffs.append(delta / n)
    return percentile(diffs, 0.025), percentile(diffs, 0.975)


def paired_compare(b4: list[bool], b9: list[bool]) -> dict[str, Any]:
    if len(b4) != len(b9) or not b4:
        raise ValueError("Paired vectors must be equal and non-empty")
    four_only = sum(a and not b for a, b in zip(b4, b9))
    nine_only = sum((not a) and b for a, b in zip(b4, b9))
    ci = paired_bootstrap_ci(b4, b9)
    return {
        "n": len(b4),
        "rate_4b": sum(b4) / len(b4),
        "rate_9b": sum(b9) / len(b9),
        "difference_9b_minus_4b": sum(b9) / len(b9) - sum(b4) / len(b4),
        "bootstrap_95_ci_difference": [ci[0], ci[1]],
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "mcnemar": {
            "4b_only_success": four_only,
            "9b_only_success": nine_only,
            "discordant_pairs": four_only + nine_only,
            "exact_two_sided_p": exact_mcnemar_p(four_only, nine_only),
        },
    }


def by_id(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in run["items"]}


def metric_vector(
    run: dict[str, Any],
    key: str,
    *,
    condition: set[str] | None = None,
    transform: Callable[[Any], bool] | None = None,
) -> tuple[list[str], list[bool]]:
    ids, values = [], []
    for item in run["items"]:
        if condition is not None and item["condition"] not in condition:
            continue
        value = item["common_evaluation"].get(key)
        if value is None:
            raise ValueError(f"Metric {key} unavailable on {item['id']}")
        ids.append(item["id"])
        values.append(transform(value) if transform else bool(value))
    return ids, values


def paired_metric(
    run4: dict[str, Any],
    run9: dict[str, Any],
    key: str,
    *,
    condition: set[str] | None = None,
    transform: Callable[[Any], bool] | None = None,
) -> dict[str, Any]:
    ids4, v4 = metric_vector(run4, key, condition=condition, transform=transform)
    ids9, v9 = metric_vector(run9, key, condition=condition, transform=transform)
    if ids4 != ids9:
        raise ValueError(f"Item alignment mismatch for metric {key}")
    result = paired_compare(v4, v9)
    result["metric"] = key
    return result


def latency_summary(run: dict[str, Any]) -> dict[str, float | int | None]:
    vals = [float(i["latency_sec"]) for i in run["items"] if i.get("latency_sec") is not None]
    if not vals:
        return {"n": 0, "mean_sec": None, "median_sec": None}
    return {"n": len(vals), "mean_sec": mean(vals), "median_sec": median(vals)}


def validate_runs(run4: dict[str, Any], run9: dict[str, Any], system: str) -> None:
    if run4["run_metadata"].get("model") != "Qwen/Qwen3.5-4B":
        raise RuntimeError(f"{system} 4B baseline has unexpected model")
    if run9["run_metadata"].get("model") != "Qwen/Qwen3.5-9B":
        raise RuntimeError(f"{system} 9B run has unexpected model")
    if run4["run_metadata"].get("dataset_sha256") != run9["run_metadata"].get("dataset_sha256"):
        raise RuntimeError(f"{system}: 4B/9B dataset hashes differ")
    ids4 = [i["id"] for i in run4["items"]]
    ids9 = [i["id"] for i in run9["items"]]
    if ids4 != ids9:
        raise RuntimeError(f"{system}: item IDs/order differ between 4B and 9B")
    if run9["common_summary"].get("not_run") != 0:
        raise RuntimeError(f"{system}: 9B run is incomplete")


def main() -> None:
    paths = {
        "A4": MODEL_SCALE_4B_DIR / "system_a_final_test.json",
        "B4": MODEL_SCALE_4B_DIR / "system_b_final_test.json",
        "A9": MODEL_SCALE_9B_DIR / "system_a_final_test.json",
        "B9": MODEL_SCALE_9B_DIR / "system_b_final_test.json",
    }
    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing model-scale result(s):\n" + "\n".join(missing))

    a4, b4, a9, b9 = (load_json(paths[k]) for k in ("A4", "B4", "A9", "B9"))
    validate_runs(a4, a9, "A")
    validate_runs(b4, b9, "B")

    comparisons: dict[str, Any] = {
        "analysis_role": "post_hoc_model_scale_sensitivity",
        "models": {"baseline": "Qwen/Qwen3.5-4B", "larger": "Qwen/Qwen3.5-9B"},
        "dataset_sha256": a4["run_metadata"]["dataset_sha256"],
        "systems": {},
        "cross_system_gap": {},
        "method": {
            "paired_test": "two-sided exact McNemar",
            "bootstrap": "paired nonparametric bootstrap of 9B-4B accuracy difference",
            "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
    }

    for system, r4, r9 in (("A", a4, a9), ("B", b4, b9)):
        s4, s9 = r4["common_summary"], r9["common_summary"]
        sys: dict[str, Any] = {
            "summary_4b": s4,
            "summary_9b": s9,
            "delta_9b_minus_4b": {
                "final_task_success_rate": s9["final_task_success_rate"] - s4["final_task_success_rate"],
                "material_accuracy_on_sufficient": s9["material_accuracy_on_sufficient"] - s4["material_accuracy_on_sufficient"],
                "routing_exact_rate_on_sufficient": s9["routing_exact_rate_on_sufficient"] - s4["routing_exact_rate_on_sufficient"],
                "required_fields_accuracy_on_missing": s9["required_fields_accuracy_on_missing"] - s4["required_fields_accuracy_on_missing"],
                "dangerous_guess_rate_on_missing": s9["dangerous_guess_rate_on_missing"] - s4["dangerous_guess_rate_on_missing"],
                "over_clarification_rate_on_sufficient": s9["over_clarification_rate_on_sufficient"] - s4["over_clarification_rate_on_sufficient"],
            },
            "paired_statistics": {
                "final_task_success": paired_metric(r4, r9, "final_task_success"),
                "routing_exact_sufficient": paired_metric(r4, r9, "routing_exact", condition={"NORMAL", "VARIANT"}),
                "required_fields_correct_missing": paired_metric(r4, r9, "required_fields_correct", condition={"MISSING"}),
                "no_dangerous_guess_missing": paired_metric(r4, r9, "dangerous_guess", condition={"MISSING"}, transform=lambda x: not bool(x)),
            },
            "latency_descriptive": {"4b": latency_summary(r4), "9b": latency_summary(r9)},
            "final_task_success_by_condition": {},
        }
        if system == "A":
            sys["delta_9b_minus_4b"]["attribute_exact_rate"] = s9["attribute_exact_rate"] - s4["attribute_exact_rate"]
            sys["paired_statistics"]["attribute_exact"] = paired_metric(r4, r9, "attribute_exact")
        for condition in ("NORMAL", "VARIANT", "MISSING"):
            c4 = r4["common_summary_by_condition"][condition]
            c9 = r9["common_summary_by_condition"][condition]
            sys["final_task_success_by_condition"][condition] = {
                "4b": c4["final_task_success_rate"],
                "9b": c9["final_task_success_rate"],
                "delta_9b_minus_4b": c9["final_task_success_rate"] - c4["final_task_success_rate"],
            }
        comparisons["systems"][system] = sys

    for label, a, b in (("4b", a4, b4), ("9b", a9, b9)):
        sa, sb = a["common_summary"], b["common_summary"]
        comparisons["cross_system_gap"][label] = {
            "A_minus_B_final_task_success": sa["final_task_success_rate"] - sb["final_task_success_rate"],
            "A_minus_B_routing_exact_sufficient": sa["routing_exact_rate_on_sufficient"] - sb["routing_exact_rate_on_sufficient"],
        }

    MODEL_SCALE_COMPARISON_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_SCALE_COMPARISON_JSON_PATH.write_text(
        json.dumps(comparisons, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    def pct(x: float) -> str:
        return f"{x * 100:.1f}%"

    lines = [
        "# Qwen3.5 4B vs 9B 모델 규모 추가 분석",
        "",
        "> 본 분석은 4B 본 실험 완료 후 수행하는 post-hoc model-scale sensitivity analysis이다.",
        "> Final Test, 프롬프트, 규칙, 스키마, 평가 기준은 변경하지 않고 모델 ID만 4B→9B로 변경한다.",
        "",
        "## 핵심 성능",
        "",
        "| System | Metric | 4B | 9B | Δ(9B-4B) |",
        "|---|---|---:|---:|---:|",
    ]
    metric_rows = [
        ("A", "Final Task Success", "final_task_success_rate"),
        ("A", "Attribute Exact", "attribute_exact_rate"),
        ("A", "Routing Exact (sufficient)", "routing_exact_rate_on_sufficient"),
        ("B", "Final Task Success", "final_task_success_rate"),
        ("B", "Routing Exact (sufficient)", "routing_exact_rate_on_sufficient"),
        ("B", "Material Accuracy (sufficient)", "material_accuracy_on_sufficient"),
        ("B", "Required Fields (missing)", "required_fields_accuracy_on_missing"),
    ]
    for system, label, key in metric_rows:
        x = comparisons["systems"][system]
        v4 = x["summary_4b"][key]
        v9 = x["summary_9b"][key]
        lines.append(f"| {system} | {label} | {pct(v4)} | {pct(v9)} | {v9-v4:+.1%} |")

    lines += ["", "## Paired 통계", ""]
    for system in ("A", "B"):
        lines.append(f"### System {system}")
        lines.append("")
        for metric, r in comparisons["systems"][system]["paired_statistics"].items():
            ci = r["bootstrap_95_ci_difference"]
            lines.append(
                f"- **{metric}**: 4B={pct(r['rate_4b'])}, 9B={pct(r['rate_9b'])}, "
                f"Δ={r['difference_9b_minus_4b']:+.1%}, 95% CI=[{ci[0]:+.1%}, {ci[1]:+.1%}], "
                f"McNemar p={r['mcnemar']['exact_two_sided_p']:.6g}"
            )
        lines.append("")

    gap4 = comparisons["cross_system_gap"]["4b"]
    gap9 = comparisons["cross_system_gap"]["9b"]
    lines += [
        "## A-B 구조적 격차",
        "",
        f"- Final Task Success 격차: 4B {gap4['A_minus_B_final_task_success']:+.1%}p → 9B {gap9['A_minus_B_final_task_success']:+.1%}p",
        f"- Routing Exact 격차: 4B {gap4['A_minus_B_routing_exact_sufficient']:+.1%}p → 9B {gap9['A_minus_B_routing_exact_sufficient']:+.1%}p",
        "",
        "## 해석 주의",
        "",
        "- 9B 실험은 본 실험 종료 후 계획된 추가 분석이므로 탐색적 결과로 보고한다.",
        "- 동일 Final Test를 재사용하므로 9B 결과는 독립적인 새 테스트셋 성능 추정치가 아니라 모델 규모 민감도 분석이다.",
        "- latency는 동일 서버/하드웨어 조건에서의 기술적 참고 지표이며 주 연구가설의 검정 지표가 아니다.",
        "",
    ]
    MODEL_SCALE_COMPARISON_MD_PATH.write_text("\n".join(lines), encoding="utf-8")

    print("MODEL SCALE: Qwen3.5-4B vs Qwen3.5-9B")
    for system in ("A", "B"):
        s = comparisons["systems"][system]
        print(
            f"{system}: task {s['summary_4b']['final_task_success_rate']:.4f} -> "
            f"{s['summary_9b']['final_task_success_rate']:.4f} "
            f"({s['delta_9b_minus_4b']['final_task_success_rate']:+.4f})"
        )
        print(
            f"   routing {s['summary_4b']['routing_exact_rate_on_sufficient']:.4f} -> "
            f"{s['summary_9b']['routing_exact_rate_on_sufficient']:.4f} "
            f"({s['delta_9b_minus_4b']['routing_exact_rate_on_sufficient']:+.4f})"
        )
    print(f"Saved: {MODEL_SCALE_COMPARISON_JSON_PATH}")
    print(f"Saved: {MODEL_SCALE_COMPARISON_MD_PATH}")


if __name__ == "__main__":
    main()
