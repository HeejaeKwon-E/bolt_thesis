# v0.13 — Qwen3.5-4B 실험 마감

v0.13은 새로운 모델 추론을 수행하지 않고, 이미 완료된 Qwen3.5-4B Final Test 결과를 정식으로 마감하는 버전입니다.

## 추가 사항

- `scripts/analyze_final_test_failures.py`
  - A/B/C Final Test 실패 유형 자동 분류
  - 대표 실패 사례 및 JSON/Markdown 보고서 생성
- `scripts/statistics_final_test.py`
  - 기존 JSON에 계산되던 RQ1/RQ2 통계를 콘솔에도 명시적으로 출력
- `scripts/finalize_4b_experiment.py`
  - frozen artifact와 Final Test dataset SHA256 검증
  - 4B summary/manifest 생성
  - canonical 결과를 `results/model_scale/qwen3_5_4b/`에 보존
  - `experiment_lock.json`을 `COMPLETED_4B_FINAL_TEST`로 갱신
  - Qwen3.5-9B 추가 분석을 `PLANNED_NOT_RUN`으로 기록

## 주의

v0.13은 4B Prompt, Rule, Regex, Schema, Dataset 또는 기존 Final Test 결과를 수정하지 않습니다.
9B 실험은 4B 본 실험과 구분되는 post-hoc sensitivity analysis로 취급합니다.
