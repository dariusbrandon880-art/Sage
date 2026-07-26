#!/usr/bin/env python3
"""SAGE Mission 0.7 — Shadow Evidence Collection Execution Script.

Triggers standard (success) and failed transitions to collect shadow evidence.
Generates exactly 8 validation receipt JSONs in `sage_data/evidence_capture/`
(3 PASS, 5 FAIL) representing all target error codes and transition types.
"""

import os
import sys
import json
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# Force SAGE_BOND_MODE=shadow before imports
os.environ["SAGE_BOND_MODE"] = "shadow"

from sage.runtime.engine import SageRuntime
from sage.acr.bond import BondValidationError
from sage.core.boundary import BoundaryEnforcer


def write_failure_receipt(error_code: str, message: str, details: dict, raw_payload: dict, capture_dir: Path):
    """Helper to generate a deterministic VALIDATION_FAIL receipt JSON."""
    event_id = f"evid_{uuid.uuid4().hex[:8]}"
    ts = datetime.now(timezone.utc).isoformat()

    transition_info = {}
    if isinstance(raw_payload, dict):
        transition_info = {
            "transition_id": raw_payload.get("transition_id", f"trans_{uuid.uuid4().hex[:8]}"),
            "from_state": raw_payload.get("from_state", "unknown"),
            "to_state": raw_payload.get("to_state", "unknown"),
            "author": raw_payload.get("author", "unknown"),
            "validation_score": raw_payload.get("validation_score", 0.0),
            "evidence_refs": raw_payload.get("evidence_refs", []),
            "auth_token": raw_payload.get("auth_token", "unknown")
        }
    else:
        transition_info = {"raw_payload": str(raw_payload)}

    receipt_payload = {
        "event_id": event_id,
        "timestamp": ts,
        "status": "VALIDATION_FAIL",
        "error_code": error_code,
        "transition": transition_info,
        "failure_details": {
            "message": message,
            **details
        }
    }

    # Deterministic SHA-256 HMAC / Hash representation of the receipt
    receipt_hash = hashlib.sha256(json.dumps(receipt_payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    receipt_payload["receipt_hash"] = receipt_hash

    transition_id = transition_info.get("transition_id", f"trans_{uuid.uuid4().hex[:8]}")
    file_name = f"evidence_{transition_id}_{uuid.uuid4().hex[:6]}.json"
    file_path = capture_dir / file_name

    with open(file_path, "w") as f:
        json.dump(receipt_payload, f, indent=2, default=str)

    print(f"[FAIL REC] Generated failure receipt for {error_code}: {file_name}")


def main():
    print("=" * 60)
    print(" SAGE MISSION 0.7 — SHADOW EVIDENCE COLLECTION")
    print("=" * 60)

    # Initialize SAGE Runtime
    runtime = SageRuntime("sage_data")
    capture_dir = Path("sage_data/evidence_capture")
    capture_dir.mkdir(parents=True, exist_ok=True)

    # Clean previous evidence capture files to guarantee exactly 8 receipts
    for f in capture_dir.glob("evidence_*.json"):
        try:
            f.unlink()
        except Exception:
            pass

    print(f"Cleared previous evidence captures in '{capture_dir}'. Ready to populate.")

    # --- 1. TRIGGER SUCCESSFUL (VALIDATION_PASS) TRANSITIONS ---
    print("\n--- Phase 1: Triggering Successful (VALIDATION_PASS) Transitions ---")

    # Success 1: S0 -> Delta
    state_s0 = {"current_project_state": "S0"}
    payload_success_1 = {
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Standard transition S0 to Delta state",
        "author": "system_runtime",
        "validation_score": 1.0,
        "evidence_refs": [],
        "parent_ids": [],
        "contradictions": [],
        "auth_token": BoundaryEnforcer.SYSTEM_TOKEN,
        "metadata": {"step": "1_s0_to_delta"}
    }
    try:
        res1 = runtime.bond_manager.execute_transition(state_s0, payload_success_1)
        print(f"[PASS REC] Successfully executed transition S0 -> Delta (Target: {res1.get('current_project_state')})")
    except Exception as e:
        print(f"[ERROR] S0 -> Delta failed: {e}")

    # Success 2: Delta -> Evidence
    state_delta = {"current_project_state": "Delta"}
    payload_success_2 = {
        "from_state": "Delta",
        "to_state": "Evidence",
        "description": "Standard transition Delta to Evidence state",
        "author": "system_runtime",
        "validation_score": 1.0,
        "evidence_refs": [],
        "parent_ids": [],
        "contradictions": [],
        "auth_token": BoundaryEnforcer.SYSTEM_TOKEN,
        "metadata": {"step": "2_delta_to_evidence"}
    }
    try:
        res2 = runtime.bond_manager.execute_transition(state_delta, payload_success_2)
        print(f"[PASS REC] Successfully executed transition Delta -> Evidence (Target: {res2.get('current_project_state')})")
    except Exception as e:
        print(f"[ERROR] Delta -> Evidence failed: {e}")

    # Success 3: Evidence -> Validation
    state_evidence = {"current_project_state": "Evidence"}
    payload_success_3 = {
        "from_state": "Evidence",
        "to_state": "Validation",
        "description": "Standard transition Evidence to Validation state",
        "author": "system_runtime",
        "validation_score": 1.0,
        "evidence_refs": [],
        "parent_ids": [],
        "contradictions": [],
        "auth_token": BoundaryEnforcer.SYSTEM_TOKEN,
        "metadata": {"step": "3_evidence_to_validation"}
    }
    try:
        res3 = runtime.bond_manager.execute_transition(state_evidence, payload_success_3)
        print(f"[PASS REC] Successfully executed transition Evidence -> Validation (Target: {res3.get('current_project_state')})")
    except Exception as e:
        print(f"[ERROR] Evidence -> Validation failed: {e}")

    # --- 2. TRIGGER FAILED (VALIDATION_FAIL) TRANSITIONS ---
    print("\n--- Phase 2: Triggering Failed (VALIDATION_FAIL) Transitions ---")

    # Fail 1: CIV-ERR-AUTH-001 (Authority Mismatch / Invalid Token)
    state_s0_auth = {"current_project_state": "S0"}
    payload_auth_fail = {
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Unauthorized token attempt",
        "author": "malicious_actor",
        "validation_score": 1.0,
        "evidence_refs": [],
        "parent_ids": [],
        "contradictions": [],
        "auth_token": "INVALID_ACCESS_TOKEN_999"  # invalid
    }
    try:
        runtime.bond_manager.execute_transition(state_s0_auth, payload_auth_fail)
    except BondValidationError as bve:
        write_failure_receipt(bve.error_code, bve.message, bve.details, payload_auth_fail, capture_dir)
    except Exception as e:
        print(f"[ERROR] Expected BondValidationError, got {type(e).__name__}: {e}")

    # Fail 2: CIV-ERR-MUT-003 (Identity Mutation / Sequence Drift)
    state_s0_mut = {"current_project_state": "S0"}
    payload_mut_fail = {
        "from_state": "S0",
        "to_state": "Validation",  # Out of order, skipping Delta and Evidence
        "description": "Out of order state transition sequence attempt",
        "author": "system_runtime",
        "validation_score": 1.0,
        "evidence_refs": [],
        "parent_ids": [],
        "contradictions": [],
        "auth_token": BoundaryEnforcer.SYSTEM_TOKEN
    }
    try:
        runtime.bond_manager.execute_transition(state_s0_mut, payload_mut_fail)
    except BondValidationError as bve:
        write_failure_receipt(bve.error_code, bve.message, bve.details, payload_mut_fail, capture_dir)
    except Exception as e:
        print(f"[ERROR] Expected BondValidationError, got {type(e).__name__}: {e}")

    # Fail 3: CIV-ERR-SCHM-002 (Malformed Structure / Secondary Schema Failure)
    state_s0_schm = {"current_project_state": "S0"}
    # Missing 'author' and 'validation_score' to trigger schema validation failure
    payload_schm_fail = {
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Malformed structural payload missing required Pydantic fields",
        "auth_token": BoundaryEnforcer.SYSTEM_TOKEN
    }
    try:
        runtime.bond_manager.execute_transition(state_s0_schm, payload_schm_fail)
    except BondValidationError as bve:
        write_failure_receipt(bve.error_code, bve.message, bve.details, payload_schm_fail, capture_dir)
    except Exception as e:
        print(f"[ERROR] Expected BondValidationError, got {type(e).__name__}: {e}")

    # Fail 4: CIV-ERR-SCHM-005 (Causality / Contradiction Loop)
    state_s0_causal = {"current_project_state": "S0"}
    payload_causal_fail = {
        "transition_id": "trans_circular_loop",
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Circular dependency causality violation attempt",
        "author": "system_runtime",
        "validation_score": 1.0,
        "evidence_refs": [],
        "parent_ids": ["trans_circular_loop"],  # Self-referencing cycle
        "contradictions": [],
        "auth_token": BoundaryEnforcer.SYSTEM_TOKEN
    }
    try:
        runtime.bond_manager.execute_transition(state_s0_causal, payload_causal_fail)
    except BondValidationError as bve:
        write_failure_receipt(bve.error_code, bve.message, bve.details, payload_causal_fail, capture_dir)
    except Exception as e:
        print(f"[ERROR] Expected BondValidationError, got {type(e).__name__}: {e}")

    # Fail 5: CIV-ERR-EXT-004 (Ambiguous Payload / Low Evidence Score)
    state_s0_ext = {"current_project_state": "S0"}
    payload_ext_fail = {
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Low evidence transition attempt",
        "author": "system_runtime",
        "validation_score": 0.45,  # Below threshold 0.7
        "evidence_refs": [],
        "parent_ids": [],
        "contradictions": [],
        "auth_token": BoundaryEnforcer.SYSTEM_TOKEN
    }
    try:
        runtime.bond_manager.execute_transition(state_s0_ext, payload_ext_fail)
    except BondValidationError as bve:
        write_failure_receipt(bve.error_code, bve.message, bve.details, payload_ext_fail, capture_dir)
    except Exception as e:
        print(f"[ERROR] Expected BondValidationError, got {type(e).__name__}: {e}")

    # --- 3. AUDIT RECEPTACLE COUNT ---
    receipt_files = list(capture_dir.glob("evidence_*.json"))
    print("\n" + "=" * 60)
    print(f" EVIDENCE COLLECTION COMPLETION SUMMARY")
    print("=" * 60)
    print(f"Capture Directory: {capture_dir}")
    print(f"Total Receipts Generated: {len(receipt_files)}")

    passes = 0
    failures = 0
    classifications = {}

    for f in receipt_files:
        try:
            with open(f, "r") as rf:
                data = json.load(rf)
                status = data.get("status")
                if status == "VALIDATION_PASS":
                    passes += 1
                elif status == "VALIDATION_FAIL":
                    failures += 1
                    err_code = data.get("error_code", "UNKNOWN")
                    classifications[err_code] = classifications.get(err_code, 0) + 1
        except Exception as e:
            print(f"Error reading file {f.name}: {e}")

    print(f"  - VALIDATION_PASS count: {passes}")
    print(f"  - VALIDATION_FAIL count: {failures}")
    print(f"  - CIV Error Classifications:")
    for err, count in classifications.items():
        print(f"    * {err}: {count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
