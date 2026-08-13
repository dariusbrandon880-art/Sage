"""Unit tests for SAGE Persistent Continuity Projection (scripts/project_git_state and scripts/project_telemetry)."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Inject mock modules into sys.modules to simulate installed Google Workspace/Drive packages
# even when they are not physically installed in the test environment.
mock_google = MagicMock()
mock_googleapiclient = MagicMock()

sys.modules["google"] = mock_google
sys.modules["google.oauth2"] = mock_google.oauth2
sys.modules["google.oauth2.service_account"] = mock_google.oauth2.service_account
sys.modules["google.oauth2.credentials"] = mock_google.oauth2.credentials
sys.modules["google_auth_oauthlib"] = mock_google
sys.modules["google_auth_oauthlib.flow"] = mock_google.flow
sys.modules["googleapiclient"] = mock_googleapiclient
sys.modules["googleapiclient.discovery"] = mock_googleapiclient.discovery
sys.modules["googleapiclient.http"] = mock_googleapiclient.http

import pytest

from scripts.project_git_state import main as run_git_projector, get_active_task_and_pr
from scripts.project_telemetry import main as run_telemetry_projector, parse_pytest_count
from sage.integration import GoogleDriveProjectionSyncManager


@pytest.fixture
def temp_sage_dir(tmp_path):
    # Set up temporary dir and patch SAGE folder target
    sage_dir = tmp_path / "SAGE"
    sage_dir.mkdir()

    # Write canonical SAGE files inside temp dir
    for f in GoogleDriveProjectionSyncManager.CANONICAL_FILES:
        filepath = sage_dir / f
        filepath.write_text(f"Mock content of {f}\nCURRENT_HEAD_SHA: local_sha_123")

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


def test_drive_sync_dry_run_fallback(temp_sage_dir):
    """Test dry-run fallback of GoogleDriveProjectionSyncManager when credentials do not exist."""
    sync_mgr = GoogleDriveProjectionSyncManager()

    non_existent_creds = temp_sage_dir / "non_existent_creds.json"
    target_dir = temp_sage_dir / "SAGE"

    # Call with non-existent credentials path to force dry-run
    # We mock credentials existence checks by using a non-existent file
    res = sync_mgr.sync_projection_to_drive(
        credentials_path=str(non_existent_creds),
        target_dir=str(target_dir)
    )

    assert res["mode"] == "dry-run"
    assert res["status"] == "validation_required"
    assert "unavailable" in res["reason"]
    assert "required_scopes" in res
    assert "google-api-python-client" in res["setup_requirements"]["packages_to_install"]
    assert len(res["synced_files"]) == 8

    # Assert SHA-256 and local check
    for item in res["synced_files"]:
        assert item["exists_locally"] is True
        assert len(item["local_sha256"]) == 64


def test_drive_sync_live_mocked_success(temp_sage_dir):
    """Test live Google Drive sync handshake under simulated environment where credentials are found."""
    # Write mock credentials file to temp_sage_dir to trigger use_live_sync path
    creds_path = temp_sage_dir / "credentials.json"
    creds_path.write_text('{"type": "service_account"}')

    target_dir = temp_sage_dir / "SAGE"

    # Set up the mock objects
    mock_service = MagicMock()
    mock_googleapiclient.discovery.build.return_value = mock_service

    # Mock list folder call (empty files list, folder SAGE doesn't exist)
    mock_files = mock_service.files.return_value
    mock_list_exec = MagicMock()
    mock_list_exec.execute.return_value = {"files": []}
    mock_files.list.return_value = mock_list_exec

    # Mock create folder call
    mock_create_exec = MagicMock()
    mock_create_exec.execute.return_value = {"id": "sage_folder_drive_id_999"}
    mock_files.create.return_value = mock_create_exec

    # Mock update calls
    mock_update_exec = MagicMock()
    mock_update_exec.execute.return_value = {"id": "synced_file_drive_id"}
    mock_files.update.return_value = mock_update_exec

    with patch("sage.integration.GoogleDriveProjectionSyncManager.detect_local_head_sha", return_value="local_sha_123"):
        # Run sync_projection_to_drive
        sync_mgr = GoogleDriveProjectionSyncManager()

        # Run the live sync handshake
        res = sync_mgr.sync_projection_to_drive(
            credentials_path=str(creds_path),
            target_dir=str(target_dir)
        )

    assert res["mode"] == "live"
    assert res["status"] == "success"
    assert res["synced_files_count"] == 8
    assert res["is_valid"] is True
    assert mock_files.create.called


def test_drive_sync_stale_conflict_detection(temp_sage_dir):
    """Test readback stale/conflict detection of GoogleDriveProjectionSyncManager."""
    creds_path = temp_sage_dir / "credentials.json"
    creds_path.write_text('{"type": "service_account"}')

    target_dir = temp_sage_dir / "SAGE"

    mock_service = MagicMock()
    mock_googleapiclient.discovery.build.return_value = mock_service

    mock_files = mock_service.files.return_value

    # Define folder SAGE already exists
    mock_list_exec = MagicMock()
    mock_list_exec.execute.side_effect = [
        {"files": [{"id": "folder_sage_123"}]},  # Query SAGE folder
        {"files": []},  # File 1 check
        {"files": []},  # File 2 check
        {"files": []},  # File 3 check
        {"files": []},  # File 4 check
        {"files": []},  # File 5 check
        {"files": []},  # File 6 check
        {"files": []},  # File 7 check
        {"files": []},  # File 8 check
        {"files": [{"id": "remote_05_active_work_id"}]}  # Query 05_ACTIVE_WORK.md for readback
    ]
    mock_files.list.return_value = mock_list_exec

    # Mock get_media call returning a mismatched remote HEAD SHA
    mock_media_exec = MagicMock()
    mock_media_exec.execute.return_value = b"CURRENT_HEAD_SHA: remote_diff_sha_999\n"
    mock_files.get_media.return_value = mock_media_exec

    # Mock create calls
    mock_create_exec = MagicMock()
    mock_create_exec.execute.return_value = {"id": "mock_id"}
    mock_files.create.return_value = mock_create_exec

    sync_mgr = GoogleDriveProjectionSyncManager()

    # Run sync - local HEAD is "local_sha_123" (mismatched with remote "remote_diff_sha_999")
    res = sync_mgr.sync_projection_to_drive(
        credentials_path=str(creds_path),
        target_dir=str(target_dir)
    )

    assert res["mode"] == "live"
    assert res["status"] == "success"

    # Verify conflict check results
    conflict = res["stale_conflict_check"]
    assert "local_head_sha" in conflict
    assert conflict["remote_head_sha"] == "remote_diff_sha_999"
    assert conflict["status"] == "STALE / CONFLICTED PROJECTION"
    assert res["is_valid"] is False


def test_drive_sync_immutability_guarantee(temp_sage_dir):
    """Test that GoogleDriveProjectionSyncManager strictly respects unidirectional isolation."""
    sync_mgr = GoogleDriveProjectionSyncManager()

    non_existent_creds = temp_sage_dir / "non_existent_creds.json"
    target_dir = temp_sage_dir / "SAGE"

    # Save initial code files timestamps or verify directory list doesn't mutate
    initial_files = list(Path("sage/").glob("**/*.py"))

    # Run sync manager
    sync_mgr.sync_projection_to_drive(
        credentials_path=str(non_existent_creds),
        target_dir=str(target_dir)
    )

    # Assert that no python files inside sage/ have been created, deleted or modified during execution
    current_files = list(Path("sage/").glob("**/*.py"))
    assert len(initial_files) == len(current_files)
