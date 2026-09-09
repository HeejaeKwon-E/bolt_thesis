from __future__ import annotations

import json
from pathlib import Path

from bolt_thesis.rule_engine import RuleEngine
from bolt_thesis.paths import PILOT_DATASET_PATH

engine = RuleEngine()

# Pilot: 정상 10 / 표기 변형 10 / 필수정보 누락 10
cases = [
    # NORMAL
    ('P-N-001','NORMAL','M8×30 규격, 8.8급, 무도금 육각볼트 개발 요청',8,30,'8.8','NONE',[]),
    ('P-N-002','NORMAL','M10×50 규격의 8.8급 아연도금 육각볼트 검토 요청',10,50,'8.8','ZINC_PLATED',[]),
    ('P-N-003','NORMAL','M12×80, 강도등급 10.9, 무도금 육각볼트 개발 요청',12,80,'10.9','NONE',[]),
    ('P-N-004','NORMAL','M16×60 규격, 10.9급, 아연도금 육각볼트 요청',16,60,'10.9','ZINC_PLATED',[]),
    ('P-N-005','NORMAL','M20×100 규격의 12.9급 무도금 육각볼트 개발 검토',20,100,'12.9','NONE',[]),
    ('P-N-006','NORMAL','M8×120, 10.9급, 아연도금 육각볼트 개발 요청',8,120,'10.9','ZINC_PLATED',[]),
    ('P-N-007','NORMAL','M12×30 규격, 강도등급 12.9, 아연도금 육각볼트 요청',12,30,'12.9','ZINC_PLATED',[]),
    ('P-N-008','NORMAL','M16×80 규격의 8.8급 무도금 육각볼트 개발 요청',16,80,'8.8','NONE',[]),
    ('P-N-009','NORMAL','M20×60, 10.9급, 아연도금 육각볼트 검토 요청',20,60,'10.9','ZINC_PLATED',[]),
    ('P-N-010','NORMAL','M10×100 규격, 12.9급, 무도금 육각볼트 개발 요청',10,100,'12.9','NONE',[]),

    # VARIANT: Pilot에서 공개 표현으로 취급
    ('P-V-001','VARIANT','8파이 30, G8.8, 무도금 볼트',8,30,'8.8','NONE',['KOREAN_DIAMETER','GRADE_PREFIX']),
    ('P-V-002','VARIANT','볼트 10파이 L50 / 8.8 / Zn',10,50,'8.8','ZINC_PLATED',['KOREAN_DIAMETER','LENGTH_PREFIX','SYMBOL_ZN']),
    ('P-V-003','VARIANT','M12*80 G10.9 no coating',12,80,'10.9','NONE',['ASTERISK_SIZE','GRADE_PREFIX','ENGLISH_SURFACE']),
    ('P-V-004','VARIANT','16Φ-60L / class10.9 / zinc',16,60,'10.9','ZINC_PLATED',['PHI_SYMBOL','L_SUFFIX','ENGLISH_GRADE','ENGLISH_SURFACE']),
    ('P-V-005','VARIANT','20파이 100롱, 12.9, 무도금',20,100,'12.9','NONE',['KOREAN_DIAMETER','KOREAN_LENGTH_SLANG']),
    ('P-V-006','VARIANT','M8 L120, grade 10.9, Zn plated',8,120,'10.9','ZINC_PLATED',['LENGTH_PREFIX','ENGLISH_GRADE','ENGLISH_SURFACE']),
    ('P-V-007','VARIANT','12Ø x 30 / G12.9 / zinc coat',12,30,'12.9','ZINC_PLATED',['DIAMETER_SYMBOL','X_SEPARATOR','GRADE_PREFIX','ENGLISH_SURFACE']),
    ('P-V-008','VARIANT','M16-80 8.8급 표면처리X',16,80,'8.8','NONE',['HYPHEN_SIZE','NO_TREATMENT_SYMBOL']),
    ('P-V-009','VARIANT','20Ø80L / G10.9 / ZN',20,80,'10.9','ZINC_PLATED',['DIAMETER_SYMBOL','L_SUFFIX','GRADE_PREFIX','SYMBOL_ZN']),
    ('P-V-010','VARIANT','10파이 길이100, 12.9class, coating none',10,100,'12.9','NONE',['KOREAN_DIAMETER','MIXED_GRADE','ENGLISH_SURFACE']),

    # MISSING
    ('P-M-001','MISSING','M8×30, 8.8급 육각볼트 요청',8,30,'8.8',None,[]),
    ('P-M-002','MISSING','M10×50 아연도금 육각볼트 요청',10,50,None,'ZINC_PLATED',[]),
    ('P-M-003','MISSING','M12 규격, 10.9급, 무도금 육각볼트 요청',12,None,'10.9','NONE',[]),
    ('P-M-004','MISSING','길이 60mm, 10.9급, 아연도금 육각볼트 요청',None,60,'10.9','ZINC_PLATED',[]),
    ('P-M-005','MISSING','M20×100 육각볼트 개발 요청',20,100,None,None,[]),
    ('P-M-006','MISSING','12.9급 아연도금 육각볼트 요청',None,None,'12.9','ZINC_PLATED',[]),
    ('P-M-007','MISSING','M8×120 무도금 볼트',8,120,None,'NONE',[]),
    ('P-M-008','MISSING','16파이, G8.8, Zn 볼트',16,None,'8.8','ZINC_PLATED',['KOREAN_DIAMETER','GRADE_PREFIX','SYMBOL_ZN']),
    ('P-M-009','MISSING','L80 / 10.9 / 무도금 육각볼트',None,80,'10.9','NONE',['LENGTH_PREFIX']),
    ('P-M-010','MISSING','M20×60 12.9급 볼트',20,60,'12.9',None,[]),
]

items = []
for case_id, condition, text, diameter, length, grade, surface, tags in cases:
    attrs = {
        'diameter_mm': diameter,
        'length_mm': length,
        'strength_grade': grade,
        'surface_treatment': surface,
    }
    expected = engine.run(attrs)
    item = {
        'id': case_id,
        'condition': condition,
        'text': text,
        'ground_truth': {
            'attributes': attrs,
            'expected_output': expected,
        },
    }
    if tags:
        item['variation_tags'] = tags
    items.append(item)

dataset = {
    'dataset_name': 'bolt_pilot_v0_1',
    'version': '0.1',
    'purpose': '시스템 A/B/C 구현 전 전체 파이프라인 검증용 Pilot 데이터',
    'is_final_test': False,
    'notes': [
        'Pilot의 표기 변형은 공개 표현으로 간주한다.',
        'Pilot 결과를 보고 규칙, 스키마, 프롬프트, 정규식을 수정할 수 있다.',
        '최종 Test용 비공개 표현은 Pilot 이후 별도 파일로 관리한다.',
        '최종 Test 생성 후에는 규칙, 프롬프트, 정규식을 고정한다.'
    ],
    'summary': {'total': 30, 'NORMAL': 10, 'VARIANT': 10, 'MISSING': 10},
    'items': items,
}

PILOT_DATASET_PATH.write_text(
    json.dumps(dataset, ensure_ascii=False, indent=2), encoding='utf-8'
)
print('created pilot_dataset.json')
