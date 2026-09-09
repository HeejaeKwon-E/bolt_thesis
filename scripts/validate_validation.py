from __future__ import annotations
import json
from bolt_thesis.paths import EXTRACTOR_PROMPT_PATH, PILOT_DATASET_PATH, VALIDATION_DATASET_PATH
from bolt_thesis.rule_engine import RuleEngine

def combo(a): return (a["diameter_mm"],a["length_mm"],a["strength_grade"],a["surface_treatment"])
def complete(a): return all(v is not None for v in a.values())

def main() -> None:
    pilot=json.loads(PILOT_DATASET_PATH.read_text(encoding="utf-8")); prompt=json.loads(EXTRACTOR_PROMPT_PATH.read_text(encoding="utf-8")); val=json.loads(VALIDATION_DATASET_PATH.read_text(encoding="utf-8")); engine=RuleEngine()
    ptexts={x["text"] for x in pilot["items"]}; ftexts={x["input"] for x in prompt["few_shot_examples"]}
    blocked={combo(x["ground_truth"]["attributes"]) for x in pilot["items"] if complete(x["ground_truth"]["attributes"])} | {combo(x["output"]) for x in prompt["few_shot_examples"] if complete(x["output"])}
    ids=set(); combos=set(); failures=[]
    for x in val["items"]:
        if x["id"] in ids: failures.append(f"duplicate id: {x['id']}")
        ids.add(x["id"])
        if x["text"] in ptexts: failures.append(f"pilot text overlap: {x['id']}")
        if x["text"] in ftexts: failures.append(f"few-shot text overlap: {x['id']}")
        a=x["ground_truth"]["attributes"]
        if engine.run(a)!=x["ground_truth"]["expected_output"]: failures.append(f"rule mismatch: {x['id']}")
        if complete(a):
            c=combo(a)
            if c in blocked: failures.append(f"combo overlap: {x['id']} {c}")
            if c in combos: failures.append(f"duplicate validation combo: {x['id']} {c}")
            combos.add(c)
    counts={c:sum(1 for x in val["items"] if x["condition"]==c) for c in ("NORMAL","VARIANT","MISSING")}
    print(f"items: {len(val['items'])}"); print(f"condition counts: {counts}"); print(f"unique complete validation combos: {len(combos)}"); print(f"failures: {len(failures)}")
    if failures:
        print("\n".join(failures[:20])); raise SystemExit(1)

if __name__=="__main__": main()
