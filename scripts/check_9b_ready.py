from __future__ import annotations

import json
from pathlib import Path

from bolt_thesis.clients.vllm import VLLMClient
from bolt_thesis.final_test import sha256_file
from bolt_thesis.paths import (
    EXPERIMENT_LOCK_PATH,
    FINAL_TEST_DATASET_PATH,
    MODEL_QWEN3_5_9B_CONFIG_PATH,
    MODEL_SCALE_4B_DIR,
    MODEL_SCALE_9B_DIR,
)

EXPECTED_MODEL = "Qwen/Qwen3.5-9B"
REQUIRED_4B_FILES = (
    "system_a_final_test.json",
    "system_b_final_test.json",
    "system_c_final_test.json",
    "final_test_unified_evaluation.json",
    "final_test_statistics.json",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    missing = [name for name in REQUIRED_4B_FILES if not (MODEL_SCALE_4B_DIR / name).exists()]
    if missing:
        raise FileNotFoundError(
            "4B archive is incomplete. Run the 4B finalization step first. Missing: "
            + ", ".join(missing)
        )

    lock = load_json(EXPERIMENT_LOCK_PATH)
    expected_dataset_hash = lock["final_test"]["dataset_sha256"]
    actual_dataset_hash = sha256_file(FINAL_TEST_DATASET_PATH)
    if actual_dataset_hash != expected_dataset_hash:
        raise RuntimeError(
            f"Final Test dataset hash mismatch: expected={expected_dataset_hash} actual={actual_dataset_hash}"
        )

    cfg = load_json(MODEL_QWEN3_5_9B_CONFIG_PATH)
    if cfg["model"]["model_id"] != EXPECTED_MODEL:
        raise RuntimeError(f"Unexpected 9B model config: {cfg['model']['model_id']}")

    if MODEL_SCALE_9B_DIR.exists():
        existing = sorted(p.name for p in MODEL_SCALE_9B_DIR.glob("*.json"))
        if existing:
            print(f"WARNING: 9B result directory already contains JSON files: {existing}")

    client = VLLMClient(config_path=MODEL_QWEN3_5_9B_CONFIG_PATH)
    server = client.check_server()
    if not server["model_available"]:
        raise RuntimeError(
            "9B server is not ready. Expected Qwen/Qwen3.5-9B at "
            f"{client.base_url}; served={server['served_models']}"
        )

    print("4B archive: OK")
    print(f"Final Test SHA256: {actual_dataset_hash}")
    print(f"Requested model: {EXPECTED_MODEL}")
    print(f"Served models: {server['served_models']}")
    print("READY")


if __name__ == "__main__":
    main()
