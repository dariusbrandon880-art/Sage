"""Validation tests for SAGE-ACT Milestone 2 Lineage Mapping and Verification."""

import pytest
import os
import ast
from pathlib import Path

from sage.acr.session.session_state import SessionState
from sage.agents.models import AgentTask, AgentTaskState
from sage.experimental.act import SessionStateTaskLinker


def test_session_state_task_linker_successful_mapping():
    """Verify successful lineage mapping under ideal/valid conditions."""
    linker = SessionStateTaskLinker()

    session = SessionState(
        session_id="session_test_abc123",
        active_objectives=["objective_deploy_production", "objective_audit_endpoints"]
    )

    tasks = [
        AgentTask(
            task_id="task_001_deploy",
            objective_id="objective_deploy_production",
            title="Deploy runtime version",
            state=AgentTaskState.COMPLETED
        ),
        AgentTask(
            task_id="task_002_audit",
            objective_id="objective_audit_endpoints",
            title="Audit ASGI server",
            state=AgentTaskState.EXECUTING
        )
    ]

    result = linker.validate_session_task_lineage(session, tasks)

    assert result["session_id"] == "session_test_abc123"
    assert len(result["mapped_tasks"]) == 2
    assert "task_001_deploy" in result["mapped_tasks"]
    assert "task_002_audit" in result["mapped_tasks"]
    assert result["validation_status"] == "LINEAGE_VALIDATED"
    assert result["read_only_assertion"] is True
    assert "linked_at" in result


def test_session_state_task_linker_objective_mismatch_rejection():
    """Verify rejection when a task references an objective not active in the session."""
    linker = SessionStateTaskLinker()

    session = SessionState(
        session_id="session_mismatch_001",
        active_objectives=["objective_deploy_production"]
    )

    tasks = [
        AgentTask(
            task_id="task_001_deploy",
            objective_id="objective_deploy_production",
            title="Deploy runtime",
            state=AgentTaskState.COMPLETED
        ),
        AgentTask(
            task_id="task_002_rogue",
            objective_id="objective_unauthorized_objective",  # Not in active objectives
            title="Rogue task",
            state=AgentTaskState.PENDING
        )
    ]

    with pytest.raises(ValueError, match="Objective mismatch"):
        linker.validate_session_task_lineage(session, tasks)


def test_session_state_task_linker_duplicate_task_rejection():
    """Verify rejection when the input list contains tasks with duplicated IDs."""
    linker = SessionStateTaskLinker()

    session = SessionState(
        session_id="session_dup_001",
        active_objectives=["objective_deploy_production"]
    )

    tasks = [
        AgentTask(
            task_id="task_001_deploy",
            objective_id="objective_deploy_production",
            title="Deploy runtime first try",
            state=AgentTaskState.FAILED
        ),
        AgentTask(
            task_id="task_001_deploy",  # Duplicate task_id!
            objective_id="objective_deploy_production",
            title="Deploy runtime second try",
            state=AgentTaskState.PENDING
        )
    ]

    with pytest.raises(ValueError, match="Duplicate task ID detected"):
        linker.validate_session_task_lineage(session, tasks)


def test_session_state_task_linker_malformed_identifier_rejection():
    """Verify rejection of malformed session or task identifier formats."""
    linker = SessionStateTaskLinker()

    # 1. Invalid session ID format (missing session_ prefix)
    bad_session = SessionState(
        session_id="sess_bad_id",
        active_objectives=["objective_deploy_production"]
    )
    tasks = [
        AgentTask(
            task_id="task_001_deploy",
            objective_id="objective_deploy_production",
            title="Deploy runtime",
            state=AgentTaskState.PENDING
        )
    ]

    with pytest.raises(ValueError, match="Invalid session_id format"):
        linker.validate_session_task_lineage(bad_session, tasks)

    # 2. Invalid task ID format (missing task_ prefix)
    good_session = SessionState(
        session_id="session_good_id",
        active_objectives=["objective_deploy_production"]
    )
    bad_tasks = [
        AgentTask(
            task_id="deploy_task_001",  # Malformed ID
            objective_id="objective_deploy_production",
            title="Deploy runtime",
            state=AgentTaskState.PENDING
        )
    ]

    with pytest.raises(ValueError, match="Invalid task_id format"):
        linker.validate_session_task_lineage(good_session, bad_tasks)


def test_one_way_import_isolation_enforcement():
    """Verify absolute enforcement of the One-Way Import Law.

    No module in the frozen production/core namespace ('sage/acr/', 'sage/core/', etc.)
    is allowed to import from 'sage.experimental' or 'sage.experimental.act'.
    """
    root_path = Path(__file__).parent.parent.parent / "sage"
    assert root_path.exists(), f"Could not find SAGE source path at: {root_path}"

    for file_path in root_path.glob("**/*.py"):
        # Exclude files inside sage/experimental
        if "experimental" in file_path.parts:
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=str(file_path))
            except SyntaxError as e:
                pytest.fail(f"Syntax error while parsing {file_path}: {e}")

            for node in ast.walk(tree):
                # Check direct imports (e.g., 'import sage.experimental')
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "sage.experimental" not in alias.name, (
                            f"One-Way Import Law Violation inside production: '{file_path}' "
                            f"attempts to directly import '{alias.name}'"
                        )
                # Check from imports (e.g., 'from sage.experimental.act import SessionStateTaskLinker')
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        assert "sage.experimental" not in node.module, (
                            f"One-Way Import Law Violation inside production: '{file_path}' "
                            f"attempts to import from module '{node.module}'"
                        )
