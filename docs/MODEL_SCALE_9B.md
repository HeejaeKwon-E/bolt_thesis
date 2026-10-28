# Qwen3.5-9B 추가 모델 규모 실험

이 실험은 Qwen3.5-4B 본 실험 종료 후 수행하는 **post-hoc model-scale sensitivity analysis**이다.
본 실험의 결론을 다시 맞추기 위한 튜닝 단계가 아니며, 4B 결과는 수정하지 않는다.

## 고정 조건

- Dataset: 기존 Final Test 100건 그대로 사용
- System A/B의 Prompt/Schema/Rules/Evaluator 변경 없음
- temperature: 0.0
- request seed: 42
- vLLM server seed: 42
- max_model_len: 4096
- generation_config: vllm
- quantization: 사용하지 않음
- VLLM_BATCH_INVARIANT: 사용하지 않음
- 변경점: `Qwen/Qwen3.5-4B` → `Qwen/Qwen3.5-9B`만 변경

System C는 LLM을 사용하지 않으므로 재실행하지 않는다.

## 1. 4B archive 확인

```bash
ls -lah results/model_scale/qwen3_5_4b/
```

## 2. 9B vLLM 서버 시작

기존 4B 서버를 종료한 뒤 실행한다.

```bash
CUDA_VISIBLE_DEVICES=1 uv run scripts/run_vllm_server_9b.sh
```

로그에서 다음을 확인한다.

```text
model=Qwen/Qwen3.5-9B
seed=42
max_model_len=4096
```

vLLM 실제 dtype 로그가 `torch.bfloat16`인지도 기록한다.

## 3. 준비상태 확인

새 터미널에서:

```bash
uv run python scripts/check_9b_ready.py
```

마지막에 `READY`가 나와야 한다.

## 4. 9B canonical scale run

각 시스템은 정상 완료된 canonical run을 하나만 사용한다.
명백한 서버/API 장애로 중단된 경우에만 `--resume`을 사용한다.
완료된 결과를 보고 재실행해서 더 좋은 run을 선택하지 않는다.

```bash
uv run python scripts/run_system_a_final_test_9b.py
uv run python scripts/run_system_b_final_test_9b.py
```

결과:

```text
results/model_scale/qwen3_5_9b/system_a_final_test.json
results/model_scale/qwen3_5_9b/system_b_final_test.json
```

## 5. 4B vs 9B 비교

```bash
uv run python scripts/evaluate_model_scale.py
```

결과:

```text
results/model_scale/qwen3_5_4b_vs_9b.json
results/model_scale/qwen3_5_4b_vs_9b.md
```

주요 해석 포인트는 System B의 Final Task Success와 Routing Exact가 9B에서 얼마나 개선되는지,
그리고 A-B 성능 격차가 모델 규모 증가로 얼마나 줄어드는지이다.
