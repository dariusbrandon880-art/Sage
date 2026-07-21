"""Tests for SAGE Autonomous Continuity Runtime (ACR) snapshot persistence and restoration."""

import pytest
import tempfile
from pathlib import Path
from sage.models import MemoryObject, ConfidenceLevel, DecisionType
from sage.runtime import SageRuntime


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_state_before_equal_state_after(temp_workspace):
    """Assert State Before == State After (Session -> Snapshot -> Reload/Restore)."""
    # Initialize runtime A
    runtime = SageRuntime(str(temp_workspace))

    # Setup some state
    runtime.set_objective("Objective Alpha")
    runtime.set_task("Task 1")
    runtime.add_blocker("Blocker 1")

    # Add memory, decision, checkpoint
    obj = MemoryObject(
        object_type="rule",
        content={"key": "val"},
        tags=["test"],
        confidence=ConfidenceLevel.HYPOTHESIS
    )
    runtime.memory.store(obj)

    runtime.decisions.record_decision(
        decision_type=DecisionType.ARCHITECTURAL,
        description="Choose Postgres",
        rationale="Scalability"
    )

    checkpoint_id = runtime.checkpoint()

    # Store some custom ACR continuity bridge state
    runtime.acr.update_state_value("session_marker", "marker_abc")

    # Take workspace snapshot
    snapshot_id = runtime.create_workspace_snapshot()
    assert snapshot_id.startswith("snapshot_")

    # Modify state before restoration to ensure we notice the change
    runtime.set_task("Modified Task")
    runtime.add_blocker("Blocker 2")

    # Restore snapshot
    success = runtime.restore_workspace_snapshot(snapshot_id)
    assert success is True

    # Assert State Before == State After
    assert runtime.current_state.current_objective == "Objective Alpha"
    assert runtime.current_state.active_task == "Task 1"
    assert "Blocker 1" in runtime.current_state.blockers
    assert "Blocker 2" not in runtime.current_state.blockers

    # Assert memories restored
    mems = runtime.memory.list_all()
    assert len(mems) == 1
    assert mems[0].object_type == "rule"
    assert mems[0].content == {"key": "val"}

    # Assert decisions restored
    decs = runtime.decisions.list_all()
    assert len(decs) == 1
    assert decs[0].description == "Choose Postgres"

    # Assert checkpoints restored
    checkpoint_file = temp_workspace / f"{checkpoint_id}.json"
    assert checkpoint_file.exists()

    # Assert continuity bridge restored
    assert runtime.acr.get_state_value("session_marker") == "marker_abc"


def test_complete_memory_survival_across_reboots(temp_workspace):
    """Assert complete memory survival across hard runtime shutdown/reboot cycles."""
    # 1. Initialize Runtime Session 1
    runtime1 = SageRuntime(str(temp_workspace))
    runtime1.set_objective("Memory Survival Objective")

    # Add multiple memory objects
    obj1 = MemoryObject(
        object_type="schema",
        content={"table": "users"},
        tags=["database"],
        confidence=ConfidenceLevel.VALIDATED
    )
    obj2 = MemoryObject(
        object_type="policy",
        content={"role": "admin"},
        tags=["security"],
        confidence=ConfidenceLevel.HYPOTHESIS
    )
    runtime1.memory.store(obj1)
    runtime1.memory.store(obj2)

    # Add decision
    runtime1.decisions.record_decision(
        decision_type=DecisionType.STRATEGIC,
        description="Core Strategy",
        rationale="Market conditions"
    )

    # Create snapshot
    snapshot_id = runtime1.create_workspace_snapshot()

    # Stop runtime 1
    runtime1.stop()
    del runtime1

    # 2. Hard Reboot: Initialize completely fresh Runtime Session 2 pointing to a clean workspace
    # (But with the same global snapshot registry path '.sage/sage_state.json' preserved)
    runtime2 = SageRuntime(str(temp_workspace / "fresh_workspace"))
    assert len(runtime2.memory.list_all()) == 0
    assert len(runtime2.decisions.list_all()) == 0

    # Restore from the snapshot
    success = runtime2.restore_workspace_snapshot(snapshot_id)
    assert success is True

    # Assert memories survived and present
    mems = runtime2.memory.list_all()
    assert len(mems) == 2
    mem_types = [m.object_type for m in mems]
    assert "schema" in mem_types
    assert "policy" in mem_types

    # Assert decisions survived and present
    decs = runtime2.decisions.list_all()
    assert len(decs) == 1
    assert decs[0].description == "Core Strategy"


def test_cross_session_rehydration(temp_workspace):
    """Assert cross-session rehydration (Session B flawlessly resumes from Session A state)."""
    # Session A Runtime
    workspace_a = temp_workspace / "session_a"
    runtime_a = SageRuntime(str(workspace_a))

    runtime_a.set_objective("Mission Mars")
    runtime_a.set_task("Build rocket")

    # Save memory in Session A
    obj = MemoryObject(
        object_type="design",
        content={"fuel": "methane"},
        tags=["rocket"],
        confidence=ConfidenceLevel.HYPOTHESIS
    )
    runtime_a.memory.store(obj)

    # Snapshot Session A state
    snapshot_id = runtime_a.create_workspace_snapshot()

    # Session B Runtime (using complete separate workspace directory)
    workspace_b = temp_workspace / "session_b"
    runtime_b = SageRuntime(str(workspace_b))

    assert runtime_b.current_state.current_objective is None
    assert len(runtime_b.memory.list_all()) == 0

    # Rehydrate Session B from Session A's snapshot
    success = runtime_b.restore_workspace_snapshot(snapshot_id)
    assert success is True

    # Verify Session B is flawlessly rehydrated
    assert runtime_b.current_state.current_objective == "Mission Mars"
    assert runtime_b.current_state.active_task == "Build rocket"

    # Verify memories in Session B
    mems_b = runtime_b.memory.list_all()
    assert len(mems_b) == 1
    assert mems_b[0].object_type == "design"
    assert mems_b[0].content == {"fuel": "methane"}
