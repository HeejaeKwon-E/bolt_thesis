# Bolt Thesis

볼트 개발의뢰를 대상으로 **LLM 자연어 추출 + 규칙엔진** 하이브리드 구조를 평가하는 석사논문 실험 프로젝트입니다.

## 현재 구현 범위

- 속성 4종: 직경, 길이, 강도등급, 표면처리
- 제조 규칙 11개
- Pilot Dataset 30건
- 시스템 A: vLLM 속성 추출 → 필수 속성 검사 → 규칙엔진
- JSON Schema Structured Output
- Pilot 평가 및 조건별 결과 요약

## 프로젝트 구조

```text
bolt_thesis/
├── config/
│   ├── attributes.json
│   ├── rules.json
│   ├── model.json
│   ├── extractor_prompt.json
│   └── extractor_schema.json
│
├── data/
│   ├── pilot/
│   │   ├── pilot_dataset.json
│   │   └── system_a_run_template.json
│   ├── validation/
│   └── test/
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PILOT_DATASET.md
│   └── RUN_VLLM.md
│
├── results/
│
├── scripts/
│   ├── check_cuda.py
│   ├── check_vllm_server.py
│   ├── generate_pilot_dataset.py
│   ├── generate_validation_dataset.py
│   ├── run_system_a_pilot.py
│   ├── run_system_a_validation.py
│   ├── run_vllm_server.sh
│   ├── summarize_system_a_pilot.py
│   ├── summarize_system_a_validation.py
│   ├── validate_pilot.py
│   ├── validate_validation.py
│   └── validate_rules.py
│
├── src/
│   └── bolt_thesis/
│       ├── clients/
│       │   └── vllm.py
│       ├── evaluation/
│       │   └── system_a.py
│       ├── extractor/
│       │   ├── prompt.py
│       │   └── validator.py
│       ├── pipelines/
│       │   └── system_a.py
│       ├── paths.py
│       └── rule_engine.py
│
├── tests/
│   ├── test_extractor.py
│   └── test_rule_engine.py
│
├── .gitignore
├── pyproject.toml
└── README.md
```

## 시작

```bash
uv sync --dev
uv run python scripts/validate_rules.py
uv run python scripts/validate_pilot.py
```

vLLM 실행 방법은 [`docs/RUN_VLLM.md`](docs/RUN_VLLM.md)를 참고합니다.

## 다음 연구 단계

1. 시스템 A Pilot 30건 실행
2. Pilot 결과를 기준으로 프롬프트 수정
3. Validation 50건 실행
4. 시스템 B 구현
5. 시스템 C 구현


## v0.7 Validation

Validation 50건과 실행 스크립트를 추가했습니다.

```bash
uv run python scripts/validate_validation.py
uv run python scripts/run_system_a_validation.py --limit 5
```

자세한 내용은 `docs/VALIDATION_DATASET.md`를 참고합니다.
