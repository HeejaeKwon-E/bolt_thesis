from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

from bolt_thesis.extractor.prompt import (
    build_system_prompt,
    build_user_prompt,
    load_prompt_config,
)
from bolt_thesis.paths import EXTRACTOR_SCHEMA_PATH, MODEL_CONFIG_PATH


class VLLMClient:
    def __init__(
        self,
        config_path: str | Path = MODEL_CONFIG_PATH,
        schema_path: str | Path = EXTRACTOR_SCHEMA_PATH,
    ) -> None:
        with Path(config_path).open("r", encoding="utf-8") as f:
            self.config: dict[str, Any] = json.load(f)

        with Path(schema_path).open("r", encoding="utf-8") as f:
            self.schema: dict[str, Any] = json.load(f)

        self.model_id = self.config["model"]["model_id"]
        server_cfg = self.config["vllm_server"]
        generation_cfg = self.config["generation"]

        self.base_url = server_cfg["base_url"]
        self.seed = int(generation_cfg["seed"])
        self.temperature = float(generation_cfg["temperature"])
        self.max_tokens = int(generation_cfg["max_tokens"])
        self.structured_output = bool(generation_cfg["structured_output"])

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=server_cfg.get("api_key", "EMPTY"),
        )

        self.system_prompt = build_system_prompt(load_prompt_config())

    def check_server(self) -> dict[str, Any]:
        models = self.client.models.list()
        ids = [item.id for item in models.data]

        return {
            "base_url": self.base_url,
            "served_models": ids,
            "requested_model": self.model_id,
            "model_available": self.model_id in ids,
        }

    def generate(self, text: str) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": build_user_prompt(text)},
            ],
            "temperature": self.temperature,
            "seed": self.seed,
            "max_tokens": self.max_tokens,
        }

        if self.structured_output:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "bolt_attribute_extraction",
                    "schema": self.schema,
                },
            }

        started = time.perf_counter()
        response = self.client.chat.completions.create(**kwargs)
        latency_sec = time.perf_counter() - started

        usage = response.usage
        message = response.choices[0].message

        return {
            "raw_output": (message.content or "").strip(),
            "latency_sec": latency_sec,
            "input_tokens": int(usage.prompt_tokens) if usage else None,
            "output_tokens": int(usage.completion_tokens) if usage else None,
            "finish_reason": response.choices[0].finish_reason,
        }
