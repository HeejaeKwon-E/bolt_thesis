from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bolt_thesis.paths import (
    EXTRACTOR_PROMPT_PATH,
    RULES_PATH,
    SYSTEM_B_PROMPT_PATH,
)
from bolt_thesis.rule_engine import RuleEngine


def _load(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def _condition_to_text(condition: dict[str, Any]) -> str:
    if condition.get("always") is True:
        return "항상"

    if "all" in condition:
        return " AND ".join(
            f"({_condition_to_text(item)})" for item in condition["all"]
        )

    if "any" in condition:
        return " OR ".join(f"({_condition_to_text(item)})" for item in condition["any"])

    field = condition["field"]
    op = condition["op"]
    value = condition["value"]

    if op == "in":
        return f"{field} IN {json.dumps(value, ensure_ascii=False)}"

    return f"{field} {op} {json.dumps(value, ensure_ascii=False)}"


def _action_to_text(action: dict[str, Any]) -> str:
    if action["type"] == "SET_MATERIAL":
        return f"material = {action['value']}"
    if action["type"] == "ADD_OPERATION":
        return f"routing에 {action['value']} 추가"
    raise ValueError(f"Unsupported action: {action}")


def _build_few_shot_examples() -> list[dict[str, Any]]:
    extractor = _load(EXTRACTOR_PROMPT_PATH)
    engine = RuleEngine()

    examples = []
    for example in extractor["few_shot_examples"]:
        final = engine.run(example["output"])
        if final["status"] == "OK":
            output = {
                "status": "OK",
                "material": final["material"],
                "routing": final["routing"],
                "required_fields": [],
            }
        else:
            output = {
                "status": "CLARIFICATION_REQUIRED",
                "material": None,
                "routing": [],
                "required_fields": final["required_fields"],
            }
        examples.append({"input": example["input"], "output": output})

    return examples


def build_system_b_prompt() -> str:
    cfg = _load(SYSTEM_B_PROMPT_PATH)
    extractor = _load(EXTRACTOR_PROMPT_PATH)
    rules = _load(RULES_PATH)

    parts: list[str] = [cfg["system_instruction"], ""]

    parts.append("필수정보 처리:")
    for idx, rule in enumerate(cfg["required_field_policy"], start=1):
        parts.append(f"{idx}. {rule}")

    # A의 입력 정규화 지침 중 출력 형식 관련 항목은 제외하고 의미 해석 지침만 동일하게 제공.
    parts.extend(["", "입력 표현 정규화 지침(System A와 동일):"])
    normalization_rules = [
        rule
        for rule in extractor["rules"]
        if not any(
            phrase in rule
            for phrase in (
                "추출 대상은",
                "다른 정보는 출력하지 않는다",
                "JSON 객체만 반환",
            )
        )
    ]
    for idx, rule in enumerate(normalization_rules, start=1):
        parts.append(f"{idx}. {rule}")

    parts.extend(["", "제조 규칙(rules.json과 동일):"])
    for rule in rules["rules"]:
        cond = _condition_to_text(rule["condition"])
        actions = ", ".join(_action_to_text(a) for a in rule["actions"])
        parts.append(f"{rule['id']}: IF {cond} THEN {actions}")

    parts.append("")
    parts.append("Routing 출력 순서:")
    parts.append(" -> ".join(rules["routing_order"]))

    parts.extend(["", "출력 규칙:"])
    for idx, rule in enumerate(cfg["output_policy"], start=1):
        parts.append(f"{idx}. {rule}")

    parts.extend(["", "Few-shot 예시(System A와 동일한 입력 5개):"])
    for ex in _build_few_shot_examples():
        parts.append(f"입력: {ex['input']}")
        parts.append(
            "출력: "
            + json.dumps(ex["output"], ensure_ascii=False, separators=(",", ":"))
        )
        parts.append("")

    return "\n".join(parts).strip()


def build_user_prompt(text: str) -> str:
    return f"다음 개발의뢰를 처리하라.\n입력: {text}"
