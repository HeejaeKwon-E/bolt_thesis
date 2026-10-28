from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from itertools import product
from pathlib import Path
from typing import Any

from bolt_thesis.paths import (
    ATTRIBUTES_PATH,
    PILOT_DATASET_PATH,
    VALIDATION_DATASET_PATH,
)
from bolt_thesis.rule_engine import RuleEngine

SEED = 20261001
FIELDS = ("diameter_mm", "length_mm", "strength_grade", "surface_treatment")
VARIANT_CATEGORIES = (
    "SYMBOL_SPACE",
    "WORD_ORDER",
    "COLLOQUIAL_KR",
    "KOREAN_ENGLISH_MIX",
    "TYPO_ABBREVIATION",
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "final_test" / "final_test_dataset.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def complete_combo_from_attrs(attrs: dict[str, Any]) -> tuple[Any, ...] | None:
    if any(attrs[field] is None for field in FIELDS):
        return None
    return tuple(attrs[field] for field in FIELDS)


def development_complete_combos() -> set[tuple[Any, ...]]:
    combos: set[tuple[Any, ...]] = set()
    for dataset_path in (PILOT_DATASET_PATH, VALIDATION_DATASET_PATH):
        dataset = load_json(dataset_path)
        for item in dataset["items"]:
            combo = complete_combo_from_attrs(item["ground_truth"]["attributes"])
            if combo is not None:
                combos.add(combo)
    return combos


def balanced_select(
    pool: list[tuple[Any, ...]], n: int, rng: random.Random
) -> tuple[list[tuple[Any, ...]], list[tuple[Any, ...]]]:
    selected: list[tuple[Any, ...]] = []
    counts = [Counter() for _ in range(4)]
    forming_counts: Counter[str] = Counter()
    available = list(pool)

    while len(selected) < n:
        scored = []
        for combo in available:
            score = sum(counts[i][combo[i]] for i in range(4))
            diameter, length, _, _ = combo
            forming = "COLD" if diameter <= 12 and length <= 80 else "HOT"
            score += forming_counts[forming] * 0.25
            scored.append((score, rng.random(), combo))

        _, _, chosen = min(scored, key=lambda row: (row[0], row[1]))
        selected.append(chosen)
        available.remove(chosen)
        for i, value in enumerate(chosen):
            counts[i][value] += 1
        diameter, length, _, _ = chosen
        forming_counts["COLD" if diameter <= 12 and length <= 80 else "HOT"] += 1

    return selected, available


def surface_kr(value: str) -> str:
    return "무도금" if value == "NONE" else "아연도금"


def surface_plain(value: str) -> str:
    return "도금 없이" if value == "NONE" else "아연 처리"


def surface_eng(value: str) -> str:
    return "uncoated" if value == "NONE" else "zinc finish"


def surface_typo(value: str, index: int) -> str:
    if value == "NONE":
        return ("무 도금", "no coarting", "uncoated", "no plating")[index % 4]
    return ("아연 도금", "zinc plted", "zinc finish", "zinc coating")[index % 4]


def normal_text(combo: tuple[Any, ...], index: int) -> str:
    d, l, g, s = combo
    templates = (
        f"육각볼트 신규 개발 요청입니다. M{d}×{l}, 강도 {g}급, 표면처리 {surface_kr(s)} 조건입니다.",
        f"요청 사양: 직경 {d} mm, 길이 {l} mm, 강도등급 {g}, {surface_kr(s)} 육각볼트.",
        f"육각볼트 {d}mm x {l}mm 규격으로 부탁드립니다. 강도는 {g}급이고 마감은 {surface_kr(s)}입니다.",
        f"신규 볼트 사양은 M{d} x {l}이며 property class {g}, 표면은 {surface_kr(s)}입니다.",
        f"개발 검토: Ø{d}, L{l}, {g}급, {surface_kr(s)} 조건의 육각볼트.",
        f"M{d}×{l} 육각볼트 생산 검토 요청. 강도등급 {g}, 표면처리 {surface_kr(s)}.",
    )
    return templates[index % len(templates)]


def variant_text(combo: tuple[Any, ...], category: str, index: int) -> str:
    d, l, g, s = combo

    if category == "SYMBOL_SPACE":
        templates = (
            f"M {d} × {l} / {g}급 / {surface_kr(s)}",
            f"{d} ⌀, {l} mm, class {g}, {surface_eng(s)}",
            f"M-{d} x L-{l}; grade {g}; {surface_eng(s)}",
            f"Ø {d} · {l}L · {g} · {surface_kr(s)}",
            f"{d}Φ / {l} long / G{g} / {surface_eng(s)}",
            f"D={d}mm | L={l}mm | PC={g} | {surface_eng(s)}",
            f"M{d}—{l} ; {g} ; {surface_kr(s)}",
            f"{d}mm⌀ x {l}mm / {g} / {surface_eng(s)}",
        )
    elif category == "WORD_ORDER":
        templates = (
            f"{surface_kr(s)}으로 하고 강도는 {g}급입니다. 길이 {l}mm, 직경 {d}mm 육각볼트 요청.",
            f"강도 {g}, {surface_kr(s)} 조건. 육각볼트 크기는 길이 {l}에 M{d}입니다.",
            f"표면은 {surface_kr(s)}. {l}mm 길이의 {d}mm 직경 볼트이고 등급은 {g}입니다.",
            f"길이는 {l}, 마감 {surface_kr(s)}, 강도등급 {g}, 마지막으로 직경은 {d}mm입니다.",
            f"property class {g} 먼저 적용하고 {surface_kr(s)} 처리, 규격은 {l}L / M{d}.",
            f"{surface_kr(s)} 육각볼트가 필요합니다. {g}급이고 {d}파이, 길이 {l}입니다.",
            f"길이 {l}짜리로 요청하며 표면 {surface_kr(s)}, 직경 {d}, 강도 {g} 조건입니다.",
            f"강도는 {g}로, 사이즈는 L{l}에 Ø{d}, 표면 조건은 {surface_kr(s)}입니다.",
        )
    elif category == "COLLOQUIAL_KR":
        coating = "도금은 안 하고" if s == "NONE" else "아연을 입혀서"
        coating2 = "표면은 그냥 무도금으로" if s == "NONE" else "겉은 아연 처리해서"
        templates = (
            f"굵기 {d}미리에 길이 {l}미리짜리 육각볼트요. 강도 {g}급이고 {coating} 부탁해요.",
            f"{d}미리 굵기, {l}미리 길이로 해주세요. {g}급에 {coating2} 부탁드립니다.",
            f"육각볼트인데 지름 {d}, 길이 {l}짜리고 강도는 {g}. {surface_plain(s)}로 가면 됩니다.",
            f"사이즈는 굵기 {d}에 길이 {l}, 강도 {g}짜리예요. {coating} 주세요.",
            f"{g}급 볼트로요. {d}미리 굵기에 {l} 길이, {coating2} 해주세요.",
            f"지름은 {d}mm, 길이는 {l}mm입니다. {g}급이고 {surface_plain(s)} 조건이에요.",
            f"{d}파이짜리 육각볼트로 길이는 {l}. 강도 {g}급이고 {coating} 진행해주세요.",
            f"볼트 굵기 {d}, 길이 {l}, 강도는 {g}급. 마감은 {surface_plain(s)}면 됩니다.",
        )
    elif category == "KOREAN_ENGLISH_MIX":
        templates = (
            f"dia {d}mm, 길이 {l}mm, property class {g}, finish: {surface_eng(s)}",
            f"직경 {d}, length {l}, grade {g}, surface {surface_eng(s)} 육각볼트",
            f"M{d} with {l} mm length / 강도 {g}급 / finish {surface_eng(s)}",
            f"diameter={d}; L={l}; 강도등급={g}; coating={surface_eng(s)}",
            f"육각 bolt: dia.{d}, {l} long, class {g}, {surface_eng(s)}",
            f"size M{d}, 길이 {l}; strength grade {g}; 표면 {surface_plain(s)}",
            f"D {d} / length {l} / G{g} / finish {surface_eng(s)}",
            f"{g} class hex bolt, 지름 {d}mm x {l}mm, surface: {surface_eng(s)}",
        )
    elif category == "TYPO_ABBREVIATION":
        surface = surface_typo(s, index)
        templates = (
            f"diamter {d}mm / length {l}mm / grade {g} / {surface}",
            f"diameter {d}, lenght {l}, class {g}, {surface}",
            f"M{d}x{l} / grdae {g} / {surface}",
            f"규격 M{d}x{l}, 강도 {g}, 표면 {surface}",
            f"D{d} L{l} G{g} / {surface}",
            f"M{d}*{l}; str grade {g}; finish {surface}",
            f"직경 {d}mm, 길이 {l}mm, {g}급, {surface}",
            f"size {d}x{l}, prop.class {g}, coating {surface}",
        )
    else:
        raise ValueError(f"Unknown variant category: {category}")

    return templates[index % 8]


def missing_text(full: dict[str, Any], missing: tuple[str, ...], index: int) -> str:
    present = []
    if "diameter_mm" not in missing:
        present.append(f"직경 {full['diameter_mm']}mm")
    if "length_mm" not in missing:
        present.append(f"길이 {full['length_mm']}mm")
    if "strength_grade" not in missing:
        present.append(f"강도 {full['strength_grade']}급")
    if "surface_treatment" not in missing:
        present.append(f"표면 {surface_kr(full['surface_treatment'])}")

    labels = {
        "diameter_mm": "직경",
        "length_mm": "길이",
        "strength_grade": "강도등급",
        "surface_treatment": "표면처리",
    }
    missing_kr = [labels[field] for field in missing]

    if index % 3 == 0:
        return (
            "육각볼트 요청: "
            + ", ".join(present)
            + ". "
            + " / ".join(missing_kr)
            + " 정보는 아직 없습니다."
        )
    if index % 3 == 1:
        return (
            ", ".join(present)
            + " 조건입니다. "
            + "와 ".join(missing_kr)
            + "은 확인 중입니다."
        )
    return "개발 요청 - " + "; ".join(present) + ". " + ", ".join(missing_kr) + " TBD."


def main() -> None:
    rng = random.Random(SEED)
    attributes = load_json(ATTRIBUTES_PATH)["attributes"]
    diameters = attributes["diameter_mm"]["values"]
    lengths = attributes["length_mm"]["values"]
    grades = attributes["strength_grade"]["values"]
    surfaces = attributes["surface_treatment"]["values"]

    all_combos = list(product(diameters, lengths, grades, surfaces))
    development_combos = development_complete_combos()
    remaining = [combo for combo in all_combos if combo not in development_combos]

    normal_combos, remaining = balanced_select(remaining, 30, rng)
    variant_combos, remaining = balanced_select(remaining, 40, rng)

    engine = RuleEngine()
    items: list[dict[str, Any]] = []

    for index, combo in enumerate(normal_combos, start=1):
        d, l, g, s = combo
        attrs = {
            "diameter_mm": d,
            "length_mm": l,
            "strength_grade": g,
            "surface_treatment": s,
        }
        items.append(
            {
                "id": f"F-N-{index:03d}",
                "condition": "NORMAL",
                "text": normal_text(combo, index - 1),
                "ground_truth": {
                    "attributes": attrs,
                    "expected_output": engine.run(attrs),
                },
                "variation_tags": ["NATURAL_SENTENCE"],
            }
        )

    for index, combo in enumerate(variant_combos, start=1):
        category = VARIANT_CATEGORIES[(index - 1) // 8]
        within_category = (index - 1) % 8
        d, l, g, s = combo
        attrs = {
            "diameter_mm": d,
            "length_mm": l,
            "strength_grade": g,
            "surface_treatment": s,
        }
        items.append(
            {
                "id": f"F-V-{index:03d}",
                "condition": "VARIANT",
                "text": variant_text(combo, category, within_category),
                "ground_truth": {
                    "attributes": attrs,
                    "expected_output": engine.run(attrs),
                },
                "variation_tags": [category],
            }
        )

    missing_specs: list[tuple[str, ...]] = []
    for field in FIELDS:
        missing_specs.extend([(field,)] * 5)

    pairs = (
        ("diameter_mm", "length_mm"),
        ("diameter_mm", "strength_grade"),
        ("diameter_mm", "surface_treatment"),
        ("length_mm", "strength_grade"),
        ("length_mm", "surface_treatment"),
        ("strength_grade", "surface_treatment"),
    )
    missing_specs.extend(
        (
            pairs[0],
            pairs[1],
            pairs[2],
            pairs[3],
            pairs[4],
            pairs[5],
            pairs[0],
            pairs[3],
            pairs[4],
            pairs[5],
        )
    )

    # Select missing-case bases so the actually visible information is unique.
    # Hidden values must not create duplicate semantic cases.
    shuffled_bases = list(all_combos)
    rng.shuffle(shuffled_bases)
    chosen_missing_bases: list[tuple[Any, ...]] = []
    visible_keys: set[tuple[Any, ...]] = set()
    for missing in missing_specs:
        for candidate in shuffled_bases:
            candidate_map = dict(zip(FIELDS, candidate))
            visible_key = tuple(
                (field, candidate_map[field])
                for field in FIELDS
                if field not in missing
            ) + (("missing", tuple(missing)),)
            if visible_key in visible_keys:
                continue
            visible_keys.add(visible_key)
            chosen_missing_bases.append(candidate)
            break
        else:
            raise AssertionError(f"Could not select unique missing case for {missing}")

    for index, missing in enumerate(missing_specs, start=1):
        d, l, g, s = chosen_missing_bases[index - 1]
        full = {
            "diameter_mm": d,
            "length_mm": l,
            "strength_grade": g,
            "surface_treatment": s,
        }
        attrs = {
            key: (None if key in missing else value) for key, value in full.items()
        }
        items.append(
            {
                "id": f"F-M-{index:03d}",
                "condition": "MISSING",
                "text": missing_text(full, missing, index),
                "ground_truth": {
                    "attributes": attrs,
                    "expected_output": engine.run(attrs),
                },
                "missing_fields": list(missing),
                "variation_tags": [
                    "EXPLICIT_MISSINGNESS" if index % 2 else "MIXED_MISSINGNESS"
                ],
            }
        )

    if len(items) != 100:
        raise AssertionError(f"Expected 100 items, got {len(items)}")
    if len({item["id"] for item in items}) != 100:
        raise AssertionError("Duplicate Final Test IDs")
    if len({item["text"] for item in items}) != 100:
        duplicates = [
            text
            for text, count in Counter(item["text"] for item in items).items()
            if count > 1
        ]
        raise AssertionError(f"Duplicate Final Test texts: {duplicates}")

    condition_counts = Counter(item["condition"] for item in items)
    expected_conditions = Counter({"NORMAL": 30, "VARIANT": 40, "MISSING": 30})
    if condition_counts != expected_conditions:
        raise AssertionError(f"Condition mismatch: {condition_counts}")

    variant_counts = Counter(
        item["variation_tags"][0] for item in items if item["condition"] == "VARIANT"
    )
    expected_variants = Counter({category: 8 for category in VARIANT_CATEGORIES})
    if variant_counts != expected_variants:
        raise AssertionError(f"Variant category mismatch: {variant_counts}")

    final_complete = [
        complete_combo_from_attrs(item["ground_truth"]["attributes"])
        for item in items
        if item["condition"] != "MISSING"
    ]
    if any(combo is None for combo in final_complete):
        raise AssertionError("NORMAL/VARIANT contains missing attribute")
    final_complete_set = set(final_complete)
    if len(final_complete) != 70 or len(final_complete_set) != 70:
        raise AssertionError(
            "Final complete combinations are not 70 unique combinations"
        )
    overlap = final_complete_set & development_combos
    if overlap:
        raise AssertionError(
            f"Final/development combination overlap: {sorted(overlap)}"
        )

    dataset = {
        "dataset_name": "bolt_final_test_v1_0",
        "version": "1.0",
        "purpose": "Frozen unseen final test for A/B/C comparison after development settings are locked.",
        "is_final_test": True,
        "creation_policy": {
            "seed": SEED,
            "condition_counts": {"NORMAL": 30, "VARIANT": 40, "MISSING": 30},
            "variant_categories": {category: 8 for category in VARIANT_CATEGORIES},
            "complete_combo_policy": "70 complete-input combinations are unique and have zero overlap with all complete Pilot/Validation combinations.",
            "missing_policy": "20 single-field missing cases and 10 two-field missing cases.",
            "post_test_tuning_prohibited": True,
        },
        "summary": {
            "total": 100,
            "NORMAL": 30,
            "VARIANT": 40,
            "MISSING": 30,
            "complete_cases": 70,
            "missing_cases": 30,
        },
        "items": items,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    digest = hashlib.sha256(OUTPUT_PATH.read_bytes()).hexdigest()

    print(f"Saved: {OUTPUT_PATH}")
    print(f"sha256: {digest}")
    print(f"development unique complete combos: {len(development_combos)}")
    print(f"final unique complete combos: {len(final_complete_set)}")
    print(f"conditions: {dict(condition_counts)}")
    print(f"variant categories: {dict(variant_counts)}")


if __name__ == "__main__":
    main()
