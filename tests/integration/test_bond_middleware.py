"""Integration tests for SAGE ACR/CIV Connection Bond Middleware."""

import json
import tempfile
import pytest
from pathlib import Path

from sage.core.boundary import BoundaryEnforcer
from sage.core.spek import SpekEngine
from sage.acr.bond import BondManager, BondValidationError, StateTransitionPayload


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
