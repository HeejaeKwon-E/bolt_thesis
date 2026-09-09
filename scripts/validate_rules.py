from __future__ import annotations

import itertools
import json

from bolt_thesis.paths import ATTRIBUTES_PATH
from bolt_thesis.rule_engine import RuleEngine


def main() -> None:
    with ATTRIBUTES_PATH.open("r", encoding="utf-8") as f:
        definitions = json.load(f)["attributes"]

    engine = RuleEngine()
    failures = []
    total = 0

    for diameter, length, grade, surface in itertools.product(
        definitions["diameter_mm"]["values"],
        definitions["length_mm"]["values"],
        definitions["strength_grade"]["values"],
        definitions["surface_treatment"]["values"],
    ):
        total += 1
        attrs = {
            "diameter_mm": diameter,
            "length_mm": length,
            "strength_grade": grade,
            "surface_treatment": surface,
        }

        try:
            result = engine.run(attrs)
            if result["status"] != "OK":
                failures.append({"attrs": attrs, "result": result})
        except Exception as exc:
            failures.append({"attrs": attrs, "error": repr(exc)})

    print(f"combinations: {total}")
    print(f"failures: {len(failures)}")

    if failures:
        print(json.dumps(failures[:10], ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
