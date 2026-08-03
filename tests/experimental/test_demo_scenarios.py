"""Unit test suite for SAGE Demonstration Scenario Experience with Outcome Contrast."""

import os
import json
import pytest
from sage.experimental.act.demo_scenarios import SAGEScenarioRegistry, SAGEScenarioExecutor


def test_scenario_registry_list_and_get():
    """Verify that scenarios are correctly registered, listed, and retrieved with intelligence metadata."""
    registry = SAGEScenarioRegistry()

    scenarios = registry.list_scenarios()
    assert len(scenarios) == 3

    scenario_ids = [s["scenario_id"] for s in scenarios]
    assert "scenario_a_clean" in scenario_ids
    assert "scenario_b_override" in scenario_ids
    assert "scenario_c_divergence" in scenario_ids

    # Correct retrieval
    scen_b = registry.get_scenario("scenario_b_override")
    assert scen_b["name"] == "Scenario B: Protected Workspace Modification & Override Flow"
    assert "spek.py" in scen_b["config"]["modified_files"][0]
    assert "unauthorized attempt" in scen_b["intelligence"]["explanation"]


def test_scenario_executor_run_all(tmp_path):
    """Verify loading, executing, outcome contrast summaries, and evidence generation for all scenarios."""
    evidence_file = tmp_path / "demo_scenario_evidence.json"
    executor = SAGEScenarioExecutor(output_path=str(evidence_file))

    # Test Scenario B execution (protected modification override)
    run_b = executor.execute_scenario("scenario_b_override")
    assert run_b["scenario_run_id"].startswith("scen_run_")
    assert run_b["scenario_id"] == "scenario_b_override"
    assert run_b["launcher_evidence"]["context_guard_validation"]["status"] == "PROTECTION_VIOLATION_DETECTED"
    assert run_b["boundary_integrity_verification"]["sage_runtime_untouched"] is True
    assert run_b["observed_results"]["scenario_execution_success"] is True

    # Test decision interpretation fields are present
    assert "unauthorized attempt" in run_b["decision_interpretation"]["explanation"]
    assert "Critical path" in run_b["decision_interpretation"]["governed_outcome_advantage"]
    assert "Silent core" in run_b["decision_interpretation"]["baseline_uncontrolled_risk"]

    # Test visual presentation text contains contrast sections
    assert len(run_b["visual_presentation"]) > 0
    presentation_text = "\n".join(run_b["visual_presentation"])
    assert "SAGE REPEATABLE SCENARIO EXPERIENCE: SCENARIO B" in presentation_text
    assert "=== SAGE DECISION INTERPRETATION ===" in presentation_text
    assert "=== GOVERNED OUTCOME VS. BASELINE RISK CONTRAST ===" in presentation_text

    # Verify file was written to disk
    assert evidence_file.exists()
    with open(evidence_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["scenario_run_id"] == run_b["scenario_run_id"]
    assert loaded["decision_interpretation"]["explanation"] == run_b["decision_interpretation"]["explanation"]

    # Test Scenario A execution (clean workspace)
    run_a = executor.execute_scenario("scenario_a_clean")
    assert run_a["scenario_id"] == "scenario_a_clean"
    assert "no modifications" in run_a["decision_interpretation"]["explanation"]

    # Test Scenario C execution (divergence resolution)
    run_c = executor.execute_scenario("scenario_c_divergence")
    assert run_c["scenario_id"] == "scenario_c_divergence"
    assert "Authority Priority" in run_c["decision_interpretation"]["explanation"]
