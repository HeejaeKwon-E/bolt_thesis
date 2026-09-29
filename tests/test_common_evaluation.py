from bolt_thesis.evaluation.common import _routing_prf, _system_b_semantic_valid


def test_routing_prf_exact() -> None:
    p, r, f1 = _routing_prf(["CUTTING", "INSPECTION"], ["CUTTING", "INSPECTION"])
    assert (p, r, f1) == (1.0, 1.0, 1.0)


def test_semantic_invalid_clarification_with_routing() -> None:
    valid, errors = _system_b_semantic_valid(
        {
            "status": "CLARIFICATION_REQUIRED",
            "material": None,
            "routing": ["CUTTING"],
            "required_fields": ["strength_grade"],
        }
    )
    assert valid is False
    assert "CLARIFICATION_REQUIRES_EMPTY_ROUTING" in errors
