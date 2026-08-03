"""Unit test suite for SAGE Demonstration Launch Experience."""

import os
import json
import pytest
from sage.experimental.act.demo_launcher import SAGEDemoLauncher, load_class_from_git_commit


def test_demo_launcher_load_inputs():
    """Verify standard and custom input configurations can be loaded successfully."""
    launcher = SAGEDemoLauncher(output_path=None)

    # Standard default inputs
    inputs = launcher.load_inputs()
    assert inputs["session_id"] == "session_demo_launcher_2026"
    assert inputs["user_id"] == "usr_lead_developer"
    assert inputs["approver"] == "supervisor_charlie"
    assert "sage/core/spek.py" in inputs["modified_files"]

    # Custom override inputs
    custom = {
        "session_id": "session_custom_launcher",
        "user_id": "usr_test_user",
        "modified_files": ["src/custom.py"]
    }
    loaded_custom = launcher.load_inputs(custom)
    assert loaded_custom["session_id"] == "session_custom_launcher"
    assert loaded_custom["user_id"] == "usr_test_user"
    assert loaded_custom["modified_files"] == ["src/custom.py"]
    assert loaded_custom["approver"] == "supervisor_charlie"  # Preserved default


def test_demo_launcher_execute_end_to_end(tmp_path):
    """Verify end-to-end SAGE launch experience executes and writes evidence successfully."""
    evidence_file = tmp_path / "demo_launcher_evidence.json"
    launcher = SAGEDemoLauncher(output_path=str(evidence_file))

    launcher.load_inputs({
        "session_id": "session_test_execution_2026",
        "user_id": "usr_tester_99"
    })

    evidence = launcher.execute_demo()

    # Structural assertions
    assert evidence["launcher_run_id"].startswith("launch_")
    assert evidence["standard_inputs"]["user_id"] == "usr_tester_99"
    assert evidence["sdr_004_divergence"]["conflicts_detected"] == 1
    assert evidence["sdr_004_divergence"]["resolution_status"] == "RESOLVED"
    assert evidence["repeatable_experience"]["status"] == "EXPERIENCE_SUCCESS"
    assert evidence["act_prod_demonstrator"]["non_repudiation_status"] == "VERIFIED_INDISPUTABLE"

    # Attestation and security assertions
    assert evidence["attestation"]["signer_identity"] == "supervisor_charlie"
    assert len(evidence["attestation"]["signature"]) > 0
    assert evidence["boundary_integrity_verification"]["sage_runtime_untouched"] is True
    assert evidence["boundary_integrity_verification"]["sage_core_untouched"] is True

    # Terminal presentation dashboard
    assert len(evidence["terminal_presentation"]) > 0
    dashboard_text = "\n".join(evidence["terminal_presentation"])
    assert "SAGE DEMONSTRATION EXPERIENCE LAUNCHER CONTROL CONSOLE" in dashboard_text
    assert "=== SAGE CHRONOLOGICAL DEMONSTRATION LINEAGE ===" in dashboard_text
    assert "=== FINAL SAGE DEMONSTRATION WORKFLOW RUN SUMMARY ===" in dashboard_text

    # Verify file was written to disk and has identical content
    assert evidence_file.exists()
    with open(evidence_file, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    assert loaded_data["launcher_run_id"] == evidence["launcher_run_id"]
    assert loaded_data["standard_inputs"]["session_id"] == "session_test_execution_2026"


def test_load_class_from_git_commit_invalid():
    """Verify that attempting to load from non-existent commit or file handles failure gracefully."""
    # Invalid commit
    cls = load_class_from_git_commit("0000000000000000000000000000000000000000", "nonexistent.py", "AnyClass")
    assert cls is None

    # Invalid path
    cls2 = load_class_from_git_commit("5806293", "sage/experimental/act/non_existent.py", "SAGEDemoExperienceManager")
    assert cls2 is None
