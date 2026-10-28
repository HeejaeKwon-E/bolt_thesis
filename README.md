# Bolt Thesis v0.13.0

볼트 자연어 개발의뢰에서 **LLM + 규칙엔진 하이브리드 구조**를 평가하는 석사논문 실험 프로젝트입니다.

## 연구 시스템

- **System A**: Qwen3.5-4B 속성 추출 → 필수정보 확인 → 결정론적 Rule Engine
- **System B**: Qwen3.5-4B가 동일 제조 규칙을 바탕으로 Material / Routing을 직접 생성
- **System C**: Regex/Dictionary 속성 추출 → 필수정보 확인 → System A와 동일한 Rule Engine

대상 속성은 `diameter_mm`, `length_mm`, `strength_grade`, `surface_treatment` 4개이며, 출력은 Material과 Routing입니다. 필수정보가 없으면 `CLARIFICATION_REQUIRED`로 처리합니다.

## 현재 상태

**Qwen3.5-4B 본 실험은 완료되었습니다.**

- Rule Engine 180개 완전 조합 검증 완료
- Pilot 30건 / Validation 50건 완료
- A/B/C 공통 evaluator 완료
- A/B 반복 실행 재현성 확인 완료
- Final Test 100건 완료
- paired exact McNemar test + paired bootstrap 95% CI 완료
- Final Test failure analysis 완료
- 4B 결과 summary / manifest / archive 완료
- 다음 단계: **Qwen3.5-9B post-hoc model-scale sensitivity analysis**

## 4B Final Test 결과

| System | Final Task Success | Material (sufficient) | Routing Exact (sufficient) | Missing Required Fields |
|---|---:|---:|---:|---:|
| A | **99%** | **100%** | **100%** | 96.7% |
| B | 76% | **100%** | 68.6% | 93.3% |
| C | 68% | 54.3% | 54.3% | **100%** |

조건별 Final Task Success:

| Condition | A | B | C |
|---|---:|---:|---:|
| NORMAL | 100% | 70.0% | 83.3% |
| VARIANT | **100%** | 67.5% | 32.5% |
| MISSING | 96.7% | 93.3% | **100%** |

핵심 통계:

- A vs B Final Task Success: Δ=+23%p, 95% CI [+15, +32]p, McNemar p=1.55e-6
- A vs B Routing Exact (sufficient): Δ=+31.4%p, 95% CI [+21.4, +42.9]p, p=4.77e-7
- A vs C Final Task Success: Δ=+31%p, 95% CI [+22, +40]p, p=7.92e-9
- A vs C VARIANT Attribute Exact: 100% vs 32.5%, Δ=+67.5%p, p=1.49e-8
- A vs B MISSING dangerous guess: 둘 다 0건

## 4B 결과 파일

```text
results/system_a_final_test.json
results/system_b_final_test.json
results/system_c_final_test.json
results/final_test_unified_evaluation.json
results/final_test_statistics.json
results/final_test_failure_analysis.json
results/final_test_failure_analysis.md
results/4b_final_summary.json
results/4b_final_summary.md
results/4b_experiment_manifest.json
results/model_scale/qwen3_5_4b/
```

`results/model_scale/qwen3_5_4b/`는 이후 9B 실험 과정에서 4B canonical 결과를 덮어쓰지 않기 위한 보존본입니다.

## 4B 마감 재생성/검증

Final Test 추론을 다시 돌릴 필요는 없습니다. 기존 canonical 결과에서 분석 산출물만 다시 만들려면:

```bash
uv run python scripts/statistics_final_test.py
uv run python scripts/analyze_final_test_failures.py
uv run python scripts/finalize_4b_experiment.py
```

`finalize_4b_experiment.py`는 Final Test dataset SHA256과 frozen artifact SHA256을 먼저 확인한 뒤 summary/manifest/archive와 experiment lock을 갱신합니다.

## 동결 조건

- Model: `Qwen/Qwen3.5-4B`
- vLLM: `0.30.0`
- dtype: BF16
- temperature: 0
- request seed: 42
- server seed: 42
- max model length: 4096
- Prompt / Rule / Regex / Schema / Final Test dataset은 4B Final Test 이후 수정하지 않음

상세 상태와 SHA256은 `config/experiment_lock.json`을 기준으로 합니다.

## 다음 단계: 9B 추가 분석

9B 실험은 **본 실험을 다시 정의하는 것이 아니라 post-hoc 모델 규모 민감도 분석**으로 수행합니다.

원칙:

- `Qwen/Qwen3.5-4B` → `Qwen/Qwen3.5-9B`만 변경
- 동일 Final Test 100건 사용
- System A/B Prompt, Rule, Schema 및 generation settings 유지
- System C는 모델을 사용하지 않으므로 모델 규모 비교에서는 재실행 불필요
- 4B canonical 결과는 `results/model_scale/qwen3_5_4b/`에 보존

## 주요 문서

- `config/experiment_lock.json`: 4B 완료 상태, frozen SHA256, 9B 추가 분석 계획
- `docs/ARCHITECTURE.md`: 전체 구조
- `docs/EVALUATION_V2.md`: 공통 평가 정의
- `docs/FINAL_TEST.md`: Final Test 설계
- `results/4b_final_summary.md`: 4B 핵심 결과 요약
- `results/final_test_failure_analysis.md`: A/B/C 실패 유형 분석

## v0.14: Qwen3.5-9B 모델 규모 추가 분석

4B 본 실험은 완료/동결되어 있으며, 9B는 post-hoc sensitivity analysis로 분리한다.

```bash
CUDA_VISIBLE_DEVICES=1 uv run scripts/run_vllm_server_9b.sh
uv run python scripts/check_9b_ready.py
uv run python scripts/run_system_a_final_test_9b.py
uv run python scripts/run_system_b_final_test_9b.py
uv run python scripts/evaluate_model_scale.py
```

9B 결과는 `results/model_scale/qwen3_5_9b/`에 저장되어 기존 4B canonical 결과를 덮어쓰지 않는다. 상세 절차는 `docs/MODEL_SCALE_9B.md`를 참조한다.
