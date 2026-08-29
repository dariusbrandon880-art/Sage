"""Unit and regression tests for SAGE CLI audit subcommand integration."""

import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch

from sage.cli import main


def test_cli_audit_summary_empty(tmp_path, capsys):
    """Verify SAGE CLI 'audit' action 'summary' runs cleanly on an empty archive path."""
    archive_dir = tmp_path / "empty_archive"
    archive_dir.mkdir()

    test_args = [
        "sage/cli.py",
        "audit",
        "--action", "summary",
        "--archive-path", str(archive_dir)
    ]

    with patch.object(sys, "argv", test_args):
        main()

    captured = capsys.readouterr()
    stdout_json = json.loads(captured.out)

    assert stdout_json["total_archived_traces"] == 0
    assert stdout_json["revalidation_metrics"]["total_missions_evaluated"] == 0


def test_cli_audit_scan_clean(tmp_path, capsys):
    """Verify SAGE CLI 'audit' action 'scan' runs cleanly on a healthy archive path."""
    archive_dir = tmp_path / "clean_archive"
    archive_dir.mkdir()

    test_args = [
        "sage/cli.py",
        "audit",
        "--action", "scan",
        "--archive-path", str(archive_dir)
    ]

    with patch.object(sys, "argv", test_args):
        main()

    captured = capsys.readouterr()
    stdout_json = json.loads(captured.out)

    assert stdout_json["status"] == "ok"
    assert stdout_json["corrupted_count"] == 0


def test_cli_audit_diagnostics_missing(tmp_path, capsys):
    """Verify SAGE CLI 'audit' action 'diagnostics' prints error and exits when mission ID is absent/missing."""
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()

    test_args = [
        "sage/cli.py",
        "audit",
        "--action", "diagnostics",
        "--mission-id", "missing_id_trace",
        "--archive-path", str(archive_dir)
    ]

    with patch.object(sys, "argv", test_args), pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "No archived trace found for mission" in captured.out
