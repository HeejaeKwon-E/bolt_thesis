# System B — Direct LLM Generation

## 목적

System B는 자연어 개발의뢰와 제조 규칙을 LLM에 함께 제공하고,
LLM이 **Material과 Routing을 직접 생성**하도록 하는 비교 시스템입니다.

System A와의 핵심 차이는 다음 하나입니다.

```text
System A
자연어 → LLM 속성 추출 → Python Rule Engine → 최종 결과

System B
자연어 + 동일 제조 규칙 → LLM 직접 최종 결과
```

## 공정성 통제

System B에는 다음을 System A와 동일하게 제공합니다.

> 현재 본 실험 모델은 `Qwen/Qwen3.5-4B`이며 텍스트 입력만 사용합니다.

- 동일 모델: `Qwen/Qwen3.5-4B`
- 동일 vLLM 서버
- `temperature=0`
- `seed=42`
- 동일 Structured Output 사용
- System A와 동일한 입력 표현 정규화 지침
- 동일한 Few-shot 입력 5개
- `config/rules.json`의 동일한 11개 제조 규칙

Few-shot의 입력은 A와 같고, B의 출력만 Rule Engine을 통해
`Material/Routing/Clarification` 정답으로 변환합니다.

## System B 출력

충분한 정보:

```json
{
  "status": "OK",
  "material": "MAT_ALLOY_01",
  "routing": [
    "CUTTING",
    "HOT_FORMING",
    "THREAD_ROLLING",
    "HEAT_TREATMENT",
    "ZINC_PLATING",
    "INSPECTION",
    "PACKAGING"
  ],
  "required_fields": []
}
```

필수정보 누락:

```json
{
  "status": "CLARIFICATION_REQUIRED",
  "material": null,
  "routing": [],
  "required_fields": ["strength_grade"]
}
```

## 실행 순서

기존 vLLM 서버는 그대로 사용합니다.

먼저 Pilot 3건:

```bash
uv run python scripts/run_system_b.py --split pilot --limit 3
```

정상 확인 후 전체 Pilot:

```bash
rm -f results/system_b_pilot.json
uv run python scripts/run_system_b.py --split pilot
uv run python scripts/summarize_system_b.py --split pilot
```

Pilot에 구현상 문제가 없다면 Validation 5건:

```bash
uv run python scripts/run_system_b.py --split validation --limit 5
```

그다음 전체 Validation:

```bash
rm -f results/system_b_validation.json
uv run python scripts/run_system_b.py --split validation
uv run python scripts/summarize_system_b.py --split validation
```

## 주요 평가값

- Task Success
- Material 정확도
- Routing exact match
- Routing operation Precision / Recall / F1
- 누락 필드 정확 식별
- Dangerous Guess
- Over-clarification

Structured Output을 사용하므로 Schema Valid Rate는 주 성능지표가 아니라
파이프라인 정상동작 확인값으로 해석합니다.


## vLLM 0.28 Structured Output 호환성

`system_b_schema.json`의 배열에는 `uniqueItems`를 사용하지 않습니다.

vLLM Structured Output backend에서 해당 JSON Schema keyword가 지원되지 않을 수 있기 때문입니다.
중복 검사는 Structured Output 이후 Python validator에서 수행합니다.

- 중복 Routing operation -> `DUPLICATE_ROUTING_OPERATION`
- 중복 required field -> `DUPLICATE_REQUIRED_FIELD`

따라서 실험의 의미 제약은 그대로 유지됩니다.
