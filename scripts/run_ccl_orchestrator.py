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

    print("[*] Running end-to-end Production Reliability & Failure Injection simulation...")
    report = macc_orch.execute_production_reliability_simulation(
        task_objective="obj_continuous_development",
        milestones=[
            "Harden multi-agent persistence keys",
            "Verify fault interception mechanics",
            "Onboard future Gemini validation scouts"
        ]
    )

    print("\n[+] Operational Production Reliability Scenario Run Succeeded!")
    print(f"    - Run ID: {report['orchestrator_run_id']}")
    print(f"    - Onboarded Future Contract ID: {report['future_agent_entry_contract']['agent_id']}")
    print(f"    - Active Recovered Faults: {len(report['failure_recovery_logs'])}")
    print(f"    - Evidence logged to: {macc_orch.evidence_output_path}\n")
    print(report["control_tower_status"])
    print("==========================================================")


if __name__ == "__main__":
    main()
