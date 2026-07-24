"""Unit and integration tests for C.11 state calibration, reconciliation, and security."""

import tempfile
from pathlib import Path

import pytest

from sage.acr.state_calibration import (
    ContinuitySecurity,
    IdentityDriftMonitor,
    StateCalibrationSync,
    StateReconciliation,
)
from sage.models import ConfidenceLevel, MemoryObject
from sage.runtime import SAGERuntime


@pytest.fixture
def clean_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_identity_drift_monitor():
    """Test identity drift evaluation logic."""
    monitor = IdentityDriftMonitor()
    assert monitor.evaluate_drift("Jules", "Jules") == 0.0
    assert monitor.evaluate_drift("ChatGPT", "Jules") == 0.5


def test_continuity_security_lineage_verification():
    """Test append-only lineage and promo signatures verification."""
    security = ContinuitySecurity()

    # Valid non-cyclic lineage chain
    valid_chain = ["session_1", "session_2", "session_3"]
    assert security.verify_lineage_integrity(valid_chain) is True

    # Invalid cyclic lineage chain
    cyclic_chain = ["session_1", "session_2", "session_1"]
    assert security.verify_lineage_integrity(cyclic_chain) is False

    # Invalid session prefix key
    bad_prefix = ["session_1", "external_session"]
    assert security.verify_lineage_integrity(bad_prefix) is False

    # Signature authorization
    assert security.authorize_promotion_signature("human_jules_sig_123") is True
    assert security.authorize_promotion_signature("invalid_sig") is False


def test_state_calibration_and_reconciliation_flow(clean_workspace):
    """Test proactive calibration and non-destructive reconciliation of drift."""
    runtime = SAGERuntime(str(clean_workspace))
    runtime.start()

    # Set up some initial checkpointed state representing historical reference
    checkpoint_id = f"checkpoint_{uuid_mock()}"
    runtime.checkpoint_manager.create_checkpoint(
        current_sage_state={"current_objective": "Original Objective", "active_task": "Original Task"},
        active_goals=["Original Objective", "Original Task"],
        recent_decisions=[],
        validation_status={"is_valid": True},
        checkpoint_id=checkpoint_id,
    )

    # Simulate drift by clearing the active runtime state
    runtime.current_state.current_objective = None
    runtime.current_state.active_task = None
    runtime._save_state()

    # Create StateCalibrationSync and perform sync
    calibration_sync = StateCalibrationSync(runtime)
    results = calibration_sync.calibrate_and_reconcile()

    # Assert that objective and task were non-destructively recovered from checkpoint
    assert results["status"] == "synchronized"
    assert "rehydrate_objective:Original Objective" in results["reconciliation_actions"]
    assert "rehydrate_task:Original Task" in results["reconciliation_actions"]

    assert runtime.current_state.current_objective == "Original Objective"
    assert runtime.current_state.active_task == "Original Task"

    runtime.stop()


def uuid_mock():
    import uuid
    return uuid.uuid4().hex[:8]
