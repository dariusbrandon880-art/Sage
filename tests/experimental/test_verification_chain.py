"""Unit test suite for SAGE Capability Verification Chain (SAGE-CVC)."""

import pytest
from sage.experimental.act.capability_passport import CapabilityPassport
from sage.experimental.act.verification_chain import CapabilityVerificationChain


def test_cvc_verified_capability():
    """Verify that a compliant capability with tests, evidence, and boundary security returns VERIFIED."""
    chain = CapabilityVerificationChain()

    passport = CapabilityPassport(
        name="CAP-SDR-004",
        purpose="Multi-agent state recovery and priority resolutions",
        lifecycle_state="VALIDATED",
        validation_strategy="test_sdr_004_divergence",
        evidence_path="evidence_capture/sdr_004_divergence_resolution_evidence.json",
        archive_location="Main Archive/INDEX.md",
        allowed_next_state="CANONICAL"
    )

    result = chain.evaluate_capability_status(
        passport=passport,
        executed_tests=["test_sdr_004_divergence"],
        captured_evidence_files=["evidence_capture/sdr_004_divergence_resolution_evidence.json"],
        has_measurement=True,
        protected_boundary_secure=True
    )

    assert result["verification_status"] == "VERIFIED"
    assert result["evidence_supported"] is True
    # Ensure no automatic status mutation (passport's lifecycle state remains unchanged)
    assert passport.lifecycle_state == "VALIDATED"


def test_cvc_missing_validation_evidence():
    """Verify that missing both test and evidence files yields INSUFFICIENT_EVIDENCE."""
    chain = CapabilityVerificationChain()

    passport = CapabilityPassport(
        name="CAP-SDR-004",
        purpose="Multi-agent state recovery and priority resolutions",
        lifecycle_state="VALIDATED",
        validation_strategy="test_sdr_004_divergence",
        evidence_path="evidence_capture/sdr_004_divergence_resolution_evidence.json",
        archive_location="Main Archive/INDEX.md"
    )

    result = chain.evaluate_capability_status(
        passport=passport,
        executed_tests=[],
        captured_evidence_files=[],
        has_measurement=True,
        protected_boundary_secure=True
    )

    assert result["verification_status"] == "INSUFFICIENT_EVIDENCE"
    assert result["evidence_supported"] is False


def test_cvc_missing_measurement_or_boundary():
    """Verify that missing measurement or failing protected-boundary checks yields PARTIALLY_VERIFIED."""
    chain = CapabilityVerificationChain()

    passport = CapabilityPassport(
        name="CAP-SDR-004",
        purpose="Multi-agent state recovery and priority resolutions",
        lifecycle_state="VALIDATED",
        validation_strategy="test_sdr_004_divergence",
        evidence_path="evidence_capture/sdr_004_divergence_resolution_evidence.json",
        archive_location="Main Archive/INDEX.md"
    )

    result = chain.evaluate_capability_status(
        passport=passport,
        executed_tests=["test_sdr_004_divergence"],
        captured_evidence_files=["evidence_capture/sdr_004_divergence_resolution_evidence.json"],
        has_measurement=False,  # Missing measurement
        protected_boundary_secure=True
    )

    assert result["verification_status"] == "PARTIALLY_VERIFIED"
    assert result["evidence_supported"] is False


def test_cvc_contradictory_evidence():
    """Verify that contradictory declarations yield INCONSISTENT status."""
    chain = CapabilityVerificationChain()

    class MockInconsistentPassport:
        name = "CAP-CONTRADICT"
        purpose = "Test contradictions"
        lifecycle_state = "VALIDATED"
        validation_strategy = "test_strategy"
        evidence_path = "evidence.json"
        archive_location = "INDEX.md"
        allowed_next_state = "PROPOSED"  # Contradictory: downgrading allowed next state

    result = chain.evaluate_capability_status(
        passport=MockInconsistentPassport(),
        executed_tests=["test_sdr_004_divergence"],
        captured_evidence_files=["evidence_capture/sdr_004_divergence_resolution_evidence.json"]
    )

    assert result["verification_status"] == "INCONSISTENT"
    assert result["evidence_supported"] is False


def test_cvc_invalid_orphan_lineage():
    """Verify that orphan capability records yield INCOMPARABLE status."""
    chain = CapabilityVerificationChain()

    class MockOrphanPassport:
        name = "SAGE-ORPHAN"  # Missing CAP- prefix
        purpose = "Unregistered capability"
        lifecycle_state = "PROPOSED"
        validation_strategy = "No Strategy"
        evidence_path = "invalid_path.txt"
        archive_location = "INDEX.md"
        allowed_next_state = "VALIDATED"

    result = chain.evaluate_capability_status(
        passport=MockOrphanPassport(),
        executed_tests=[],
        captured_evidence_files=[]
    )

    assert result["verification_status"] == "INCOMPARABLE"
    assert result["evidence_supported"] is False
