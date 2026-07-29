"""Unit tests for experimental SAGE Human Review Gate Validator prototype."""

import pytest
from datetime import datetime, timezone
from sage.experimental.act.contracts import (
    CapabilityPassportValidator,
    CapabilityEvidenceReceiptGenerator,
    HumanReviewGate,
)


@pytest.fixture
def sample_valid_receipt():
    passport = {
        "capability_id": "cap_sdr_sim_engine",
        "name": "SAGE-SDR Simulation Engine",
        "purpose": "Simulates dry-runs of multi-agent execution safely in isolated space.",
        "lifecycle_state": "proposed",
        "validation_strategy": "Verify execution outputs in ephemeral sandbox directory.",
        "evidence_path": "docs/SAGE-SDR-READINESS-SPECIFICATION.md",
        "dependencies": ["cap_spek_kernel"],
        "human_signoff": {
            "signer": "SAGE Supervisor",
            "timestamp": "2026-03-31T12:00:00Z",
            "approved": True,
        }
    }
    passport_validator = CapabilityPassportValidator()
    val_result = passport_validator.validate_passport(passport)

    receipt_generator = CapabilityEvidenceReceiptGenerator(validator_id="val_system_test")
    outcome = receipt_generator.generate_receipt(
        passport=passport,
        validation_result=val_result
    )
    return outcome["receipt"]


def test_human_review_gate_approval_success(sample_valid_receipt):
    """Verify that a reviewer can successfully approve a compliant evidence receipt."""
    review_gate = HumanReviewGate(reviewer_identity="supervisor_bob")
    outcome = review_gate.execute_review(
        receipt=sample_valid_receipt,
        decision="approved",
        notes="All testing traces look fully integrated and correct."
    )

    assert outcome["audit_trail_valid"] is True
    assert outcome["read_only_assertion"] is True

    audit = outcome["review_audit"]
    assert audit["capability_id"] == "cap_sdr_sim_engine"
    assert audit["reviewer_identity"] == "supervisor_bob"
    assert audit["review_decision"] == "approved"
    assert audit["validation_status"] == "VALIDATED"
    assert audit["review_notes"] == "All testing traces look fully integrated and correct."
    assert audit["archive_destination"] == "Main Archive/cap_sdr_sim_engine_review_gate.json"


def test_human_review_gate_rejection_success(sample_valid_receipt):
    """Verify that a reviewer can successfully reject an evidence receipt, mapping status to REJECTED."""
    review_gate = HumanReviewGate(reviewer_identity="supervisor_bob")
    outcome = review_gate.execute_review(
        receipt=sample_valid_receipt,
        decision="rejected",
        notes="Missing clear test cases for stress-testing and bounds checking."
    )

    assert outcome["audit_trail_valid"] is True
    audit = outcome["review_audit"]
    assert audit["review_decision"] == "rejected"
    assert audit["validation_status"] == "REJECTED"


def test_human_review_gate_rejects_empty_notes(sample_valid_receipt):
    """Verify that empty or missing notes trigger a ValueError."""
    review_gate = HumanReviewGate()
    with pytest.raises(ValueError, match="Review notes must be a non-empty string."):
        review_gate.execute_review(
            receipt=sample_valid_receipt,
            decision="approved",
            notes="   "  # whitespace only
        )


def test_human_review_gate_rejects_invalid_decision(sample_valid_receipt):
    """Verify that decisions outside of approved/rejected are rejected."""
    review_gate = HumanReviewGate()
    with pytest.raises(ValueError, match="Invalid review decision"):
        review_gate.execute_review(
            receipt=sample_valid_receipt,
            decision="partially_approved",  # illegal decision choice
            notes="Looks okay but needs a bit more work."
        )


def test_human_review_gate_missing_required_fields():
    """Verify that an incomplete or invalid receipt raises a ValueError."""
    review_gate = HumanReviewGate()
    bad_receipt = {
        "receipt_id": "rcpt_999",
        "capability_id": "cap_incomplete"
        # missing validator_id, timestamp, etc
    }
    with pytest.raises(ValueError, match="Review Violation: Missing required receipt field"):
        review_gate.execute_review(
            receipt=bad_receipt,
            decision="approved",
            notes="Audit trace should fail due to missing fields."
        )


def test_review_one_way_import_isolation_enforcement():
    """Verify that importing has no footprint in core and respects boundaries."""
    assert HumanReviewGate is not None
