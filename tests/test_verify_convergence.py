"""Tests for SAGE Merge Convergence and Milestone Verification logic."""

from pathlib import Path
from unittest.mock import patch
from scripts.verify_convergence import (
    check_linting,
    check_formatting,
    scan_for_merge_conflict_markers,
    check_repo_cleanliness,
)


def test_verify_convergence_quality_gates():
    """Verify that linting and formatting checker gates return valid status mappings."""
    # Ensure they return standard boolean/string formats
    lint_res = check_linting()
    assert "passed" in lint_res
    assert isinstance(lint_res["passed"], bool)

    format_res = check_formatting()
    assert "passed" in format_res
    assert isinstance(format_res["passed"], bool)


def test_scan_for_merge_conflict_markers(tmp_path):
    """Test that scan_for_merge_conflict_markers flags actual git merge markers correctly."""
    # Create mock clean document
    clean_file = tmp_path / "CLEAN_DOC.md"
    clean_file.write_text("# A Clean Document\nSome normal content here.", encoding="utf-8")

    # Create mock corrupted document with conflict markers
    conflict_file = tmp_path / "CONFLICT_DOC.md"
    conflict_file.write_text(
        "# State document\n<<<<<<< SEARCH\nOld content\n=======\nNew content\n>>>>>>> REPLACE",
        encoding="utf-8",
    )

    with (
        patch("scripts.verify_convergence.Path.glob") as mock_glob,
        patch("scripts.verify_convergence.Path.exists", return_value=True),
    ):
        mock_glob.return_value = [clean_file, conflict_file]

        res = scan_for_merge_conflict_markers()
        assert res["passed"] is False
        assert len(res["files"]) == 1
        assert "CONFLICT_DOC.md" in res["files"][0]


def test_check_repo_cleanliness_validation(tmp_path):
    """Test that check_repo_cleanliness correctly spots forbidden temporary files."""
    # 1. Mock a clean list
    clean_paths = [Path("sage"), Path("tests"), Path("pyproject.toml")]
    with patch("scripts.verify_convergence.Path.glob") as mock_glob:
        mock_glob.return_value = clean_paths
        res = check_repo_cleanliness()
        assert res["passed"] is True

    # 2. Mock a dirty list with sage_data
    dirty_paths = [Path("sage"), Path("sage_data"), Path("tests")]
    with patch("scripts.verify_convergence.Path.glob") as mock_glob:
        mock_glob.return_value = dirty_paths
        res = check_repo_cleanliness()
        assert res["passed"] is False
        assert len(res["unintended_files"]) == 1
        assert "sage_data" in res["unintended_files"][0]
