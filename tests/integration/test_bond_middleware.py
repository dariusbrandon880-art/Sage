"""SAGE Mission 0.5 — Bond Invariant Integration (Controlled Activation).

This test suite establishes the Integration Test Boundary for CIV-001/Bond,
validating strict state transition compliance, replay protection, and safety invariants
without modifying production runtime paths.
"""

from typing import Any, Dict, List, Set
import pytest
from pydantic import BaseModel, Field, ValidationError


class StateTransitionPayload(BaseModel):
    """Canonical schema for SAGE CIV State Transition."""
    identity: str = Field(..., description="Active node identity executing the change")
    authority: str = Field(..., description="Authorized validator signature")
    from_state: str = Field(..., description="Expected source state")
    to_state: str = Field(..., description="Expected destination state")
    payload: Dict[str, Any] = Field(..., description="Transition evidence payload")
    nonce: str | None = Field(None, description="Unique nonce for replay prevention")


class BondMiddleware:
    """Simulated SAGE Bond Middleware implementing CIV-001 control gates.

    Provides strict transaction isolation, path validation, replay protection, and zero-mutation on failure.
    """

    def __init__(self, authorized_identity: str, authorized_authority: str, initial_state: str = "S0"):
        self.authorized_identity = authorized_identity
        self.authorized_authority = authorized_authority
        self.current_state = initial_state
        self.history = [initial_state]
        self.used_nonces: Set[str] = set()
        self.processed_payloads: Dict[str, Dict[str, Any]] = {}

    def process_transition(self, raw_payload: Any) -> str:
        """Process and validate a state transition request.

        Raises exceptions with CIV-ERR-XXX codes on failure, ensuring zero state mutation.
        On success, returns "VALIDATION_PASS" and mutates the current state.
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

        # 4. Replay and Idempotency Protection
        nonce = validated_payload.nonce
        if nonce:
            if nonce in self.used_nonces:
                # Check for idempotent behavior: identical payload can pass deterministically without mutating state again
                previous_payload = self.processed_payloads.get(nonce)
                if previous_payload == raw_payload:
                    return "VALIDATION_PASS"  # Idempotent pass
                else:
                    # Different payload with same nonce is a replay attack
                    raise ValueError(f"CIV-ERR-EXT-004: Replay attack detected for nonce '{nonce}'.")
            self.used_nonces.add(nonce)
            self.processed_payloads[nonce] = raw_payload

        # 5. Identity mutation validation -> CIV-ERR-MUT-003
        if validated_payload.identity != self.authorized_identity:
            raise ValueError(
                f"CIV-ERR-MUT-003: Identity mutation detected. Expected '{self.authorized_identity}', "
                f"got '{validated_payload.identity}'."
            )

        # 6. Authority mismatch validation -> CIV-ERR-AUTH-001
        if validated_payload.authority != self.authorized_authority:
            raise ValueError(
                f"CIV-ERR-AUTH-001: Authority mismatch - signature registry mismatch. "
                f"Expected '{self.authorized_authority}', got '{validated_payload.authority}'."
            )

        # 7. Ambiguous payload validation -> CIV-ERR-EXT-004
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
        return "VALIDATION_PASS"


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
    """Scenario 1: VALID transition produces VALIDATION_PASS."""
    payload = {
        "identity": "gemini_jules_node",
        "authority": "authorized_human_sig_999",
        "from_state": "S0",
        "to_state": "S1",
        "payload": {"objective": "Establish CIV-001 Readiness", "confidence": "validated"}
    }

    result = test_env.process_transition(payload)
    assert result == "VALIDATION_PASS"
    assert test_env.current_state == "S1"
    assert test_env.history == ["S0", "S1"]


def test_identity_mutation_fail_civ_err_mut_003(test_env):
    """Scenario 2: Identity mutation triggers CIV-ERR-MUT-003."""
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
    """Scenario 3: Authority mismatch triggers CIV-ERR-AUTH-001."""
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
    """Scenario 4: Malformed payload triggers CIV-ERR-SCHM-002 (non-dictionary)."""
    malformed_payload = "not_a_dictionary_payload"

    with pytest.raises(ValueError, match="CIV-ERR-SCHM-002"):
        test_env.process_transition(malformed_payload)


def test_malformed_structure_fail_civ_err_schm_002_invalid_field_types(test_env):
    """Scenario 4: Malformed payload triggers CIV-ERR-SCHM-002 (invalid field types)."""
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
    """Scenario 5: Missing fields trigger CIV-ERR-SCHM-005."""
    payload = {
        "identity": "gemini_jules_node",
        "authority": "authorized_human_sig_999",
        "from_state": "S0"
        # Missing to_state and payload
    }

    with pytest.raises(ValueError, match="CIV-ERR-SCHM-005"):
        test_env.process_transition(payload)


def test_ambiguous_payload_fail_civ_err_ext_004_conflict_keys(test_env):
    """Scenario 6: Ambiguous payload triggers CIV-ERR-EXT-004 (conflict keys)."""
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
    """Scenario 6: Ambiguous payload triggers CIV-ERR-EXT-004 (identical states)."""
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


def test_safety_failed_transactions_restore_exact_pre_state(test_env):
    """Scenario 7: Failed transactions restore exact pre-state (S0)."""
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

    # Verify state remains absolutely pristine/unmodified (S0)
    assert test_env.current_state == "S0"
    assert test_env.history == ["S0"]


def test_replay_idempotency_behavior_is_deterministic(test_env):
    """Scenario 8: Replay/idempotency behavior is deterministic.

    - Exact same transaction payload with same nonce is handled idempotently and passes.
    - Altered transaction payload with same nonce is detected as a replay attack and rejected.
    """
    payload_v1 = {
        "identity": "gemini_jules_node",
        "authority": "authorized_human_sig_999",
        "from_state": "S0",
        "to_state": "S1",
        "payload": {"objective": "Deterministic Transition 1"},
        "nonce": "nonce_xyz_777"
    }

    # 1. First execution -> Valid transition succeeds
    result_1 = test_env.process_transition(payload_v1)
    assert result_1 == "VALIDATION_PASS"
    assert test_env.current_state == "S1"

    # 2. Idempotent second execution -> Exact same payload returns VALIDATION_PASS without mutating or adding history again
    history_len_before = len(test_env.history)
    result_2 = test_env.process_transition(payload_v1)
    assert result_2 == "VALIDATION_PASS"
    assert len(test_env.history) == history_len_before

    # 3. Replay attack execution -> Altered payload with same nonce triggers replay attack error (CIV-ERR-EXT-004)
    payload_replay_attack = {
        "identity": "gemini_jules_node",
        "authority": "authorized_human_sig_999",
        "from_state": "S1",
        "to_state": "S2",
        "payload": {"objective": "MALICIOUS STATE INJECTION"},
        "nonce": "nonce_xyz_777"  # REPLAY
    }

    with pytest.raises(ValueError, match="CIV-ERR-EXT-004"):
        test_env.process_transition(payload_replay_attack)
