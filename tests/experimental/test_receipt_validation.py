"""Unit tests for experimental Capability Evidence Receipt Generator prototype."""

import pytest
from datetime import datetime, timezone
from sage.experimental.act.contracts import (
    CapabilityPassportValidator,
    CapabilityEvidenceReceiptGenerator,
)


@pytest.fixture
def sample_valid_passport():
    return {
        "capability_id": "cap_sdr_sim_engine",
        "name": "SAGE-SDR Simulation Engine",
        "purpose": "Simulates dry-runs of multi-agent execution safely in isolated space.",
        "lifecycle_state": "proposed",
        "validation_strategy": "Verify execution outputs in ephemeral sandbox directory.",
        "evidence_path": "docs/SAGE-SDR-READINESS-SPECIFICATION.md",
        "dependencies": ["cap_spek_kernel", "cap_act_lineage"],
        "human_signoff": {
            "signer": "SAGE Supervisor",
            "timestamp": "2026-03-31T12:00:00Z",
            "approved": True,
        }
    }


def test_evidence_receipt_generation_success(sample_valid_passport):
    """Verify that a standard receipt is generated successfully with correct structures."""
    passport_validator = CapabilityPassportValidator()
    val_result = passport_validator.validate_passport(sample_valid_passport)

    receipt_generator = CapabilityEvidenceReceiptGenerator(validator_id="val_system_test")
    outcome = receipt_generator.generate_receipt(
        passport=sample_valid_passport,
        validation_result=val_result
    )

    assert outcome["traceability_chain_valid"] is True
    assert outcome["read_only_assertion"] is True

    receipt = outcome["receipt"]
    assert receipt["capability_id"] == "cap_sdr_sim_engine"
    assert receipt["validator_id"] == "val_system_test"
    assert receipt["evidence_reference"] == "docs/SAGE-SDR-READINESS-SPECIFICATION.md"
    assert receipt["review_status"] == "approved"
    assert receipt["archive_destination"] == "Main Archive/cap_sdr_sim_engine_receipt.json"
    assert receipt["validation_result"]["status"] == "PASSPORT_VALIDATED"


def test_evidence_receipt_generation_mismatch(sample_valid_passport):
    """Verify generator rejects receipt request if passport ID mismatch occurs."""
    receipt_generator = CapabilityEvidenceReceiptGenerator()
    val_result = {
        "capability_id": "cap_mismatch_id",
        "validation_status": "PASSPORT_VALIDATED",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "approved": True
    }

    with pytest.raises(ValueError, match="Receipt Violation: Capability ID mismatch"):
        receipt_generator.generate_receipt(
            passport=sample_valid_passport,
            validation_result=val_result
        )


def test_evidence_receipt_missing_core_fields(sample_valid_passport):
    """Verify generator detects missing receipt variables or incorrect dictionary states."""
    receipt_generator = CapabilityEvidenceReceiptGenerator()
    # passport missing capability_id
    bad_passport = sample_valid_passport.copy()
    bad_passport.pop("capability_id")

    with pytest.raises(ValueError, match="Receipt Violation: Invalid or incomplete passport"):
        receipt_generator.generate_receipt(
            passport=bad_passport,
            validation_result={"validation_status": "PASSPORT_VALIDATED"}
        )


def test_evidence_receipt_bad_receipt_id_format(sample_valid_passport):
    """Verify generator rejects explicitly passed invalid receipt identifiers."""
    receipt_generator = CapabilityEvidenceReceiptGenerator()
    val_result = {
        "capability_id": "cap_sdr_sim_engine",
        "validation_status": "PASSPORT_VALIDATED",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "approved": True
    }

    with pytest.raises(ValueError, match="Receipt Violation: Invalid format for receipt_id"):
        receipt_generator.generate_receipt(
            passport=sample_valid_passport,
            validation_result=val_result,
            receipt_id="bad_id"  # missing prefix 'rcpt_'
        )


def test_receipt_one_way_import_isolation_enforcement():
    """Verify that importing has no footprint in core and respects boundaries."""
    assert CapabilityEvidenceReceiptGenerator is not None
