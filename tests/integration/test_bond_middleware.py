"""SAGE Mission 0.3 & 0.4 — CIV Integration and Connection Bond Middleware Tests.

This test suite establishes the Integration Test Boundary for both the CIV-001
readiness baseline (Mission 0.3) and the actual SAGE BondManager connection
boundary (Mission 0.4), validating strict state transition compliance and safety invariants.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List
import pytest
from pydantic import BaseModel, Field, ValidationError

from sage.core.boundary import BoundaryEnforcer
from sage.core.spek import SpekEngine
from sage.acr.bond import BondManager, BondValidationError, StateTransitionPayload as ActualStateTransitionPayload


# ==========================================
# MISSION 0.3: CIV-001 MOCK READINESS BOUNDARY
# ==========================================

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


# --- TEST CASES FOR MISSION 0.3 ---

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


# ==========================================
# MISSION 0.4: ACTUAL SAGE CONNECTION BOND
# ==========================================

@pytest.fixture
def temp_capture_dir():
    """Create a temporary directory for SAGE-EVID-003 evidence capture."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_spek_paths(tmp_path):
    """Fixture providing isolated temporary paths for SpekEngine validation."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_path = config_dir / "runtime.json"

    # Write a default test config with evidence threshold 0.7
    config_data = {
        "spek_version": "1.1",
        "evidence_threshold": 0.7,
        "csi_threshold": 0.5,
        "attestation_provider": "Mock",
        "runtime_mode": "testing",
    }
    with open(config_path, "w") as f:
        json.dump(config_data, f)

    audit_dir = tmp_path / "validation" / "audit"
    audit_dir.mkdir(parents=True)

    vault_path = audit_dir / "spek_vault.json"
    promotion_path = audit_dir / "promotion_queue.log"
    rejection_path = audit_dir / "negative_results.json"
    hdg_path = audit_dir / "hdg_causality.json"

    # Initialize ledgers
    with open(vault_path, "w") as f:
        json.dump([], f)
    with open(rejection_path, "w") as f:
        json.dump([], f)
    with open(hdg_path, "w") as f:
        json.dump([], f)
    promotion_path.touch()

    return {
        "config_path": config_path,
        "vault_path": vault_path,
        "promotion_path": promotion_path,
        "rejection_path": rejection_path,
        "hdg_path": hdg_path,
    }


@pytest.fixture
def spek_engine(temp_spek_paths):
    """Fixture for pre-configured SpekEngine."""
    return SpekEngine(
        config_path=temp_spek_paths["config_path"],
        vault_path=temp_spek_paths["vault_path"],
        promotion_path=temp_spek_paths["promotion_path"],
        rejection_path=temp_spek_paths["rejection_path"],
        hdg_path=temp_spek_paths["hdg_path"],
    )


@pytest.fixture
def bond_manager(spek_engine, temp_capture_dir):
    """Fixture for BondManager connected to the SpekEngine."""
    return BondManager(
        spek_engine=spek_engine,
        evidence_capture_dir=str(temp_capture_dir)
    )


def test_bond_validation_pass(bond_manager, temp_capture_dir):
    """Test standard VALIDATION_PASS state transition and SAGE-EVID-003 receipt generation."""
    s0_state = {
        "current_project_state": "S0",
        "unresolved_items": ["task_implement_bond"],
        "active_milestone": "milestone_0",
    }

    payload = {
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Propose initial transition to Delta state",
        "author": "jules",
        "validation_score": 0.85,  # Meets 0.7 threshold
        "evidence_refs": ["task_implement_bond"],
        "parent_ids": [],
        "contradictions": [],
        "auth_token": BoundaryEnforcer.SYSTEM_TOKEN,
        "metadata": {"milestone": "milestone_1"}
    }

    s1_state = bond_manager.execute_transition(s0_state, payload)

    # 1. State Mutation check
    assert s1_state["current_project_state"] == "Delta"
    assert s1_state["active_milestone"] == "milestone_1"
    assert "task_implement_bond" not in s1_state["unresolved_items"]
    assert "last_applied_transition" in s1_state

    # 2. Evidence Capture (SAGE-EVID-003) check
    captured_files = list(temp_capture_dir.glob("evidence_*.json"))
    assert len(captured_files) == 1

    with open(captured_files[0], "r") as f:
        event_data = json.load(f)

    assert event_data["status"] == "VALIDATION_PASS"
    assert "receipt_hash" in event_data
    assert event_data["transition"]["from_state"] == "S0"
    assert event_data["transition"]["to_state"] == "Delta"


def test_bond_civ_err_auth_001_security_boundary(bond_manager):
    """Test CIV-ERR-AUTH-001 boundary violation and rollback integrity."""
    s0_state = {
        "current_project_state": "S0",
    }

    payload = {
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Unauthorized token attempt",
        "author": "attacker",
        "validation_score": 0.9,
        "auth_token": "BAD_ACCESS_TOKEN"  # Invalid token
    }

    # Verify exact error code emission
    with pytest.raises(BondValidationError) as exc_info:
        bond_manager.execute_transition(s0_state, payload)

    assert exc_info.value.error_code == "CIV-ERR-AUTH-001"
    assert "Security Boundary" in exc_info.value.message

    # Rollback verification: original S0 state must be untouched
    assert s0_state["current_project_state"] == "S0"
    assert "last_applied_transition" not in s0_state


def test_bond_civ_err_mut_003_invalid_transition(bond_manager):
    """Test CIV-ERR-MUT-003 out-of-order state transition and rollback integrity."""
    s0_state = {
        "current_project_state": "S0",
    }

    payload = {
        "from_state": "S0",
        "to_state": "Validation",  # Skipping 'Delta' and 'Evidence' states
        "description": "Skipping mandatory STP lifecycle steps",
        "author": "jules",
        "validation_score": 0.9,
        "auth_token": BoundaryEnforcer.SYSTEM_TOKEN
    }

    with pytest.raises(BondValidationError) as exc_info:
        bond_manager.execute_transition(s0_state, payload)

    assert exc_info.value.error_code == "CIV-ERR-MUT-003"
    assert "Invalid state transition sequence" in exc_info.value.message

    # Rollback verification
    assert s0_state["current_project_state"] == "S0"


def test_bond_civ_err_schm_002_malformed_payload(bond_manager):
    """Test CIV-ERR-SCHM-002 payload schema invalidation and rollback integrity."""
    s0_state = {
        "current_project_state": "S0",
    }

    # Missing required 'author' and 'validation_score' parameters
    payload = {
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Malformed schema",
        "auth_token": BoundaryEnforcer.SYSTEM_TOKEN
    }

    with pytest.raises(BondValidationError) as exc_info:
        bond_manager.execute_transition(s0_state, payload)

    assert exc_info.value.error_code == "CIV-ERR-SCHM-002"
    assert "Schema validation failed" in exc_info.value.message

    # Rollback verification
    assert s0_state["current_project_state"] == "S0"


def test_bond_civ_err_schm_005_causality_contradiction(bond_manager):
    """Test CIV-ERR-SCHM-005 causality loop or contradiction violation and rollback integrity."""
    s0_state = {
        "current_project_state": "S0",
    }

    # Part A: Circular dependency cycle reference
    payload_circular = {
        "transition_id": "trans_cycle_1",
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Causality loop",
        "author": "jules",
        "validation_score": 0.8,
        "parent_ids": ["trans_cycle_1"],  # References itself as ancestor
        "auth_token": BoundaryEnforcer.SYSTEM_TOKEN
    }

    with pytest.raises(BondValidationError) as exc_info:
        bond_manager.execute_transition(s0_state, payload_circular)

    assert exc_info.value.error_code == "CIV-ERR-SCHM-005"
    assert "Circular dependency" in exc_info.value.message
    assert s0_state["current_project_state"] == "S0"

    # Part B: Ancestor contradiction reference
    payload_contradiction = {
        "transition_id": "trans_node_b",
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Contradicting ancestor state node",
        "author": "jules",
        "validation_score": 0.8,
        "parent_ids": ["node_a"],
        "contradictions": ["node_a"],  # Contradicts listed ancestor
        "auth_token": BoundaryEnforcer.SYSTEM_TOKEN
    }

    with pytest.raises(BondValidationError) as exc_info:
        bond_manager.execute_transition(s0_state, payload_contradiction)

    assert exc_info.value.error_code == "CIV-ERR-SCHM-005"
    assert "Contradiction detected with ancestor nodes" in exc_info.value.message
    assert s0_state["current_project_state"] == "S0"


def test_bond_civ_err_ext_004_low_evidence(bond_manager):
    """Test CIV-ERR-EXT-004 low evidence rejection and rollback integrity."""
    s0_state = {
        "current_project_state": "S0",
    }

    payload = {
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Insufficient evidence validation score",
        "author": "jules",
        "validation_score": 0.55,  # Below 0.7 default threshold
        "auth_token": BoundaryEnforcer.SYSTEM_TOKEN
    }

    with pytest.raises(BondValidationError) as exc_info:
        bond_manager.execute_transition(s0_state, payload)

    assert exc_info.value.error_code == "CIV-ERR-EXT-004"
    assert "is below evidence threshold" in exc_info.value.message

    # Rollback verification
    assert s0_state["current_project_state"] == "S0"
