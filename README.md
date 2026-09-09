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
│   ├── run_system_a_pilot.py
│   ├── run_vllm_server.sh
│   ├── summarize_system_a_pilot.py
│   ├── validate_pilot.py
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
3. Validation 약 50건 작성
4. 시스템 B 구현
5. 시스템 C 구현
