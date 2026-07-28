"""SAGE-ACT Milestone 2A Lineage Mapping Validation Test Suite."""

import pytest
import ast
from pathlib import Path

from sage.experimental.act import SessionStateTaskLinker
from sage.acr.session.session_state import SessionState
from sage.agents.models import AgentTask, AgentTaskState


def test_session_state_task_linker_valid_dict():
    """Verify lineage validation with valid dictionary structures."""
    linker = SessionStateTaskLinker()
    session = {
        "session_id": "session_f6b3d4e5",
        "active_objectives": ["obj_001_deploy", "obj_002_test"],
    }
    tasks = [
        {"task_id": "task_001", "objective_id": "obj_001_deploy"},
        {"task_id": "task_002", "objective_id": "obj_002_test"},
    ]

    result = linker.validate_session_task_lineage(session, tasks)

    assert result["session_id"] == "session_f6b3d4e5"
    assert result["mapped_tasks"] == ["task_001", "task_002"]
    assert result["validation_status"] == "LINEAGE_VALIDATED"
    assert result["read_only_assertion"] is True
    assert "validated_at" in result


def test_session_state_task_linker_valid_models():
    """Verify lineage validation using actual SessionState and AgentTask Pydantic models."""
    linker = SessionStateTaskLinker()

    session = SessionState(
        session_id="session_f6b3d4e5",
        active_objectives=["obj_001_deploy", "obj_002_test"],
    )
    tasks = [
        AgentTask(
            task_id="task_001",
            objective_id="obj_001_deploy",
            title="Deploy SAGE",
            state=AgentTaskState.PENDING,
        ),
        AgentTask(
            task_id="task_002",
            objective_id="obj_002_test",
            title="Test SAGE",
            state=AgentTaskState.PENDING,
        ),
    ]

    result = linker.validate_session_task_lineage(session, tasks)

    assert result["session_id"] == "session_f6b3d4e5"
    assert result["mapped_tasks"] == ["task_001", "task_002"]
    assert result["validation_status"] == "LINEAGE_VALIDATED"
    assert result["read_only_assertion"] is True


def test_session_state_task_linker_missing_session_id():
    """Verify error raised when session_id is missing from session state."""
    linker = SessionStateTaskLinker()
    session = {
        "active_objectives": ["obj_001"],
    }
    tasks = [
        {"task_id": "task_001", "objective_id": "obj_001"},
    ]

    with pytest.raises(ValueError, match="Missing 'session_id' in session state"):
        linker.validate_session_task_lineage(session, tasks)


def test_session_state_task_linker_invalid_session_id_prefix():
    """Verify rejection of invalid session ID formats."""
    linker = SessionStateTaskLinker()
    session = {
        "session_id": "invalid_session_123",  # Must start with session_
        "active_objectives": ["obj_001"],
    }
    tasks = [
        {"task_id": "task_001", "objective_id": "obj_001"},
    ]

    with pytest.raises(ValueError, match="Invalid session_id format"):
        linker.validate_session_task_lineage(session, tasks)


def test_session_state_task_linker_invalid_task_id_prefix():
    """Verify rejection of invalid task ID formats."""
    linker = SessionStateTaskLinker()
    session = {
        "session_id": "session_f6b3d4e5",
        "active_objectives": ["obj_001"],
    }
    tasks = [
        {"task_id": "invalid_task_001", "objective_id": "obj_001"},  # Must start with task_
    ]

    with pytest.raises(ValueError, match="Invalid task_id format"):
        linker.validate_session_task_lineage(session, tasks)


def test_session_state_task_linker_missing_task_id():
    """Verify rejection when task lacks a task_id."""
    linker = SessionStateTaskLinker()
    session = {
        "session_id": "session_f6b3d4e5",
        "active_objectives": ["obj_001"],
    }
    tasks = [
        {"objective_id": "obj_001"},
    ]

    with pytest.raises(ValueError, match="Missing 'task_id' in task"):
        linker.validate_session_task_lineage(session, tasks)


def test_session_state_task_linker_missing_objective_id():
    """Verify rejection when task lacks an objective_id."""
    linker = SessionStateTaskLinker()
    session = {
        "session_id": "session_f6b3d4e5",
        "active_objectives": ["obj_001"],
    }
    tasks = [
        {"task_id": "task_001"},
    ]

    with pytest.raises(ValueError, match="Missing 'objective_id' in task"):
        linker.validate_session_task_lineage(session, tasks)


def test_session_state_task_linker_duplicate_task_detection():
    """Verify rejection of duplicate task IDs in lineage mapping."""
    linker = SessionStateTaskLinker()
    session = {
        "session_id": "session_f6b3d4e5",
        "active_objectives": ["obj_001"],
    }
    tasks = [
        {"task_id": "task_001", "objective_id": "obj_001"},
        {"task_id": "task_001", "objective_id": "obj_001"},
    ]

    with pytest.raises(ValueError, match="Duplicate task ID detected"):
        linker.validate_session_task_lineage(session, tasks)


def test_session_state_task_linker_objective_mismatch():
    """Verify rejection when task maps to an objective not listed in session."""
    linker = SessionStateTaskLinker()
    session = {
        "session_id": "session_f6b3d4e5",
        "active_objectives": ["obj_001_deploy"],
    }
    tasks = [
        {"task_id": "task_001", "objective_id": "obj_002_unauthorized"},
    ]

    with pytest.raises(ValueError, match="Objective mismatch"):
        linker.validate_session_task_lineage(session, tasks)


def test_one_way_import_boundary_preservation():
    """Verify strict adherence to the One-Way Import Law for SessionStateTaskLinker.

    Ensure that 'sage/experimental/' modules do not import from core/production namespaces
    other than utilizing them via generic type annotations or argument parameters.
    No imports of production components should exist inside sage/experimental/act/.
    """
    contracts_file = Path(__file__).parent.parent.parent / "sage" / "experimental" / "act" / "contracts.py"
    assert contracts_file.exists(), f"Could not find contracts.py at: {contracts_file}"

    with open(contracts_file, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(contracts_file))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("sage.acr"), (
                    f"One-Way Import Law Violation: 'contracts.py' directly imports production module '{alias.name}'"
                )
                assert not alias.name.startswith("sage.core"), (
                    f"One-Way Import Law Violation: 'contracts.py' directly imports production module '{alias.name}'"
                )
                assert not alias.name.startswith("sage.agents"), (
                    f"One-Way Import Law Violation: 'contracts.py' directly imports production module '{alias.name}'"
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert not node.module.startswith("sage.acr"), (
                    f"One-Way Import Law Violation: 'contracts.py' imports from production module '{node.module}'"
                )
                assert not node.module.startswith("sage.core"), (
                    f"One-Way Import Law Violation: 'contracts.py' imports from production module '{node.module}'"
                )
                assert not node.module.startswith("sage.agents"), (
                    f"One-Way Import Law Violation: 'contracts.py' imports from production module '{node.module}'"
                )


def test_session_state_task_linker_finalization_invariant_dict():
    """Verify that finalized or archived sessions in dictionary format are rejected."""
    linker = SessionStateTaskLinker()

    finalized_session = {
        "session_id": "session_f6b3d4e5",
        "active_objectives": ["obj_001"],
        "metadata": {"finalized": True},
    }
    with pytest.raises(ValueError, match="Cannot perform lineage validation on a finalized session"):
        linker.validate_session_task_lineage(finalized_session, [])

    archived_session = {
        "session_id": "session_f6b3d4e5",
        "active_objectives": ["obj_001"],
        "metadata": {"archived": True},
    }
    with pytest.raises(ValueError, match="Cannot perform lineage validation on an archived session"):
        linker.validate_session_task_lineage(archived_session, [])


def test_session_state_task_linker_finalization_invariant_model():
    """Verify that finalized or archived SessionState models are rejected."""
    linker = SessionStateTaskLinker()

    finalized_session = SessionState(
        session_id="session_f6b3d4e5",
        active_objectives=["obj_001"],
        metadata={"finalized": True},
    )
    with pytest.raises(ValueError, match="Cannot perform lineage validation on a finalized session"):
        linker.validate_session_task_lineage(finalized_session, [])

    archived_session = SessionState(
        session_id="session_f6b3d4e5",
        active_objectives=["obj_001"],
        metadata={"archived": True},
    )
    with pytest.raises(ValueError, match="Cannot perform lineage validation on an archived session"):
        linker.validate_session_task_lineage(archived_session, [])


def test_session_state_task_linker_enhanced_metrics_and_metadata():
    """Verify improved structured output contains correct validation metrics and audit flags."""
    linker = SessionStateTaskLinker()
    session = {
        "session_id": "session_f6b3d4e5",
        "active_objectives": ["obj_001", "obj_002"],
    }
    tasks = [
        {"task_id": "task_001", "objective_id": "obj_001"},
        {"task_id": "task_002", "objective_id": "obj_001"},
        {"task_id": "task_003", "objective_id": "obj_002"},
    ]

    result = linker.validate_session_task_lineage(session, tasks)

    assert result["total_tasks_validated"] == 3
    assert result["validated_objectives"] == ["obj_001", "obj_002"]
    assert "audit_metrics" in result
    assert result["audit_metrics"]["finalization_checked"] is True
    assert result["audit_metrics"]["objectives_verified"] is True
    assert result["audit_metrics"]["duplicate_checks_passed"] is True


def test_session_state_task_linker_empty_tasks():
    """Verify lineage validation with an empty list of tasks."""
    linker = SessionStateTaskLinker()
    session = {
        "session_id": "session_f6b3d4e5",
        "active_objectives": ["obj_001"],
    }

    result = linker.validate_session_task_lineage(session, [])

    assert result["session_id"] == "session_f6b3d4e5"
    assert result["mapped_tasks"] == []
    assert result["total_tasks_validated"] == 0
    assert result["validated_objectives"] == []


def test_session_state_task_linker_no_metadata_field():
    """Verify that sessions without any metadata field validate normally."""
    linker = SessionStateTaskLinker()
    session = {
        "session_id": "session_f6b3d4e5",
        "active_objectives": ["obj_001"],
    }
    tasks = [
        {"task_id": "task_001", "objective_id": "obj_001"},
    ]

    result = linker.validate_session_task_lineage(session, tasks)
    assert result["session_id"] == "session_f6b3d4e5"
    assert result["total_tasks_validated"] == 1
