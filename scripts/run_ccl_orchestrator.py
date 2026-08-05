#!/usr/bin/env python3
"""Repeatable runner script for SAGE Multi-Agent Operational Scenario Validation."""

import os
import sys
from pathlib import Path

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sage.experimental.act.ccl_orchestrator import SAGEOperationalOrchestrator


def main():
    print("==========================================================")
    print("  SAGE MULTI-AGENT OPERATIONAL SCENARIO VALIDATION RUNNER")
    print("==========================================================")

    macc_orch = SAGEOperationalOrchestrator(session_id="session_operational_validation")

    # Assert and verify emergency stop check is operational beforehand
    print("[*] Running programmatic emergency stop safety check...")
    macc_orch.check_emergency_stop_override()
    print("    - Safety check passed cleanly. No EMERGENCY_STOP files found.")

    print("\n[*] Running end-to-end SAGE Controlled Runtime Activation Validation loop...")
    report = macc_orch.execute_controlled_runtime_activation_validation(
        task_objective="obj_continuous_development",
        milestones=[
            "Formulate multi-agent operational boundaries",
            "Coordinate secure custody handoffs",
            "Audit state-window contextual checksums"
        ]
    )

    print("\n[+] Controlled Runtime Activation Run Succeeded!")
    print(f"    - Run ID: {report['orchestrator_run_id']}")
    print(f"    - Active Recoveries (Rollback Corrupted PML Checkpoints): {len(report['failure_recovery_logs'])}")
    print(f"    - Baseline Tasks Processed: {report['metrics_baseline']['tasks_processed']}")
    print(f"    - Evidence logged to: {macc_orch.evidence_output_path}\n")
    print(report["control_tower_status"])
    print("==========================================================")


if __name__ == "__main__":
    main()
