from bolt_thesis.system_c import RegexDictionaryExtractor


def test_normal_size_pair():
    ex = RegexDictionaryExtractor()
    assert ex.extract("M10×50 규격의 8.8급 아연도금 육각볼트") == {
        "diameter_mm": 10,
        "length_mm": 50,
        "strength_grade": "8.8",
        "surface_treatment": "ZINC_PLATED",
    }


def test_variant_heavy():
    ex = RegexDictionaryExtractor()
    assert ex.extract("no coat / G10.9 / 100L / 20파이") == {
        "diameter_mm": 20,
        "length_mm": 100,
        "strength_grade": "10.9",
        "surface_treatment": "NONE",
    }


def test_missing_surface_is_not_none_coating():
    ex = RegexDictionaryExtractor()
    assert ex.extract("Ø16 x 60L, 8.8급. coating 정보 없음.") == {
        "diameter_mm": 16,
        "length_mm": 60,
        "strength_grade": "8.8",
        "surface_treatment": None,
    }


def test_standalone_m_size():
    ex = RegexDictionaryExtractor()
    assert ex.extract("M12 규격, 10.9급, 무도금 육각볼트 요청") == {
        "diameter_mm": 12,
        "length_mm": None,
        "strength_grade": "10.9",
        "surface_treatment": "NONE",
    }
