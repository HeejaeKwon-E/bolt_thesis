# Validation Dataset v0.1

Pilot 30건 통과 후 System A의 프롬프트/파이프라인을 점검하기 위한 Validation 50건입니다.

## 구성

| 조건 | 건수 | 목적 |
|---|---:|---|
| NORMAL | 15 | 일반적인 자연어 요청 |
| VARIANT | 20 | 기호, 순서 변경, 구어 표현, 영문 혼용, 축약 표현 |
| MISSING | 15 | 필수 속성 1~2개 누락 및 `null` 처리 |

## Pilot보다 어려워진 점

- 단순 규격 나열보다 자연스러운 문장 비중 증가
- 속성 순서 변경
- `미리`, `짜리`, `롱` 등의 구어 표현
- `dia`, `len`, `finish`, `property class` 등의 영문 표현
- 여러 구분자와 기호 사용
- `미정`, `TBD`, `정보 없음` 같은 누락 표현

새 제조 속성은 추가하지 않았으며 정답 대상은 기존 네 속성뿐입니다.

## 데이터 분리

- Pilot과 동일 문장 없음
- Few-shot과 동일 문장 없음
- 완전 입력 35건은 Pilot/Few-shot의 완전 속성 조합과 중복 없음
- Validation 내부 완전 속성 조합도 중복 없음

Validation 결과를 보고 Prompt를 수정할 수 있습니다. 다만 Prompt를 동결한 뒤 Final Test를 만들고, Test 결과를 본 뒤에는 Prompt를 수정하지 않습니다.


## 재생성

Validation 데이터와 실행 템플릿은 아래 명령으로 동일하게 다시 만들 수 있습니다.

```bash
uv run python scripts/generate_validation_dataset.py
```

생성 스크립트는 Pilot/Few-shot 문장 중복, 완전 입력 조합 중복, 조건별 건수를 함께 검사합니다.

## 실행

```bash
uv run python scripts/validate_validation.py
uv run python scripts/run_system_a_validation.py --limit 5
```

5건이 정상이라면:

```bash
rm -f results/system_a_validation.json
uv run python scripts/run_system_a_validation.py
uv run python scripts/summarize_system_a_validation.py
```
