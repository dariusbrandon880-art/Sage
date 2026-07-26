#!/usr/bin/env python3
"""SAGE Mission 0.7 Readiness Verification Script.

Automates the verification of shadow-mode, staging enforce-mode isolation,
telemetry availability, evidence pipeline storage writability, and receipt-chain integrity.
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

# Adjust path to import SAGE components
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sage.runtime.engine import SageRuntime
from sage.api import app
from sage.acr.bond import BondValidationError
from sage.core.boundary import BoundaryEnforcer


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f" {title.upper()}")
    print("=" * 60)


def verify_shadow_mode() -> bool:
    print("\n--- Checking Step 1: Shadow-Mode Production Configuration ---")
    # Setup temporary environment
    original_mode = os.environ.get("SAGE_BOND_MODE")
    os.environ["SAGE_BOND_MODE"] = "shadow"

    temp_dir = tempfile.mkdtemp()
    try:
        runtime = SageRuntime(workspace_path=temp_dir)
        if runtime.bond_mode != "shadow":
            print(f"[✗] SAGE_BOND_MODE is not resolved to 'shadow' (got: {runtime.bond_mode})")
            return False
        print("[✓] Shadow-mode configuration correctly resolved in SageRuntime.")

        # Test non-blocking transition with standard operation
        session_id = runtime.set_objective("Test Shadow Transition")
        print(f"[✓] Transition successful. Objective set to 'Test Shadow Transition'. Session: {session_id}")

        # Check if validation receipts were written in shadow mode
        evidence_dir = Path(temp_dir) / "evidence_capture"
        receipts = list(evidence_dir.glob("*.json"))
        if not receipts:
            print("[✗] No shadow validation receipt written in evidence_capture.")
            return False

        print(f"[✓] Evidence captured: {len(receipts)} receipt(s) generated under shadow mode.")
        with open(receipts[0], "r") as f:
            data = json.load(f)
            print(f"    Sample receipt ID: {data.get('event_id')} - Status: {data.get('status')}")

        return True
    except Exception as e:
        print(f"[✗] Shadow-mode verification failed with exception: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)
        if original_mode is not None:
            os.environ["SAGE_BOND_MODE"] = original_mode
        else:
            os.environ.pop("SAGE_BOND_MODE", None)


def verify_staging_enforce_mode() -> bool:
    print("\n--- Checking Step 2: Staging Enforce-Mode Isolation ---")
    original_mode = os.environ.get("SAGE_BOND_MODE")
    os.environ["SAGE_BOND_MODE"] = "enforce"

    temp_dir = tempfile.mkdtemp()
    try:
        runtime = SageRuntime(workspace_path=temp_dir)
        if runtime.bond_mode != "enforce":
            print(f"[✗] SAGE_BOND_MODE is not resolved to 'enforce' (got: {runtime.bond_mode})")
            return False
        print("[✓] Enforce-mode configuration correctly resolved in SageRuntime.")

        # Simulate unauthorized transition with bad auth token
        s0_state = {"current_project_state": "S0"}
        bad_payload = {
            "from_state": "S0",
            "to_state": "Delta",
            "description": "Unauthorized token attempt",
            "author": "external_agent",
            "validation_score": 0.95,
            "auth_token": "INVALID_TOKEN_999"
        }

        # Expect BondValidationError (CIV-ERR-AUTH-001)
        try:
            runtime.bond_manager.execute_transition(s0_state, bad_payload)
            print("[✗] Enforce mode failed to block transition with invalid auth token!")
            return False
        except BondValidationError as bve:
            if bve.error_code == "CIV-ERR-AUTH-001":
                print(f"[✓] Enforce mode strictly blocked unauthorized mutation with error: {bve.error_code}")
            else:
                print(f"[✗] Enforce mode blocked transaction but returned wrong error code: {bve.error_code}")
                return False

        # Verify Rollback Isolation - s0_state dictionary must not be mutated
        if s0_state.get("current_project_state") != "S0" or "last_applied_transition" in s0_state:
            print("[✗] Rollback isolation failed! s0_state mutated despite validation failure.")
            return False
        print("[✓] Rollback isolation verified. In-memory state remains unmodified (S0).")

        return True
    except Exception as e:
        print(f"[✗] Staging enforce-mode verification failed with exception: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)
        if original_mode is not None:
            os.environ["SAGE_BOND_MODE"] = original_mode
        else:
            os.environ.pop("SAGE_BOND_MODE", None)


def verify_telemetry_endpoints() -> bool:
    print("\n--- Checking Step 3: Telemetry Endpoints Availability ---")
    try:
        client = TestClient(app)

        # 1. Check GET /health
        response_health = client.get("/health")
        if response_health.status_code != 200:
            print(f"[✗] GET /health returned status code {response_health.status_code}")
            return False
        health_data = response_health.json()
        print("[✓] GET /health is available and online.")
        print(f"    Overall Health Status: {health_data.get('status')}")
        print(f"    Subcomponents status: {health_data.get('components')}")

        if "cognitive_control_plane" not in health_data:
            print("[✗] GET /health is missing 'cognitive_control_plane' metrics.")
            return False
        print("[✓] GET /health exposes cognitive_control_plane metrics.")

        # 2. Check GET /runtime/control-plane
        response_cp = client.get("/runtime/control-plane")
        if response_cp.status_code != 200:
            print(f"[✗] GET /runtime/control-plane returned status code {response_cp.status_code}")
            return False
        cp_data = response_cp.json()
        print("[✓] GET /runtime/control-plane is available and online.")
        print(f"    Observer component: {cp_data.get('observer', {}).get('name')}")
        print(f"    Enforcer component: {cp_data.get('enforcer', {}).get('name')}")
        print(f"    Receipt chain integrity valid: {cp_data.get('receipt_chain', {}).get('integrity_valid')}")

        return True
    except Exception as e:
        print(f"[✗] Telemetry verification failed with exception: {e}")
        return False


def verify_evidence_storage() -> bool:
    print("\n--- Checking Step 4: Evidence Storage Path Writability ---")
    evidence_path = Path("sage_data/evidence_capture")
    try:
        evidence_path.mkdir(parents=True, exist_ok=True)
        # Test write access
        test_file = evidence_path / ".readiness_write_test"
        test_file.write_text("SAGE-M07-READINESS-TEST", encoding="utf-8")
        content = test_file.read_text(encoding="utf-8")
        if content != "SAGE-M07-READINESS-TEST":
            print("[✗] Content verification mismatch during write test.")
            return False
        test_file.unlink()
        print(f"[✓] Directory '{evidence_path}' is fully writeable and functional.")
        return True
    except Exception as e:
        print(f"[✗] Write verification on '{evidence_path}' failed: {e}")
        return False


def verify_receipt_chain() -> bool:
    print("\n--- Checking Step 5: Receipt-Chain Verification Readiness ---")
    temp_dir = tempfile.mkdtemp()
    try:
        runtime = SageRuntime(workspace_path=temp_dir)
        chain = runtime.validation.receipt_chain

        # Check initial empty chain integrity
        if not chain.verify_chain_integrity():
            print("[✗] Empty receipt chain integrity check failed.")
            return False
        print("[✓] Initial receipt chain integrity verified.")

        # Generate mock receipts to verify chain appending and cryptographic back-link hash linkage
        receipt1 = chain.generate_receipt(
            memory_id="mem_test_1",
            action="validate_memory",
            content={"title": "First rule test"},
            rules_applied=["non_empty_content"]
        )
        receipt2 = chain.generate_receipt(
            memory_id="mem_test_2",
            action="promote_validated",
            content={"title": "Second rule test"},
            rules_applied=["content_substance"]
        )

        if receipt2.previous_receipt_hash == "0" * 64:
            print("[✗] Chain linkage hash mismatch. Second receipt failed to back-link to first.")
            return False
        print("[✓] Receipt hash back-linking successfully verified.")

        if not chain.verify_chain_integrity():
            print("[✗] Mutated receipt chain integrity verification failed.")
            return False
        print("[✓] Multi-node cryptographic receipt chain integrity verified successfully.")

        return True
    except Exception as e:
        print(f"[✗] Receipt-chain verification failed with exception: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)


def main():
    print_header("SAGE Mission 0.7 Readiness Auditor")

    results = {
        "shadow_mode": verify_shadow_mode(),
        "staging_enforce": verify_staging_enforce_mode(),
        "telemetry": verify_telemetry_endpoints(),
        "evidence_storage": verify_evidence_storage(),
        "receipt_chain": verify_receipt_chain()
    }

    print_header("Readiness Summary Results")
    all_passed = True
    for check_name, passed in results.items():
        status_str = "PASSED" if passed else "FAILED"
        print(f"{check_name.replace('_', ' ').title():<30} : {status_str}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print(" [✓] SAGE PLATFORM IS FULLY READY FOR SHADOW OBSERVATION!")
        print("=" * 60)
        sys.exit(0)
    else:
        print(" [✗] READINESS AUDIT DETECTED FAILURES. FIX BEFORE PROCEEDING.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
