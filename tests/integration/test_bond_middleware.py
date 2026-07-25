import pytest
from sage.runtime.interceptors.bond import (
    BondValidator,
    AuthorityMismatchError,
    UnauthorizedIdentityMutationError,
    MalformedPayloadError,
    MissingSchemaFieldsError,
    AmbiguousPayloadError,
)

# ==============================================================================
# SAGE Mission 0.5 — Comprehensive Integration Tests & Shadow Activation
# ==============================================================================

def test_shadow_validation_pass_logging():
    """Verify that in shadow mode, valid payload returns VALIDATION_PASS and records audit trail."""
    validator = BondValidator(mode="shadow")
    state = {"active_state": "S0", "identity_ref": "agent_jules"}
    payload = {
        "tx_id": "tx_sh_001",
        "auth_token": "sys_trust_token_abc",
        "identity_ref": "agent_jules",
        "target_state": "S1",
        "evidence_refs": ["ev_ref_shadow_1"]
    }

    result = validator.validate_transition(state, payload)

    assert result["status"] == "VALIDATION_PASS"
    assert state["active_state"] == "S1"
    assert len(validator.audit_log) == 1
    assert validator.audit_log[0]["status"] == "VALIDATION_PASS"
    assert validator.audit_log[0]["tx_id"] == "tx_sh_001"


def test_shadow_validation_failure_capture_no_blocking():
    """
    Verify that in shadow mode, invalid payloads (e.g. Authority Mismatch)
    generate VALIDATION_FAIL_SHADOWED logs but DO NOT block the state mutation.
    """
    validator = BondValidator(mode="shadow")
    state = {"active_state": "S0", "identity_ref": "agent_jules"}
    payload = {
        "tx_id": "tx_sh_002",
        "auth_token": "hacked_untrusted_token", # Authority mismatch
        "identity_ref": "agent_jules",
        "target_state": "S1",
        "evidence_refs": ["ev_ref_shadow_2"]
    }

    result = validator.validate_transition(state, payload)

    # Result should be shadowed, indicating failure but permitting transition
    assert result["status"] == "VALIDATION_FAIL_SHADOWED"

    # Verify the failure was recorded in the audit trail with correct code
    assert len(validator.audit_log) == 1
    assert validator.audit_log[0]["status"] == "VALIDATION_FAIL"
    assert validator.audit_log[0]["code"] == "CIV-ERR-AUTH-001"
    assert validator.audit_log[0]["mode"] == "shadow"

    # State mutation must NOT be blocked during shadow mode
    assert state["active_state"] == "S1"
    assert state["last_tx_id"] == "tx_sh_002"


def test_enforce_validation_failure_blocks_mutation():
    """Verify that in enforce mode, validation failure blocks state change and rolls back to S0."""
    validator = BondValidator(mode="enforce")
    state = {"active_state": "S0", "identity_ref": "agent_jules", "sensitive_attribute": "keep"}
    payload = {
        "tx_id": "tx_enf_001",
        "auth_token": "sys_trust_token_abc",
        "identity_ref": "agent_hacker_mutated", # Identity mutation violation
        "target_state": "S1",
        "evidence_refs": ["ev_ref_enf_1"]
    }

    result = validator.validate_transition(state, payload)

    assert result["status"] == "VALIDATION_FAIL"
    assert result["code"] == "CIV-ERR-MUT-003"
    assert len(validator.audit_log) == 1
    assert validator.audit_log[0]["status"] == "VALIDATION_FAIL"

    # Enforce mode rollback guarantees: state must remain completely unchanged (S0 == restored state)
    assert state["active_state"] == "S0"
    assert state["identity_ref"] == "agent_jules"
    assert state["sensitive_attribute"] == "keep"


def test_enforce_validation_missing_schema_fields():
    """Verify missing required keys raises CIV-ERR-SCHM-005 and blocks transition in enforce mode."""
    validator = BondValidator(mode="enforce")
    state = {"active_state": "S0"}
    payload = {
        "tx_id": "tx_enf_002",
        "auth_token": "sys_trust_token_abc",
        "target_state": "S1",
        "evidence_refs": ["ev_ref_enf_2"]
        # "identity_ref" is missing
    }

    result = validator.validate_transition(state, payload)

    assert result["status"] == "VALIDATION_FAIL"
    assert result["code"] == "CIV-ERR-SCHM-005"
    assert state["active_state"] == "S0"


def test_enforce_validation_malformed_payload():
    """Verify malformed JSON payload fields raises CIV-ERR-SCHM-002 and blocks transition."""
    validator = BondValidator(mode="enforce")
    state = {"active_state": "S0"}
    payload = {
        "tx_id": "tx_enf_003",
        "auth_token": "sys_trust_token_abc",
        "identity_ref": "agent_jules",
        "target_state": "S1",
        "evidence_refs": "invalid_string_instead_of_list" # Malformed
    }

    result = validator.validate_transition(state, payload)

    assert result["status"] == "VALIDATION_FAIL"
    assert result["code"] == "CIV-ERR-SCHM-002"
    assert state["active_state"] == "S0"


def test_enforce_validation_ambiguous_payload():
    """Verify conflicting destination keys raises CIV-ERR-EXT-004 and blocks transition."""
    validator = BondValidator(mode="enforce")
    state = {"active_state": "S0"}
    payload = {
        "tx_id": "tx_enf_004",
        "auth_token": "sys_trust_token_abc",
        "identity_ref": "agent_jules",
        "target_state": "S1",
        "state_destination": "S1_duplicate_conflict", # Conflicting
        "evidence_refs": ["ev_ref_enf_4"]
    }

    result = validator.validate_transition(state, payload)

    assert result["status"] == "VALIDATION_FAIL"
    assert result["code"] == "CIV-ERR-EXT-004"
    assert state["active_state"] == "S0"
