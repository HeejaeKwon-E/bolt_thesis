from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from bolt_thesis.paths import (
    EXTRACTOR_PROMPT_PATH,
    PILOT_DATASET_PATH,
    VALIDATION_DATASET_PATH,
    VALIDATION_SYSTEM_A_RUN_TEMPLATE_PATH,
)
from bolt_thesis.rule_engine import RuleEngine


CASES = [{'id': 'V-N-001',
  'condition': 'NORMAL',
  'text': '육각볼트 개발 건입니다. 규격은 M8×30, 강도등급은 8.8, 표면처리는 아연도금로 요청합니다.',
  'attributes': {'diameter_mm': 8, 'length_mm': 30, 'strength_grade': '8.8', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-N-002',
  'condition': 'NORMAL',
  'text': 'M8 x 50 육각볼트가 필요합니다. 강도 8.8급, 표면은 무도금 조건입니다.',
  'attributes': {'diameter_mm': 8, 'length_mm': 50, 'strength_grade': '8.8', 'surface_treatment': 'NONE'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-N-003',
  'condition': 'NORMAL',
  'text': '개발 요청: 직경 8mm, 길이 50mm, 강도등급 12.9, 아연도금 육각볼트.',
  'attributes': {'diameter_mm': 8, 'length_mm': 50, 'strength_grade': '12.9', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-N-004',
  'condition': 'NORMAL',
  'text': '볼트 사양은 M8×60이고 강도등급 12.9, 표면처리 무도금입니다.',
  'attributes': {'diameter_mm': 8, 'length_mm': 60, 'strength_grade': '12.9', 'surface_treatment': 'NONE'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-N-005',
  'condition': 'NORMAL',
  'text': '신규 육각볼트 검토 부탁드립니다. M8×80, 10.9급, 아연도금 조건입니다.',
  'attributes': {'diameter_mm': 8, 'length_mm': 80, 'strength_grade': '10.9', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-N-006',
  'condition': 'NORMAL',
  'text': '육각볼트 개발 건입니다. 규격은 M8×100, 강도등급은 10.9, 표면처리는 무도금로 요청합니다.',
  'attributes': {'diameter_mm': 8, 'length_mm': 100, 'strength_grade': '10.9', 'surface_treatment': 'NONE'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-N-007',
  'condition': 'NORMAL',
  'text': 'M8 x 120 육각볼트가 필요합니다. 강도 8.8급, 표면은 아연도금 조건입니다.',
  'attributes': {'diameter_mm': 8, 'length_mm': 120, 'strength_grade': '8.8', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-N-008',
  'condition': 'NORMAL',
  'text': '개발 요청: 직경 10mm, 길이 30mm, 강도등급 8.8, 아연도금 육각볼트.',
  'attributes': {'diameter_mm': 10, 'length_mm': 30, 'strength_grade': '8.8', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-N-009',
  'condition': 'NORMAL',
  'text': '볼트 사양은 M10×50이고 강도등급 8.8, 표면처리 무도금입니다.',
  'attributes': {'diameter_mm': 10, 'length_mm': 50, 'strength_grade': '8.8', 'surface_treatment': 'NONE'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-N-010',
  'condition': 'NORMAL',
  'text': '신규 육각볼트 검토 부탁드립니다. M10×60, 8.8급, 무도금 조건입니다.',
  'attributes': {'diameter_mm': 10, 'length_mm': 60, 'strength_grade': '8.8', 'surface_treatment': 'NONE'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-N-011',
  'condition': 'NORMAL',
  'text': '육각볼트 개발 건입니다. 규격은 M10×60, 강도등급은 12.9, 표면처리는 아연도금로 요청합니다.',
  'attributes': {'diameter_mm': 10, 'length_mm': 60, 'strength_grade': '12.9', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-N-012',
  'condition': 'NORMAL',
  'text': 'M10 x 80 육각볼트가 필요합니다. 강도 12.9급, 표면은 무도금 조건입니다.',
  'attributes': {'diameter_mm': 10, 'length_mm': 80, 'strength_grade': '12.9', 'surface_treatment': 'NONE'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-N-013',
  'condition': 'NORMAL',
  'text': '개발 요청: 직경 10mm, 길이 100mm, 강도등급 10.9, 아연도금 육각볼트.',
  'attributes': {'diameter_mm': 10, 'length_mm': 100, 'strength_grade': '10.9', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-N-014',
  'condition': 'NORMAL',
  'text': '볼트 사양은 M10×120이고 강도등급 10.9, 표면처리 아연도금입니다.',
  'attributes': {'diameter_mm': 10, 'length_mm': 120, 'strength_grade': '10.9', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-N-015',
  'condition': 'NORMAL',
  'text': '신규 육각볼트 검토 부탁드립니다. M12×30, 10.9급, 무도금 조건입니다.',
  'attributes': {'diameter_mm': 12, 'length_mm': 30, 'strength_grade': '10.9', 'surface_treatment': 'NONE'},
  'variation_tags': ['NATURAL_SENTENCE']},
 {'id': 'V-V-001',
  'condition': 'VARIANT',
  'text': '직경 12미리, 길이는 50짜리. 강도 10.9, 표면은 무도금로.',
  'attributes': {'diameter_mm': 12, 'length_mm': 50, 'strength_grade': '10.9', 'surface_treatment': 'NONE'},
  'variation_tags': ['MM_COLLOQUIAL', 'ORDER_VARIATION']},
 {'id': 'V-V-002',
  'condition': 'VARIANT',
  'text': '길이 60mm / M12 / class 8.8 / zinc plated',
  'attributes': {'diameter_mm': 12, 'length_mm': 60, 'strength_grade': '8.8', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['ORDER_VARIATION', 'MIXED_LANGUAGE']},
 {'id': 'V-V-003',
  'condition': 'VARIANT',
  'text': 'Ø12 × 80L, grade=8.8, finish=no coating',
  'attributes': {'diameter_mm': 12, 'length_mm': 80, 'strength_grade': '8.8', 'surface_treatment': 'NONE'},
  'variation_tags': ['SYMBOL_DIAMETER', 'L_SUFFIX', 'MIXED_LANGUAGE']},
 {'id': 'V-V-004',
  'condition': 'VARIANT',
  'text': '12파이-100롱 / G8.8 / no coat',
  'attributes': {'diameter_mm': 12, 'length_mm': 100, 'strength_grade': '8.8', 'surface_treatment': 'NONE'},
  'variation_tags': ['KOREAN_SLANG', 'GRADE_PREFIX', 'SURFACE_SHORTHAND']},
 {'id': 'V-V-005',
  'condition': 'VARIANT',
  'text': 'bolt req: dia 12 mm, len 100 mm, 12.9 class, zinc plated',
  'attributes': {'diameter_mm': 12, 'length_mm': 100, 'strength_grade': '12.9', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['ENGLISH_ABBREVIATION', 'MIXED_LANGUAGE']},
 {'id': 'V-V-006',
  'condition': 'VARIANT',
  'text': '규격 120L에 M12, 강도는 12.9급이고 무도금',
  'attributes': {'diameter_mm': 12, 'length_mm': 120, 'strength_grade': '12.9', 'surface_treatment': 'NONE'},
  'variation_tags': ['ORDER_VARIATION', 'L_SUFFIX']},
 {'id': 'V-V-007',
  'condition': 'VARIANT',
  'text': 'M16 X 30; GRADE 10.9; coating: zinc plated',
  'attributes': {'diameter_mm': 16, 'length_mm': 30, 'strength_grade': '10.9', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['UPPERCASE', 'PUNCTUATION', 'MIXED_LANGUAGE']},
 {'id': 'V-V-008',
  'condition': 'VARIANT',
  'text': '10.9급 볼트, 무도금. 치수는 M16에 길이 50.',
  'attributes': {'diameter_mm': 16, 'length_mm': 50, 'strength_grade': '10.9', 'surface_treatment': 'NONE'},
  'variation_tags': ['ORDER_VARIATION', 'NATURAL_SENTENCE']},
 {'id': 'V-V-009',
  'condition': 'VARIANT',
  'text': 'M16/60mm, strength 8.8, surface zinc plated',
  'attributes': {'diameter_mm': 16, 'length_mm': 60, 'strength_grade': '8.8', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['SLASH_SIZE', 'MIXED_LANGUAGE']},
 {'id': 'V-V-010',
  'condition': 'VARIANT',
  'text': '직경=16, L=80, class=10.9, finish=no coating',
  'attributes': {'diameter_mm': 16, 'length_mm': 80, 'strength_grade': '10.9', 'surface_treatment': 'NONE'},
  'variation_tags': ['KEY_VALUE_STYLE', 'MIXED_LANGUAGE']},
 {'id': 'V-V-011',
  'condition': 'VARIANT',
  'text': '길이 100짜리 16미리 육각볼트. 아연도금이고 강도는 8.8.',
  'attributes': {'diameter_mm': 16, 'length_mm': 100, 'strength_grade': '8.8', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['COLLOQUIAL', 'ORDER_VARIATION']},
 {'id': 'V-V-012',
  'condition': 'VARIANT',
  'text': '무도금 처리, 강도 8.8. 볼트 크기는 16Ø에 120mm.',
  'attributes': {'diameter_mm': 16, 'length_mm': 120, 'strength_grade': '8.8', 'surface_treatment': 'NONE'},
  'variation_tags': ['ORDER_VARIATION', 'DIAMETER_SYMBOL']},
 {'id': 'V-V-013',
  'condition': 'VARIANT',
  'text': 'hex bolt 16mm dia x 120mm long, 12.9, zinc plated',
  'attributes': {'diameter_mm': 16, 'length_mm': 120, 'strength_grade': '12.9', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['ENGLISH_SENTENCE']},
 {'id': 'V-V-014',
  'condition': 'VARIANT',
  'text': 'M20—30 / no coat / 12.9급',
  'attributes': {'diameter_mm': 20, 'length_mm': 30, 'strength_grade': '12.9', 'surface_treatment': 'NONE'},
  'variation_tags': ['DASH_SEPARATOR', 'SURFACE_SHORTHAND', 'ORDER_VARIATION']},
 {'id': 'V-V-015',
  'condition': 'VARIANT',
  'text': '20 Φ, L 50; property class 10.9; zinc plated',
  'attributes': {'diameter_mm': 20, 'length_mm': 50, 'strength_grade': '10.9', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['SPACED_SYMBOL', 'ENGLISH_GRADE']},
 {'id': 'V-V-016',
  'condition': 'VARIANT',
  'text': '사이즈는 M20 * 60이고요. 강도 10.9, 표면처리는 무도금.',
  'attributes': {'diameter_mm': 20, 'length_mm': 60, 'strength_grade': '10.9', 'surface_treatment': 'NONE'},
  'variation_tags': ['ASTERISK_SIZE', 'CONVERSATIONAL']},
 {'id': 'V-V-017',
  'condition': 'VARIANT',
  'text': 'M20x80짜리로, 무도금. 강도등급은 10.9로 부탁.',
  'attributes': {'diameter_mm': 20, 'length_mm': 80, 'strength_grade': '10.9', 'surface_treatment': 'NONE'},
  'variation_tags': ['LOWER_X', 'CONVERSATIONAL']},
 {'id': 'V-V-018',
  'condition': 'VARIANT',
  'text': 'no coat / G10.9 / 100L / 20파이',
  'attributes': {'diameter_mm': 20, 'length_mm': 100, 'strength_grade': '10.9', 'surface_treatment': 'NONE'},
  'variation_tags': ['ORDER_VARIATION', 'SHORTHAND_HEAVY']},
 {'id': 'V-V-019',
  'condition': 'VARIANT',
  'text': 'diameter 20, length 120, grade 10.9, no coating',
  'attributes': {'diameter_mm': 20, 'length_mm': 120, 'strength_grade': '10.9', 'surface_treatment': 'NONE'},
  'variation_tags': ['ENGLISH_KEYS']},
 {'id': 'V-V-020',
  'condition': 'VARIANT',
  'text': '10.9 class, M8, 아연도금, length=30mm',
  'attributes': {'diameter_mm': 8, 'length_mm': 30, 'strength_grade': '10.9', 'surface_treatment': 'ZINC_PLATED'},
  'variation_tags': ['ORDER_VARIATION', 'MIXED_LANGUAGE']},
 {'id': 'V-M-001',
  'condition': 'MISSING',
  'text': 'M8×50, 8.8급 육각볼트 요청. 표면처리는 아직 미정입니다.',
  'attributes': {'diameter_mm': 8, 'length_mm': 50, 'strength_grade': '8.8', 'surface_treatment': None},
  'missing_fields': ['surface_treatment'],
  'variation_tags': ['EXPLICIT_MISSINGNESS']},
 {'id': 'V-M-002',
  'condition': 'MISSING',
  'text': 'M10×60 아연도금 볼트입니다. 강도등급은 확인이 필요합니다.',
  'attributes': {'diameter_mm': 10, 'length_mm': 60, 'strength_grade': None, 'surface_treatment': 'ZINC_PLATED'},
  'missing_fields': ['strength_grade'],
  'variation_tags': ['EXPLICIT_MISSINGNESS']},
 {'id': 'V-M-003',
  'condition': 'MISSING',
  'text': 'M12 볼트, 10.9급, 무도금으로 요청합니다. 길이는 아직 정해지지 않았습니다.',
  'attributes': {'diameter_mm': 12, 'length_mm': None, 'strength_grade': '10.9', 'surface_treatment': 'NONE'},
  'missing_fields': ['length_mm'],
  'variation_tags': ['EXPLICIT_MISSINGNESS']},
 {'id': 'V-M-004',
  'condition': 'MISSING',
  'text': '길이 100mm, 12.9급, 아연도금 육각볼트. 직경 정보는 없습니다.',
  'attributes': {'diameter_mm': None, 'length_mm': 100, 'strength_grade': '12.9', 'surface_treatment': 'ZINC_PLATED'},
  'missing_fields': ['diameter_mm'],
  'variation_tags': ['EXPLICIT_MISSINGNESS']},
 {'id': 'V-M-005',
  'condition': 'MISSING',
  'text': 'M16×120 볼트 개발 요청. 강도와 표면처리는 미정.',
  'attributes': {'diameter_mm': 16, 'length_mm': 120, 'strength_grade': None, 'surface_treatment': None},
  'missing_fields': ['strength_grade', 'surface_treatment'],
  'variation_tags': ['EXPLICIT_MISSINGNESS']},
 {'id': 'V-M-006',
  'condition': 'MISSING',
  'text': '8.8급 무도금 육각볼트 요청. 직경과 길이는 추후 전달.',
  'attributes': {'diameter_mm': None, 'length_mm': None, 'strength_grade': '8.8', 'surface_treatment': 'NONE'},
  'missing_fields': ['diameter_mm', 'length_mm'],
  'variation_tags': ['EXPLICIT_MISSINGNESS']},
 {'id': 'V-M-007',
  'condition': 'MISSING',
  'text': '20파이 80롱, Zn 처리. grade는 아직 몰라.',
  'attributes': {'diameter_mm': 20, 'length_mm': 80, 'strength_grade': None, 'surface_treatment': 'ZINC_PLATED'},
  'missing_fields': ['strength_grade'],
  'variation_tags': ['EXPLICIT_MISSINGNESS', 'MIXED_LANGUAGE']},
 {'id': 'V-M-008',
  'condition': 'MISSING',
  'text': 'L50 / class10.9 / no coating. diameter TBD.',
  'attributes': {'diameter_mm': None, 'length_mm': 50, 'strength_grade': '10.9', 'surface_treatment': 'NONE'},
  'missing_fields': ['diameter_mm'],
  'variation_tags': ['EXPLICIT_MISSINGNESS', 'MIXED_LANGUAGE']},
 {'id': 'V-M-009',
  'condition': 'MISSING',
  'text': 'M10 / G12.9 / zinc plated. 길이는 미정.',
  'attributes': {'diameter_mm': 10, 'length_mm': None, 'strength_grade': '12.9', 'surface_treatment': 'ZINC_PLATED'},
  'missing_fields': ['length_mm'],
  'variation_tags': ['EXPLICIT_MISSINGNESS']},
 {'id': 'V-M-010',
  'condition': 'MISSING',
  'text': 'Ø16 x 60L, 8.8급. coating 정보 없음.',
  'attributes': {'diameter_mm': 16, 'length_mm': 60, 'strength_grade': '8.8', 'surface_treatment': None},
  'missing_fields': ['surface_treatment'],
  'variation_tags': ['EXPLICIT_MISSINGNESS', 'MIXED_LANGUAGE']},
 {'id': 'V-M-011',
  'condition': 'MISSING',
  'text': '길이 30mm 볼트, 아연도금. 직경과 강도등급 확인 필요.',
  'attributes': {'diameter_mm': None, 'length_mm': 30, 'strength_grade': None, 'surface_treatment': 'ZINC_PLATED'},
  'missing_fields': ['diameter_mm', 'strength_grade'],
  'variation_tags': ['EXPLICIT_MISSINGNESS']},
 {'id': 'V-M-012',
  'condition': 'MISSING',
  'text': 'M20, no coating. length와 property class는 아직 없음.',
  'attributes': {'diameter_mm': 20, 'length_mm': None, 'strength_grade': None, 'surface_treatment': 'NONE'},
  'missing_fields': ['length_mm', 'strength_grade'],
  'variation_tags': ['EXPLICIT_MISSINGNESS', 'MIXED_LANGUAGE']},
 {'id': 'V-M-013',
  'condition': 'MISSING',
  'text': 'G10.9 / 120L / Zn. dia 미정.',
  'attributes': {'diameter_mm': None, 'length_mm': 120, 'strength_grade': '10.9', 'surface_treatment': 'ZINC_PLATED'},
  'missing_fields': ['diameter_mm'],
  'variation_tags': ['EXPLICIT_MISSINGNESS', 'MIXED_LANGUAGE']},
 {'id': 'V-M-014',
  'condition': 'MISSING',
  'text': 'M8x100, 12.9 class. 표면처리 조건은 전달받지 못했습니다.',
  'attributes': {'diameter_mm': 8, 'length_mm': 100, 'strength_grade': '12.9', 'surface_treatment': None},
  'missing_fields': ['surface_treatment'],
  'variation_tags': ['EXPLICIT_MISSINGNESS', 'MIXED_LANGUAGE']},
 {'id': 'V-M-015',
  'condition': 'MISSING',
  'text': '직경 12mm, 무도금 요청. 길이와 강도등급은 확인 중.',
  'attributes': {'diameter_mm': 12, 'length_mm': None, 'strength_grade': None, 'surface_treatment': 'NONE'},
  'missing_fields': ['length_mm', 'strength_grade'],
  'variation_tags': ['EXPLICIT_MISSINGNESS']}]


def _combo(attrs: dict) -> tuple:
    return (
        attrs["diameter_mm"],
        attrs["length_mm"],
        attrs["strength_grade"],
        attrs["surface_treatment"],
    )


def _is_complete(attrs: dict) -> bool:
    return all(value is not None for value in attrs.values())


def main() -> None:
    pilot = json.loads(PILOT_DATASET_PATH.read_text(encoding="utf-8"))
    prompt = json.loads(EXTRACTOR_PROMPT_PATH.read_text(encoding="utf-8"))
    engine = RuleEngine()

    pilot_texts = {item["text"] for item in pilot["items"]}
    fewshot_texts = {item["input"] for item in prompt["few_shot_examples"]}

    blocked_combos = {
        _combo(item["ground_truth"]["attributes"])
        for item in pilot["items"]
        if _is_complete(item["ground_truth"]["attributes"])
    }
    blocked_combos |= {
        _combo(item["output"])
        for item in prompt["few_shot_examples"]
        if _is_complete(item["output"])
    }

    items: list[dict] = []
    seen_ids: set[str] = set()
    seen_texts: set[str] = set()
    seen_complete_combos: set[tuple] = set()
    failures: list[str] = []

    for case in CASES:
        item_id = case["id"]
        text = case["text"]
        attrs = case["attributes"]

        if item_id in seen_ids:
            failures.append(f"duplicate id: {item_id}")
        seen_ids.add(item_id)

        if text in seen_texts:
            failures.append(f"duplicate validation text: {item_id}")
        seen_texts.add(text)

        if text in pilot_texts:
            failures.append(f"pilot text overlap: {item_id}")
        if text in fewshot_texts:
            failures.append(f"few-shot text overlap: {item_id}")

        if _is_complete(attrs):
            combo = _combo(attrs)
            if combo in blocked_combos:
                failures.append(f"pilot/few-shot complete combo overlap: {item_id} {combo}")
            if combo in seen_complete_combos:
                failures.append(f"duplicate validation complete combo: {item_id} {combo}")
            seen_complete_combos.add(combo)

        item = {
            "id": item_id,
            "condition": case["condition"],
            "text": text,
            "ground_truth": {
                "attributes": attrs,
                "expected_output": engine.run(attrs),
            },
        }

        if "missing_fields" in case:
            item["missing_fields"] = case["missing_fields"]
        if "variation_tags" in case:
            item["variation_tags"] = case["variation_tags"]

        items.append(item)

    counts = Counter(item["condition"] for item in items)
    expected_counts = Counter({"NORMAL": 15, "VARIANT": 20, "MISSING": 15})
    if counts != expected_counts:
        failures.append(f"unexpected condition counts: {dict(counts)}")
    if len(items) != 50:
        failures.append(f"unexpected item count: {len(items)}")

    if failures:
        raise RuntimeError("Validation generation failed:\n- " + "\n- ".join(failures))

    dataset = {
        "dataset_name": "bolt_validation_v0_1",
        "version": "0.1",
        "purpose": "Pilot 이후 System A 프롬프트/파이프라인 검증 및 동결 판단용 Validation 데이터",
        "is_final_test": False,
        "split_policy": {
            "pilot_text_overlap_allowed": False,
            "few_shot_text_overlap_allowed": False,
            "complete_attribute_combo_overlap_with_pilot_or_fewshot": False,
            "notes": [
                "Validation 결과는 프롬프트/코드 조정에 사용할 수 있다.",
                "Final Test는 Validation 완료 후 별도로 생성하며 Test를 본 뒤 Prompt를 수정하지 않는다.",
            ],
        },
        "summary": {
            "total": 50,
            "NORMAL": 15,
            "VARIANT": 20,
            "MISSING": 15,
        },
        "items": items,
    }

    VALIDATION_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_DATASET_PATH.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    run_template = {
        "run_metadata": {
            "system": "A",
            "component": "LLM_ATTRIBUTE_EXTRACTOR",
            "dataset": "bolt_validation_v0_1",
            "model": None,
            "prompt_version": prompt["version"],
            "temperature": 0.0,
            "seed": 42,
            "backend": "vllm",
            "structured_output": True,
        },
        "items": [
            {
                "id": item["id"],
                "text": item["text"],
                "ground_truth_attributes": item["ground_truth"]["attributes"],
                "model_output_raw": None,
                "parsed_attributes": None,
                "schema_valid": None,
                "field_correctness": {
                    "diameter_mm": None,
                    "length_mm": None,
                    "strength_grade": None,
                    "surface_treatment": None,
                },
                "all_attributes_correct": None,
                "pipeline_result": None,
                "error": None,
            }
            for item in items
        ],
    }

    VALIDATION_SYSTEM_A_RUN_TEMPLATE_PATH.write_text(
        json.dumps(run_template, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"created: {VALIDATION_DATASET_PATH}")
    print(f"created: {VALIDATION_SYSTEM_A_RUN_TEMPLATE_PATH}")
    print(f"conditions: {dict(counts)}")
    print(f"unique complete validation combos: {len(seen_complete_combos)}")


if __name__ == "__main__":
    main()
