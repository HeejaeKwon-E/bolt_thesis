from __future__ import annotations

import json
import time

from bolt_thesis.evaluation.common import evaluate_run_common
from bolt_thesis.final_test import load_final_test_dataset, sha256_file
from bolt_thesis.paths import (
    DEFAULT_SYSTEM_C_FINAL_TEST_RESULT_PATH,
    EXPERIMENT_LOCK_PATH,
    FINAL_TEST_DATASET_PATH,
)
from bolt_thesis.rule_engine import RuleEngine
from bolt_thesis.system_c import RegexDictionaryExtractor


def main() -> None:
    dataset = load_final_test_dataset()
    extractor = RegexDictionaryExtractor()
    engine = RuleEngine()

    run = {
        "run_metadata": {
            "system": "C",
            "component": "REGEX_DICTIONARY_EXTRACTOR_PLUS_RULE_ENGINE",
            "dataset": dataset["dataset_name"],
            "split": "final_test",
            "final_test": True,
            "config_version": extractor.config["version"],
            "deterministic": True,
            "uses_llm": False,
            "dataset_sha256": sha256_file(FINAL_TEST_DATASET_PATH),
            "experiment_lock_sha256": sha256_file(EXPERIMENT_LOCK_PATH),
        },
        "items": [],
    }

    started_all = time.perf_counter()
    for index, item in enumerate(dataset["items"], start=1):
        print(f"[{index}/{len(dataset['items'])}] {item['id']} ...", flush=True)
        started = time.perf_counter()
        attrs = extractor.extract(item["text"])
        result = engine.run(attrs)
        raw = json.dumps(attrs, ensure_ascii=False, separators=(",", ":"))
        run["items"].append(
            {
                "id": item["id"],
                "condition": item["condition"],
                "variation_tags": item.get("variation_tags", []),
                "text": item["text"],
                "ground_truth_attributes": item["ground_truth"]["attributes"],
                "system_output_raw": raw,
                "model_output_raw": raw,
                "parsed_attributes": attrs,
                "pipeline_result": {"attributes": attrs, "result": result},
                "latency_sec": time.perf_counter() - started,
                "error": None,
            }
        )

    run["run_metadata"]["wall_time_sec"] = time.perf_counter() - started_all
    evaluated = evaluate_run_common(run, "C")
    DEFAULT_SYSTEM_C_FINAL_TEST_RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_SYSTEM_C_FINAL_TEST_RESULT_PATH.write_text(
        json.dumps(evaluated, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(evaluated["common_summary"], ensure_ascii=False, indent=2))
    print(f"Saved: {DEFAULT_SYSTEM_C_FINAL_TEST_RESULT_PATH}")


if __name__ == "__main__":
    main()
