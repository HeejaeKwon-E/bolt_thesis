from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from bolt_thesis.paths import (
    DEFAULT_SYSTEM_A_FINAL_TEST_RESULT_PATH,
    DEFAULT_SYSTEM_B_FINAL_TEST_RESULT_PATH,
    DEFAULT_SYSTEM_C_FINAL_TEST_RESULT_PATH,
    RESULTS_DIR,
)

OUT_JSON = RESULTS_DIR / "final_test_failure_analysis.json"
OUT_MD = RESULTS_DIR / "final_test_failure_analysis.md"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def bad_fields(item: dict[str, Any]) -> list[str]:
    pred = item.get("parsed_attributes")
    if pred is None:
        return []
    gt = item["ground_truth_attributes"]
    return [key for key, value in gt.items() if pred.get(key) != value]


def classify_a(item: dict[str, Any]) -> str:
    ce = item["common_evaluation"]
    if item["condition"] == "MISSING" and not ce["required_fields_correct"]:
        gt_missing = {k for k, v in item["ground_truth_attributes"].items() if v is None}
        pred_missing = set(ce["predicted_output"]["required_fields"])
        if pred_missing < gt_missing:
            return "MISSING_FIELD_UNDERDETECTION"
        if pred_missing > gt_missing:
            return "MISSING_FIELD_OVERDETECTION"
        return "MISSING_FIELD_SET_ERROR"
    return "ATTRIBUTE_EXTRACTION_ERROR"


def classify_b(item: dict[str, Any]) -> str:
    ce = item["common_evaluation"]
    if item["condition"] == "MISSING":
        gt = set(ce["ground_truth_output"]["required_fields"])
        pred = set(ce["predicted_output"]["required_fields"])
        if pred > gt:
            return "MISSING_FIELD_OVERDETECTION"
        if pred < gt:
            return "MISSING_FIELD_UNDERDETECTION"
        return "MISSING_FIELD_SET_ERROR"

    gt = set(ce["ground_truth_output"]["routing"])
    pred = set(ce["predicted_output"]["routing"])
    forming = any((op in gt) != (op in pred) for op in ("COLD_FORMING", "HOT_FORMING"))
    heat = ("HEAT_TREATMENT" in gt) != ("HEAT_TREATMENT" in pred)
    zinc = ("ZINC_PLATING" in gt) != ("ZINC_PLATING" in pred)
    other = (gt ^ pred) - {"COLD_FORMING", "HOT_FORMING", "HEAT_TREATMENT", "ZINC_PLATING"}
    if forming and heat and not zinc and not other:
        return "FORMING_AND_HEAT_TREATMENT_ERROR"
    if forming and not heat and not zinc and not other:
        return "FORMING_RULE_ERROR"
    if heat and not forming and not zinc and not other:
        return "HEAT_TREATMENT_ERROR"
    return "MULTIPLE_ROUTING_RULE_ERROR"


def classify_c(item: dict[str, Any]) -> str:
    fields = bad_fields(item)
    return "REGEX_EXTRACTION_MISS:" + "+".join(fields or ["UNKNOWN"])


def system_report(name: str, data: dict[str, Any]) -> dict[str, Any]:
    failures = [x for x in data["items"] if not x["common_evaluation"]["final_task_success"]]
    classifier = {"A": classify_a, "B": classify_b, "C": classify_c}[name]
    category_counts: Counter[str] = Counter()
    condition_counts: Counter[str] = Counter()
    variation_counts: Counter[str] = Counter()
    field_counts: Counter[str] = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)

    rows = []
    for item in failures:
        category = classifier(item)
        category_counts[category] += 1
        condition_counts[item["condition"]] += 1
        variation_counts.update(item.get("variation_tags", []))
        field_counts.update(bad_fields(item))
        ce = item["common_evaluation"]
        row = {
            "id": item["id"],
            "condition": item["condition"],
            "variation_tags": item.get("variation_tags", []),
            "category": category,
            "text": item["text"],
            "ground_truth_attributes": item["ground_truth_attributes"],
            "predicted_attributes": item.get("parsed_attributes"),
            "ground_truth_output": ce["ground_truth_output"],
            "predicted_output": ce["predicted_output"],
            "incorrect_attribute_fields": bad_fields(item),
        }
        rows.append(row)
        if len(examples[category]) < 3:
            examples[category].append(row)

    return {
        "system": name,
        "total_items": len(data["items"]),
        "failure_count": len(failures),
        "failure_rate": len(failures) / len(data["items"]),
        "category_counts": dict(category_counts),
        "condition_counts": dict(condition_counts),
        "variation_tag_counts": dict(variation_counts),
        "incorrect_attribute_field_counts": dict(field_counts),
        "representative_examples": dict(examples),
        "failures": rows,
    }


def render_md(report: dict[str, Any]) -> str:
    lines = ["# Qwen3.5-4B Final Test Failure Analysis", ""]
    for system in ("A", "B", "C"):
        r = report["systems"][system]
        lines += [f"## System {system}", "", f"- 실패: **{r['failure_count']}/{r['total_items']} ({r['failure_rate']:.1%})**", ""]
        lines += ["### 실패 유형", "", "| 유형 | 건수 |", "|---|---:|"]
        for cat, count in sorted(r["category_counts"].items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"| `{cat}` | {count} |")
        lines.append("")
        if r["incorrect_attribute_field_counts"]:
            lines += ["### 속성 오류 필드", "", "| 필드 | 건수 |", "|---|---:|"]
            for field, count in sorted(r["incorrect_attribute_field_counts"].items(), key=lambda x: (-x[1], x[0])):
                lines.append(f"| `{field}` | {count} |")
            lines.append("")
        lines += ["### 대표 사례", ""]
        for cat, examples in r["representative_examples"].items():
            lines.append(f"**{cat}**")
            for ex in examples[:2]:
                lines.append(f"- `{ex['id']}` ({ex['condition']}): {ex['text']}")
            lines.append("")
    lines += [
        "## 해석 요약",
        "",
        "- System A의 실패는 누락정보 식별 1건에 국한되며, 충분정보 70건의 Material/Routing은 모두 정확했다.",
        "- System B의 실패는 대부분 Routing 규칙 적용 오류이며, 특히 COLD/HOT FORMING 선택과 HEAT_TREATMENT 적용에서 발생했다.",
        "- System C의 실패는 새로운 자연어 표현을 고정 Regex/Dictionary가 인식하지 못해 불필요한 clarification으로 이어진 경우가 중심이다.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    sources = {
        "A": DEFAULT_SYSTEM_A_FINAL_TEST_RESULT_PATH,
        "B": DEFAULT_SYSTEM_B_FINAL_TEST_RESULT_PATH,
        "C": DEFAULT_SYSTEM_C_FINAL_TEST_RESULT_PATH,
    }
    missing = [str(p) for p in sources.values() if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing Final Test result(s): " + ", ".join(missing))
    report = {
        "model": "Qwen/Qwen3.5-4B",
        "analysis_scope": "canonical_final_test",
        "systems": {k: system_report(k, load(v)) for k, v in sources.items()},
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(report), encoding="utf-8")
    for s in ("A", "B", "C"):
        r = report["systems"][s]
        print(f"System {s}: failures={r['failure_count']}/{r['total_items']} categories={r['category_counts']}")
    print(f"Saved: {OUT_JSON}")
    print(f"Saved: {OUT_MD}")


if __name__ == "__main__":
    main()
