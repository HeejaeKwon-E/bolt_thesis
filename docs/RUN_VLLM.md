# vLLM 실행 가이드

## 1. 환경 설치

```bash
uv sync --dev
```

## 2. GPU 확인

```bash
uv run python scripts/check_cuda.py
```

## 3. vLLM 서버 실행

```bash
CUDA_VISIBLE_DEVICES=0 uv run scripts/run_vllm_server.sh
```

## 4. 서버 확인

새 터미널에서:

```bash
uv run python scripts/check_vllm_server.py
```

## 5. Pilot 3건 실행

```bash
uv run python scripts/run_system_a_pilot.py --limit 3
```

결과는 `results/system_a_pilot.json`에 저장됩니다.

## 6. Pilot 전체 30건

3건 실행 결과가 정상이라면:

```bash
rm -f results/system_a_pilot.json
uv run python scripts/run_system_a_pilot.py
```

중간에 중단된 경우:

```bash
uv run python scripts/run_system_a_pilot.py --resume
```

## 7. 결과 요약

```bash
uv run python scripts/summarize_system_a_pilot.py
```

## 8. 규칙/Pilot 데이터 검증

```bash
uv run python scripts/validate_rules.py
uv run python scripts/validate_pilot.py
```
