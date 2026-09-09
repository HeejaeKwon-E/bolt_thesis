from __future__ import annotations

from typing import Any

from bolt_thesis.extractor.validator import validate_extraction
from bolt_thesis.rule_engine import RuleEngine


class SystemAPipeline:
    def __init__(self) -> None:
        self.rule_engine = RuleEngine()

    def run_from_extraction(
        self,
        extraction: str | dict[str, Any],
    ) -> dict[str, Any]:
        attributes = validate_extraction(extraction)
        result = self.rule_engine.run(attributes)

        return {
            "attributes": attributes,
            "result": result,
        }
