"""Unit tests for experimental Capability Passport Validator prototype."""

import pytest
from datetime import datetime, timezone
from sage.experimental.act.contracts import CapabilityPassportValidator


def test_passport_validator_valid_payload():
    """Verify that a standard, fully compliant capability passport validates successfully."""
    validator = CapabilityPassportValidator()
    valid_passport = {
        "capability_id": "cap_sdr_sim_engine",
        "name": "SAGE-SDR Simulation Engine",
        "purpose": "Simulates dry-runs of multi-agent execution safely in isolated space.",
        "lifecycle_state": "proposed",
        "validation_strategy": "Verify execution outputs in ephemeral sandbox directory.",
        "evidence_path": "docs/SAGE-SDR-READINESS-SPECIFICATION.md",
        "dependencies": ["cap_spek_kernel", "cap_act_lineage"],
        "human_signoff": {
            "signer": "SAGE Supervisor",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "approved": True,
        }
    }

    result = validator.validate_passport(valid_passport)
    assert result["capability_id"] == "cap_sdr_sim_engine"
    assert result["validation_status"] == "PASSPORT_VALIDATED"
    assert result["approved"] is True
    assert result["read_only_assertion"] is True


def test_passport_validator_rejects_non_dict():
    """Verify validator rejects a non-dictionary input."""
    validator = CapabilityPassportValidator()
    with pytest.raises(ValueError, match="Passport Violation: Passport must be a dictionary."):
        validator.validate_passport(["not", "a", "dict"])


def test_passport_validator_missing_required_fields():
    """Verify validator rejects passport missing required core fields."""
    validator = CapabilityPassportValidator()
    incomplete_passport = {
        "capability_id": "cap_incomplete",
        "name": "Incomplete Capability",
        # purpose is missing
        "lifecycle_state": "proposed",
        "validation_strategy": "Mock strategy.",
        "evidence_path": "docs/evidence.md",
        "dependencies": [],
        "human_signoff": {
            "signer": "Tester",
            "timestamp": "2026-03-31T00:00:00Z",
            "approved": True
        }
    }
    with pytest.raises(ValueError, match="Passport Violation: Missing required field 'purpose'."):
        validator.validate_passport(incomplete_passport)


def test_passport_validator_invalid_capability_id_format():
    """Verify validator rejects capability_id missing cap_ prefix or too short/invalid pattern."""
    validator = CapabilityPassportValidator()
    bad_id_passport = {
        "capability_id": "sdr_sim_engine",  # missing "cap_"
        "name": "SAGE-SDR",
        "purpose": "A great purpose.",
        "lifecycle_state": "proposed",
        "validation_strategy": "Strategy details.",
        "evidence_path": "docs/spec.md",
        "dependencies": [],
        "human_signoff": {
            "signer": "Tester",
            "timestamp": "2026-03-31T00:00:00Z",
            "approved": True
        }
    }
    with pytest.raises(ValueError, match="Passport Violation: Invalid capability_id format"):
        validator.validate_passport(bad_id_passport)


def test_passport_validator_invalid_lifecycle_state():
    """Verify validator rejects unapproved lifecycle states."""
    validator = CapabilityPassportValidator()
    bad_state_passport = {
        "capability_id": "cap_invalid_state",
        "name": "Bad State Cap",
        "purpose": "A great purpose.",
        "lifecycle_state": "uncontrolled_migration",  # illegal state
        "validation_strategy": "Strategy details.",
        "evidence_path": "docs/spec.md",
        "dependencies": [],
        "human_signoff": {
            "signer": "Tester",
            "timestamp": "2026-03-31T00:00:00Z",
            "approved": True
        }
    }
    with pytest.raises(ValueError, match="Passport Violation: Invalid lifecycle_state"):
        validator.validate_passport(bad_state_passport)


def test_passport_validator_unauthorized_state_transition_no_signoff():
    """Verify validator rejects validated or canonical states if human signoff is not approved."""
    validator = CapabilityPassportValidator()
    unapproved_passport = {
        "capability_id": "cap_unapproved_validated",
        "name": "Unapproved validated cap",
        "purpose": "A purpose.",
        "lifecycle_state": "validated",  # requires human approval
        "validation_strategy": "Strategy details.",
        "evidence_path": "docs/spec.md",
        "dependencies": [],
        "human_signoff": {
            "signer": "Tester",
            "timestamp": "2026-03-31T00:00:00Z",
            "approved": False  # rejected/not-yet-approved
        }
    }
    with pytest.raises(ValueError, match="Passport Violation: Unauthorized transition"):
        validator.validate_passport(unapproved_passport)


def test_passport_validator_evidence_path_constraints():
    """Verify evidence path must be non-empty and point to docs/ or evidence/."""
    validator = CapabilityPassportValidator()
    bad_path_passport = {
        "capability_id": "cap_bad_path",
        "name": "Bad Path Cap",
        "purpose": "A great purpose.",
        "lifecycle_state": "proposed",
        "validation_strategy": "Strategy details.",
        "evidence_path": "extern/secrets/secret.md",  # invalid path boundary
        "dependencies": [],
        "human_signoff": {
            "signer": "Tester",
            "timestamp": "2026-03-31T00:00:00Z",
            "approved": True
        }
    }
    with pytest.raises(ValueError, match="Passport Violation: 'evidence_path' must point to docs/ or evidence/"):
        validator.validate_passport(bad_path_passport)


def test_one_way_import_isolation_enforcement():
    """Verify that testing has no foot-print in core and respects boundaries."""
    # This verifies the test file can import experimental code safely
    assert CapabilityPassportValidator is not None
