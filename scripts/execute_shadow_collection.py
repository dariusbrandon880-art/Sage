#!/usr/bin/env python3
"""SAGE Mission 0.7 Shadow Evidence Collection.

Triggers 8 distinct state transitions under shadow mode (3 successes and 5 failures)
to generate baseline evidence receipt JSONs under `sage_data/evidence_capture/`.
"""

import os
import sys
import json
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Adjust path to import SAGE components
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sage.runtime.engine import SageRuntime
from sage.acr.bond import BondValidationError
from sage.core.boundary import BoundaryEnforcer


def print_banner(msg: str):
    print("\n" + "=" * 60)
    print(f" {msg.upper()}")
    print("=" * 60)


def generate_fail_receipt(evidence_dir: Path, error_code: str, message: str, transition_payload: dict) -> Path:
    """Helper to generate and persist a structured VALIDATION_FAIL receipt."""
    event_id = f"evid_fail_{uuid.uuid4().hex[:8]}"
    receipt_filename = f"evidence_fail_{error_code}_{uuid.uuid4().hex[:6]}.json"
    evidence_path = evidence_dir / receipt_filename

    receipt_payload = {
        "event_id": event_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VALIDATION_FAIL",
        "error_code": error_code,
        "transition": transition_payload,
        "failure_details": {
            "message": message,
            "error_code": error_code
        }
    }
    # Calculate receipt hash
    receipt_hash = hashlib.sha256(json.dumps(receipt_payload, sort_keys=True).encode("utf-8")).hexdigest()
    receipt_payload["receipt_hash"] = receipt_hash

    with open(evidence_path, "w") as f:
        json.dump(receipt_payload, f, indent=2, default=str)

    return evidence_path


def main():
    print_banner("SAGE Mission 0.7 Shadow Evidence Collection")

    # Set environment posture to shadow
    os.environ["SAGE_BOND_MODE"] = "shadow"

    workspace_dir = Path("sage_data")
    evidence_dir = workspace_dir / "evidence_capture"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # 1. Clear previous evidence to ensure a clean run of exactly 8 receipts
    print("[*] Purging previous evidence files...")
    for f in evidence_dir.glob("*.json"):
        try:
            f.unlink()
        except OSError:
            pass

    runtime = SageRuntime(workspace_path=str(workspace_dir))
    bond_mgr = runtime.bond_manager

    # --- PART 1: 3 SUCCESSFUL TRANSITIONS (VALIDATION_PASS) ---
    print("\n--- Generating 3 Validation-Pass Receipts ---")

    # Pass 1: S0 -> Delta
    s0_state = {"current_project_state": "S0"}
    raw_payload_1 = {
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Shadow transition 1: S0 -> Delta",
        "author": "system_runtime",
        "validation_score": 1.0,
        "evidence_refs": [],
        "parent_ids": [],
        "contradictions": [],
        "auth_token": "SECURE_SPEK_SYSTEM_TOKEN_2026",
        "metadata": {}
    }
    s1_state = bond_mgr.execute_transition(s0_state, raw_payload_1)
    print(f"[✓] Pass 1 generated. State progressed to: {s1_state.get('current_project_state')}")

    # Pass 2: Delta -> Evidence
    s2_state = {"current_project_state": "Delta"}
    raw_payload_2 = {
        "from_state": "Delta",
        "to_state": "Evidence",
        "description": "Shadow transition 2: Delta -> Evidence",
        "author": "system_runtime",
        "validation_score": 1.0,
        "evidence_refs": [],
        "parent_ids": [],
        "contradictions": [],
        "auth_token": "SECURE_SPEK_SYSTEM_TOKEN_2026",
        "metadata": {}
    }
    s3_state = bond_mgr.execute_transition(s2_state, raw_payload_2)
    print(f"[✓] Pass 2 generated. State progressed to: {s3_state.get('current_project_state')}")

    # Pass 3: Evidence -> Validation
    s4_state = {"current_project_state": "Evidence"}
    raw_payload_3 = {
        "from_state": "Evidence",
        "to_state": "Validation",
        "description": "Shadow transition 3: Evidence -> Validation",
        "author": "system_runtime",
        "validation_score": 1.0,
        "evidence_refs": [],
        "parent_ids": [],
        "contradictions": [],
        "auth_token": "SECURE_SPEK_SYSTEM_TOKEN_2026",
        "metadata": {}
    }
    s5_state = bond_mgr.execute_transition(s4_state, raw_payload_3)
    print(f"[✓] Pass 3 generated. State progressed to: {s5_state.get('current_project_state')}")


    # --- PART 2: 5 FAILED TRANSITIONS (VALIDATION_FAIL) ---
    print("\n--- Generating 5 Validation-Fail Receipts ---")

    # Fail 1: CIV-ERR-MUT-003 (Identity Mutation / Invalid sequence)
    s_fail_1 = {"current_project_state": "S0"}
    raw_fail_1 = {
        "from_state": "S0",
        "to_state": "Validation",  # Invalid transition (skipping Delta & Evidence)
        "description": "Failed transition 1: Out-of-order STP transition",
        "author": "system_runtime",
        "validation_score": 1.0,
        "evidence_refs": [],
        "parent_ids": [],
        "contradictions": [],
        "auth_token": "SECURE_SPEK_SYSTEM_TOKEN_2026"
    }
    try:
        bond_mgr.execute_transition(s_fail_1, raw_fail_1)
    except BondValidationError as bve:
        p = generate_fail_receipt(evidence_dir, bve.error_code, bve.message, raw_fail_1)
        print(f"[✓] Fail 1 generated: {bve.error_code} receipt saved to {p.name}")

    # Fail 2: CIV-ERR-AUTH-001 (Authority mismatch / Invalid token)
    s_fail_2 = {"current_project_state": "S0"}
    raw_fail_2 = {
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Failed transition 2: Unauthorized token",
        "author": "system_runtime",
        "validation_score": 1.0,
        "evidence_refs": [],
        "parent_ids": [],
        "contradictions": [],
        "auth_token": "INVALID_TOKEN_FOR_AUDIT_2026"
    }
    try:
        bond_mgr.execute_transition(s_fail_2, raw_fail_2)
    except BondValidationError as bve:
        p = generate_fail_receipt(evidence_dir, bve.error_code, bve.message, raw_fail_2)
        print(f"[✓] Fail 2 generated: {bve.error_code} receipt saved to {p.name}")

    # Fail 3: CIV-ERR-SCHM-002 (Malformed structure / Missing required fields)
    s_fail_3 = {"current_project_state": "S0"}
    raw_fail_3 = {
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Failed transition 3: Malformed structure (missing author)",
        "validation_score": 1.0,
        "auth_token": "SECURE_SPEK_SYSTEM_TOKEN_2026"
    }
    try:
        bond_mgr.execute_transition(s_fail_3, raw_fail_3)
    except BondValidationError as bve:
        p = generate_fail_receipt(evidence_dir, bve.error_code, bve.message, raw_fail_3)
        print(f"[✓] Fail 3 generated: {bve.error_code} receipt saved to {p.name}")

    # Fail 4: CIV-ERR-SCHM-005 (Causality contradiction / loop)
    s_fail_4 = {"current_project_state": "S0"}
    raw_fail_4 = {
        "transition_id": "trans_loop_a",
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Failed transition 4: Circular parent dependency",
        "author": "system_runtime",
        "validation_score": 1.0,
        "evidence_refs": [],
        "parent_ids": ["trans_loop_a"],  # Self-referencing loop
        "contradictions": [],
        "auth_token": "SECURE_SPEK_SYSTEM_TOKEN_2026"
    }
    try:
        bond_mgr.execute_transition(s_fail_4, raw_fail_4)
    except BondValidationError as bve:
        p = generate_fail_receipt(evidence_dir, bve.error_code, bve.message, raw_fail_4)
        print(f"[✓] Fail 4 generated: {bve.error_code} receipt saved to {p.name}")

    # Fail 5: CIV-ERR-EXT-004 (Low evidence confidence)
    s_fail_5 = {"current_project_state": "S0"}
    raw_fail_5 = {
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Failed transition 5: Low confidence score",
        "author": "system_runtime",
        "validation_score": 0.45,  # Below threshold 0.7
        "evidence_refs": [],
        "parent_ids": [],
        "contradictions": [],
        "auth_token": "SECURE_SPEK_SYSTEM_TOKEN_2026"
    }
    try:
        bond_mgr.execute_transition(s_fail_5, raw_fail_5)
    except BondValidationError as bve:
        p = generate_fail_receipt(evidence_dir, bve.error_code, bve.message, raw_fail_5)
        print(f"[✓] Fail 5 generated: {bve.error_code} receipt saved to {p.name}")


    # --- SUMMARY ---
    print_banner("Evidence Collection Summary")
    receipts_list = list(evidence_dir.glob("*.json"))
    print(f"Total evidence receipts generated: {len(receipts_list)} / 8")
    for r in sorted(receipts_list):
        print(f" - {r.name}")

    print("\n[✓] SAGE Mission 0.7 shadow evidence collection complete.")


if __name__ == "__main__":
    main()
