"""Unit test suite for SAGE Demonstration Scenario Experience."""

import os
import json
import pytest
from sage.experimental.act.demo_scenarios import SAGEScenarioRegistry, SAGEScenarioExecutor


def test_scenario_registry_list_and_get():
    """Verify that scenarios are correctly registered, listed, and retrieved."""
    registry = SAGEScenarioRegistry()

    scenarios = registry.list_scenarios()
    assert len(scenarios) == 3

    scenario_ids = [s["scenario_id"] for s in scenarios]
    assert "scenario_a_clean" in scenario_ids
    assert "scenario_b_override" in scenario_ids
    assert "scenario_c_divergence" in scenario_ids

    # Correct retrieval
    scen_a = registry.get_scenario("scenario_a_clean")
    assert scen_a["name"] == "Scenario A: Joint Research & Clean Workspace Flow"
    assert scen_a["config"]["user_id"] == "usr_analyst_alice"

    # Invalid retrieval
    with pytest.raises(ValueError, match="is not registered"):
        registry.get_scenario("non_existent_scenario")


def test_scenario_executor_run_all(tmp_path):
    """Verify loading, executing, and evidence generation for all scenarios."""
    evidence_file = tmp_path / "demo_scenario_evidence.json"
    executor = SAGEScenarioExecutor(output_path=str(evidence_file))

    # Test Scenario A execution
    run_a = executor.execute_scenario("scenario_a_clean")
    assert run_a["scenario_run_id"].startswith("scen_run_")
    assert run_a["scenario_id"] == "scenario_a_clean"
    assert run_a["launcher_evidence"]["context_guard_validation"]["status"] == "CLEAN_WORKSPACE"
    assert run_a["boundary_integrity_verification"]["sage_runtime_untouched"] is True
    assert run_a["observed_results"]["scenario_execution_success"] is True

    # Test visual presentation text exists
    assert len(run_a["visual_presentation"]) > 0
    presentation_text = "\n".join(run_a["visual_presentation"])
    assert "SAGE REPEATABLE SCENARIO EXPERIENCE: SCENARIO A" in presentation_text

    # Verify file was written to disk
    assert evidence_file.exists()
    with open(evidence_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["scenario_run_id"] == run_a["scenario_run_id"]
    assert loaded["scenario_id"] == "scenario_a_clean"

    # Test Scenario B execution
    run_b = executor.execute_scenario("scenario_b_override")
    assert run_b["scenario_id"] == "scenario_b_override"
    assert run_b["launcher_evidence"]["context_guard_validation"]["status"] == "PROTECTION_VIOLATION_DETECTED"
    assert run_b["launcher_evidence"]["context_guard_validation"]["supervisor_decision"]["action_taken"] == "COMMIT_APPROVED"

    # Test Scenario C execution
    run_c = executor.execute_scenario("scenario_c_divergence")
    assert run_c["scenario_id"] == "scenario_c_divergence"
    assert run_c["launcher_evidence"]["sdr_004_divergence"]["applied_strategy"] == "AUTHORITY_PRIORITY"
