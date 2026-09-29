# Unified evaluator condition fix

기존 `scripts/reevaluate_results.py`를 이 파일로 덮어쓰면 됩니다.

문제:
- System A의 과거 결과 JSON에는 `condition` 필드가 없음
- 따라서 NORMAL/VARIANT/MISSING 조건별 집계가 0건으로 표시됨

수정:
- 결과 JSON의 `condition`을 신뢰하지 않고,
  Pilot/Validation 원본 dataset의 `id -> condition` 매핑을 사용

수정 후 다시 실행:

```bash
uv run python scripts/reevaluate_results.py --split pilot
uv run python scripts/reevaluate_results.py --split validation
```
