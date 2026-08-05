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

    print("[*] Running end-to-end SAGE Operational Intelligence (OIL) closed-loop optimization...")
    report = macc_orch.execute_operational_intelligence_optimization(
        task_objective="obj_continuous_development",
        milestones=[
            "Formulate multi-agent operational boundaries",
            "Coordinate secure custody handoffs",
            "Audit state-window contextual checksums"
        ]
    )

    print("\n[+] Operational Intelligence Closed-Loop Scenario Run Succeeded!")
    print(f"    - Run ID: {report['orchestrator_run_id']}")
    print(f"    - Anomaly Isolated: {report['latest_oil_incident']['incident_id']}")
    print(f"    - Prioritized Candidate ID: {report['latest_oil_improvement']['candidate_id']}")
    print(f"    - Prioritized Score: {report['latest_oil_improvement']['priority_score']}")
    print(f"    - MVI (Cycle Velocity speedup): {report['oil_metrics']['mission_velocity_index']}x")
    print(f"    - Evidence logged to: {macc_orch.evidence_output_path}\n")
    print(report["control_tower_status"])
    print("==========================================================")


if __name__ == "__main__":
    main()
