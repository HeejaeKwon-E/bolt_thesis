# Evaluation v2 — A/B 공통 평가 기준

Qwen3.5-4B 본 실험부터 System A와 System B를 동일한 최종 업무 기준으로 비교합니다.

## 핵심 원칙

1. **Structured Output Validity**와 **Semantic Output Validity**를 분리합니다.
   - Structured: JSON 구조/필드/허용값이 올바른가?
   - Semantic: `CLARIFICATION_REQUIRED`인데 Routing을 같이 내는 등 필드 간 의미 충돌이 없는가?
2. 충분정보와 누락정보의 분모를 분리합니다.
3. System A도 속성 추출 정확도뿐 아니라 **최종 Task Success**를 계산합니다.
4. Routing operation P/R/F1은 공정 집합의 포함 여부를 평가하고, 순서까지 완전히 동일한지는 Routing Exact Match로 별도 평가합니다.

## 공통 지표

- Final Task Success
- Structured Output Valid Rate
- Semantic Output Valid Rate
- Material Accuracy on Sufficient Cases
- Routing Exact Match on Sufficient Cases
- Routing Macro Precision / Recall / F1 on Sufficient Cases
- Missing Status Accuracy
- Required Fields Accuracy on Missing Cases
- Dangerous Guess Rate on Missing Cases
- Over-clarification Rate on Sufficient Cases

System A에만 추가로 다음을 계산합니다.

- Attribute Exact Match
- Field-level Attribute Accuracy

## 실행

기존 결과 JSON을 다시 추론하지 않고 재평가할 수 있습니다.

```bash
uv run python scripts/reevaluate_results.py --split pilot
uv run python scripts/reevaluate_results.py --split validation
```

실패 사례:

```bash
uv run python scripts/show_common_failures.py --system A --split validation
uv run python scripts/show_common_failures.py --system B --split validation
```

결과 JSON:

```text
results/unified_evaluation_pilot.json
results/unified_evaluation_validation.json
```

## 지표 해석 주의

`Material Accuracy`의 분모는 전체 데이터가 아니라 **Material을 생성해야 하는 sufficient cases**입니다.
누락 입력에서는 Material을 생성하지 않는 것이 정답이므로 이 분모에 포함하지 않습니다.

`Dangerous Guess`는 누락 입력에서 다음 중 하나가 발생하면 1건으로 계산합니다.

- `status == OK`
- `material != null`
- `routing`이 비어 있지 않음

따라서 추가 확인을 표시하면서 동시에 생산 Routing을 출력하는 경우도 위험한 추측으로 집계됩니다.
