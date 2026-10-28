from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

ATTRIBUTES_PATH = CONFIG_DIR / "attributes.json"
RULES_PATH = CONFIG_DIR / "rules.json"
MODEL_CONFIG_PATH = CONFIG_DIR / "model.json"
EXTRACTOR_PROMPT_PATH = CONFIG_DIR / "extractor_prompt.json"
EXTRACTOR_SCHEMA_PATH = CONFIG_DIR / "extractor_schema.json"

PILOT_DATASET_PATH = DATA_DIR / "pilot" / "pilot_dataset.json"
SYSTEM_A_RUN_TEMPLATE_PATH = DATA_DIR / "pilot" / "system_a_run_template.json"
DEFAULT_SYSTEM_A_RESULT_PATH = RESULTS_DIR / "system_a_pilot.json"

VALIDATION_DATASET_PATH = DATA_DIR / "validation" / "validation_dataset.json"
VALIDATION_SYSTEM_A_RUN_TEMPLATE_PATH = (
    DATA_DIR / "validation" / "system_a_run_template.json"
)
DEFAULT_SYSTEM_A_VALIDATION_RESULT_PATH = RESULTS_DIR / "system_a_validation.json"

SYSTEM_B_PROMPT_PATH = CONFIG_DIR / "system_b_prompt.json"
SYSTEM_B_SCHEMA_PATH = CONFIG_DIR / "system_b_schema.json"

SYSTEM_B_PILOT_TEMPLATE_PATH = DATA_DIR / "pilot" / "system_b_run_template.json"
SYSTEM_B_VALIDATION_TEMPLATE_PATH = (
    DATA_DIR / "validation" / "system_b_run_template.json"
)

DEFAULT_SYSTEM_B_PILOT_RESULT_PATH = RESULTS_DIR / "system_b_pilot.json"
DEFAULT_SYSTEM_B_VALIDATION_RESULT_PATH = RESULTS_DIR / "system_b_validation.json"

SYSTEM_C_CONFIG_PATH = CONFIG_DIR / "system_c.json"
DEFAULT_SYSTEM_C_PILOT_RESULT_PATH = RESULTS_DIR / "system_c_pilot.json"
DEFAULT_SYSTEM_C_VALIDATION_RESULT_PATH = RESULTS_DIR / "system_c_validation.json"
FINAL_TEST_DATASET_PATH = DATA_DIR / "final_test" / "final_test_dataset.json"
DEFAULT_SYSTEM_A_FINAL_TEST_RESULT_PATH = RESULTS_DIR / "system_a_final_test.json"
DEFAULT_SYSTEM_B_FINAL_TEST_RESULT_PATH = RESULTS_DIR / "system_b_final_test.json"
DEFAULT_SYSTEM_C_FINAL_TEST_RESULT_PATH = RESULTS_DIR / "system_c_final_test.json"
FINAL_TEST_UNIFIED_RESULT_PATH = RESULTS_DIR / "final_test_unified_evaluation.json"
FINAL_TEST_STATISTICS_PATH = RESULTS_DIR / "final_test_statistics.json"
EXPERIMENT_LOCK_PATH = CONFIG_DIR / "experiment_lock.json"
# Post-hoc model-scale analysis (Qwen3.5-9B)
MODEL_QWEN3_5_9B_CONFIG_PATH = CONFIG_DIR / "model_qwen3_5_9b.json"
MODEL_SCALE_RESULTS_DIR = RESULTS_DIR / "model_scale"
MODEL_SCALE_4B_DIR = MODEL_SCALE_RESULTS_DIR / "qwen3_5_4b"
MODEL_SCALE_9B_DIR = MODEL_SCALE_RESULTS_DIR / "qwen3_5_9b"
SYSTEM_A_9B_FINAL_TEST_RESULT_PATH = MODEL_SCALE_9B_DIR / "system_a_final_test.json"
SYSTEM_B_9B_FINAL_TEST_RESULT_PATH = MODEL_SCALE_9B_DIR / "system_b_final_test.json"
MODEL_SCALE_COMPARISON_JSON_PATH = MODEL_SCALE_RESULTS_DIR / "qwen3_5_4b_vs_9b.json"
MODEL_SCALE_COMPARISON_MD_PATH = MODEL_SCALE_RESULTS_DIR / "qwen3_5_4b_vs_9b.md"

