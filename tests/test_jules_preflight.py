import ast
import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock

from scripts.jules_preflight import (
    check_repository_state,
    check_historical_evidence,
    check_one_way_import_law,
    check_protected_boundary,
    check_scope_drift,
    run_assembly_line_preflight,
)


def test_check_repository_state_clean(monkeypatch):
    """Test repository state returns True when work tree is clean."""
    mock_run = MagicMock()
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="true\n"),
        MagicMock(returncode=0, stdout="main\n"),
        MagicMock(returncode=0, stdout=""),
    ]
    monkeypatch.setattr("scripts.jules_preflight.run_command", mock_run)

    assert check_repository_state() is True


def test_check_repository_state_dirty(monkeypatch):
    """Test repository state shows warning but returns True (uncommitted changes are allowed)."""
    mock_run = MagicMock()
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="true\n"),
        MagicMock(returncode=0, stdout="main\n"),
        MagicMock(returncode=0, stdout=" M sage/api.py\n"),
    ]
    monkeypatch.setattr("scripts.jules_preflight.run_command", mock_run)

    assert check_repository_state() is True


def test_check_repository_state_invalid_git(monkeypatch):
    """Test repository state returns False when not inside a git repository."""
    mock_run = MagicMock()
    mock_run.side_effect = [
        MagicMock(returncode=128, stdout=""),
    ]
    monkeypatch.setattr("scripts.jules_preflight.run_command", mock_run)

    assert check_repository_state() is False


def test_check_historical_evidence_clean(monkeypatch):
    """Test historical check returns True when no phase_4 or phase_5 files are modified."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = " M sage/api.py\n M tests/test_api.py\n"
    monkeypatch.setattr("scripts.jules_preflight.run_command", lambda cmd, **kwargs: mock_run)

    assert check_historical_evidence() is True


def test_check_historical_evidence_contaminated(monkeypatch):
    """Test historical check returns False when phase_4/5 files are modified (Failure Class 03)."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = " M evidence_capture/phase_4_controlled_evaluation_evidence.json\n"
    monkeypatch.setattr("scripts.jules_preflight.run_command", lambda cmd, **kwargs: mock_run)

    assert check_historical_evidence() is False


def test_check_protected_boundary_clean(monkeypatch):
    """Test protected boundary returns True when modifications do not touch core."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = "sage/experimental/act/continuity_control.py\ntests/experimental/test_continuity_control.py\n"
    monkeypatch.setattr("scripts.jules_preflight.run_command", lambda cmd, **kwargs: mock_run)

    assert check_protected_boundary() is True


def test_check_protected_boundary_violation(monkeypatch):
    """Test protected boundary returns False when modifications touch core without authorization."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = "sage/core/spek.py\n"
    monkeypatch.setattr("scripts.jules_preflight.run_command", lambda cmd, **kwargs: mock_run)

    # Without override, it should fail
    assert check_protected_boundary(allow_core_modification=False) is False
    # With override, it should warn and succeed
    assert check_protected_boundary(allow_core_modification=True) is True


def test_check_one_way_import_law_clean(tmp_path, monkeypatch):
    """Test One-Way Import Law checks AST correctly on clean folders."""
    clean_core = tmp_path / "sage_core"
    clean_core.mkdir()

    file_a = clean_core / "engine.py"
    file_a.write_text("import json\nfrom pydantic import BaseModel\n", encoding="utf-8")

    monkeypatch.setattr("scripts.jules_preflight.CORE_DIRS", [str(clean_core)])
    monkeypatch.setattr("scripts.jules_preflight.CORE_FILES", [])

    assert check_one_way_import_law() is True


def test_check_one_way_import_law_violation(tmp_path, monkeypatch):
    """Test One-Way Import Law catches illegal static import from experimental namespace."""
    violated_core = tmp_path / "sage_core"
    violated_core.mkdir()

    file_a = violated_core / "engine.py"
    file_a.write_text("import json\nimport sage.experimental.cognitive\n", encoding="utf-8")

    monkeypatch.setattr("scripts.jules_preflight.CORE_DIRS", [str(violated_core)])
    monkeypatch.setattr("scripts.jules_preflight.CORE_FILES", [])

    assert check_one_way_import_law() is False


def test_check_scope_drift_any(monkeypatch):
    """Test any scope drift allows any changes."""
    assert check_scope_drift(active_scope="any") is True


def test_check_scope_drift_ci_only_pass(monkeypatch):
    """Test ci-only scope passes if only CI-relevant files are edited."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = ".github/workflows/main.yml\nscripts/production_check.py\n"
    monkeypatch.setattr("scripts.jules_preflight.run_command", lambda cmd, **kwargs: mock_run)

    assert check_scope_drift(active_scope="ci-only") is True


def test_check_scope_drift_ci_only_app_fail(monkeypatch):
    """Test ci-only scope fails if application files are edited (Requirement 1)."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = ".github/workflows/main.yml\nsage/api.py\n"
    monkeypatch.setattr("scripts.jules_preflight.run_command", lambda cmd, **kwargs: mock_run)

    assert check_scope_drift(active_scope="ci-only") is False


def test_check_scope_drift_ci_only_test_fail(monkeypatch):
    """Test ci-only scope fails if test files are edited (Requirement 2)."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = ".github/workflows/main.yml\ntests/test_spek.py\n"
    monkeypatch.setattr("scripts.jules_preflight.run_command", lambda cmd, **kwargs: mock_run)

    assert check_scope_drift(active_scope="ci-only") is False


def test_check_scope_drift_ci_only_doc_fail(monkeypatch):
    """Test ci-only scope fails if documentation files are edited (Requirement 3)."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = ".github/workflows/main.yml\ndocs/master/SESSION_STATE.md\n"
    monkeypatch.setattr("scripts.jules_preflight.run_command", lambda cmd, **kwargs: mock_run)

    assert check_scope_drift(active_scope="ci-only") is False


def test_check_scope_drift_ci_only_evidence_fail(monkeypatch):
    """Test ci-only scope fails if evidence capture files are edited (Requirement 4)."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = ".github/workflows/main.yml\nevidence_capture/ccl_operational_feedback.json\n"
    monkeypatch.setattr("scripts.jules_preflight.run_command", lambda cmd, **kwargs: mock_run)

    assert check_scope_drift(active_scope="ci-only") is False


def test_check_scope_drift_audit_only_pass(monkeypatch):
    """Test audit-only scope passes if zero implementation/test files are edited."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = "docs/master/SESSION_STATE.md\nREADME.md\n"
    monkeypatch.setattr("scripts.jules_preflight.run_command", lambda cmd, **kwargs: mock_run)

    assert check_scope_drift(active_scope="audit-only") is True


def test_check_scope_drift_audit_only_fail(monkeypatch):
    """Test audit-only scope fails if tests or implementation files are edited."""
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = "tests/test_api.py\n"
    monkeypatch.setattr("scripts.jules_preflight.run_command", lambda cmd, **kwargs: mock_run)

    assert check_scope_drift(active_scope="audit-only") is False
