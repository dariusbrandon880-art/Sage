"""SAGE Mission 0.3 — CIV Integration Readiness Tests for Bond Middleware.

This test suite establishes the Integration Test Boundary for CIV-001,
validating strict state transition compliance and safety invariants
without modifying production runtime paths.
"""

from typing import Any, Dict, List
import pytest
from pydantic import BaseModel, Field, ValidationError


class StateTransitionPayload(BaseModel):
    """Canonical schema for SAGE CIV State Transition."""
    identity: str = Field(..., description="Active node identity executing the change")
    authority: str = Field(..., description="Authorized validator signature")
    from_state: str = Field(..., description="Expected source state")
    to_state: str = Field(..., description="Expected destination state")
    payload: Dict[str, Any] = Field(..., description="Transition evidence payload")


class BondMiddleware:
    """Simulated SAGE Bond Middleware implementing CIV-001 control gates.

    Provides strict transaction isolation, path validation, and zero-mutation on failure.
    """

    def __init__(self, authorized_identity: str, authorized_authority: str, initial_state: str = "S0"):
        self.authorized_identity = authorized_identity
        self.authorized_authority = authorized_authority
        self.current_state = initial_state
        self.history = [initial_state]

    def process_transition(self, raw_payload: Any) -> str:
        """Process and validate a state transition request.

        Raises exceptions with CIV-ERR-XXX codes on failure, ensuring zero state mutation.
        """
        # 1. Malformed structure check (non-dictionary raw payload) -> CIV-ERR-SCHM-002
        if not isinstance(raw_payload, dict):
            raise ValueError("CIV-ERR-SCHM-002: Malformed structure - payload must be a dictionary.")

        # 2. Missing schema field validation -> CIV-ERR-SCHM-005
        required_fields = ["identity", "authority", "from_state", "to_state", "payload"]
        missing_fields = [f for f in required_fields if f not in raw_payload]
        if missing_fields:
            raise ValueError(f"CIV-ERR-SCHM-005: Missing schema fields: {', '.join(missing_fields)}")

        # 3. Malformed structure check (field types or internal models invalid) -> CIV-ERR-SCHM-002
        if not isinstance(raw_payload.get("identity"), str) or not isinstance(raw_payload.get("authority"), str):
            raise ValueError("CIV-ERR-SCHM-002: Malformed structure - field types are invalid.")
        if not isinstance(raw_payload.get("payload"), dict):
            raise ValueError("CIV-ERR-SCHM-002: Malformed structure - 'payload' must be a dictionary.")

        # Pydantic schema validation as secondary barrier
        try:
            validated_payload = StateTransitionPayload(**raw_payload)
        except ValidationError as e:
            raise ValueError(f"CIV-ERR-SCHM-002: Pydantic validation failed: {e!s}")

        # 4. Identity mutation validation -> CIV-ERR-MUT-003
        if validated_payload.identity != self.authorized_identity:
            raise ValueError(
                f"CIV-ERR-MUT-003: Identity mutation detected. Expected '{self.authorized_identity}', "
                f"got '{validated_payload.identity}'."
            )

        # 5. Authority mismatch validation -> CIV-ERR-AUTH-001
        if validated_payload.authority != self.authorized_authority:
            raise ValueError(
                f"CIV-ERR-AUTH-001: Authority mismatch - signature registry mismatch. "
                f"Expected '{self.authorized_authority}', got '{validated_payload.authority}'."
            )

        # 6. Ambiguous payload validation -> CIV-ERR-EXT-004
        payload_data = validated_payload.payload
        if "conflict" in payload_data or ("success" in payload_data and "failure" in payload_data):
            raise ValueError("CIV-ERR-EXT-004: Ambiguous payload specifications detected.")
        if validated_payload.from_state == validated_payload.to_state and validated_payload.to_state != "S0":
            raise ValueError("CIV-ERR-EXT-004: Ambiguous payload - source and destination states are identical.")

        # State transition validation
        if validated_payload.from_state != self.current_state:
            raise ValueError(
                f"CIV-ERR-EXT-004: Ambiguous state transition path. "
                f"Current state is '{self.current_state}', payload from_state is '{validated_payload.from_state}'."
            )

        # All gates passed. Execute safe state mutation
        self.current_state = validated_payload.to_state
        self.history.append(self.current_state)
        return self.current_state


# --- TEST CASES ---

@pytest.fixture
def test_env():
    """Initializes a standard secure BondMiddleware instance."""
    return BondMiddleware(
        authorized_identity="gemini_jules_node",
        authorized_authority="authorized_human_sig_999",
        initial_state="S0"
    )


def test_valid_state_transition_pass(test_env):
    """Scenario PASS: A perfectly formed, authorized transition succeeds."""
    payload = {
        "identity": "gemini_jules_node",
        "authority": "authorized_human_sig_999",
        "from_state": "S0",
        "to_state": "S1",
        "payload": {"objective": "Establish CIV-001 Readiness", "confidence": "validated"}
    }

    new_state = test_env.process_transition(payload)
    assert new_state == "S1"
    assert test_env.current_state == "S1"
    assert test_env.history == ["S0", "S1"]


def test_identity_mutation_fail_civ_err_mut_003(test_env):
    """Scenario FAIL: Attempting to mutate identity or node ownership mid-transaction fails."""
    payload = {
        "identity": "unauthorized_impostor_node",
        "authority": "authorized_human_sig_999",
        "from_state": "S0",
        "to_state": "S1",
        "payload": {"objective": "Establish CIV-001 Readiness"}
    }

    with pytest.raises(ValueError, match="CIV-ERR-MUT-003"):
        test_env.process_transition(payload)


def test_authority_mismatch_fail_civ_err_auth_001(test_env):
    """Scenario FAIL: Forged or invalid authority/signature fails."""
    payload = {
        "identity": "gemini_jules_node",
        "authority": "forged_malicious_sig_666",
        "from_state": "S0",
        "to_state": "S1",
        "payload": {"objective": "Establish CIV-001 Readiness"}
    }

    with pytest.raises(ValueError, match="CIV-ERR-AUTH-001"):
        test_env.process_transition(payload)


def test_malformed_structure_fail_civ_err_schm_002_non_dict(test_env):
    """Scenario FAIL: Non-dictionary or raw malformed structure fails."""
    malformed_payload = "not_a_dictionary_payload"

    with pytest.raises(ValueError, match="CIV-ERR-SCHM-002"):
        test_env.process_transition(malformed_payload)


def test_malformed_structure_fail_civ_err_schm_002_invalid_field_types(test_env):
    """Scenario FAIL: Dictionary containing malformed field types fails."""
    payload = {
        "identity": 12345,  # Should be string
        "authority": "authorized_human_sig_999",
        "from_state": "S0",
        "to_state": "S1",
        "payload": "not_a_dictionary"  # Should be dict
    }

    with pytest.raises(ValueError, match="CIV-ERR-SCHM-002"):
        test_env.process_transition(payload)


def test_missing_schema_field_fail_civ_err_schm_005(test_env):
    """Scenario FAIL: Payload missing key fields fails."""
    payload = {
        "identity": "gemini_jules_node",
        "authority": "authorized_human_sig_999",
        "from_state": "S0"
        # Missing to_state and payload
    }

    with pytest.raises(ValueError, match="CIV-ERR-SCHM-005"):
        test_env.process_transition(payload)


def test_ambiguous_payload_fail_civ_err_ext_004_conflict_keys(test_env):
    """Scenario FAIL: Payload with ambiguous or conflicting signals fails."""
    payload = {
        "identity": "gemini_jules_node",
        "authority": "authorized_human_sig_999",
        "from_state": "S0",
        "to_state": "S1",
        "payload": {"conflict": True, "action": "abort_and_proceed"}
    }

    with pytest.raises(ValueError, match="CIV-ERR-EXT-004"):
        test_env.process_transition(payload)


def test_ambiguous_payload_fail_civ_err_ext_004_identical_states(test_env):
    """Scenario FAIL: Payload with identical states (excluding S0) is ambiguous."""
    # S1 -> S1 transition is ambiguous/invalid
    test_env.current_state = "S1"
    payload = {
        "identity": "gemini_jules_node",
        "authority": "authorized_human_sig_999",
        "from_state": "S1",
        "to_state": "S1",
        "payload": {"status": "heartbeat"}
    }

    with pytest.raises(ValueError, match="CIV-ERR-EXT-004"):
        test_env.process_transition(payload)


def test_safety_failed_validation_does_not_mutate_state(test_env):
    """Safety Invariant: Any failed validation must result in zero state mutation."""
    # Record initial state
    initial_state = test_env.current_state
    initial_history = list(test_env.history)

    # Trigger a series of failures
    failed_payloads = [
        # 1. Identity mutation
        {
            "identity": "unauthorized_impostor_node",
            "authority": "authorized_human_sig_999",
            "from_state": "S0",
            "to_state": "S1",
            "payload": {}
        },
        # 2. Authority mismatch
        {
            "identity": "gemini_jules_node",
            "authority": "forged_malicious_sig_666",
            "from_state": "S0",
            "to_state": "S1",
            "payload": {}
        },
        # 3. Malformed structure
        "malformed_structure_string",
        # 4. Missing fields
        {
            "identity": "gemini_jules_node",
            "authority": "authorized_human_sig_999"
        }
    ]

    for bad_payload in failed_payloads:
        try:
            test_env.process_transition(bad_payload)
        except ValueError:
            pass

    # Verify state remains absolutely pristine/unmodified
    assert test_env.current_state == initial_state
    assert test_env.history == initial_history
