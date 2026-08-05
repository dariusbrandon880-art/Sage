#!/usr/bin/env python3
"""Repeatable runner script for SAGE Multi-Agent Operational Scenario Validation."""

import os
import sys

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sage.experimental.act.ccl_orchestrator import SAGEOperationalOrchestrator


def main():
    print("==========================================================")
    print("  SAGE MULTI-AGENT OPERATIONAL SCENARIO VALIDATION RUNNER")
    print("==========================================================")

    macc_orch = SAGEOperationalOrchestrator(session_id="session_operational_validation")

    print("[*] Running end-to-end Operational Workflow scenario validation...")
    report = macc_orch.execute_two_role_coordination_and_recovery_loop(
        task_objective="obj_continuous_development",
        milestones=[
            "Formulate multi-agent operational boundaries",
            "Coordinate secure custody handoffs",
            "Audit state-window contextual checksums"
        ],
        simulate_recovery=True
    )

    print("\n[+] Operational Scenario Validation Run Succeeded!")
    print(f"    - Run ID: {report['orchestrator_run_id']}")
    print(f"    - Claude Review Contract: {report['review_contract']['contract_id']}")
    print(f"    - Evidence logged to: {macc_orch.evidence_output_path}\n")
    print(report["control_tower_status"])
    print("==========================================================")


if __name__ == "__main__":
    main()
