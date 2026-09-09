from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from bolt_thesis.clients.vllm import VLLMClient
from bolt_thesis.evaluation.system_a import evaluate_system_a_run
from bolt_thesis.paths import DEFAULT_SYSTEM_A_RESULT_PATH, SYSTEM_A_RUN_TEMPLATE_PATH


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str | Path, data: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run System A Pilot with vLLM")
    parser.add_argument("--output", default=str(DEFAULT_SYSTEM_A_RESULT_PATH))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    output_path = Path(args.output)

    if args.resume and output_path.exists():
        run_data = load_json(output_path)
    else:
        run_data = load_json(SYSTEM_A_RUN_TEMPLATE_PATH)

    client = VLLMClient()
    server = client.check_server()

    if not server["model_available"]:
        raise RuntimeError(
            f"vLLM server does not serve {client.model_id!r}: "
            f"{server['served_models']}"
        )

    run_data["run_metadata"].update(
        {
            "backend": "vllm",
            "api_style": "openai_chat_completions",
            "base_url": client.base_url,
            "model": client.model_id,
            "temperature": client.temperature,
            "seed": client.seed,
            "max_tokens": client.max_tokens,
            "structured_output": client.structured_output,
            "quantization": None,
        }
    )

    items = run_data["items"][: args.limit] if args.limit else run_data["items"]
    started_all = time.perf_counter()

    for index, item in enumerate(items, start=1):
        if args.resume and item.get("model_output_raw") is not None:
            print(f"[{index}/{len(items)}] {item['id']} SKIP")
            continue

        print(f"[{index}/{len(items)}] {item['id']} ...", flush=True)

        try:
            generated = client.generate(item["text"])
            item["model_output_raw"] = generated["raw_output"]
            item["latency_sec"] = generated["latency_sec"]
            item["input_tokens"] = generated["input_tokens"]
            item["output_tokens"] = generated["output_tokens"]
            item["finish_reason"] = generated["finish_reason"]
            item["error"] = None
        except Exception as exc:
            item["error"] = f"{type(exc).__name__}: {exc}"

        save_json(output_path, run_data)

    run_data["run_metadata"]["wall_time_sec"] = time.perf_counter() - started_all
    evaluated = evaluate_system_a_run(run_data)
    evaluated["summary"]["structured_output"] = client.structured_output
    save_json(output_path, evaluated)

    print(json.dumps(evaluated["summary"], ensure_ascii=False, indent=2))
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
