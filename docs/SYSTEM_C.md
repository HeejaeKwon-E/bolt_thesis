# System C — Regex/Dictionary + Rule Engine

## 목적

System C는 LLM을 사용하지 않는 전통적인 deterministic baseline입니다.

```text
자연어 개발의뢰
    ↓
Regex + Dictionary
    ↓
diameter_mm / length_mm / strength_grade / surface_treatment
    ↓
System A와 동일한 missing check
    ↓
System A와 동일한 Python Rule Engine
    ↓
Material / Routing 또는 Clarification
```

System C의 목적은 복잡한 자연어 이해 모델을 사용하지 않고도
미리 정의한 표현 패턴만으로 어느 정도 처리할 수 있는지를 비교하는 것입니다.

## 지원 원칙

정규식/사전은 명시적으로 정의한 표현만 처리합니다.

예:

- Diameter: `M12`, `12파이`, `12Φ`, `12Ø`, `직경 12`, `dia 12`
- Length: `L80`, `80L`, `80롱`, `길이 80`, `length 80`
- Strength: `8.8`, `10.9`, `12.9`
- Surface NONE: `무도금`, `no coating`, `no coat`, `coating none`, `표면처리X`
- Surface ZINC: `아연도금`, `zinc`, `zinc plated`, `Zn`

패턴으로 하나의 허용값을 확정하지 못하면 `null`을 반환합니다.

Validation은 개발 데이터이므로 현재 단계에서 패턴을 확인할 수 있지만,
A/B/C Validation 비교가 끝난 뒤 System C 패턴을 동결합니다.
Final Test 결과를 본 뒤에는 패턴을 수정하지 않습니다.

## 실행

System C는 vLLM 서버가 필요하지 않습니다.

```bash
uv run python scripts/run_system_c.py --split pilot
uv run python scripts/run_system_c.py --split validation
```

그다음 A/B/C 통합 비교:

```bash
uv run python scripts/reevaluate_results.py --split pilot
uv run python scripts/reevaluate_results.py --split validation
```

실패 사례:

```bash
uv run python scripts/show_common_failures.py --system C --split validation
```
