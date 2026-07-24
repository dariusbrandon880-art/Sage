"""Tests for newly implemented SAGE systems: models, decisions, validation, and cli."""

import tempfile
from pathlib import Path

import pytest

from sage.archive import Archive
from sage.decision import DecisionTracker
from sage.memory import Memory
from sage.models import ConfidenceLevel, DecisionType, MemoryObject
from sage.validation import ValidationSystem


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_memory_and_models(temp_dir):
    """Test Memory database and MemoryObject models."""
    memory_store = Memory(str(temp_dir / "memory"))

    obj = MemoryObject(
        object_type="rule",
        content={"key": "val"},
        tags=["test", "unit"],
        confidence=ConfidenceLevel.HYPOTHESIS,
    )

    obj_id = memory_store.store(obj)
    assert obj_id == obj.id

    retrieved = memory_store.retrieve(obj_id)
    assert retrieved is not None
    assert retrieved.object_type == "rule"
    assert retrieved.content == {"key": "val"}
    assert retrieved.confidence == ConfidenceLevel.HYPOTHESIS

    all_objs = memory_store.list_all()
    assert len(all_objs) == 1

    tagged_objs = memory_store.search_by_tag("unit")
    assert len(tagged_objs) == 1
    assert tagged_objs[0].id == obj_id

    type_objs = memory_store.search_by_type("rule")
    assert len(type_objs) == 1


def test_decision_tracker(temp_dir):
    """Test DecisionTracker and DecisionEntry models."""
    tracker = DecisionTracker(str(temp_dir / "decisions"))

    decision_id = tracker.record_decision(
        decision_type=DecisionType.ARCHITECTURAL,
        description="Migrate memory models",
        rationale="Improve modularity",
        evidence=["benchmarks"],
    )

    retrieved = tracker.retrieve_decision(decision_id)
    assert retrieved is not None
    assert retrieved.decision_type == DecisionType.ARCHITECTURAL
    assert retrieved.description == "Migrate memory models"
    assert retrieved.rationale == "Improve modularity"
    assert retrieved.evidence == ["benchmarks"]

    all_decisions = tracker.list_all()
    assert len(all_decisions) == 1


def test_validation_and_archive_promotion(temp_dir):
    """Test ValidationSystem and promotion workflow."""
    memory_store = Memory(str(temp_dir / "memory"))
    archive_store = Archive(str(temp_dir / "archive"))

    validation = ValidationSystem(memory_store, archive_store)

    # Store dynamic hypothesis
    obj = MemoryObject(
        object_type="schema",
        content={"fields": ["id", "name"]},
        tags=["database"],
        confidence=ConfidenceLevel.HYPOTHESIS,
    )
    memory_store.store(obj)

    # Validate
    is_valid, failed = validation.validate_memory(obj.id)
    assert is_valid is True
    assert len(failed) == 0

    # Promote to validated
    success, msg = validation.promote_to_validated(obj.id)
    assert success is True

    reloaded = memory_store.retrieve(obj.id)
    assert reloaded.confidence == ConfidenceLevel.VALIDATED

    # Promote to archive
    success, archive_id = validation.promote_to_archive(
        obj.id, "Validated Database Schema", ["core"]
    )
    assert success is True
    assert archive_id.startswith("archive_")

    # Check original object changed to ARCHIVED
    reloaded_after_archive = memory_store.retrieve(obj.id)
    assert reloaded_after_archive.confidence == ConfidenceLevel.ARCHIVED

    # Verify inside archive
    archive_entry = archive_store.retrieve_entry(archive_id)
    assert archive_entry is not None
    assert archive_entry.title == "Validated Database Schema"
    assert "core" in archive_entry.tags
    assert "database" in archive_entry.tags


def test_handoff_and_restoration(temp_dir):
    """Test SAGE Runtime handoff generation and session restoration."""
    from sage.runtime import SageRuntime

    runtime = SageRuntime(str(temp_dir))

    # Setup some initial state
    runtime.set_objective("Achieve world class automated AI development")
    runtime.set_task("Implement handoff feature")
    runtime.add_blocker("Lack of handoff test coverage")

    # Store memory objects
    obj = MemoryObject(
        object_type="schema",
        content={"fields": ["id"]},
        tags=["test_tag"],
        confidence=ConfidenceLevel.VALIDATED,
    )
    runtime.memory.store(obj)

    # Generate handoff
    handoff_file_path = runtime.generate_handoff()
    assert Path(handoff_file_path).exists()

    # Create another fresh runtime instance representing a new session
    new_runtime = SageRuntime(str(temp_dir / "new_workspace"))
    assert new_runtime.current_state.current_objective is None

    # Restore state from handoff
    success = new_runtime.restore_session(handoff_file_path)
    assert success is True

    # Assert state restored correctly
    assert (
        new_runtime.current_state.current_objective
        == "Achieve world class automated AI development"
    )
    assert new_runtime.current_state.active_task == "Implement handoff feature"
    assert "Lack of handoff test coverage" in new_runtime.current_state.blockers


def test_sage_rt_kl_002_enforcement(temp_dir):
    """Test SAGE-RT-KL-002 contract enforcement on rule candidate promotion."""
    memory_store = Memory(str(temp_dir / "memory_rule"))
    archive_store = Archive(str(temp_dir / "archive_rule"))
    validation = ValidationSystem(memory_store, archive_store)

    # 1. Store a rule candidate WITHOUT an authorized signature
    unsigned_rule = MemoryObject(
        object_type="rule_candidate",
        content={"pattern": "If X then Y"},
        tags=["rule"],
        confidence=ConfidenceLevel.HYPOTHESIS,
    )
    memory_store.store(unsigned_rule)

    # Validate should fail due to SAGE-RT-KL-002 contract violation
    is_valid, failed = validation.validate_memory(unsigned_rule.id)
    assert is_valid is False
    assert any("SAGE-RT-KL-002" in f for f in failed)

    # Promotion should fail
    success, msg = validation.promote_to_validated(unsigned_rule.id)
    assert success is False
    assert "SAGE-RT-KL-002" in msg

    # Promotion to archive should fail
    success, msg = validation.promote_to_archive(unsigned_rule.id, "Unsigned Rule")
    assert success is False
    assert "SAGE-RT-KL-002" in msg

    # 2. Store a rule candidate WITH an authorized signature
    signed_rule = MemoryObject(
        object_type="rule_candidate",
        content={"pattern": "If A then B", "authorized_signature": "human_jules_sig_123"},
        tags=["rule"],
        confidence=ConfidenceLevel.HYPOTHESIS,
    )
    memory_store.store(signed_rule)

    # Validate should pass
    is_valid, failed = validation.validate_memory(signed_rule.id)
    assert is_valid is True
    assert len(failed) == 0

    # Promotion to validated should succeed
    success, msg = validation.promote_to_validated(signed_rule.id)
    assert success is True

    # Promotion to archive should succeed
    success, archive_id = validation.promote_to_archive(signed_rule.id, "Signed SAGE Rule")
    assert success is True
    assert archive_id.startswith("archive_")
