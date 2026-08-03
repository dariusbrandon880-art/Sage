"""SAGE Demonstration Scenario Experience test suite."""

import os
import json
import pytest

from sage.experimental.act.demo_scenarios import SAGEDemoScenarioRegistry


def test_scenario_registry_and_execution():
    """Verify standard happy path of the SAGE scenario registry and execution."""
    registry = SAGEDemoScenarioRegistry(output_path="evidence_capture/demo_scenario_evidence.json")

    # Verify scenario list retrieval
    scenarios = registry.get_registered_scenarios()
    assert len(scenarios) == 2
    assert scenarios[0]["scenario_id"] == "scenario_default_audit"

    # Execute a selected scenario
    run_payload = registry.execute_selected_scenario(
        scenario_id="scenario_stress_recovery",
        approver="supervisor_charlie",
        signature="sig_scenario_approved_1100",
    )

    assert run_payload["scenario_id"] == "scenario_stress_recovery"
    assert "scenario_checksum" in run_payload
    assert "SAGE SCENARIO EXPERIENCE" in run_payload["improved_result_summary"]

    # Export scenario evidence and verify file structure
    path = registry.export_scenario_evidence()
    assert path == "evidence_capture/demo_scenario_evidence.json"
    assert os.path.exists(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["scenario_id"] == "scenario_stress_recovery"
    assert data["scenario_details"]["difficulty"] == "advanced"


def test_scenario_unregistered():
    """Verify that attempting to execute an unregistered scenario raises an error."""
    registry = SAGEDemoScenarioRegistry()
    with pytest.raises(ValueError, match="is not registered"):
        registry.execute_selected_scenario(scenario_id="scenario_unregistered")


def test_scenario_unexecuted_export():
    """Verify error on attempting to export scenario evidence before any run has executed."""
    registry = SAGEDemoScenarioRegistry()
    with pytest.raises(ValueError, match="No scenarios have been executed yet"):
        registry.export_scenario_evidence()
