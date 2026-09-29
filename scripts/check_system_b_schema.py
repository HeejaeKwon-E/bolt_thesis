from __future__ import annotations

import json

from bolt_thesis.paths import SYSTEM_B_SCHEMA_PATH


def main() -> None:
    schema = json.loads(SYSTEM_B_SCHEMA_PATH.read_text(encoding="utf-8"))
    routing = schema["properties"]["routing"]
    required_fields = schema["properties"]["required_fields"]
    print("System B schema compatibility check")
    print("routing.uniqueItems:", routing.get("uniqueItems"))
    print("required_fields.uniqueItems:", required_fields.get("uniqueItems"))
    assert "uniqueItems" not in routing
    assert "uniqueItems" not in required_fields
    print("PASS")


if __name__ == "__main__":
    main()
