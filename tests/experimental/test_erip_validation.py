"""Unit tests for SAGE Evidence Reconciliation & Ingestion Protocol (SAGE-ERIP) Milestone 1 Validation Core."""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from sage.experimental.erip import (
    ERIPCompliancePack,
    ERIPValidationCore,
    ERIPValidationResult,
)
from scripts.execute_erip_milestone1 import build_sample_valid_pack


def test_erip_validation_valid_package():
    """Verify that a compliant evidence package successfully passes all 6 validation stages."""
    validator = ERIPValidationCore()
    pack = build_sample_valid_pack(nonce="nonce_test_valid_001")

    res: ERIPValidationResult = validator.validate_compliance_pack(pack)

    assert res.status == "PASS"
    assert res.failed_stage is None
    assert res.failure_reason is None
    assert res.integrity_root_verified is True
    assert res.promoted_to_canonical is False
    assert len(res.stages_executed) == 6
    assert res.stages_executed == [
        "INTAKE_VALIDATION",
        "IDENTITY_VERIFICATION",
        "INTEGRITY_VERIFICATION",
        "RECEIPT_RECONCILIATION",
        "CONTRADICTION_DETECTION",
        "DETERMINISTIC_RESULT_GENERATION",
    ]
    assert len(res.provenance_hash) == 64


def test_erip_validation_malformed_package():
    """Verify fail-closed behavior when an evidence package is malformed or missing required top-level fields."""
    validator = ERIPValidationCore()

    # Missing cmaps_payload
    pack = build_sample_valid_pack(nonce="nonce_test_malformed_001")
    del pack["cmaps_payload"]
    res = validator.validate_compliance_pack(pack)

    assert res.status == "REJECT"
    assert res.failed_stage == "INTAKE_VALIDATION"
    assert "missing required field 'cmaps_payload'" in res.failure_reason
    assert res.promoted_to_canonical is False

    # Invalid CMAPS structure inside payload
    pack2 = build_sample_valid_pack(nonce="nonce_test_malformed_002")
    pack2["cmaps_payload"]["task_lineage"]["session_id"] = "invalid_session_id_format"
    res2 = validator.validate_compliance_pack(pack2)

    assert res2.status == "REJECT"
    assert res2.failed_stage == "INTAKE_VALIDATION"
    assert "CMAPS validation boundary violation" in res2.failure_reason


def test_erip_validation_invalid_unknown_identity():
    """Verify fail-closed rejection on unknown actor identity or unauthorized governance tier."""
    validator = ERIPValidationCore()

    # Unknown agent_id
    pack = build_sample_valid_pack(nonce="nonce_test_identity_001")
    pack["actor_identity"]["agent_id"] = "UNKNOWN_ROGUE_AGENT"
    res = validator.validate_compliance_pack(pack)

    assert res.status == "REJECT"
    assert res.failed_stage == "IDENTITY_VERIFICATION"
    assert "Unknown or unauthorized actor identity" in res.failure_reason

    # Invalid governance tier
    pack2 = build_sample_valid_pack(nonce="nonce_test_identity_002")
    pack2["actor_identity"]["governance_tier"] = "untrusted_tier"
    res2 = validator.validate_compliance_pack(pack2)

    assert res2.status == "REJECT"
    assert res2.failed_stage == "IDENTITY_VERIFICATION"
    assert "Invalid governance tier" in res2.failure_reason


def test_erip_validation_invalid_signature():
    """Verify fail-closed rejection when cryptographic signature or key fingerprint is missing or empty."""
    validator = ERIPValidationCore()

    # Missing signature
    pack = build_sample_valid_pack(nonce="nonce_test_sig_001")
    pack["actor_identity"]["signature"] = ""
    res = validator.validate_compliance_pack(pack)

    assert res.status == "REJECT"
    assert res.failed_stage == "IDENTITY_VERIFICATION"
    assert "Missing or empty cryptographic actor signature" in res.failure_reason

    # Missing key fingerprint
    pack2 = build_sample_valid_pack(nonce="nonce_test_sig_002")
    pack2["actor_identity"]["key_fingerprint"] = None
    res2 = validator.validate_compliance_pack(pack2)

    assert res2.status == "REJECT"
    assert res2.failed_stage == "IDENTITY_VERIFICATION"
    assert "Missing or empty cryptographic key fingerprint" in res2.failure_reason


def test_erip_validation_cryptographic_attestation_failure():
    """Verify fail-closed rejection when cryptographic attestation signature is tampered with or invalid."""
    validator = ERIPValidationCore()

    # Tampered SPEK signature
    pack = build_sample_valid_pack(nonce="nonce_test_crypto_sig_001")
    pack["actor_identity"]["signature"] = "mock_spek_sig_invalid_tampered_digest_00000"
    res = validator.validate_compliance_pack(pack)

    assert res.status == "REJECT"
    assert res.failed_stage == "IDENTITY_VERIFICATION"
    assert "Cryptographic signature verification failed" in res.failure_reason


def test_erip_validation_hash_chain_success_and_tampering():
    """Verify reconstruction of SAGE-CRC SHA-256 linear hash chain and detection of terminal root tampering."""
    validator = ERIPValidationCore()

    # Hash chain tampering
    pack = build_sample_valid_pack(nonce="nonce_test_hash_tamper_001")
    pack["terminal_root_hash"] = "f" * 64
    res = validator.validate_compliance_pack(pack)

    assert res.status == "REJECT"
    assert res.failed_stage == "INTEGRITY_VERIFICATION"
    assert "hash-chain tampering detected" in res.failure_reason
    assert res.integrity_root_verified is False

    # Empty hash chain
    pack2 = build_sample_valid_pack(nonce="nonce_test_hash_empty_002")
    pack2["hash_chain"] = []
    res2 = validator.validate_compliance_pack(pack2)

    assert res2.status == "REJECT"
    assert res2.failed_stage == "INTEGRITY_VERIFICATION"
    assert "hash_chain must be a non-empty list" in res2.failure_reason


def test_erip_validation_receipt_mismatch_and_orphan():
    """Verify detection of orphaned evidence packages and mismatched parent receipt references."""
    validator = ERIPValidationCore()

    # Parent task ID specified in CMAPS but parent_receipt is missing
    pack = build_sample_valid_pack(nonce="nonce_test_receipt_orphan_001")
    pack["parent_receipt"] = None
    res = validator.validate_compliance_pack(pack)

    assert res.status == "REJECT"
    assert res.failed_stage == "RECEIPT_RECONCILIATION"
    assert "Orphaned evidence detected" in res.failure_reason

    # Parent task ID mismatch between receipt and CMAPS
    pack2 = build_sample_valid_pack(nonce="nonce_test_receipt_mismatch_002")
    pack2["parent_receipt"]["parent_task_id"] = "task_different_parent_999"
    res2 = validator.validate_compliance_pack(pack2)

    assert res2.status == "REJECT"
    assert res2.failed_stage == "RECEIPT_RECONCILIATION"
    assert "Receipt mismatch" in res2.failure_reason


def test_erip_validation_duplicate_nonce():
    """Verify detection of duplicate nonces across evidence intake stream."""
    validator = ERIPValidationCore()
    pack1 = build_sample_valid_pack(nonce="nonce_duplicate_reuse_001")

    # First intake succeeds
    res1 = validator.validate_compliance_pack(pack1)
    assert res1.status == "PASS"

    # Second intake with same nonce fails contradiction check
    pack2 = build_sample_valid_pack(nonce="nonce_duplicate_reuse_001")
    # Need distinct audit_id and timestamps for CMAPS
    pack2["cmaps_payload"]["audit_id"] = "audit_99999999999999999999999999999999"
    res2 = validator.validate_compliance_pack(pack2)

    assert res2.status == "REJECT"
    assert res2.failed_stage == "CONTRADICTION_DETECTION"
    assert any(c["contradiction_type"] == "DUPLICATE_NONCE" for c in res2.contradiction_findings)


def test_erip_validation_stale_evidence():
    """Verify detection of stale evidence exceeding max age threshold or with future timestamps."""
    validator = ERIPValidationCore(max_age_seconds=10.0)

    # Stale timestamp (older than 10s)
    old_ts = (datetime.now(timezone.utc) - timedelta(seconds=100)).isoformat()
    pack = build_sample_valid_pack(nonce="nonce_test_stale_001")
    pack["timestamp"] = old_ts
    pack["cmaps_payload"]["timestamp"] = old_ts
    pack["cmaps_payload"]["execution_state"]["started_at"] = old_ts
    pack["cmaps_payload"]["execution_state"]["updated_at"] = old_ts
    pack["cmaps_payload"]["decision_events"][0]["timestamp"] = old_ts

    res = validator.validate_compliance_pack(pack)

    assert res.status == "REJECT"
    assert res.failed_stage == "CONTRADICTION_DETECTION"
    assert any(c["contradiction_type"] == "STALE_EVIDENCE" for c in res.contradiction_findings)


def test_erip_validation_conflicting_evidence():
    """Verify detection of subtask/decision mismatch and historical archive divergence."""
    validator = ERIPValidationCore()

    # Subtasks declared but zero decision events recorded
    pack = build_sample_valid_pack(nonce="nonce_test_conflict_001")
    pack["cmaps_payload"]["decision_events"] = []
    res = validator.validate_compliance_pack(pack)

    assert res.status == "REJECT"
    assert res.failed_stage == "CONTRADICTION_DETECTION"
    assert any(c["contradiction_type"] == "MISSING_RECEIPTS" for c in res.contradiction_findings)

    # Historical archive reference file does not exist
    pack2 = build_sample_valid_pack(nonce="nonce_test_conflict_002")
    pack2["historical_archive_ref"] = "nonexistent_dir/NONEXISTENT_INDEX.md"
    res2 = validator.validate_compliance_pack(pack2)

    assert res2.status == "REJECT"
    assert res2.failed_stage == "CONTRADICTION_DETECTION"
    assert any(c["contradiction_type"] == "ARCHIVE_DIVERGENCE" for c in res2.contradiction_findings)


def test_erip_validation_no_canonical_promotion():
    """Assert hard governance rule: ERIP validation results NEVER automatically promote state to CANONICAL."""
    validator = ERIPValidationCore()
    pack = build_sample_valid_pack(nonce="nonce_test_promotion_boundary_001")

    res = validator.validate_compliance_pack(pack)

    assert res.status == "PASS"
    assert res.promoted_to_canonical is False
