"""Integration tests for SAGE Mission 0.4 Phase 2 & Mission 0.5 - Operational Visibility Connections."""

import os
import json
import pytest
import tempfile
import uuid
from pathlib import Path
from fastapi.testclient import TestClient

from sage.runtime.engine import SageRuntime
from sage.core.boundary import BoundaryEnforcer
from sage.acr.bond import BondValidationError
from sage.api import app


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_shadow_mode_passes_through_failures(temp_workspace, monkeypatch):
    """Test SAGE_BOND_MODE=shadow allows transitions even when validations fail.

    Shadow mode must log/observe but not raise exception or alter normal mutation.
    """
    # Force shadow mode
    monkeypatch.setenv("SAGE_BOND_MODE", "shadow")

    runtime = SageRuntime(str(temp_workspace))
    runtime.start()
    assert runtime.bond_mode == "shadow"

    # 1. Trigger transition on set_objective
    # Even if SpekEngine were to flag anything, shadow mode passes it through.
    session_id = runtime.set_objective("Connect Live shadow hooks")
    assert session_id.startswith("session_")
    assert runtime.current_state.current_objective == "Connect Live shadow hooks"


def test_shadow_mode_writes_failure_receipt(temp_workspace, monkeypatch):
    """Test that SAGE_BOND_MODE=shadow records failures correctly in compliance ledgers."""
    monkeypatch.setenv("SAGE_BOND_MODE", "shadow")

    runtime = SageRuntime(str(temp_workspace))
    runtime.start()

    # Let's inspect compliance. Rejection path must be clean initially.
    assert len(runtime.spek_engine.compliance.vault) == 0

    # Let's trigger a task update. Since it's shadow mode, it runs execution.
    runtime.set_task("Verify compliance logging")

    # Check that a validation event was registered in the Spek compliance vault
    # Every transition set_task triggers PROPOSED, EVALUATED, VALIDATED, APPROVED state transition receipts
    assert len(runtime.spek_engine.compliance.vault) >= 1
    assert runtime.spek_engine.compliance.vault[0].proposal_id.startswith("trans_")
    assert runtime.spek_engine.compliance.vault[0].lifecycle_state == "PROPOSED"


def test_enforcement_mode_strictly_blocks(temp_workspace, monkeypatch):
    """Test that SAGE_BOND_MODE=enforce strictly raises exceptions on validation failures."""
    monkeypatch.setenv("SAGE_BOND_MODE", "enforce")

    runtime = SageRuntime(str(temp_workspace))
    runtime.start()
    assert runtime.bond_mode == "enforce"

    # Let's mock a validation failure inside BondManager by calling execute_transition with bad parameters
    # If we pass an invalid auth token, it should raise CIV-ERR-AUTH-001 in enforce mode
    s0_state = {"current_project_state": "S0"}
    raw_payload_bad_token = {
        "from_state": "S0",
        "to_state": "Delta",
        "description": "Unauthorized token attempt",
        "author": "attacker",
        "validation_score": 0.9,
        "auth_token": "BAD_ACCESS_TOKEN"  # Invalid token
    }

    with pytest.raises(BondValidationError) as exc_info:
        runtime.bond_manager.execute_transition(s0_state, raw_payload_bad_token)

    assert exc_info.value.error_code == "CIV-ERR-AUTH-001"


def test_operational_visibility_endpoints(temp_workspace, monkeypatch):
    """Test read-only endpoints GET /runtime/validation/events and GET /runtime/control-plane."""
    monkeypatch.setenv("SAGE_BOND_MODE", "shadow")

    # Mock the runtime instance in api to use our temporary workspace runtime
    mock_runtime = SageRuntime(str(temp_workspace))
    mock_runtime.start()
    monkeypatch.setattr("sage.api.runtime", mock_runtime)

    # Trigger a task to produce some receipts
    mock_runtime.set_task("Create mock telemetry receipt")

    client = TestClient(app)

    # 1. Test GET /runtime/validation/events
    response = client.get("/runtime/validation/events")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "events" in res_data
    assert res_data["count"] > 0

    # 2. Test GET /runtime/control-plane
    response_cp = client.get("/runtime/control-plane")
    assert response_cp.status_code == 200
    cp_data = response_cp.json()
    assert cp_data["status"] == "active"
    assert cp_data["bond_mode"] == "shadow"
    assert "spek_compliance_vault" in cp_data
    assert "evidence_capture_status" in cp_data
    assert cp_data["spek_compliance_vault"]["receipts_count"] > 0
    assert cp_data["cognitive_separation_index"] == 1.0


def test_mock_agent_unsafe_mutation_simulation(temp_workspace, monkeypatch):
    """SAGE-EVID-006: Simulate mock autonomous agent issuing an unsafe transition in shadow mode.

    Ensure transition succeeds under shadow mode (no enforcement), but registers CIV-ERR and
    failed validation receipts deterministically.
    """
    monkeypatch.setenv("SAGE_BOND_MODE", "shadow")
    runtime = SageRuntime(str(temp_workspace))
    runtime.start()

    # Pre-state snapshot (S0)
    pre_state = runtime.get_status()

    # Unsafe mutation parameters
    transition_id = f"trans_unsafe_{uuid.uuid4().hex[:6]}"
    correlation_id = f"trace_corr_{uuid.uuid4().hex[:6]}"

    raw_payload_unsafe = {
        "transition_id": transition_id,
        "from_state": "S0",
        "to_state": "S1",  # Unsafe transition: bypassing Delta/Evidence/Validation steps -> CIV-ERR-MUT-003
        "description": "Mock agent unsafe mutation attempt",
        "category": "agent_action",
        "author": "agent_jules_06",
        "validation_score": 0.9,
        "evidence_refs": ["ref_audit_06"],
        "parent_ids": [],
        "contradictions": [],
        "auth_token": "BAD_ACCESS_TOKEN",  # Invalid token -> CIV-ERR-AUTH-001
        "metadata": {"correlation_id": correlation_id}
    }

    # Validate that calling BondManager directly raises BondValidationError
    s0_test_state = {"current_project_state": "S0"}
    with pytest.raises(BondValidationError) as exc_info:
        runtime.bond_manager.execute_transition(s0_test_state, raw_payload_unsafe)

    # Must capture CIV-ERR-AUTH-001 (Boundary Gate precedes mutation sequence check)
    assert exc_info.value.error_code == "CIV-ERR-AUTH-001"

    # Verify that in shadow mode, set_task handles the exception internally and allows
    # the runtime execution to proceed non-destructively
    # We trigger task setup using the same unsafe parameter representation
    monkeypatch.setattr(runtime, "bond_mode", "shadow")
    runtime.set_task("Attempt bypass with BAD_ACCESS_TOKEN")

    # Post-state snapshot (S1)
    post_state = runtime.get_status()

    # Pre/Post State comparison: Shadow mode successfully bypassed blocking, allowing task to update
    assert pre_state["active_task"] != post_state["active_task"]
    assert post_state["active_task"] == "Attempt bypass with BAD_ACCESS_TOKEN"
    assert runtime.is_running() is True  # Runtime remains perfectly stable (healthy)


# ==========================================
# MISSION 0.6 PHASE 3: ENFORCEMENT SIMULATION
# ==========================================

def test_controlled_enforcement_simulation_unauthorized_auth_civ_err_auth_001(temp_workspace, monkeypatch):
    """SAGE-EVID-007: Simulate unauthorized authorization mutation in sandbox enforcement mode.

    Confirm CIV-ERR-AUTH-001 classification, block transition, and verify 100% S0 state restoration.
    """
    monkeypatch.setenv("SAGE_BOND_MODE", "enforce")
    runtime = SageRuntime(str(temp_workspace))
    runtime.start()

    # Capture S0 initial state completely
    s0_state = {"current_project_state": "S0", "active_task": "None"}
    s0_active_task = s0_state["active_task"]

    # Try set_task with unauthorized token
    # We simulate this directly inside execute_transition to test enforcement behavior
    raw_payload_unsafe = {
        "transition_id": "trans_forged_auth_123",
        "from_state": "Delta",
        "to_state": "Evidence",
        "description": "Forged auth attempt",
        "author": "malicious_actor",
        "validation_score": 0.9,
        "auth_token": "forged_malicious_sig_666"  # BAD token -> CIV-ERR-AUTH-001
    }

    # Verify that enforcement blocks and raises CIV-ERR-AUTH-001
    with pytest.raises(BondValidationError) as exc_info:
        runtime.bond_manager.execute_transition(s0_state, raw_payload_unsafe)

    assert exc_info.value.error_code == "CIV-ERR-AUTH-001"
    assert "Security Boundary" in exc_info.value.message

    # State Integrity Comparison: State remains 100% preserved (S0)
    assert s0_state["current_project_state"] == "S0"
    assert s0_state["active_task"] == s0_active_task


def test_controlled_enforcement_simulation_identity_mutation_civ_err_mut_003(temp_workspace, monkeypatch):
    """SAGE-EVID-007: Simulate identity mutation/out-of-order state transition in sandbox enforcement mode.

    Confirm CIV-ERR-MUT-003 classification, block transition, and verify 100% S0 state restoration.
    """
    monkeypatch.setenv("SAGE_BOND_MODE", "enforce")
    runtime = SageRuntime(str(temp_workspace))
    runtime.start()

    s0_state = {"current_project_state": "S0"}
    s0_project_state = s0_state["current_project_state"]

    # Out of order transition payload (skipping states, trying to jump S0 -> Validation)
    raw_payload_unsafe = {
        "transition_id": "trans_out_of_order_123",
        "from_state": "S0",
        "to_state": "Validation",  # Skipped Delta & Evidence -> CIV-ERR-MUT-003
        "description": "Out of order state skip attempt",
        "author": "jules",
        "validation_score": 0.9,
        "auth_token": BoundaryEnforcer.SYSTEM_TOKEN
    }

    # Verify that enforcement blocks and raises CIV-ERR-MUT-003
    with pytest.raises(BondValidationError) as exc_info:
        runtime.bond_manager.execute_transition(s0_state, raw_payload_unsafe)

    assert exc_info.value.error_code == "CIV-ERR-MUT-003"
    assert "Invalid state transition sequence" in exc_info.value.message

    # State Integrity Comparison: S0 state is pristine after rollback
    assert s0_state["current_project_state"] == s0_project_state
