from __future__ import annotations
import argparse, json
from collections import defaultdict
from pathlib import Path
from bolt_thesis.paths import DEFAULT_SYSTEM_A_VALIDATION_RESULT_PATH, VALIDATION_DATASET_PATH

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--result",default=str(DEFAULT_SYSTEM_A_VALIDATION_RESULT_PATH)); args=ap.parse_args()
    dataset=json.loads(VALIDATION_DATASET_PATH.read_text(encoding="utf-8")); result=json.loads(Path(args.result).read_text(encoding="utf-8"))
    cond={x["id"]:x["condition"] for x in dataset["items"]}; rows=defaultdict(lambda:{"total":0,"correct":0,"schema_valid":0})
    for x in result["items"]:
        if x.get("model_output_raw") is None: continue
        r=rows[cond[x["id"]]]; r["total"]+=1; r["schema_valid"]+=int(x.get("schema_valid") is True); r["correct"]+=int(x.get("all_attributes_correct") is True)
    print("condition,total,schema_valid,all_attributes_correct,accuracy")
    for c in ("NORMAL","VARIANT","MISSING"):
        r=rows[c]; acc=r["correct"]/r["total"] if r["total"] else 0.0
        print(f"{c},{r['total']},{r['schema_valid']},{r['correct']},{acc:.4f}")

if __name__=="__main__": main()
