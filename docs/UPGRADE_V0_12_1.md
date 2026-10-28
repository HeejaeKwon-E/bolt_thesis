# v0.12.1 업그레이드 메모

`bolt_thesis_1012.zip` 기준으로 Final Test 파이프라인을 추가한 버전입니다.

## 추가된 기능

- Final Test 100건 (`NORMAL 30 / VARIANT 40 / MISSING 30`)
- Final Test 사전 validator
- System A/B/C Final Test runner
- A/B/C 통합 평가
- paired exact McNemar test
- paired bootstrap 95% CI
- Final Test 이전 artifact SHA256 동결

## 보존 사항

기존 Pilot/Validation 및 반복실행 결과 JSON은 수정하지 않았습니다.

## 실행

```bash
uv run python scripts/validate_final_test.py
```

반드시 `PASS`를 확인한 후 다음 순서로 한 번씩 실행합니다.

```bash
uv run python scripts/run_system_a_final_test.py
uv run python scripts/run_system_b_final_test.py
uv run python scripts/run_system_c_final_test.py
uv run python scripts/evaluate_final_test.py
uv run python scripts/statistics_final_test.py
```

자세한 동결 정책은 `config/experiment_lock.json`, 상세 절차는 `docs/FINAL_TEST.md`를 참고합니다.
