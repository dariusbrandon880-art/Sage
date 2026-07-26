"""SAGE Mission 0.6 Phase 3 — Sandbox Active Enforcement Simulation.

Demonstrates:
"Anomalous action observed -> SAGE evaluated -> execution blocked -> state rolled back -> integrity preserved."
"""

import os
import json
import tempfile
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sage.runtime import SageRuntime
from sage.acr.bond import BondValidationError
from sage.core.boundary import BoundaryEnforcer


def run_enforcement_simulation():
    print("=== SAGE MISSION 0.6 PHASE 3 ENFORCEMENT SIMULATION ===")

    # 1. Force SAGE_BOND_MODE="enforce"
    os.environ["SAGE_BOND_MODE"] = "enforce"
    print("[*] SAGE_BOND_MODE set to 'enforce'")

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"[*] Initializing SageRuntime in temporary workspace: {workspace}")
        runtime = SageRuntime(str(workspace))
        runtime.start()

        # Confirm BondManager initialized and mode matches enforce
        assert runtime.bond_mode == "enforce"
        print("[✓] Runtime active. BondManager in active enforce mode.")

        # Let's check initial state (S0 backup baseline)
        s0_state = {"current_project_state": "S0", "active_milestone": "milestone_0"}
        print(f"[*] S0 State Baseline: {s0_state}")

        # --- STEP 1: Simulating Prohibited State Mutation (Out-of-order sequence) ---
        print("\n--- STEP 1: Simulating Prohibited Sequence Mutation ---")

        # Out-of-order sequence: S0 -> Validation directly (bypassing Delta and Evidence)
        prohibited_payload = {
            "from_state": "S0",
            "to_state": "Validation",  # Prohibited sequence!
            "description": "Malicious autonomous workflow bypassing STP stages",
            "author": "autonomous_agent_node_x",
            "validation_score": 0.95,
            "auth_token": BoundaryEnforcer.SYSTEM_TOKEN
        }

        print(f"[*] Requesting mutation: S0 -> Validation (Author: '{prohibited_payload['author']}')")

        # --- STEP 2: Policy Evaluation & Active Enforcement Decision ---
        print("\n--- STEP 2: Evaluating Policy & Executing Enforcement ---")
        try:
            runtime.bond_manager.execute_transition(s0_state, prohibited_payload)
            print("[✗] Error: Prohibited transition was allowed! Enforcement failed.")
        except BondValidationError as bve:
            print("[✓] ACTIVE ENFORCEMENT TRIGGERED!")
            print(f"[Evidence] Error Code: {bve.error_code}")
            print(f"[Evidence] Verification Result: {bve.message}")

            assert bve.error_code == "CIV-ERR-MUT-003"

        # --- STEP 3: State Preservation Comparison (Rollback Verification) ---
        print("\n--- STEP 3: Verifying State Preservation ---")
        print(f"[*] Current State Post-Enforcement: {s0_state}")
        assert s0_state["current_project_state"] == "S0"
        assert "last_applied_transition" not in s0_state
        print("[✓] State remains completely pristine. Rollback successfully executed.")

        # --- STEP 4: Telemetry & Health Verification ---
        print("\n--- STEP 4: Verifying Telemetry and Health Status ---")

        from sage.runtime.health import check_health
        health = check_health(runtime)
        print(f"[✓] Health status: {health['status']}")
        print(f"[✓] Validation Subsystem: {health['validation_subsystem_health']}")
        print(f"[✓] Rejected Mutations count: {runtime.bond_manager.rejected_transitions}")

        assert health["status"] == "healthy"
        assert health["validation_subsystem_health"] == "healthy"
        assert runtime.bond_manager.rejected_transitions == 1

        # Stop runtime
        runtime.stop()
        print("\n[✓] Enforcement simulation completed successfully!")


if __name__ == "__main__":
    run_enforcement_simulation()
