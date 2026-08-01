"""SAGE-CPC: Continuity Proof Chamber Validation Tests."""

import pytest
import json
import hashlib
from typing import Dict, Any
from sage.experimental.act.cpc import ContinuityProofChamber
from sage.experimental.act.contracts import CryptographicSessionReceiptChain


def _build_test_crc_chain(session_id: str, payload_hash: str) -> list:
    """Helper to build a valid single-block SAGE-CRC chain for testing."""
    chain_validator = CryptographicSessionReceiptChain()
    genesis = chain_validator.build_genesis_block(session_id, payload_hash, "agent_chatgpt")
    return [genesis]


def test_cpc_success_path_rehydration():
    """Verify that a standard capture, interruption, and recovery sequence succeeds with zero context drift."""
    cpc = ContinuityProofChamber()

    session_data = {
        "session_id": "session_f1e2d3c4",
        "active_objectives": ["obj_001", "obj_002"],
        "mapped_tasks": ["task_001", "task_002"]
    }

    # 1. Capture State footprint (H_pre)
    pre_capture = cpc.capture_state(session_data)
    assert pre_capture["session_id"] == session_data["session_id"]
    assert "state_hash" in pre_capture

    # 2. Build SAGE-CRC Chain linked to our state payload
    payload_hash = hashlib.sha256(json.dumps(session_data, sort_keys=True).encode("utf-8")).hexdigest()
    chain = _build_test_crc_chain(session_data["session_id"], payload_hash)

    # 3. Simulate sudden process interruption (clearing memory)
    active_memory = dict(session_data)
    cpc.simulate_interruption(active_memory)
    assert len(active_memory) == 0  # cleared!

    # 4. Execute Recovery (Stateless rehydration)
    rehydrated = cpc.execute_recovery(session_data, chain)
    assert rehydrated["session_id"] == session_data["session_id"]

    # 5. Compare States and assert zero context drift
    assert cpc.compare_states(pre_capture["state_hash"], rehydrated) is True

    # 6. Generate and verify structured CPC evidence package
    evidence = cpc.generate_evidence_package("sdr_cpc_01", pre_capture, rehydrated, chain)
    assert evidence["cpc_run_id"] == "cpc_sdr_cpc_01"
    assert evidence["integrity_comparison_result"]["match"] is True
    assert evidence["human_review_status"] == "PENDING_HUMAN_SIGN_OFF"


def test_cpc_corrupted_payload_rejection():
    """Verify that a modified recovery payload fails cryptographic linkage checks."""
    cpc = ContinuityProofChamber()

    session_data = {
        "session_id": "session_f1e2d3c4",
        "active_objectives": ["obj_001"],
        "mapped_tasks": ["task_001"]
    }

    # Build chain linked to original session payload
    payload_hash = hashlib.sha256(json.dumps(session_data, sort_keys=True).encode("utf-8")).hexdigest()
    chain = _build_test_crc_chain(session_data["session_id"], payload_hash)

    # Corrupt/Alter the payload (add a new task) without re-signing SAGE-CRC
    corrupted_data = dict(session_data)
    corrupted_data["mapped_tasks"] = ["task_001", "task_002"]

    with pytest.raises(ValueError, match="Cryptographic linkage mismatch"):
        cpc.execute_recovery(corrupted_data, chain)


def test_cpc_broken_crc_linkage_rejection():
    """Verify that a broken SAGE-CRC chain is detected and blocked during recovery execution."""
    cpc = ContinuityProofChamber()

    session_data = {
        "session_id": "session_f1e2d3c4",
        "active_objectives": ["obj_001"],
        "mapped_tasks": ["task_001"]
    }

    payload_hash = hashlib.sha256(json.dumps(session_data, sort_keys=True).encode("utf-8")).hexdigest()
    chain = _build_test_crc_chain(session_data["session_id"], payload_hash)

    # Break chain validation (e.g. alter previous hash)
    chain[0]["previous_hash"] = "f" * 64

    with pytest.raises(ValueError, match="Genesis block previous_hash must be sixty-four zeros"):
        cpc.execute_recovery(session_data, chain)


def test_cpc_state_mismatch_context_drift_rejection():
    """Verify that any post-recovery context drift is rejected and throws ValueError."""
    cpc = ContinuityProofChamber()

    session_data = {
        "session_id": "session_f1e2d3c4",
        "active_objectives": ["obj_001"],
        "mapped_tasks": ["task_001"]
    }

    # Pre-interruption footprint
    pre_capture = cpc.capture_state(session_data)

    # Post-recovery session data with drift (altered objective)
    drifted_session_data = {
        "session_id": "session_f1e2d3c4",
        "active_objectives": ["obj_001_drifted_value"],
        "mapped_tasks": ["task_001"]
    }

    with pytest.raises(ValueError, match="Critical Rehydration Context Drift Detected"):
        cpc.compare_states(pre_capture["state_hash"], drifted_session_data)
