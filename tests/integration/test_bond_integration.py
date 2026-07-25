"""SAGE Mission 0.4 Phase 2 — Bond Invariant Integration Tests.

Verifies shadow validation success paths, shadow validation failure logging,
enforcement boundaries, state non-mutation invariants, and snapshot consistency.
"""

import os
import tempfile
from pathlib import Path
import pytest

from sage.runtime import SAGERuntime


@pytest.fixture
def clean_runtime():
    """Provides a fresh SAGERuntime instance with a clean workspace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runtime = SAGERuntime(tmpdir)
        runtime.start()
        yield runtime
        runtime.stop()


def test_shadow_validation_success_path(clean_runtime, monkeypatch):
    """Verify that a valid mutation under SAGE_BOND_MODE=shadow logs a success event."""
    monkeypatch.setenv("SAGE_BOND_MODE", "shadow")

    # We perform a valid mutation: set_objective on the runtime using the gate
    session_id = clean_runtime.authority_gate.request_mutation(clean_runtime, "set_objective", "Shadow Validation Objective")

    assert session_id is not None
    assert clean_runtime.current_state.current_objective == "Shadow Validation Objective"

    # Verify that a success event was captured in the validation events ledger
    events = clean_runtime.authority_gate.validation_events
    assert len(events) == 1
    assert events[0].event_type == "VALIDATION_PASS"
    assert events[0].transition_from == "S0"
    assert events[0].transition_to == "S1"


def test_shadow_validation_failure_logging(clean_runtime, monkeypatch):
    """Verify that an invalid mutation under SAGE_BOND_MODE=shadow is observed but not blocked."""
    monkeypatch.setenv("SAGE_BOND_MODE", "shadow")

    # Propose an invalid action: set_objective with semantic injection "delete the database"
    # In shadow mode, this should NOT raise a PermissionError and should execute successfully!
    result = clean_runtime.authority_gate.request_mutation(
        clean_runtime, "set_objective", "delete the database"
    )

    # Verify action executed successfully (did not raise an exception)
    assert result is not None
    assert clean_runtime.current_state.current_objective == "delete the database"

    # Verify that a failure event was correctly logged
    events = clean_runtime.authority_gate.validation_events
    assert len(events) == 1
    assert events[0].event_type == "VALIDATION_FAIL"
    assert events[0].error_code == "CIV-ERR-MUT-003"  # Identity/Mutation violation
    assert "Semantic" in events[0].error_message


def test_enforce_validation_rejection_no_mutation(clean_runtime, monkeypatch):
    """Verify that an invalid transition under SAGE_BOND_MODE=enforce blocks state mutation."""
    monkeypatch.setenv("SAGE_BOND_MODE", "enforce")

    # Set initial stable objective
    clean_runtime.set_objective("Pristine Pre-State S0")
    initial_objective = clean_runtime.current_state.current_objective

    # Propose set_objective with semantic injection "delete the database"
    # In enforce mode, this MUST raise PermissionError and not mutate state
    with pytest.raises(PermissionError):
        clean_runtime.authority_gate.request_mutation(
            clean_runtime, "set_objective", "delete the database"
        )

    # Verify state remains pristine (S0)
    assert clean_runtime.current_state.current_objective == initial_objective


def test_snapshot_creation_consistency_during_transitions(clean_runtime, monkeypatch):
    """Verify snapshot creation consistency and state restoration across transitions."""
    monkeypatch.setenv("SAGE_BOND_MODE", "shadow")

    # 1. State transition
    clean_runtime.authority_gate.request_mutation(clean_runtime, "set_objective", "Initial Target Objective")

    # 2. Checkpoint and Snapshot
    checkpoint_id = clean_runtime.checkpoint()
    snapshot_id = clean_runtime.create_workspace_snapshot()

    assert checkpoint_id is not None
    assert snapshot_id is not None

    # 3. Modify state further
    clean_runtime.authority_gate.request_mutation(clean_runtime, "set_objective", "Modified Post-Snapshot Objective")
    assert clean_runtime.current_state.current_objective == "Modified Post-Snapshot Objective"

    # 4. Restore and verify snapshot consistency
    success = clean_runtime.restore_workspace_snapshot(snapshot_id)
    assert success is True
    assert clean_runtime.current_state.current_objective == "Initial Target Objective"
