from bolt_thesis.rule_engine import RuleEngine


def test_complete_input() -> None:
    engine = RuleEngine()
    result = engine.run(
        {
            "diameter_mm": 20,
            "length_mm": 80,
            "strength_grade": "10.9",
            "surface_treatment": "ZINC_PLATED",
        }
    )

    assert result["status"] == "OK"
    assert result["material"] == "MAT_ALLOY_01"
    assert "HOT_FORMING" in result["routing"]
    assert "ZINC_PLATING" in result["routing"]


def test_missing_required_field() -> None:
    engine = RuleEngine()
    result = engine.run(
        {
            "diameter_mm": 20,
            "length_mm": 80,
            "strength_grade": None,
            "surface_treatment": "ZINC_PLATED",
        }
    )

    assert result["status"] == "CLARIFICATION_REQUIRED"
    assert result["required_fields"] == ["strength_grade"]
