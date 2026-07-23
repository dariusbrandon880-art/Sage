"""Tests for SAGE Continuity Intelligence Layer expansion."""

import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

from sage.acr.session import (
    SessionState,
    SessionStateManager,
    ContextTracker,
    CheckpointManager,
)
from sage.runtime import SageRuntime
from sage.models import ExternalSessionPayload


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests and clean up afterwards."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_session_state_creation_and_updates():
    """Test creating and updating a SessionState model."""
    state = SessionState(session_id="test_sess_1")
    assert state.session_id == "test_sess_1"
    assert isinstance(state.timestamp, datetime)

    state.add_objective("Implement Continuity Intelligence")
    assert "Implement Continuity Intelligence" in state.active_objectives

    state.add_pending_action("Write unit tests")
    assert "Write unit tests" in state.pending_actions

    state.add_completed_action("Write unit tests")
    assert "Write unit tests" in state.completed_actions
    assert "Write unit tests" not in state.pending_actions

    state.add_decision("dec_001")
    assert "dec_001" in state.important_decisions

    state.add_archive_reference("archive_mem_002")
    assert "archive_mem_002" in state.related_archive_references


def test_session_state_manager(temp_dir):
    """Test saving, retrieving, and listing session states using SessionStateManager."""
    mgr = SessionStateManager(storage_path=temp_dir)
    state = mgr.create_session(
        session_id="sess_123",
        active_objectives=["Sprint 3 Planning"],
        metadata={"author": "Jules"},
    )

    assert state.session_id == "sess_123"
    assert state.active_objectives == ["Sprint 3 Planning"]
    assert state.metadata == {"author": "Jules"}

    # Retrieve from memory / cache
    retrieved = mgr.retrieve_session("sess_123")
    assert retrieved is not None
    assert retrieved.session_id == "sess_123"

    # Instantiate new manager to test disk retrieval
    mgr_new = SessionStateManager(storage_path=temp_dir)
    retrieved_disk = mgr_new.retrieve_session("sess_123")
    assert retrieved_disk is not None
    assert retrieved_disk.session_id == "sess_123"
    assert retrieved_disk.active_objectives == ["Sprint 3 Planning"]

    # List all
    all_sessions = mgr_new.list_all()
    assert len(all_sessions) == 1
    assert all_sessions[0].session_id == "sess_123"


def test_context_tracker_and_history_traversal(temp_dir):
    """Test ContextTracker milestone updates, unresolved items, and previous context traversal."""
    sess_mgr = SessionStateManager(storage_path=str(Path(temp_dir) / "sessions"))
    tracker = ContextTracker(storage_path=str(Path(temp_dir) / "context"), session_manager=sess_mgr)

    # Initial context check
    ctx = tracker.get_current_context()
    assert ctx.current_project_state == "active"
    assert ctx.active_milestone is None

    # Update milestone (record transition)
    tracker.set_milestone("v1.1.0-alpha", reason="Kicking off Phase 3")
    ctx = tracker.get_current_context()
    assert ctx.active_milestone == "v1.1.0-alpha"
    assert len(ctx.important_context_transitions) == 1
    assert ctx.important_context_transitions[0].from_state == "milestone:None"
    assert ctx.important_context_transitions[0].to_state == "milestone:v1.1.0-alpha"

    # Unresolved items and changes
    tracker.add_unresolved_item("Fix auth boundary bypass issue")
    assert "Fix auth boundary bypass issue" in ctx.unresolved_items

    tracker.resolve_item("Fix auth boundary bypass issue")
    assert "Fix auth boundary bypass issue" not in ctx.unresolved_items
    assert any("Resolved: Fix auth boundary bypass" in change for change in ctx.recent_changes)

    tracker.add_recent_change("Implemented secure webhooks")
    assert "Implemented secure webhooks" in ctx.recent_changes

    # Set up some sessions to test lineage traversal ("What was happening before this session?")
    sess1 = sess_mgr.create_session(session_id="session_one")
    sess1.add_objective("Set up repository structure")
    sess1.add_completed_action("Created docs directory")
    sess1.add_pending_action("Write code readiness script")
    sess1.add_decision("dec_001")
    sess1.add_archive_reference("archive_001")
    sess_mgr.save_session(sess1)

    sess2 = sess_mgr.create_session(session_id="session_two")
    sess2.add_objective("Publish documentation")
    sess_mgr.save_session(sess2)

    # Traverse lineage
    prev_context = tracker.get_previous_context(lineage=["session_one"])
    assert prev_context is not None
    assert prev_context["session_id"] == "session_one"
    assert prev_context["last_objectives"] == ["Set up repository structure"]
    assert prev_context["last_completed_actions"] == ["Created docs directory"]
    assert prev_context["last_pending_actions"] == ["Write code readiness script"]
    assert prev_context["last_important_decisions"] == ["dec_001"]
    assert prev_context["last_archive_references"] == ["archive_001"]


def test_checkpoint_manager_and_git_reference(temp_dir):
    """Test CheckpointManager saves and retrieves checkpoints with Git repository references."""
    chk_mgr = CheckpointManager(storage_path=temp_dir)

    checkpoint = chk_mgr.create_checkpoint(
        current_sage_state={"current_objective": "Build platform core"},
        active_goals=["Build platform core"],
        recent_decisions=["dec_999"],
        validation_status={"is_valid": True},
        metadata={"sprint": 3},
    )

    assert checkpoint.id.startswith("chk_")
    assert checkpoint.active_goals == ["Build platform core"]
    assert checkpoint.recent_decisions == ["dec_999"]
    assert checkpoint.validation_status == {"is_valid": True}
    assert checkpoint.metadata == {"sprint": 3}
    assert "branch" in checkpoint.repository_state_reference

    # Retrieve checkpoint
    retrieved = chk_mgr.retrieve_checkpoint(checkpoint.id)
    assert retrieved is not None
    assert retrieved.id == checkpoint.id
    assert retrieved.active_goals == ["Build platform core"]


def test_sageruntime_continuity_intelligence_integration(temp_dir):
    """E2E Test verifying SageRuntime initializes, ingests payload and snapshot/restores continuity elements."""
    runtime = SageRuntime(workspace_path=temp_dir)

    # 1. Verification of initialization
    assert runtime.session_manager is not None
    assert runtime.context_tracker is not None
    assert runtime.checkpoint_manager is not None

    # 2. Set objective and task updates
    session_id = runtime.set_objective("Launch Continuity Intelligence Layer")
    assert session_id is not None

    sess_state = runtime.session_manager.retrieve_session(session_id)
    assert sess_state is not None
    assert "Launch Continuity Intelligence Layer" in sess_state.active_objectives

    runtime.set_task("Write comprehensive tests")
    assert "task:Write comprehensive tests" in sess_state.pending_actions

    # 3. Payload ingestion
    payload = ExternalSessionPayload(
        session_id="ingested_sess_01",
        objective="Verify system capabilities",
        task="Test checkpointing",
        memories=[
            {
                "id": "mem_001",
                "object_type": "technical",
                "content": {"archive": True, "title": "Memory Content"},
                "tags": ["intelligence"],
                "confidence": "validated",
            }
        ],
        decisions=[
            {
                "id": "dec_001",
                "decision_type": "technical",
                "description": "Choose local files for sessions persistence",
                "rationale": "High speed and local control",
                "evidence": ["mem_001"],
            }
        ],
    )

    result = runtime.ingest_session_payload(payload)
    assert result["status"] == "success"

    # Confirm SessionState was populated during Ingestion
    ing_sess = runtime.session_manager.retrieve_session("ingested_sess_01")
    assert ing_sess is not None
    assert "Verify system capabilities" in ing_sess.active_objectives
    assert (
        "task:Test checkpointing" in ing_sess.completed_actions
        or "task:Test checkpointing" in ing_sess.pending_actions
    )
    assert "dec_001" in ing_sess.important_decisions
    assert "archive_mem_001" in ing_sess.related_archive_references

    # Confirm Checkpoint was created
    chks = runtime.checkpoint_manager.list_all()
    assert len(chks) > 0

    # 4. Generate handoff & restore
    handoff_file = runtime.generate_handoff()
    assert Path(handoff_file).exists()

    # Create a fresh runtime instance and restore
    runtime_fresh = SageRuntime(workspace_path=temp_dir)
    success = runtime_fresh.restore_session(handoff_file)
    assert success is True

    # Confirm rehydrated session and checkpoints
    fresh_sess = runtime_fresh.session_manager.retrieve_session("ingested_sess_01")
    assert fresh_sess is not None
    assert "Verify system capabilities" in fresh_sess.active_objectives


def test_workspace_snapshot_and_restore_continuity_intelligence(temp_dir):
    """Test that workspace snapshots serializes and completely rehydrates all session layers."""
    runtime = SageRuntime(workspace_path=temp_dir)

    # Setup some state
    runtime.set_objective("Global Intelligence")
    runtime.set_task("Verify snapshots")
    runtime.context_tracker.set_milestone("m_snap_1")
    runtime.context_tracker.add_unresolved_item("item_1")

    # Create workspace snapshot
    snap_id = runtime.create_workspace_snapshot()
    assert snap_id is not None

    # Modify state to simulate changes
    runtime.set_objective("New Goal")
    runtime.context_tracker.set_milestone("m_snap_2")
    runtime.context_tracker.add_unresolved_item("item_2")

    # Restore snapshot
    success = runtime.restore_workspace_snapshot(snap_id)
    assert success is True

    # Verify that original objectives, milestones, and unresolved items are restored
    assert runtime.current_state.current_objective == "Global Intelligence"
    assert runtime.context_tracker.get_current_context().active_milestone == "m_snap_1"
    assert "item_1" in runtime.context_tracker.get_current_context().unresolved_items
    assert "item_2" not in runtime.context_tracker.get_current_context().unresolved_items
