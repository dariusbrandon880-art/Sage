"""SAGE Demonstration Launcher test suite."""

import os
import json
import pytest

from sage.experimental.act.demo_launcher import SAGEDemoLauncher


def test_demo_launcher_scenario_success():
    """Verify standard happy path SAGE demonstration launcher scenario execution."""
    launcher = SAGEDemoLauncher(output_path="evidence_capture/demo_launcher_evidence.json")

    run_payload = launcher.execute_demo_scenario(
        scenario_id="scenario_default_audit",
        approver="supervisor_charlie",
        signature="sig_verified_123",
    )

    assert run_payload["scenario_id"] == "scenario_default_audit"
    assert "launcher_checksum" in run_payload
    assert "SAGE SCENARIO EXECUTION SUMMARY" in run_payload["unified_execution_summary"]

    experience = run_payload["experience_result"]
    assert experience["status"] == "EXPERIENCE_SUCCESS"

    # Export launcher evidence and verify file structure
    path = launcher.export_launcher_evidence()
    assert path == "evidence_capture/demo_launcher_evidence.json"
    assert os.path.exists(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["scenario_id"] == "scenario_default_audit"
    assert data["config_applied"]["demo_version"] == "1.0.0-demo-launch"


def test_demo_launcher_unsupported_scenario():
    """Verify that attempting to execute an unsupported scenario raises an error."""
    launcher = SAGEDemoLauncher()
    with pytest.raises(ValueError, match="Unsupported scenario 'scenario_unsupported'"):
        launcher.execute_demo_scenario(scenario_id="scenario_unsupported")


def test_demo_launcher_unexecuted_export():
    """Verify error on attempting to export launcher evidence before any run has executed."""
    launcher = SAGEDemoLauncher()
    with pytest.raises(ValueError, match="No launcher scenarios have been executed yet"):
        launcher.export_launcher_evidence()
