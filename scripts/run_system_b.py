from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from bolt_thesis.clients.vllm_system_b import SystemBVLLMClient
from bolt_thesis.evaluation.system_b import evaluate_system_b_run
from bolt_thesis.paths import (
    DEFAULT_SYSTEM_B_PILOT_RESULT_PATH,
    DEFAULT_SYSTEM_B_VALIDATION_RESULT_PATH,
    SYSTEM_B_PILOT_TEMPLATE_PATH,
    SYSTEM_B_VALIDATION_TEMPLATE_PATH,
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run System B")
    parser.add_argument("--split", choices=["pilot", "validation"], required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.split == "pilot":
        template_path = SYSTEM_B_PILOT_TEMPLATE_PATH
        default_output = DEFAULT_SYSTEM_B_PILOT_RESULT_PATH
    else:
        template_path = SYSTEM_B_VALIDATION_TEMPLATE_PATH
        default_output = DEFAULT_SYSTEM_B_VALIDATION_RESULT_PATH

    output_path = Path(args.output) if args.output else default_output

    if args.resume and output_path.exists():
        run_data = load_json(output_path)
    else:
        run_data = load_json(template_path)

    client = SystemBVLLMClient()
    server = client.check_server()
    if not server["model_available"]:
        raise RuntimeError(f"Model not served: {server}")

    run_data["run_metadata"].update(
        {
            "model": client.model_id,
            "base_url": client.base_url,
            "temperature": client.temperature,
            "seed": client.seed,
            "max_tokens": client.max_tokens,
        }
    )

    items = run_data["items"][: args.limit] if args.limit else run_data["items"]
    started = time.perf_counter()

    for idx, item in enumerate(items, start=1):
        if args.resume and item.get("model_output_raw") is not None:
            print(f"[{idx}/{len(items)}] {item['id']} SKIP")
            continue

        print(f"[{idx}/{len(items)}] {item['id']} ...", flush=True)
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

    run_data["run_metadata"]["wall_time_sec"] = time.perf_counter() - started
    evaluated = evaluate_system_b_run(run_data)
    save_json(output_path, evaluated)

    print()
    print(json.dumps(evaluated["summary"], ensure_ascii=False, indent=2))
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
