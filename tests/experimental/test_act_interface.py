"""SAGE-ACT Milestone 1 Interface validation and Import isolation test suite."""

import pytest
import os
import ast
from pathlib import Path

from sage.experimental.act import SessionTaskTreeLinker, TaskDecisionBinder


def test_session_task_tree_linker_valid():
    """Verify standard valid linkage mapping."""
    linker = SessionTaskTreeLinker()
    result = linker.link_session_to_tasks(
        session_id="session_f6b3d4e5",
        task_ids=["task_001_deploy", "task_002_test"],
    )

    assert result["session_id"] == "session_f6b3d4e5"
    assert len(result["mapped_tasks"]) == 2
    assert "task_001_deploy" in result["mapped_tasks"]
    assert result["validation_status"] == "INTERFACE_VERIFIED"
    assert result["read_only_assertion"] is True
    assert "linked_at" in result


def test_session_task_tree_linker_invalid_session_id():
    """Verify that an invalid session_id format is rejected."""
    linker = SessionTaskTreeLinker()
    with pytest.raises(ValueError, match="Invalid session_id format"):
        linker.link_session_to_tasks(
            session_id="sess_f6b3d4e5",  # Invalid prefix (must be session_)
            task_ids=["task_001"],
        )


def test_session_task_tree_linker_invalid_task_id():
    """Verify that an invalid task_id format is rejected."""
    linker = SessionTaskTreeLinker()
    with pytest.raises(ValueError, match="Invalid task_id format"):
        linker.link_session_to_tasks(
            session_id="session_f6b3d4e5",
            task_ids=["task_001", "deploy_task_002"],  # Invalid prefix
        )


def test_task_decision_binder_valid():
    """Verify standard valid decision binding mapping."""
    binder = TaskDecisionBinder()
    result = binder.bind_task_to_decisions(
        task_id="task_2026_spek",
        decision_ids=["decision_001_approve", "proposal_002_auth"],
    )

    assert result["task_id"] == "task_2026_spek"
    assert len(result["bound_decisions"]) == 2
    assert "proposal_002_auth" in result["bound_decisions"]
    assert result["validation_status"] == "INTERFACE_VERIFIED"
    assert result["read_only_assertion"] is True
    assert "bound_at" in result


def test_task_decision_binder_invalid_task_id():
    """Verify that an invalid task_id format is rejected by the binder."""
    binder = TaskDecisionBinder()
    with pytest.raises(ValueError, match="Invalid task_id format"):
        binder.bind_task_to_decisions(
            task_id="t_2026",  # Invalid prefix
            decision_ids=["decision_001"],
        )


def test_task_decision_binder_invalid_decision_id():
    """Verify that an invalid decision_id format is rejected by the binder."""
    binder = TaskDecisionBinder()
    with pytest.raises(ValueError, match="Invalid decision/proposal ID format"):
        binder.bind_task_to_decisions(
            task_id="task_2026",
            decision_ids=["decision_001", "approved_dec_002"],  # Invalid prefix
        )


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
                # Check from imports (e.g., 'from sage.experimental.act import SessionTaskTreeLinker')
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        assert "sage.experimental" not in node.module, (
                            f"One-Way Import Law Violation inside production: '{file_path}' "
                            f"attempts to import from module '{node.module}'"
                        )
