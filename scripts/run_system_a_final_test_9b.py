from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from bolt_thesis.clients.vllm import VLLMClient
from bolt_thesis.evaluation.common import evaluate_run_common
from bolt_thesis.evaluation.system_a import evaluate_system_a_run
from bolt_thesis.final_test import build_system_a_run, load_final_test_dataset, sha256_file
from bolt_thesis.paths import (
    EXPERIMENT_LOCK_PATH,
    FINAL_TEST_DATASET_PATH,
    MODEL_QWEN3_5_9B_CONFIG_PATH,
    MODEL_SCALE_4B_DIR,
    SYSTEM_A_9B_FINAL_TEST_RESULT_PATH,
)

EXPECTED_MODEL = "Qwen/Qwen3.5-9B"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run post-hoc System A Final Test with Qwen3.5-9B")
    parser.add_argument("--output", default=str(SYSTEM_A_9B_FINAL_TEST_RESULT_PATH))
    parser.add_argument("--resume", action="store_true", help="Resume only an interrupted infrastructure run")
    parser.add_argument("--limit", type=int, default=None, help="Debug only; never use for the canonical 9B scale run")
    args = parser.parse_args()

    output = Path(args.output)
    if output.exists() and not args.resume:
        raise FileExistsError(
            f"Refusing to overwrite existing 9B result: {output}. "
            "Use --resume only for an interrupted run; do not rerun a completed canonical scale experiment."
        )
    if not (MODEL_SCALE_4B_DIR / "system_a_final_test.json").exists():
        raise FileNotFoundError("4B System A archive is missing; finalize 4B before running 9B.")

    dataset = load_final_test_dataset()
    run = load_json(output) if args.resume and output.exists() else build_system_a_run(dataset)

    client = VLLMClient(config_path=MODEL_QWEN3_5_9B_CONFIG_PATH)
    if client.model_id != EXPECTED_MODEL:
        raise RuntimeError(f"9B config points to unexpected model: {client.model_id}")
    server = client.check_server()
    if not server["model_available"]:
        raise RuntimeError(f"Expected 9B model is not served: {server}")

    run["run_metadata"].update(
        {
            "analysis_role": "post_hoc_model_scale_sensitivity",
            "comparison_baseline": "Qwen/Qwen3.5-4B",
            "base_url": client.base_url,
            "model": client.model_id,
            "temperature": client.temperature,
            "seed": client.seed,
            "max_tokens": client.max_tokens,
            "structured_output": client.structured_output,
            "dataset_sha256": sha256_file(FINAL_TEST_DATASET_PATH),
            "primary_4b_lock_sha256": sha256_file(EXPERIMENT_LOCK_PATH),
        }
    )

    items = run["items"][: args.limit] if args.limit else run["items"]
    started = time.perf_counter()
    for index, item in enumerate(items, start=1):
        if args.resume and item.get("model_output_raw") is not None:
            print(f"[{index}/{len(items)}] {item['id']} SKIP")
            continue
        print(f"[{index}/{len(items)}] {item['id']} ...", flush=True)
        try:
            generated = client.generate(item["text"])
            item.update(
                {
                    "model_output_raw": generated["raw_output"],
                    "latency_sec": generated["latency_sec"],
                    "input_tokens": generated["input_tokens"],
                    "output_tokens": generated["output_tokens"],
                    "finish_reason": generated["finish_reason"],
                    "error": None,
                }
            )
        except Exception as exc:
            item["error"] = f"{type(exc).__name__}: {exc}"
        save_json(output, run)

    run["run_metadata"]["wall_time_sec"] = time.perf_counter() - started
    evaluated = evaluate_system_a_run(run)
    evaluated["summary"]["structured_output"] = client.structured_output
    evaluated = evaluate_run_common(evaluated, "A")
    save_json(output, evaluated)
    print(json.dumps(evaluated["common_summary"], ensure_ascii=False, indent=2))
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
