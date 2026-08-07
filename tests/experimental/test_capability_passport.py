"""Unit test suite for SAGE Capability Passport Governance Engine (SAGE-CPGE)."""

import pytest
from sage.experimental.act.capability_passport import (
    CapabilityPassport,
    CapabilityPassportGovernanceEngine,
    CapabilityStateTransitionRecord
)


def test_capability_passport_valid():
    """Verify that a compliant Capability Passport initializes successfully."""
    passport = CapabilityPassport(
        name="CAP-COGNITIVE-KERNEL",
        purpose="Simulates safety gate checks for mission alignment and operator constraints.",
        lifecycle_state="PROPOSED",
        dependencies=[],
        validation_strategy="Cognitive Safety Gate Test Plan",
        evidence_path="evidence_capture/cognitive_kernel_foundation_report.json",
        archive_location="Main Archive/INDEX.md",
        reviewer_decision="Pending",
        allowed_next_state="VALIDATED"
    )

    assert passport.name == "CAP-COGNITIVE-KERNEL"
    assert passport.lifecycle_state == "PROPOSED"


def test_capability_passport_invalid_name():
    """Verify that a Capability Passport rejects non-conforming name structures."""
    with pytest.raises(ValueError, match="SAGE Passport Violation: Name must start with 'CAP-'"):
        CapabilityPassport(
            name="SAGE-ACT-CCL",  # Missing CAP- prefix
            purpose="Enforce execution continuity",
            lifecycle_state="PROPOSED",
            validation_strategy="Chamber Test",
            evidence_path="evidence.json",
            archive_location="INDEX.md"
        )


def test_no_orphan_capability_rule():
    """Verify that the engine correctly detects and tags orphan capabilities."""
    engine = CapabilityPassportGovernanceEngine()

    # Valid passport satisfies No Orphan Rule
    valid_passport = CapabilityPassport(
        name="CAP-SAGE-ACT",
        purpose="Enforce execution continuity",
        lifecycle_state="PROPOSED",
        validation_strategy="Chamber Test",
        evidence_path="evidence.json",
        archive_location="INDEX.md"
    )
    assert engine.verify_no_orphan_rule(valid_passport) is True

    # Invalid evidence path format makes it an orphan
    invalid_path_passport = CapabilityPassport(
        name="CAP-SAGE-ACT",
        purpose="Enforce execution continuity",
        lifecycle_state="PROPOSED",
        validation_strategy="Chamber Test",
        evidence_path="evidence.txt",  # Must be .json
        archive_location="INDEX.md"
    )
    assert engine.verify_no_orphan_rule(invalid_path_passport) is False


def test_state_transition_approved():
    """Verify that approved reviewer decisions cleanly transition the capability state."""
    engine = CapabilityPassportGovernanceEngine()

    passport = CapabilityPassport(
        name="CAP-SAGE-ACT",
        purpose="Enforce execution continuity",
        lifecycle_state="PROPOSED",
        validation_strategy="Chamber Test",
        evidence_path="evidence.json",
        archive_location="INDEX.md",
        allowed_next_state="VALIDATED"
    )

    record = engine.process_state_transition(
        passport=passport,
        evidence_package_id="EXP-CMAPS-001",
        reviewer_decision="Approved"
    )

    assert record.capability_name == "CAP-SAGE-ACT"
    assert record.current_state == "PROPOSED"
    assert record.reviewer_decision == "Approved"
    assert record.next_allowed_state == "VALIDATED"
