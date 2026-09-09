from __future__ import annotations
import argparse, json, time
from pathlib import Path
from typing import Any
from bolt_thesis.clients.vllm import VLLMClient
from bolt_thesis.evaluation.system_a import evaluate_system_a_run
from bolt_thesis.paths import DEFAULT_SYSTEM_A_VALIDATION_RESULT_PATH, VALIDATION_SYSTEM_A_RUN_TEMPLATE_PATH

def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def save_json(path: str | Path, data: dict[str, Any]) -> None:
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

def main() -> None:
    ap=argparse.ArgumentParser(description="Run System A Validation with vLLM")
    ap.add_argument("--output",default=str(DEFAULT_SYSTEM_A_VALIDATION_RESULT_PATH))
    ap.add_argument("--limit",type=int,default=None)
    ap.add_argument("--resume",action="store_true")
    args=ap.parse_args(); output=Path(args.output)
    run=load_json(output) if args.resume and output.exists() else load_json(VALIDATION_SYSTEM_A_RUN_TEMPLATE_PATH)
    client=VLLMClient(); server=client.check_server()
    if not server["model_available"]: raise RuntimeError(f"model not served: {server['served_models']}")
    run["run_metadata"].update({"base_url":client.base_url,"model":client.model_id,"temperature":client.temperature,"seed":client.seed,"max_tokens":client.max_tokens,"structured_output":client.structured_output,"quantization":None})
    items=run["items"][:args.limit] if args.limit else run["items"]
    started=time.perf_counter()
    for i,item in enumerate(items,1):
        if args.resume and item.get("model_output_raw") is not None:
            print(f"[{i}/{len(items)}] {item['id']} SKIP"); continue
        print(f"[{i}/{len(items)}] {item['id']} ...",flush=True)
        try:
            g=client.generate(item["text"])
            item.update({"model_output_raw":g["raw_output"],"latency_sec":g["latency_sec"],"input_tokens":g["input_tokens"],"output_tokens":g["output_tokens"],"finish_reason":g["finish_reason"],"error":None})
        except Exception as exc:
            item["error"]=f"{type(exc).__name__}: {exc}"
        save_json(output,run)
    run["run_metadata"]["wall_time_sec"]=time.perf_counter()-started
    evaluated=evaluate_system_a_run(run); evaluated["summary"]["structured_output"]=client.structured_output
    save_json(output,evaluated)
    print(json.dumps(evaluated["summary"],ensure_ascii=False,indent=2)); print(f"Saved: {output}")

if __name__=="__main__": main()
