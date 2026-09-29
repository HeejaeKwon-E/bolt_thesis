from bolt_thesis.system_b.prompt import build_system_b_prompt
from bolt_thesis.system_b.validator import validate_system_b_output


def test_prompt_contains_same_rule_ids() -> None:
    prompt = build_system_b_prompt()
    for rule_id in (
        "R01",
        "R02",
        "R03",
        "R04",
        "R05",
        "R06",
        "R07",
        "R08",
        "R09",
        "R10",
        "R11",
    ):
        assert rule_id in prompt


def test_valid_ok_output() -> None:
    value = {
        "status": "OK",
        "material": "MAT_ALLOY_01",
        "routing": [
            "CUTTING",
            "HOT_FORMING",
            "THREAD_ROLLING",
            "HEAT_TREATMENT",
            "ZINC_PLATING",
            "INSPECTION",
            "PACKAGING",
        ],
        "required_fields": [],
    }
    assert validate_system_b_output(value) == value


def test_valid_clarification_output() -> None:
    value = {
        "status": "CLARIFICATION_REQUIRED",
        "material": None,
        "routing": [],
        "required_fields": ["strength_grade"],
    }
    assert validate_system_b_output(value) == value
