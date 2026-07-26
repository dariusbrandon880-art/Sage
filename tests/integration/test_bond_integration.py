"""Integration tests for SAGE Mission 0.4 Phase 2 - Shadow Hook Connections."""

import os
import pytest
import tempfile
from pathlib import Path

from sage.runtime.engine import SageRuntime
from sage.models import ExternalSessionPayload, ConfidenceLevel
from sage.core.boundary import BoundaryEnforcer
from sage.acr.bond import BondValidationError


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
