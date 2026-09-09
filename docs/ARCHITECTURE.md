# 프로젝트 구조

## 설계 원칙

- `config/`: 실험 조건과 규칙 정의
- `data/`: 입력 데이터셋
- `src/bolt_thesis/`: 재사용 가능한 연구 코드
- `scripts/`: 사람이 직접 실행하는 명령
- `tests/`: 핵심 로직 단위 테스트
- `results/`: 모델 실행 결과
- `docs/`: 실행 방법과 연구 메모

## 시스템 A 흐름

```text
Pilot 문장
  ↓
vLLM
  ↓
속성 JSON
  ↓
Extractor Validator
  ↓
Rule Engine
  ↓
Material / Routing
  ↓
Evaluation
```

## 파일 역할

### config

- `attributes.json`: 속성 값 범위
- `rules.json`: Material/Routing 규칙
- `model.json`: vLLM 및 생성 설정
- `extractor_prompt.json`: 시스템 A Few-shot 프롬프트
- `extractor_schema.json`: Structured Output JSON Schema

### src

- `rule_engine.py`: 결정론적 제조 규칙 실행
- `extractor/prompt.py`: LLM 프롬프트 구성
- `extractor/validator.py`: LLM 출력 검증
- `clients/vllm.py`: vLLM OpenAI 호환 API 호출
- `pipelines/system_a.py`: 시스템 A 후단 파이프라인
- `evaluation/system_a.py`: Pilot 평가

### scripts

실험자가 터미널에서 직접 실행할 파일만 둡니다.
