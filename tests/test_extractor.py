import pytest

from bolt_thesis.extractor.validator import (
    ExtractionValidationError,
    validate_extraction,
)


def test_valid_extraction() -> None:
    value = {
        "diameter_mm": 20,
        "length_mm": 80,
        "strength_grade": "10.9",
        "surface_treatment": "ZINC_PLATED",
    }
    assert validate_extraction(value) == value


def test_null_is_valid() -> None:
    value = {
        "diameter_mm": 20,
        "length_mm": 80,
        "strength_grade": None,
        "surface_treatment": None,
    }
    assert validate_extraction(value) == value


def test_unknown_value_is_rejected() -> None:
    value = {
        "diameter_mm": 14,
        "length_mm": 80,
        "strength_grade": "10.9",
        "surface_treatment": "ZINC_PLATED",
    }

    with pytest.raises(ExtractionValidationError):
        validate_extraction(value)
