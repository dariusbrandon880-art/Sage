"""Unit tests for SAGE Persistent Continuity Projection (scripts/project_git_state and scripts/project_telemetry)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.project_git_state import main as run_git_projector, get_active_task_and_pr
from scripts.project_telemetry import main as run_telemetry_projector, parse_pytest_count


@pytest.fixture
def temp_sage_dir(tmp_path):
    # Set up temporary dir and patch SAGE folder target
    sage_dir = tmp_path / "SAGE"
    sage_dir.mkdir()

    # Also set up a mock .sage/sage_state.json if needed
    dot_sage = tmp_path / ".sage"
    dot_sage.mkdir()

    state_file = dot_sage / "sage_state.json"
    state_data = {
        "snapshots": {
            "snapshot_1": {
                "timestamp": "2026-08-13T17:32:26.920900+00:00",
                "state": {
                    "active_task": "Custom Active Task Injected"
                }
            }
        }
    }
    with open(state_file, "w") as f:
        json.dump(state_data, f)

    yield tmp_path


def test_get_active_task_and_pr_fallback(temp_sage_dir):
    non_existent = temp_sage_dir / "does_not_exist.json"
    task, pr = get_active_task_and_pr(non_existent)
    assert "Google Continuity" in task
    assert "PR #125" in pr


def test_get_active_task_and_pr_from_file(temp_sage_dir):
    state_file = temp_sage_dir / ".sage" / "sage_state.json"
    task, pr = get_active_task_and_pr(state_file)
    assert task == "Custom Active Task Injected"


@patch("scripts.project_git_state.run_command")
def test_git_projector_success(mock_run_cmd, temp_sage_dir):
    # Mock git commands output
    def cmd_side_effect(args):
        if "--abbrev-ref" in args:
            return "mock-branch-name"
        elif "HEAD" in args:
            return "mock_head_sha_123"
        elif "origin/main" in args or "main" in args:
            return "mock_main_sha_abc"
        elif "merge-base" in args:
            return "mock_merge_base_sha"
        elif "--porcelain" in args:
            return "M sage/api.py\nM tests/test_projection.py"
        return ""

    mock_run_cmd.side_effect = cmd_side_effect

    # Set paths inside temp directory
    target_dir = temp_sage_dir / "SAGE"
    state_file_path = temp_sage_dir / ".sage" / "sage_state.json"

    # Run the projector
    run_git_projector(str(target_dir), str(state_file_path))

    # Assert correct calls and check written files
    assert mock_run_cmd.called

    active_work_file = target_dir / "05_ACTIVE_WORK.md"
    assert active_work_file.exists()

    written_active = active_work_file.read_text()
    assert "CURRENT_HEAD_SHA: mock_head_sha_123" in written_active
    assert "ORIGIN_MAIN_SHA: mock_main_sha_abc" in written_active
    assert "WORKING_BRANCH: mock-branch-name" in written_active
    assert "WORKTREE_STATUS: DIRTY" in written_active
    assert "PROJECTION_STATUS: SYNCHRONIZED" in written_active

    frontier_file = target_dir / "03_CURRENT_FRONTIER.md"
    assert frontier_file.exists()

    written_frontier = frontier_file.read_text()
    assert "SOURCE_HEAD: mock_head_sha_123" in written_frontier
    assert "CURRENT_STATUS: IMPLEMENTING" in written_frontier


def test_parse_pytest_count():
    output_1 = "=== 364 passed, 1 warning in 7.23s ==="
    assert parse_pytest_count(output_1) == 364

    output_2 = "=== 5 passed in 0.05s ==="
    assert parse_pytest_count(output_2) == 5

    output_3 = "No tests were executed. 0 passed."
    assert parse_pytest_count(output_3) == 0


@patch("scripts.project_telemetry.run_command_with_output")
@patch("scripts.project_telemetry.sys.exit")
def test_telemetry_projector_success(mock_exit, mock_run_with_out, temp_sage_dir):
    # Mock target command run
    mock_run_with_out.return_value = (0, "=== 364 passed in 7.23s ===")

    target_dir = temp_sage_dir / "SAGE"

    # Patch sys.argv to mock command arguments
    with patch("sys.argv", ["scripts/project_telemetry.py", "poetry", "run", "pytest"]):
        run_telemetry_projector(str(target_dir))

    assert mock_run_with_out.called

    report_file = target_dir / "06_LATEST_EXECUTION_REPORT.md"
    assert report_file.exists()

    # Check parsed execution parameters
    written_report = report_file.read_text()
    assert "COMMAND: poetry run pytest" in written_report
    assert "EXIT_CODE: 0" in written_report
    assert "ACTUAL_TEST_COUNT: 364" in written_report
    assert "EXECUTION_STATUS: PASS" in written_report

    next_file = target_dir / "07_NEXT_COMPOUND.md"
    assert next_file.exists()

    written_next = next_file.read_text()
    assert "NEXT_COMPOUND: SAGE Dynamic Targeted Test Orchestration" in written_next

    mock_exit.assert_called_once_with(0)
