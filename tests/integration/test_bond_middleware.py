import pytest
import copy
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError

# ==============================================================================
# SAGE Bond Layer - Custom Errors and Exceptions
# ==============================================================================
class BondError(Exception):
    """Base exception for all SAGE Bond Layer errors."""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")

class AuthorityMismatchError(BondError):
    def __init__(self, message: str = "Authority credentials do not match active session signature"):
        super().__init__("CIV-ERR-AUTH-001", message)

class UnauthorizedIdentityMutationError(BondError):
    def __init__(self, message: str = "Attempt to mutate identity context during active session is unauthorized"):
        super().__init__("CIV-ERR-MUT-003", message)

class MalformedPayloadError(BondError):
    def __init__(self, message: str = "Payload formatting is malformed or invalid"):
        super().__init__("CIV-ERR-SCHM-002", message)

class MissingSchemaFieldsError(BondError):
    def __init__(self, message: str = "Required fields are missing from the schema"):
        super().__init__("CIV-ERR-SCHM-005", message)

class AmbiguousPayloadError(BondError):
    def __init__(self, message: str = "Payload is ambiguous due to conflicting keys or parameters"):
        super().__init__("CIV-ERR-EXT-004", message)


# ==============================================================================
# SAGE Bond Layer - Schemas
# ==============================================================================
class StateTransitionPayload(BaseModel):
    tx_id: str
    auth_token: str
    identity_ref: str
    target_state: str
    evidence_refs: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ==============================================================================
# SAGE Bond Layer - Simulated Bond Middleware & Nonce Ledger
# ==============================================================================
class NonceLedger:
    def __init__(self):
        self._processed_tx_ids = set()

    def register_tx(self, tx_id: str) -> bool:
        if tx_id in self._processed_tx_ids:
            return False
        self._processed_tx_ids.add(tx_id)
        return True


class SimulatedBondMiddleware:
    def __init__(self, expected_token: str = "sys_trust_token_abc"):
        self.expected_token = expected_token
        self.nonce_ledger = NonceLedger()

    def intercept_and_validate(self, state: Dict[str, Any], raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Capture original state deep copy (for rollback guarantee)
        state_backup = copy.deepcopy(state)

        try:
            # Check for Ambiguous Payload (CIV-ERR-EXT-004)
            # Scenario: Having conflicting keys or parameters
            if "target_state" in raw_payload and "state_destination" in raw_payload:
                raise AmbiguousPayloadError()

            # Check for missing schema fields (CIV-ERR-SCHM-005)
            required_fields = ["tx_id", "auth_token", "identity_ref", "target_state", "evidence_refs"]
            for field in required_fields:
                if field not in raw_payload:
                    raise MissingSchemaFieldsError(f"Missing schema field: '{field}'")

            # Check for malformed payload types (CIV-ERR-SCHM-002)
            try:
                payload = StateTransitionPayload(**raw_payload)
            except ValidationError as ve:
                raise MalformedPayloadError(str(ve))

            # Check for Authority Mismatch (CIV-ERR-AUTH-001)
            if payload.auth_token != self.expected_token:
                raise AuthorityMismatchError()

            # Check for Identity Mutation (CIV-ERR-MUT-003)
            # Scenario: Attempt to alter active identity reference on the fly
            if state.get("identity_ref") and payload.identity_ref != state.get("identity_ref"):
                raise UnauthorizedIdentityMutationError()

            # Replay protection / Idempotency behavior
            if not self.nonce_ledger.register_tx(payload.tx_id):
                raise BondError("CIV-ERR-REPLAY-006", "Transaction already processed (replay attempt)")

            # Mutation occurs on success
            state["active_state"] = payload.target_state
            state["identity_ref"] = payload.identity_ref
            state["last_tx_id"] = payload.tx_id

            return {
                "status": "VALIDATION_PASS",
                "emitted_event": "VALIDATION_PASS",
                "state": state
            }

        except Exception as e:
            # Fallback rollback guarantee: state must be left completely unchanged on failure
            # Explicitly restore S0 to satisfy: S0 == restored state
            state.clear()
            state.update(state_backup)

            if isinstance(e, BondError):
                return {
                    "status": "VALIDATION_FAIL",
                    "code": e.code,
                    "message": e.message,
                    "state": state
                }
            raise e


# ==============================================================================
# SAGE Integration Test Suite
# ==============================================================================
def test_valid_state_transition_emits_validation_pass():
    """Verify that a valid payload transitions the state and returns VALIDATION_PASS."""
    middleware = SimulatedBondMiddleware()
    state = {"active_state": "S0", "identity_ref": "agent_jules"}
    payload = {
        "tx_id": "tx_001",
        "auth_token": "sys_trust_token_abc",
        "identity_ref": "agent_jules",
        "target_state": "S1",
        "evidence_refs": ["ev_ref_101"]
    }

    result = middleware.intercept_and_validate(state, payload)

    assert result["status"] == "VALIDATION_PASS"
    assert result["emitted_event"] == "VALIDATION_PASS"
    assert state["active_state"] == "S1"
    assert state["last_tx_id"] == "tx_001"


def test_identity_mutation_attempt_fails():
    """Verify identity mutation yields CIV-ERR-MUT-003 and leaves state unchanged."""
    middleware = SimulatedBondMiddleware()
    state = {"active_state": "S0", "identity_ref": "agent_jules"}
    payload = {
        "tx_id": "tx_002",
        "auth_token": "sys_trust_token_abc",
        "identity_ref": "agent_hacker_mutated", # Mutated identity attempt
        "target_state": "S1",
        "evidence_refs": ["ev_ref_102"]
    }

    result = middleware.intercept_and_validate(state, payload)

    assert result["status"] == "VALIDATION_FAIL"
    assert result["code"] == "CIV-ERR-MUT-003"
    # Verify state remains completely unchanged (S0 == restored state)
    assert state["active_state"] == "S0"
    assert state["identity_ref"] == "agent_jules"


def test_authority_mismatch_fails():
    """Verify unauthorized authority token yields CIV-ERR-AUTH-001 and leaves state unchanged."""
    middleware = SimulatedBondMiddleware()
    state = {"active_state": "S0", "identity_ref": "agent_jules"}
    payload = {
        "tx_id": "tx_003",
        "auth_token": "invalid_untrusted_token", # Authority Mismatch
        "identity_ref": "agent_jules",
        "target_state": "S1",
        "evidence_refs": ["ev_ref_103"]
    }

    result = middleware.intercept_and_validate(state, payload)

    assert result["status"] == "VALIDATION_FAIL"
    assert result["code"] == "CIV-ERR-AUTH-001"
    # Verify state remains completely unchanged (S0 == restored state)
    assert state["active_state"] == "S0"


def test_malformed_payload_fails():
    """Verify malformed structures (e.g. wrong evidence_refs type) yield CIV-ERR-SCHM-002."""
    middleware = SimulatedBondMiddleware()
    state = {"active_state": "S0", "identity_ref": "agent_jules"}
    payload = {
        "tx_id": "tx_004",
        "auth_token": "sys_trust_token_abc",
        "identity_ref": "agent_jules",
        "target_state": "S1",
        "evidence_refs": "should_be_a_list_not_a_string" # Malformed payload type
    }

    result = middleware.intercept_and_validate(state, payload)

    assert result["status"] == "VALIDATION_FAIL"
    assert result["code"] == "CIV-ERR-SCHM-002"
    # Verify state remains completely unchanged (S0 == restored state)
    assert state["active_state"] == "S0"


def test_missing_schema_fields_fails():
    """Verify missing required root keys yields CIV-ERR-SCHM-005."""
    middleware = SimulatedBondMiddleware()
    state = {"active_state": "S0", "identity_ref": "agent_jules"}
    payload = {
        "tx_id": "tx_005",
        "auth_token": "sys_trust_token_abc",
        # "identity_ref" is missing
        "target_state": "S1",
        "evidence_refs": ["ev_ref_105"]
    }

    result = middleware.intercept_and_validate(state, payload)

    assert result["status"] == "VALIDATION_FAIL"
    assert result["code"] == "CIV-ERR-SCHM-005"
    # Verify state remains completely unchanged (S0 == restored state)
    assert state["active_state"] == "S0"


def test_ambiguous_payload_fails():
    """Verify having conflicting state parameters yields CIV-ERR-EXT-004."""
    middleware = SimulatedBondMiddleware()
    state = {"active_state": "S0", "identity_ref": "agent_jules"}
    payload = {
        "tx_id": "tx_006",
        "auth_token": "sys_trust_token_abc",
        "identity_ref": "agent_jules",
        "target_state": "S1",
        "state_destination": "S1_ambiguous_duplicate", # Ambiguous conflict parameter
        "evidence_refs": ["ev_ref_106"]
    }

    result = middleware.intercept_and_validate(state, payload)

    assert result["status"] == "VALIDATION_FAIL"
    assert result["code"] == "CIV-ERR-EXT-004"
    # Verify state remains completely unchanged (S0 == restored state)
    assert state["active_state"] == "S0"


def test_failed_transition_leaves_state_unchanged_complex():
    """Double-check that a failing sequence doesn't leak partial state mutations."""
    middleware = SimulatedBondMiddleware()
    state = {"active_state": "S0", "identity_ref": "agent_jules", "sensitive_attribute": "keep_intact"}
    payload = {
        "tx_id": "tx_007",
        "auth_token": "sys_trust_token_abc",
        "identity_ref": "agent_jules",
        "target_state": "S1",
        "evidence_refs": "trigger_schema_failure"
    }

    middleware.intercept_and_validate(state, payload)

    assert state["active_state"] == "S0"
    assert state["sensitive_attribute"] == "keep_intact"


def test_replay_protection_and_idempotency():
    """Verify that submitting the same tx_id twice gets flagged and rejected."""
    middleware = SimulatedBondMiddleware()
    state = {"active_state": "S0", "identity_ref": "agent_jules"}
    payload = {
        "tx_id": "tx_999",
        "auth_token": "sys_trust_token_abc",
        "identity_ref": "agent_jules",
        "target_state": "S1",
        "evidence_refs": ["ev_ref_999"]
    }

    # 1. First attempt is valid
    res1 = middleware.intercept_and_validate(state, payload)
    assert res1["status"] == "VALIDATION_PASS"
    assert state["active_state"] == "S1"

    # Reset state active_state back to S0 to verify rollback/reject behavior on replay
    state["active_state"] = "S0"

    # 2. Replay attempt
    res2 = middleware.intercept_and_validate(state, payload)
    assert res2["status"] == "VALIDATION_FAIL"
    assert res2["code"] == "CIV-ERR-REPLAY-006"
    assert state["active_state"] == "S0" # Remains S0, mutation blocked
