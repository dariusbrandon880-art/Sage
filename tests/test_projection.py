"""Unit tests for SAGE Persistent Continuity Projection (scripts/project_git_state and scripts/project_telemetry)."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

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
    sage_dir = tmp_path / "SAGE"
    sage_dir.mkdir()
    for f in GoogleDriveProjectionSyncManager.CANONICAL_FILES:
        filepath = sage_dir / f
        filepath.write_text(f"Mock content of {f}\nCURRENT_HEAD_SHA: local_sha_123")
    dot_sage = tmp_path / ".sage"
    dot_sage.mkdir()
    state_file = dot_sage / "sage_state.json"
    state_data = {
        "snapshots": {
            "snapshot_1": {
                "timestamp": "2026-08-13T17:32:26.920900+00:00",
                "state": {"active_task": "Custom Active Task Injected"}
            }
        }
    }
    with open(state_file, "w") as f:
        json.dump(state_data, f)
    yield tmp_path


def test_get_active_task_and_pr_no_legacy_fallback(temp_sage_dir):
    non_existent = temp_sage_dir / "does_not_exist.json"
    task, pr = get_active_task_and_pr(non_existent)
    assert task == "UNSPECIFIED"
    assert pr == "UNBOUND"
    assert "Google Continuity" not in task
    assert "PR #125" not in pr


def test_get_active_task_and_pr_from_file(temp_sage_dir):
    state_file = temp_sage_dir / ".sage" / "sage_state.json"
    task, pr = get_active_task_and_pr(state_file)
    assert task == "Custom Active Task Injected"


@patch("scripts.project_git_state.run_command")
def test_git_projector_success(mock_run_cmd, temp_sage_dir):
    def cmd_side_effect(args):
        if "--abbrev-ref" in args:
            return "mock-branch-name"
        if "rev-parse" in args:
            return "local_sha_123"
        if "status" in args:
            return ""
        return ""
    mock_run_cmd.side_effect = cmd_side_effect
    with patch("scripts.project_git_state.SAGE_ROOT", temp_sage_dir / "SAGE"):
        run_git_projector()
    output = (temp_sage_dir / "SAGE" / "PROJECT_STATUS.md").read_text()
    assert "CURRENT_STATUS: UNSPECIFIED" in output
    assert "Google Continuity" not in output
    assert "PR #125" not in output


@patch("scripts.project_telemetry.run_command")
def test_telemetry_projector(mock_run_cmd, temp_sage_dir):
    mock_run_cmd.return_value = "123 passed, 2 failed"
    result = run_telemetry_projector()
    assert result is not None


def test_parse_pytest_count():
    assert parse_pytest_count("123 passed, 2 failed") == 123
