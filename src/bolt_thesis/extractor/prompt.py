from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bolt_thesis.paths import EXTRACTOR_PROMPT_PATH


def load_prompt_config(
    path: str | Path = EXTRACTOR_PROMPT_PATH,
) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def build_system_prompt(config: dict[str, Any]) -> str:
    parts = [config["system_instruction"], "", "규칙:"]

    for index, rule in enumerate(config["rules"], start=1):
        parts.append(f"{index}. {rule}")

    parts.extend(["", "예시:"])

    for example in config["few_shot_examples"]:
        parts.append(f"입력: {example['input']}")
        parts.append(
            "출력: "
            + json.dumps(example["output"], ensure_ascii=False, separators=(",", ":"))
        )
        parts.append("")

    return "\n".join(parts).strip()


def build_user_prompt(text: str) -> str:
    return f"다음 개발의뢰에서 속성을 추출하라.\n입력: {text}"
