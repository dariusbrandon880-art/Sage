#!/usr/bin/env python3
"""Demonstration Script for SAGE Stage 2 — Controlled Self-Application Flight.

Runs a live bounded self-application flight using `SAGEWorkflowControlLoop` to govern
a real engineering task cycle across all 8 progression stages, persisting evidence
artifacts to `evidence_capture/workflow_control_flight_001.json`.
"""

import sys
import os
import json
from pathlib import Path

repo_root = str(Path(__file__).resolve().parent.parent)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from sage.experimental.workflow_control import (
    SAGEWorkflowControlLoop,
    WorkflowExecutionRequest,
)
from sage.experimental.flight_record import SAGEFlightRecordManager


def main():
    print("=" * 70)
    print(" SAGE STAGE 2 — CONTROLLED SELF-APPLICATION FLIGHT EXECUTION")
    print("=" * 70)

    ledger_path = Path("evidence_capture/flight_records_ledger.json")
    manager = SAGEFlightRecordManager(flight_ledger_path=ledger_path)
    control_loop = SAGEWorkflowControlLoop(flight_manager=manager)

    mission_id = "mission_stage2_flight_001"
    objective = "Execute bounded engineering workflow control loop for SAGE self-application"

    print(f"[+] Initializing Request:")
    print(f"    Mission ID: {mission_id}")
    print(f"    Objective: {objective}")
    print(f"    Assigned Agent: agent_jules_sage")

    request = WorkflowExecutionRequest(
        mission_id=mission_id,
        objective=objective,
        assigned_agent="agent_jules_sage",
        priority_score=92.0,
        task_payload={"target_files": ["sage/experimental/workflow_control.py"]},
    )

    print("[+] Executing Governed 8-Stage Workflow Cycle...")
    result = control_loop.execute_governed_cycle(request)

    print(f"[+] Flight Execution Result:")
    print(f"    Execution ID: {result.execution_id}")
    print(f"    Final Stage: {result.final_stage}")
    print(f"    PFC Decision Outcome: {result.pfc_decision_outcome}")
    print(f"    Total Transition Receipts: {len(result.progression_receipts)}")
    print(f"    Integrity Hash: {result.integrity_hash}")
    print(f"    Next Decision State: {result.next_decision_state['decision']}")
    print(f"    Self-Authorization Permitted: {result.next_decision_state['self_authorization_permitted']}")

    # Persist artifact
    output_path = Path("evidence_capture/workflow_control_flight_001.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    artifact_data = {
        "metadata": {
            "flight_type": "STAGE_2_SELF_APPLICATION_FLIGHT",
            "classification": "GOVERNED_WORKFLOW_SELF_APPLICATION",
            "execution_id": result.execution_id,
            "mission_id": result.mission_id,
            "governance": "SAGE CONTROLLED STAGE 2 AUTHORIZATION ONLY",
        },
        "execution_result": result.model_dump() if hasattr(result, "model_dump") else result.__dict__,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(artifact_data, f, indent=2, default=str)

    print("=" * 70)
    print(f"[+] Execution Flight Artifact Persisted To: {output_path}")
    print(f"[+] Flight Ledger Updated At: {ledger_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
