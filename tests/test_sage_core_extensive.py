"""Comprehensive tests for SAGE core systems including runtime, models, validation, and decision tracking."""

import os
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from sage.models import (
    ConfidenceLevel,
    DecisionType,
    KnowledgeState,
    MemoryObject,
    ArchiveEntry,
    RuntimeState,
    DecisionEntry,
)
from sage.validation import ValidationSystem
from sage.decision import DecisionTracker
from sage.runtime import SageRuntime


class TestSageCoreExtensive:
    """Extensive tests for SAGE validation, decision, model, and runtime orchestration systems."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_models_initialization(self):
        """Test that all enums and Pydantic models initialize and default correctly."""
        # ConfidenceLevel and DecisionType Enums
        assert ConfidenceLevel.HYPOTHESIS == "hypothesis"
        assert DecisionType.ARCHITECTURE == "architecture"
        assert KnowledgeState.ARCHIVED == "archived"

        # MemoryObject Model
        mem_obj = MemoryObject(object_type="design_doc", content={"title": "test"})
        assert mem_obj.id is not None
        assert mem_obj.confidence == ConfidenceLevel.HYPOTHESIS
        assert mem_obj.content == {"title": "test"}
        assert len(mem_obj.tags) == 0

        # ArchiveEntry Model
        archive_entry = ArchiveEntry(title="Archived Knowledge", content={"key": "val"})
        assert archive_entry.id is not None
        assert archive_entry.knowledge_state == KnowledgeState.ARCHIVED
        assert archive_entry.validation_timestamp is None

        # RuntimeState Model
        r_state = RuntimeState()
        assert r_state.current_objective is None
        assert r_state.active_task is None
        assert len(r_state.blockers) == 0
        assert len(r_state.dependencies) == 0

        # DecisionEntry Model
        decision_entry = DecisionEntry(
            decision_type=DecisionType.ARCHITECTURE,
            description="Adopt FastAPI",
            rationale="High performance and async capabilities",
        )
        assert decision_entry.id is not None
        assert decision_entry.decision_type == DecisionType.ARCHITECTURE
        assert len(decision_entry.evidence) == 0

    def test_decision_tracker(self, temp_workspace):
        """Test DecisionTracker recording, persistence, retrieval, and state exporting."""
        tracker = DecisionTracker(storage_path=str(temp_workspace / "decisions"))

        # Record a decision
        decision_id = tracker.record_decision(
            decision_type=DecisionType.DESIGN,
            description="Use file-based JSON persistence",
            rationale="Maintains extreme readability and compatibility",
            evidence=["README.md", "pyproject.toml"],
        )
        assert decision_id is not None

        # Retrieve the decision
        retrieved = tracker.retrieve_decision(decision_id)
        assert retrieved is not None
        assert retrieved.decision_type == DecisionType.DESIGN
        assert retrieved.description == "Use file-based JSON persistence"
        assert retrieved.rationale == "Maintains extreme readability and compatibility"
        assert retrieved.evidence == ["README.md", "pyproject.toml"]

        # List all decisions
        all_decisions = tracker.list_all()
        assert len(all_decisions) == 1
        assert all_decisions[0].id == decision_id

        # Verify disk persistence across instance reconstruction
        new_tracker = DecisionTracker(storage_path=str(temp_workspace / "decisions"))
        retrieved_new = new_tracker.retrieve_decision(decision_id)
        assert retrieved_new is not None
        assert retrieved_new.id == decision_id

        # Export state
        exported = tracker.export_state()
        assert exported["decision_count"] == 1
        assert len(exported["decisions"]) == 1
        assert exported["decisions"][0]["id"] == decision_id

    def test_validation_system(self, temp_workspace):
        """Test ValidationSystem rule validation and promotion workflow."""
        runtime = SageRuntime(workspace_path=str(temp_workspace))
        validation = ValidationSystem(runtime.memory, runtime.archive)

        # Create an invalid memory object (missing tags, empty content/type)
        invalid_obj = MemoryObject(object_type="", content={})
        runtime.memory.store(invalid_obj)

        is_valid, failed_rules = validation.validate_memory(invalid_obj.id)
        assert not is_valid
        assert "Object type must not be empty" in failed_rules
        assert "Content must not be empty" in failed_rules
        assert "Memory object must have at least one tag" in failed_rules

        # Create a valid memory object
        valid_obj = MemoryObject(
            object_type="specification",
            content={"architecture": "SAGE-ACR"},
            tags=["core", "spec"],
        )
        runtime.memory.store(valid_obj)

        is_valid, failed_rules = validation.validate_memory(valid_obj.id)
        assert is_valid
        assert len(failed_rules) == 0

        # Try promoting invalid object (should fail)
        success, msg = validation.promote_to_validated(invalid_obj.id)
        assert not success
        assert "Validation failed" in msg

        # Promote valid object
        success, msg = validation.promote_to_validated(valid_obj.id)
        assert success
        assert msg == "Memory object successfully promoted to VALIDATED"

        # Verify memory object confidence level updated
        updated_obj = runtime.memory.retrieve(valid_obj.id)
        assert updated_obj.confidence == ConfidenceLevel.VALIDATED

        # Try archiving an unvalidated object
        success, res = validation.promote_to_archive(invalid_obj.id, "Invalid Archive")
        assert not success
        assert "validated before" in res

        # Archive validated object
        success, archive_id = validation.promote_to_archive(valid_obj.id, "Master Specification")
        assert success
        assert archive_id is not None

        # Verify master archive has the entry
        archive_entry = runtime.archive.retrieve_entry(archive_id)
        assert archive_entry is not None
        assert archive_entry.title == "Master Specification"
        assert archive_entry.content == {"architecture": "SAGE-ACR"}
        assert set(archive_entry.tags) == {"core", "spec"}

        # Verify original memory object's confidence is now ARCHIVED
        archived_mem_obj = runtime.memory.retrieve(valid_obj.id)
        assert archived_mem_obj.confidence == ConfidenceLevel.ARCHIVED

    def test_runtime_orchestration(self, temp_workspace):
        """Test SageRuntime settings, objectives, blockers, status, and state persistence."""
        runtime = SageRuntime(workspace_path=str(temp_workspace))
        assert not runtime.is_running()
        runtime.start()
        assert runtime.is_running()

        # Set objective and task
        session_id_1 = runtime.set_objective("Complete Autonomous Continuity Layer")
        session_id_2 = runtime.set_task("Implement engine logic and state save-restore")
        assert session_id_1 == session_id_2
        assert runtime.current_state.current_objective == "Complete Autonomous Continuity Layer"
        assert runtime.current_state.active_task == "Implement engine logic and state save-restore"

        # Checkpoint, blocker, status
        runtime.add_blocker("Missing dependency installation")
        status = runtime.get_status()
        assert status["status"] == "online"
        assert "Missing dependency installation" in status["blockers"]

        # Resolve blocker
        runtime.resolve_blocker("Missing dependency installation")
        assert "Missing dependency installation" not in runtime.current_state.blockers

        # Create checkpoint
        checkpoint_id = runtime.checkpoint()
        assert checkpoint_id is not None

        # Verify state persistence across runtime instance reload
        new_runtime = SageRuntime(workspace_path=str(temp_workspace))
        assert new_runtime.current_state.current_objective == "Complete Autonomous Continuity Layer"
        assert new_runtime.current_state.active_task == "Implement engine logic and state save-restore"
        assert len(new_runtime.current_state.blockers) == 0

        # Export all states
        export_data = runtime.export_all()
        assert "state" in export_data
        assert "memory" in export_data
        assert "archive" in export_data
        assert "decisions" in export_data
        assert export_data["state"]["current_objective"] == "Complete Autonomous Continuity Layer"
