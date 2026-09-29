from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

from bolt_thesis.paths import MODEL_CONFIG_PATH, SYSTEM_B_SCHEMA_PATH
from bolt_thesis.system_b.prompt import build_system_b_prompt, build_user_prompt


class SystemBVLLMClient:
    def __init__(
        self,
        config_path: str | Path = MODEL_CONFIG_PATH,
        schema_path: str | Path = SYSTEM_B_SCHEMA_PATH,
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
        self.max_tokens = 256

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=server_cfg.get("api_key", "EMPTY"),
        )
        self.system_prompt = build_system_b_prompt()

    def check_server(self) -> dict[str, Any]:
        models = self.client.models.list()
        ids = [item.id for item in models.data]
        return {
            "served_models": ids,
            "requested_model": self.model_id,
            "model_available": self.model_id in ids,
        }

    def generate(self, text: str) -> dict[str, Any]:
        started = time.perf_counter()

        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": build_user_prompt(text)},
            ],
            temperature=self.temperature,
            seed=self.seed,
            max_tokens=self.max_tokens,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "system_b_direct_output",
                    "schema": self.schema,
                },
            },
        )

        latency = time.perf_counter() - started
        usage = response.usage

        return {
            "raw_output": (response.choices[0].message.content or "").strip(),
            "latency_sec": latency,
            "input_tokens": int(usage.prompt_tokens) if usage else None,
            "output_tokens": int(usage.completion_tokens) if usage else None,
            "finish_reason": response.choices[0].finish_reason,
        }
