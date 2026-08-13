import os
import ast
import subprocess
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.jules_preflight import SAGEPreflightChecker


@pytest.fixture
def preflight_checker(tmp_path):
    """Provides a SAGEPreflightChecker instance with a temporary repo root."""
    return SAGEPreflightChecker(repo_root=str(tmp_path))


def test_preflight_checker_initialization(preflight_checker):
    """Verify that SAGEPreflightChecker initializes with correct paths."""
    assert len(preflight_checker.protected_paths) > 0
    assert "evidence_capture/phase_4" in preflight_checker.historical_evidence_paths


def test_one_way_import_law_clean(tmp_path, preflight_checker):
    """Verify that One-Way Import Law check passes if there are no experimental imports in core."""
    core_dir = tmp_path / "sage" / "core"
    core_dir.mkdir(parents=True)

    file_py = core_dir / "models.py"
    file_py.write_text("import json\nfrom pydantic import BaseModel\n")

    passed, msg = preflight_checker.check_one_way_import_law()
    assert passed is True
    assert "One-Way Import Law verified" in msg


def test_one_way_import_law_violation(tmp_path, preflight_checker):
    """Verify that One-Way Import Law check fails if a core file imports from sage.experimental."""
    core_dir = tmp_path / "sage" / "core"
    core_dir.mkdir(parents=True)

    # Import from sage.experimental
    file_py = core_dir / "models.py"
    file_py.write_text("import sage.experimental.cognitive.state_schema\n")

    passed, msg = preflight_checker.check_one_way_import_law()
    assert passed is False
    assert "One-Way Import Law Violation" in msg


@patch("subprocess.run")
def test_historical_evidence_immutability_clean(mock_run, preflight_checker):
    """Verify that historical evidence check passes if no phase_4 evidence files are changed."""
    mock_run.return_value = MagicMock(returncode=0, stdout=" M sage/api.py\n")

    passed, msg = preflight_checker.check_historical_evidence_immutability()
    assert passed is True
    assert "Historical evidence immutability verified" in msg


@patch("subprocess.run")
def test_historical_evidence_immutability_violation(mock_run, preflight_checker):
    """Verify that historical evidence check fails if any phase_4 evidence file is modified."""
    mock_run.return_value = MagicMock(returncode=0, stdout=" M evidence_capture/phase_4_repeatability_summary.json\n")

    passed, msg = preflight_checker.check_historical_evidence_immutability()
    assert passed is False
    assert "Historical evidence mutation violation" in msg


@patch("subprocess.run")
def test_protected_core_boundaries_clean(mock_run, preflight_checker):
    """Verify that protected core check passes if no core production files are modified."""
    mock_run.return_value = MagicMock(returncode=0, stdout=" M sage/experimental/act/continuity_control.py\n")

    passed, msg = preflight_checker.check_protected_core_boundaries()
    assert passed is True
    assert "Protected core boundaries verified" in msg


@patch("subprocess.run")
def test_protected_core_boundaries_violation(mock_run, preflight_checker):
    """Verify that protected core check fails if any core production file is modified."""
    mock_run.return_value = MagicMock(returncode=0, stdout=" M sage/core/spek.py\n")

    passed, msg = preflight_checker.check_protected_core_boundaries()
    assert passed is False
    assert "Protected core boundary violation" in msg


@patch("subprocess.run")
def test_branch_ancestry_clean(mock_run, preflight_checker):
    """Verify that branch ancestry check passes if origin/main is ancestor."""
    mock_run.return_value = MagicMock(returncode=0)

    passed, msg = preflight_checker.check_branch_ancestry()
    assert passed is True
    assert "Branch ancestry verified successfully" in msg


@patch("subprocess.run")
def test_branch_ancestry_violation(mock_run, preflight_checker):
    """Verify that branch ancestry check fails if origin/main is not ancestor."""
    mock_run.return_value = MagicMock(returncode=1)

    passed, msg = preflight_checker.check_branch_ancestry()
    assert passed is False
    assert "Branch ancestry violation" in msg


@patch("subprocess.run")
def test_scope_drift_clean(mock_run, preflight_checker):
    """Verify that scope drift check passes if modified files are inside authorized scope."""
    mock_run.return_value = MagicMock(returncode=0, stdout=" M sage/experimental/act/continuity_control.py\n M .github/workflows/main.yml\n")

    passed, msg = preflight_checker.check_scope_drift()
    assert passed is True
    assert "Scope drift check passed successfully" in msg


@patch("subprocess.run")
def test_scope_drift_violation(mock_run, preflight_checker):
    """Verify that scope drift check fails if any modified file is outside authorized scope."""
    mock_run.return_value = MagicMock(returncode=0, stdout=" M .sage/config/runtime.json\n")

    passed, msg = preflight_checker.check_scope_drift()
    assert passed is False
    assert "Scope drift violation" in msg
