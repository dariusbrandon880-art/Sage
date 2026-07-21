"""Tests for SAGE continuity persistence, serialization, snapshots, and cross-session restoration."""

import pytest
import tempfile
import json
from pathlib import Path
from sage.runtime import SageRuntime
from sage.models import MemoryObject, ConfidenceLevel


def test_runtime_state_serialization_and_persistence():
    """Test that runtime state is properly serialized and survives shutdown/restart (state persistence)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)

        # 1. Initialize runtime, modify state, and persist
        runtime = SageRuntime(str(workspace_path))
        runtime.set_objective("Design high-fidelity continuity engine")
        runtime.set_task("Verify disk serialization")
        runtime.add_blocker("Awaiting automated IO validation")

        # Verify state.json is created on disk
        state_file = workspace_path / "state.json"
        assert state_file.exists()

        with open(state_file, "r") as f:
            state_data = json.load(f)
        assert state_data["current_objective"] == "Design high-fidelity continuity engine"
        assert state_data["active_task"] == "Verify disk serialization"
        assert "Awaiting automated IO validation" in state_data["blockers"]

        # 2. Simulate shutdown (deleting instance) and restart (reloading from same workspace)
        del runtime

        new_runtime = SageRuntime(str(workspace_path))
        assert new_runtime.current_state.current_objective == "Design high-fidelity continuity engine"
        assert new_runtime.current_state.active_task == "Verify disk serialization"
        assert "Awaiting automated IO validation" in new_runtime.current_state.blockers


def test_snapshot_creation_and_restoration():
    """Test that workspace snapshots can be created, listed, and fully restored."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)

        runtime = SageRuntime(str(workspace_path))
        runtime.set_objective("Validate snapshot snapshots")

        # Create a snapshot
        snapshot_id = runtime.checkpoint()
        assert snapshot_id.startswith("checkpoint_")

        snapshot_file = workspace_path / f"{snapshot_id}.json"
        assert snapshot_file.exists()

        # Load snapshot data and verify context
        with open(snapshot_file, "r") as f:
            snapshot_data = json.load(f)
        assert snapshot_data["state"]["current_objective"] == "Validate snapshot snapshots"

        # Create a second runtime instance representing an entirely clean environment
        with tempfile.TemporaryDirectory() as secondary_dir:
            fresh_runtime = SageRuntime(str(secondary_dir))
            assert fresh_runtime.current_state.current_objective is None

            # Restore state from snapshot_file path
            success = fresh_runtime.restore_session(str(snapshot_file))
            assert success is True
            assert fresh_runtime.current_state.current_objective == "Validate snapshot snapshots"


def test_handoff_creation_and_recovery():
    """Test that handoff files preserve all lineage metadata and enable clean recovery across environments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)

        runtime = SageRuntime(str(workspace_path))
        runtime.set_objective("Generate handoff payload")
        runtime.set_task("Verify cross-session lineage tracking")

        # Add some mock memory entries to index
        obj = MemoryObject(
            object_type="design_note",
            content={"architecture": "SAGE v1"},
            tags=["continuity"],
            confidence=ConfidenceLevel.VALIDATED
        )
        runtime.memory.store(obj)

        # Generate a handoff payload
        handoff_path = runtime.generate_handoff()
        assert Path(handoff_path).exists()

        with open(handoff_path, "r") as f:
            handoff_data = json.load(f)
        assert handoff_data["state"]["current_objective"] == "Generate handoff payload"
        assert handoff_data["metadata"]["memory_count"] == 1

        # Recovery/Restoration in another workspace
        with tempfile.TemporaryDirectory() as target_dir:
            recovered_runtime = SageRuntime(str(target_dir))
            assert recovered_runtime.current_state.current_objective is None

            success = recovered_runtime.restore_session(handoff_path)
            assert success is True
            assert recovered_runtime.current_state.current_objective == "Generate handoff payload"
            assert recovered_runtime.current_state.active_task == "Verify cross-session lineage tracking"
