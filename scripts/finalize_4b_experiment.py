from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from bolt_thesis.paths import (
    DEFAULT_SYSTEM_A_FINAL_TEST_RESULT_PATH,
    DEFAULT_SYSTEM_B_FINAL_TEST_RESULT_PATH,
    DEFAULT_SYSTEM_C_FINAL_TEST_RESULT_PATH,
    EXPERIMENT_LOCK_PATH,
    FINAL_TEST_DATASET_PATH,
    FINAL_TEST_STATISTICS_PATH,
    FINAL_TEST_UNIFIED_RESULT_PATH,
    RESULTS_DIR,
)

FAIL_JSON = RESULTS_DIR / "final_test_failure_analysis.json"
FAIL_MD = RESULTS_DIR / "final_test_failure_analysis.md"
SUMMARY_JSON = RESULTS_DIR / "4b_final_summary.json"
SUMMARY_MD = RESULTS_DIR / "4b_final_summary.md"
MANIFEST_JSON = RESULTS_DIR / "4b_experiment_manifest.json"
ARCHIVE_DIR = RESULTS_DIR / "model_scale" / "qwen3_5_4b"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_frozen(lock: dict[str, Any]) -> None:
    root = EXPERIMENT_LOCK_PATH.parent.parent
    errors = []
    for rel, expected in lock["frozen_artifacts_sha256"].items():
        p = root / rel
        actual = sha256(p)
        if actual != expected:
            errors.append(f"{rel}: expected={expected} actual={actual}")
    dataset_expected = lock["final_test"]["dataset_sha256"]
    dataset_actual = sha256(FINAL_TEST_DATASET_PATH)
    if dataset_actual != dataset_expected:
        errors.append(f"Final Test dataset: expected={dataset_expected} actual={dataset_actual}")
    if errors:
        raise RuntimeError("Frozen artifact verification failed:\n" + "\n".join(errors))


def pct(x: float) -> str:
    return f"{x*100:.1f}%"


def main() -> None:
    required = [
        DEFAULT_SYSTEM_A_FINAL_TEST_RESULT_PATH,
        DEFAULT_SYSTEM_B_FINAL_TEST_RESULT_PATH,
        DEFAULT_SYSTEM_C_FINAL_TEST_RESULT_PATH,
        FINAL_TEST_UNIFIED_RESULT_PATH,
        FINAL_TEST_STATISTICS_PATH,
        FAIL_JSON,
        FAIL_MD,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required result(s): " + ", ".join(missing))

    lock = load(EXPERIMENT_LOCK_PATH)
    verify_frozen(lock)
    unified = load(FINAL_TEST_UNIFIED_RESULT_PATH)
    stats = load(FINAL_TEST_STATISTICS_PATH)
    failures = load(FAIL_JSON)

    systems = unified["systems"]
    summary = {
        "model": "Qwen/Qwen3.5-4B",
        "role": "primary_experiment",
        "dataset": unified["dataset"],
        "final_task_success": {s: systems[s]["final_task_success_rate"] for s in ("A", "B", "C")},
        "material_accuracy_on_sufficient": {s: systems[s]["material_accuracy_on_sufficient"] for s in ("A", "B", "C")},
        "routing_exact_on_sufficient": {s: systems[s]["routing_exact_rate_on_sufficient"] for s in ("A", "B", "C")},
        "required_fields_accuracy_on_missing": {s: systems[s]["required_fields_accuracy_on_missing"] for s in ("A", "B", "C")},
        "dangerous_guess_rate_on_missing": {s: systems[s]["dangerous_guess_rate_on_missing"] for s in ("A", "B", "C")},
        "attribute_exact": {s: systems[s].get("attribute_exact_rate") for s in ("A", "B", "C")},
        "failure_count": {s: failures["systems"][s]["failure_count"] for s in ("A", "B", "C")},
        "primary_statistics": stats["primary"]["final_task_success"],
        "rq1_routing_A_vs_B": stats["secondary"]["routing_exact_sufficient"]["A_vs_B"],
        "rq2_required_fields_A_vs_B": stats["secondary"]["required_fields_correct_missing"]["A_vs_B"],
        "rq2_no_dangerous_guess_A_vs_B": stats["secondary"]["no_dangerous_guess_missing"]["A_vs_B"],
        "rq3_attribute_A_vs_C_variant": stats["secondary"]["attribute_exact_A_vs_C"]["VARIANT"],
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# Qwen3.5-4B Final Experiment Summary", "",
        "## Final Task Success", "",
        "| System | Accuracy |", "|---|---:|",
        *[f"| {s} | **{pct(summary['final_task_success'][s])}** |" for s in ("A", "B", "C")],
        "", "## 핵심 해석", "",
        "- System A: Final Task Success 99%, 충분정보 Material/Routing 100%.",
        "- System B: Material 100%이나 Routing Exact 68.6%로 규칙 직접 실행에서 오류가 집중됨.",
        "- System C: VARIANT Attribute Exact 32.5%로 새로운 표현에 대한 고정 Regex 일반화 한계가 확인됨.",
        "- RQ2: A/B 모두 dangerous guess 0건으로 차이가 없었고, required-fields 정확도 차이도 통계적으로 뚜렷하지 않음.",
        "", "## 주요 통계", "",
    ]
    for label, r in summary["primary_statistics"].items():
        ci = r["bootstrap_95_ci_difference"]
        md.append(f"- {label}: Δ={r['difference_left_minus_right']:+.3f}, 95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}], McNemar p={r['mcnemar']['exact_two_sided_p']:.6g}")
    SUMMARY_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    result_files = [
        DEFAULT_SYSTEM_A_FINAL_TEST_RESULT_PATH,
        DEFAULT_SYSTEM_B_FINAL_TEST_RESULT_PATH,
        DEFAULT_SYSTEM_C_FINAL_TEST_RESULT_PATH,
        FINAL_TEST_UNIFIED_RESULT_PATH,
        FINAL_TEST_STATISTICS_PATH,
        FAIL_JSON,
        FAIL_MD,
        SUMMARY_JSON,
        SUMMARY_MD,
    ]
    manifest = {
        "model": "Qwen/Qwen3.5-4B",
        "experiment_role": "primary_experiment",
        "status": "COMPLETED_4B_FINAL_TEST",
        "final_test_dataset_sha256": sha256(FINAL_TEST_DATASET_PATH),
        "frozen_artifacts_sha256": lock["frozen_artifacts_sha256"],
        "result_files_sha256": {str(p.relative_to(RESULTS_DIR.parent)): sha256(p) for p in result_files},
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    for p in result_files + [MANIFEST_JSON]:
        shutil.copy2(p, ARCHIVE_DIR / p.name)

    lock["version"] = "1.2"
    lock["current_experiment"]["status"] = "COMPLETED_4B_FINAL_TEST"
    lock["current_experiment"]["completed_date"] = "2026-10-22"
    lock["final_test"]["execution_status"] = "COMPLETED"
    lock["final_test"]["canonical_results"] = {
        "A_final_task_success": systems["A"]["final_task_success_rate"],
        "B_final_task_success": systems["B"]["final_task_success_rate"],
        "C_final_task_success": systems["C"]["final_task_success_rate"],
    }
    lock["final_test"]["result_files_sha256"] = manifest["result_files_sha256"]
    lock["post_hoc_model_scale_analysis"] = {
        "status": "PLANNED_NOT_RUN",
        "model": "Qwen/Qwen3.5-9B",
        "role": "post-hoc model-scale sensitivity analysis",
        "policy": "Reuse the frozen Final Test and unchanged A/B prompts, rules, schemas, and generation settings; change only the model ID. Do not reinterpret the 9B run as part of the preregistered 4B primary experiment.",
    }
    EXPERIMENT_LOCK_PATH.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(EXPERIMENT_LOCK_PATH, ARCHIVE_DIR / "experiment_lock_snapshot.json")

    print("Frozen artifacts: PASS")
    print("Final Test dataset hash: PASS")
    print("4B experiment status: COMPLETED_4B_FINAL_TEST")
    print(f"Saved: {SUMMARY_JSON}")
    print(f"Saved: {SUMMARY_MD}")
    print(f"Saved: {MANIFEST_JSON}")
    print(f"Archived: {ARCHIVE_DIR}")


if __name__ == "__main__":
    main()
