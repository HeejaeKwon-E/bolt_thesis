import json

from bolt_thesis.paths import PILOT_DATASET_PATH
from scripts.reevaluate_results import _attach_conditions


def test_attach_conditions_to_system_a_shaped_result():
    dataset = json.loads(PILOT_DATASET_PATH.read_text(encoding="utf-8"))
    first = dataset["items"][0]

    run = {
        "items": [
            {
                "id": first["id"],
                "text": first["text"],
                "ground_truth_attributes": first["ground_truth"]["attributes"],
            }
        ]
    }

    result = _attach_conditions(run, "pilot")
    assert result["items"][0]["condition"] == first["condition"]
