from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from bolt_thesis.paths import (
    ATTRIBUTES_PATH,
    EXPERIMENT_LOCK_PATH,
    FINAL_TEST_DATASET_PATH,
    PILOT_DATASET_PATH,
    VALIDATION_DATASET_PATH,
)
from bolt_thesis.rule_engine import RuleEngine

FIELDS = ("diameter_mm", "length_mm", "strength_grade", "surface_treatment")
EXPECTED_COUNTS = Counter({"NORMAL": 30, "VARIANT": 40, "MISSING": 30})
EXPECTED_VARIANTS = Counter(
    {
        "SYMBOL_SPACE": 8,
        "WORD_ORDER": 8,
        "COLLOQUIAL_KR": 8,
        "KOREAN_ENGLISH_MIX": 8,
        "TYPO_ABBREVIATION": 8,
    }
)
ID_PATTERNS = {
    "NORMAL": re.compile(r"^F-N-\d{3}$"),
    "VARIANT": re.compile(r"^F-V-\d{3}$"),
    "MISSING": re.compile(r"^F-M-\d{3}$"),
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def combo(attrs: dict[str, Any]) -> tuple[Any, ...] | None:
    if any(attrs[field] is None for field in FIELDS):
        return None
    return tuple(attrs[field] for field in FIELDS)


def canonical_expected(engine_output: dict[str, Any]) -> dict[str, Any]:
    # Dataset stores RuleEngine output directly, including applied_rules and
    # routing=None for clarification cases.
    return engine_output


def main() -> None:
    errors: list[str] = []
    dataset = load_json(FINAL_TEST_DATASET_PATH)
    attributes_cfg = load_json(ATTRIBUTES_PATH)["attributes"]
    lock = load_json(EXPERIMENT_LOCK_PATH)
    engine = RuleEngine()

    if dataset.get("is_final_test") is not True:
        errors.append("is_final_test must be true")
    if len(dataset.get("items", [])) != 100:
        errors.append(f"item count must be 100, got {len(dataset.get('items', []))}")

    items = dataset.get("items", [])
    ids = [item.get("id") for item in items]
    texts = [item.get("text") for item in items]
    if len(ids) != len(set(ids)):
        errors.append("duplicate item id")
    if len(texts) != len(set(texts)):
        errors.append("duplicate text")

    condition_counts = Counter(item.get("condition") for item in items)
    if condition_counts != EXPECTED_COUNTS:
        errors.append(f"condition counts mismatch: {condition_counts}")

    variant_counts = Counter(
        item.get("variation_tags", [None])[0]
        for item in items
        if item.get("condition") == "VARIANT"
    )
    if variant_counts != EXPECTED_VARIANTS:
        errors.append(f"variant counts mismatch: {variant_counts}")

    allowed = {field: set(attributes_cfg[field]["values"]) for field in FIELDS}

    single_missing = 0
    double_missing = 0
    final_complete: list[tuple[Any, ...]] = []

    for item in items:
        item_id = item.get("id", "<missing-id>")
        condition = item.get("condition")
        if condition not in ID_PATTERNS:
            errors.append(f"{item_id}: unknown condition {condition!r}")
            continue
        if not ID_PATTERNS[condition].match(item_id):
            errors.append(f"{item_id}: id/condition mismatch")

        attrs = item.get("ground_truth", {}).get("attributes", {})
        if set(attrs) != set(FIELDS):
            errors.append(f"{item_id}: attribute keys mismatch: {sorted(attrs)}")
            continue

        for field in FIELDS:
            value = attrs[field]
            if value is not None and value not in allowed[field]:
                errors.append(f"{item_id}: invalid {field}={value!r}")

        missing = [field for field in FIELDS if attrs[field] is None]
        if condition in {"NORMAL", "VARIANT"}:
            if missing:
                errors.append(f"{item_id}: complete condition contains nulls {missing}")
            else:
                final_complete.append(combo(attrs))
        else:
            if not missing:
                errors.append(f"{item_id}: MISSING case has no missing field")
            if item.get("missing_fields") != missing:
                errors.append(
                    f"{item_id}: missing_fields mismatch: "
                    f"declared={item.get('missing_fields')} actual={missing}"
                )
            if len(missing) == 1:
                single_missing += 1
            elif len(missing) == 2:
                double_missing += 1
            else:
                errors.append(
                    f"{item_id}: expected 1 or 2 missing fields, got {missing}"
                )

        expected = item.get("ground_truth", {}).get("expected_output")
        actual = canonical_expected(engine.run(attrs))
        if expected != actual:
            errors.append(f"{item_id}: expected_output does not match RuleEngine")

    if single_missing != 20 or double_missing != 10:
        errors.append(
            f"missing-case distribution mismatch: single={single_missing}, double={double_missing}"
        )

    if len(final_complete) != 70 or len(set(final_complete)) != 70:
        errors.append(
            f"complete Final Test combinations must be 70 unique, "
            f"got {len(final_complete)} / unique {len(set(final_complete))}"
        )

    development_combos: set[tuple[Any, ...]] = set()
    development_texts: set[str] = set()
    for path in (PILOT_DATASET_PATH, VALIDATION_DATASET_PATH):
        dev = load_json(path)
        for item in dev["items"]:
            development_texts.add(item["text"])
            c = combo(item["ground_truth"]["attributes"])
            if c is not None:
                development_combos.add(c)

    overlap = set(final_complete) & development_combos
    if overlap:
        errors.append(
            f"complete combo overlap with Pilot/Validation: {sorted(overlap)}"
        )

    text_overlap = set(texts) & development_texts
    if text_overlap:
        errors.append(
            f"exact text overlap with Pilot/Validation: {sorted(text_overlap)}"
        )

    # Verify all behavior-affecting frozen artifacts before Final Test execution.
    for rel_path, expected_hash in lock.get("frozen_artifacts_sha256", {}).items():
        artifact = FINAL_TEST_DATASET_PATH.parents[2] / rel_path
        if not artifact.exists():
            errors.append(f"frozen artifact missing: {rel_path}")
            continue
        actual_hash = sha256(artifact)
        if actual_hash != expected_hash:
            errors.append(
                f"frozen artifact SHA mismatch: {rel_path}: "
                f"lock={expected_hash}, actual={actual_hash}"
            )

    dataset_hash = sha256(FINAL_TEST_DATASET_PATH)
    locked_hash = lock.get("final_test", {}).get("dataset_sha256")
    status = lock.get("current_experiment", {}).get("status")
    if status not in {"FROZEN_BEFORE_FINAL_TEST", "COMPLETED_4B_FINAL_TEST"}:
        errors.append(
            "experiment_lock status must be FROZEN_BEFORE_FINAL_TEST or COMPLETED_4B_FINAL_TEST"
        )
    if locked_hash != dataset_hash:
        errors.append(
            f"dataset SHA mismatch: lock={locked_hash!r}, actual={dataset_hash!r}"
        )

    print(f"items: {len(items)}")
    print(f"conditions: {dict(condition_counts)}")
    print(f"variant categories: {dict(variant_counts)}")
    print(f"missing distribution: single={single_missing}, double={double_missing}")
    print(f"development unique complete combos: {len(development_combos)}")
    print(f"final unique complete combos: {len(set(final_complete))}")
    print(f"complete combo overlap: {len(overlap)}")
    print(f"exact text overlap: {len(text_overlap)}")
    print(f"dataset sha256: {dataset_hash}")

    if errors:
        print("\nFAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("\nPASS")


if __name__ == "__main__":
    main()
