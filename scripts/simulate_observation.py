"""SAGE Mission 0.6 Phase 2 — Controlled Autonomous Workflow Simulation.

Demonstrates:
"Autonomous action observed -> SAGE evaluated -> evidence captured -> system integrity preserved."
"""

import os
import json
import tempfile
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sage.runtime import SageRuntime
from sage.models import ExternalSessionPayload
from sage.core.boundary import BoundaryEnforcer


def run_simulation():
    print("=== SAGE MISSION 0.6 PHASE 2 SIMULATION ===")

    # 1. Force SAGE_BOND_MODE="shadow"
    os.environ["SAGE_BOND_MODE"] = "shadow"
    print("[*] SAGE_BOND_MODE set to 'shadow'")

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"[*] Initializing SageRuntime in temporary workspace: {workspace}")
        runtime = SageRuntime(str(workspace))
        runtime.start()

        # Confirm BondManager initialized and mode matches shadow
        assert runtime.bond_mode == "shadow"
        print("[✓] Runtime active. BondManager in shadow mode.")

        # --- STEP 1: Autonomous Action Observed & Evaluated (Shadow Passes) ---
        print("\n--- STEP 1: Simulating Authorized Action Sequence ---")

        # Action A: set_objective
        print("[*] Simulating action: set_objective('Autonomous Workflow Simulation')")
        runtime.set_objective("Autonomous Workflow Simulation")

        # Action B: set_task
        print("[*] Simulating action: set_task('Verify Shadow Evidence Capture')")
        runtime.set_task("Verify Shadow Evidence Capture")

        print("[✓] Objective and task set successfully.")
        print(f"[Telemetry] shadow_passes count: {runtime.bond_manager.shadow_passes}")
        assert runtime.bond_manager.shadow_passes == 2

        # --- STEP 2: Anomaly Observation (Shadow Failures) ---
        print("\n--- STEP 2: Simulating Anomaly / Conflict Evaluation ---")

        # Let's trigger a shadow validation failure by invoking skal payload process with duplicate nonce
        payload_data = {
            "nonce": "dup_simulation_nonce_111",
            "source": "Simulation System",
            "timestamp": "2026-03-31T12:00:00Z",
            "commit_identifier": "commit_sim_001",
            "validation_results": {"status": "success"},
            "evidence_references": [],
            "confidence_metadata": {"confidence": 1.0},
        }

        # First skal ingestion (pass)
        from sage.acr.skal import process_incoming_payload
        res1 = process_incoming_payload("validation_report", payload_data, runtime)
        print("[*] SKAL payload ingest 1: Success.")

        # Second skal ingestion (replay attempt - shadow failure)
        # In shadow mode, the process_incoming_payload of SKAL won't block but will count shadow failure
        try:
            process_incoming_payload("validation_report", payload_data, runtime)
        except ValueError as e:
            # Replay protection throws because replay is an absolute security gate
            print(f"[*] SKAL Replay Attack Blocked: {e}")

        # Let's directly call execute_transition with bad parameters to trigger shadow failure logging
        s0_bad_state = {"current_project_state": "S0"}
        bad_payload = {
            "from_state": "S0",
            "to_state": "Delta",
            "description": "Unauthorized token simulation",
            "author": "attacker",
            "validation_score": 0.9,
            "auth_token": "FORGED_TOKEN"  # Invalid token
        }

        print("[*] Simulating direct BondManager transition with invalid token...")
        try:
            runtime.bond_manager.execute_transition(s0_bad_state, bad_payload)
        except Exception as e:
            print(f"[✓] Transition evaluation rejected by BondManager: {e}")

        # Let's check shadow statistics
        print(f"[Telemetry] shadow_passes: {runtime.bond_manager.shadow_passes}")
        print(f"[Telemetry] shadow_failures: {runtime.bond_manager.shadow_failures}")

        # --- STEP 3: Evidence Capture ---
        print("\n--- STEP 3: Verifying SAGE-EVID Evidence Capture ---")
        capture_dir = workspace / "evidence_capture"
        captured_receipts = list(capture_dir.glob("evidence_*.json"))
        print(f"[✓] Captured {len(captured_receipts)} evidence receipt files in capture directory.")

        for receipt_path in captured_receipts:
            with open(receipt_path, "r") as f:
                receipt = json.load(f)
                print(f"    - Receipt ID: {receipt['event_id']}, Hash: {receipt['receipt_hash'][:16]}... Status: {receipt['status']}")

        # --- STEP 4: System Integrity Verification ---
        print("\n--- STEP 4: Verifying Runtime State and Health Integrity ---")

        # Get control plane telemetry
        from sage.runtime.health import check_health
        health = check_health(runtime)
        print(f"[✓] Health status rating: {health['status']}")
        print(f"[✓] Validation subsystem health: {health['validation_subsystem_health']}")
        print(f"[✓] Authority stability index: {health['cognitive_control_plane']['authority_stability_index']}")

        assert health["status"] == "healthy"
        assert health["validation_subsystem_health"] == "healthy"

        # Stop runtime
        runtime.stop()
        print("\n[✓] Simulation completed successfully with 100% integrity!")


if __name__ == "__main__":
    run_simulation()
