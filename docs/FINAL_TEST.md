# Final Test v1.0

## 1. 목적

Final Test는 Pilot/Validation에서 개발과 튜닝을 완료한 뒤 A/B/C를 최종 비교하기 위한 **동결 평가 세트**입니다.

- 총 100건
- NORMAL 30
- VARIANT 40
- MISSING 30
- 완전정보 70건은 Pilot/Validation에서 한 번이라도 등장한 완전정보 속성 조합과 겹치지 않음
- Final Test 결과를 확인한 뒤 Prompt / Rule / Regex / Model / Schema / 생성 설정 / Final Test 문장을 수정하지 않음

## 2. VARIANT 구성

VARIANT 40건은 다음 5개 범주를 각 8건씩 포함합니다.

- `SYMBOL_SPACE`: 기호, 공백, 표기 방식 변화
- `WORD_ORDER`: 정보 순서 변화
- `COLLOQUIAL_KR`: 한국어 구어 표현
- `KOREAN_ENGLISH_MIX`: 한영 혼용
- `TYPO_ABBREVIATION`: 현실적인 오탈자/축약

특정 시스템을 깨기 위한 adversarial 문장을 만드는 것이 아니라, 연구계획에서 정의한 표현 변화 범주를 사전에 균등 배치한 것입니다.

## 3. MISSING 구성

- 단일 필드 누락: 20건 (각 필드 5건)
- 두 필드 누락: 10건

모든 필수 속성 중 `null`인 필드는 clarification 대상으로 간주합니다.

## 4. 실행 전 검증

Final Test를 실행하기 전에 반드시:

```bash
uv run python scripts/validate_final_test.py
```

`PASS`와 다음 SHA256가 확인되어야 합니다.

```text
dbe1470a676623a8cc48706a1aa1dbf15aff1c3cc509ee234bf8400989f4bf06
```

## 5. Canonical 실행

서버는 frozen 조건으로 실행합니다.

```bash
CUDA_VISIBLE_DEVICES=1 uv run scripts/run_vllm_server.sh
```

서버 확인:

```bash
curl http://127.0.0.1:8000/v1/models
```

그 다음 A/B/C를 각각 **한 번의 canonical run**으로 실행합니다.

```bash
uv run python scripts/run_system_a_final_test.py
uv run python scripts/run_system_b_final_test.py
uv run python scripts/run_system_c_final_test.py
```

정상적으로 완료된 run을 성능을 보고 다시 선택하거나 반복하지 않습니다. 서버/API 중단 등 명백한 기술적 실패가 발생한 경우에만 해당 시스템의 run 전체를 무효 처리하고 다시 실행합니다.

## 6. 통합 평가

```bash
uv run python scripts/evaluate_final_test.py
```

주요 결과 파일:

```text
results/system_a_final_test.json
results/system_b_final_test.json
results/system_c_final_test.json
results/final_test_unified_evaluation.json
```

## 7. 통계

```bash
uv run python scripts/statistics_final_test.py
```

통계 스크립트는 별도 외부 통계 패키지 없이 다음을 계산합니다.

- paired exact McNemar test
- paired nonparametric bootstrap 95% CI (10,000회, seed 42)

### Primary

- A vs B / A vs C / B vs C의 `Final Task Success`

### Secondary / RQ별

- RQ1: sufficient cases의 A vs B `Routing Exact`
- RQ2: MISSING의 `Dangerous Guess` 회피와 required-fields correctness
- RQ3: A vs C `Attribute Exact`, 특히 VARIANT 40건
- NORMAL / VARIANT / MISSING 조건별 Final Task Success

통계 결과:

```text
results/final_test_statistics.json
```
