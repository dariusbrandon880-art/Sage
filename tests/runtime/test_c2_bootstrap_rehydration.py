"""Adversarial unit tests for C2Bootstrap rehydration integrity."""

from pathlib import Path
import tempfile

from sage.acr.bridge import ACRBridge
from sage.acr.session.session_state import SessionStateManager
from sage.runtime.c2_bootstrap import C2Bootstrap
from sage.runtime.engine import SageRuntime


def test_surfaces_present_without_rehydrated_state_fails_closed():
    """Verify that available surfaces alone do NOT imply rehydrated state or execution readiness."""
    bootstrap = C2Bootstrap(available_surfaces=("acr", "memory", "archive"))
    result = bootstrap.boot()

    assert result.rehydrated is False
    assert result.direct_execution_available is False
    assert result.execution_surface_checked is True
    assert result.blocker is not None
    assert "not verified" in result.blocker or "no ACRBridge" in result.blocker


def test_surfaces_present_with_rehydrated_acr_bridge_passes():
    """Verify that a valid ACRBridge with saved state or session lineage rehydrates successfully."""
    acr_bridge = ACRBridge(use_persistence=False)
    acr_bridge.add_session_link("session_test_001")

    bootstrap = C2Bootstrap(
        available_surfaces=("acr", "memory"),
        acr_bridge=acr_bridge,
    )
    result = bootstrap.boot()

    assert result.rehydrated is True
    assert result.direct_execution_available is True
    assert result.blocker is None


def test_surfaces_present_with_rehydrated_session_manager_passes(tmp_path: Path):
    """Verify that SessionStateManager with a persisted session rehydrates successfully."""
    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    session_mgr.create_session(session_id="sess_valid_001", active_objectives=["obj_rehydration"])

    bootstrap = C2Bootstrap(
        available_surfaces=("acr", "session"),
        session_manager=session_mgr,
    )
    result = bootstrap.boot()

    assert result.rehydrated is True
    assert result.direct_execution_available is True
    assert result.blocker is None


def test_missing_required_session_id_fails_closed(tmp_path: Path):
    """Verify that requesting a specific session ID that is missing fails closed."""
    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    session_mgr.create_session(session_id="sess_other_001")

    bootstrap = C2Bootstrap(
        available_surfaces=("acr", "session"),
        session_manager=session_mgr,
        required_session_id="sess_non_existent",
    )
    result = bootstrap.boot()

    assert result.rehydrated is False
    assert result.direct_execution_available is False
    assert result.blocker is not None
    assert "sess_non_existent" in result.blocker


def test_empty_surfaces_fails_closed():
    """Verify that empty execution surfaces fail closed regardless of state."""
    bootstrap = C2Bootstrap(available_surfaces=())
    result = bootstrap.boot()

    assert result.rehydrated is False
    assert result.direct_execution_available is False
    assert result.blocker == "No execution surface available"


def test_sage_runtime_c2_status_integration(tmp_path: Path):
    """Verify SageRuntime correctly integrates C2Bootstrap rehydration checks."""
    runtime = SageRuntime(workspace_path=str(tmp_path / "runtime_workspace"))
    summary = runtime.get_active_capability_summary()

    assert "c2_rehydrated" in summary
    assert isinstance(summary["c2_rehydrated"], bool)
