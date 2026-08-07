#!/usr/bin/env python3
"""CLI Script to generate structured SAGE Capability Improvement History demonstration reports."""

import os
import sys
import json
from pathlib import Path

# Resolve project root dynamically to allow direct execution
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sage.experimental.act.capability_measurement import (
    CapabilityMeasurementEngine,
    CapabilityImprovementHistory
)


def main():
    print("==================================================================")
    print("      SAGE CAPABILITY IMPROVEMENT HISTORY ENGINE                 ")
    print("==================================================================\n")

    base_dir = Path("evidence_capture")
    baseline_path = base_dir / "phase_4_controlled_evaluation_evidence_scenario_a.json"

    if not baseline_path.exists():
        print(f"[-] Error: Baseline evidence file {baseline_path} not found.")
        sys.exit(1)

    print(f"[+] Loading baseline evidence: {baseline_path}")
    with open(baseline_path, "r", encoding="utf-8") as f:
        baseline_data = json.load(f)

    cap_id = "CAP-PHASE-4-EVAL"
    history = CapabilityImprovementHistory(capability_id=cap_id)
    engine = CapabilityMeasurementEngine()

    # 1. Run 1: Base validation run (Initial Baseline, so no comparative baseline yet)
    print("[1] Compiling Run 1: Initial Baseline...")
    rec_1 = engine.compare_runs(cap_id, current_data=baseline_data, baseline_data=None)
    history.add_measurement_run(rec_1)

    # 2. Run 2: Improved execution
    print("[2] Compiling Run 2: Improved Capability Run...")
    run_2_data = json.loads(json.dumps(baseline_data))  # Deep copy
    run_2_data["run_identifier"] = "run_phase4_eval_run_2"
    run_2_data["evaluation_id"] = "eval_phase4_scenario_a_002"
    run_2_data["timestamp"] = "2026-08-05T12:00:00Z"

    # Simulate improvements (faster execution, more steps reduced, more checks)
    m2 = run_2_data["metrics"]
    m2["efficiency"]["sage_assisted_duration_mins"] = max(1.0, m2["efficiency"]["sage_assisted_duration_mins"] - 1.5)
    m2["efficiency"]["steps_reduced"] += 2
    m2["efficiency"]["review_effort_reduction_percent"] = round(
        ((m2["efficiency"]["manual_baseline_estimate_mins"] - m2["efficiency"]["sage_assisted_duration_mins"]) / m2["efficiency"]["manual_baseline_estimate_mins"]) * 100.0,
        1
    )
    m2["governance"]["validation_checks_completed"] += 3

    rec_2 = engine.compare_runs(cap_id, current_data=run_2_data, baseline_data=baseline_data)
    history.add_measurement_run(rec_2)

    # 3. Run 3: Regressed execution
    print("[3] Compiling Run 3: Regressed Capability Run...")
    run_3_data = json.loads(json.dumps(baseline_data))  # Deep copy
    run_3_data["run_identifier"] = "run_phase4_eval_run_3"
    run_3_data["evaluation_id"] = "eval_phase4_scenario_a_003"
    run_3_data["timestamp"] = "2026-08-06T12:00:00Z"

    # Simulate regressions (longer execution, fewer steps reduced)
    m3 = run_3_data["metrics"]
    m3["efficiency"]["sage_assisted_duration_mins"] = m3["efficiency"]["sage_assisted_duration_mins"] + 2.0
    m3["efficiency"]["steps_reduced"] = max(1, m3["efficiency"]["steps_reduced"] - 3)

    rec_3 = engine.compare_runs(cap_id, current_data=run_3_data, baseline_data=run_2_data)
    history.add_measurement_run(rec_3)

    # 4. Resolve Latest Validated State
    latest_validated = history.get_latest_validated_state()
    latest_val_id = latest_validated.run_id if latest_validated else "None"
    print(f"\n[+] Progression Summary computed:")
    for summary in history.get_history_summary():
         print(f"    - Run: {summary['run_id']} | Status: {summary['classification']} | Improved metrics: {summary['improved_metrics_count']}")

    print(f"\n[+] Retained Validated State (retaining best-validated state): {latest_val_id}")

    # 5. Persist History Report
    out_path = base_dir / "capability_improvement_history.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(history.model_dump(), f, indent=2)

    print(f"\n[+] Successfully generated structured improvement history at {out_path}")


if __name__ == "__main__":
    main()
