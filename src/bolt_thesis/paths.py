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
VALIDATION_SYSTEM_A_RUN_TEMPLATE_PATH = DATA_DIR / "validation" / "system_a_run_template.json"
DEFAULT_SYSTEM_A_VALIDATION_RESULT_PATH = RESULTS_DIR / "system_a_validation.json"
