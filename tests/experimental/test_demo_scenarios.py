"""Unit test suite for SAGE Demonstration Scenario Experience."""

import os
import json
import pytest
from sage.experimental.act.demo_scenarios import (
    ScenarioRegistry,
    ScenarioExecutionWrapper,
    UserResultSummary,
    RepeatableScenarioEvidenceExporter
)


def test_scenario_registry():
    """Verify that registry holds standardized scenarios and handles missing IDs."""
    registry = ScenarioRegistry()

    # Pristine run scenario validation
    pristine = registry.get_scenario("pristine_run")
    assert pristine["scenario_id"] == "pristine_run"
    assert pristine["has_divergence"] is False
    assert pristine["human_gate_required"] is False

    # Missing ID handling
    with pytest.raises(KeyError, match="not registered"):
        registry.get_scenario("unknown_scenario")


def test_scenario_execution_and_summary():
    """Verify end-to-end repeatable flow runs and user-readable summary outputs."""
    registry = ScenarioRegistry()
    wrapper = ScenarioExecutionWrapper("session_test_scenarios")

    # 1. Test Pristine run execution
    sc_pristine = registry.get_scenario("pristine_run")
    res_pristine = wrapper.execute_scenario(sc_pristine)

    assert res_pristine["scenario_id"] == "pristine_run"
    assert res_pristine["divergence"]["divergence_found"] is False
    assert res_pristine["human_gate"]["status"] == "BYPASS"

    # 2. Test Divergence-resolution execution
    sc_div = registry.get_scenario("divergence_resolution")
    res_div = wrapper.execute_scenario(sc_div)

    assert res_div["scenario_id"] == "divergence_resolution"
    assert res_div["divergence"]["divergence_found"] is True
    assert res_div["human_gate"]["status"] == "AUTHORIZED"

    # 3. Test summary output rendering with decision contrasts
    summary_renderer = UserResultSummary()
    summary_str = summary_renderer.render_output_string(res_div)

    assert "SAGE SCENARIO RUN" in summary_str
    assert "Session ID" in summary_str
    assert "Divergence State : CONFL_RESOLVED" in summary_str
    assert "SAGE COGNITIVE CONTRAST" in summary_str
    assert "BASELINE UNGOVERNED EXECUTION" in summary_str


def test_repeatable_evidence_export(tmp_path):
    """Verify standard compliant evidence packaging and safe persistence."""
    registry = ScenarioRegistry()
    wrapper = ScenarioExecutionWrapper("session_test_evidence")

    sc_div = registry.get_scenario("divergence_resolution")
    res_div = wrapper.execute_scenario(sc_div)

    evidence_file = tmp_path / "demo_scenario_evidence.json"
    exporter = RepeatableScenarioEvidenceExporter(output_path=str(evidence_file))

    evidence_pack = exporter.write_scenario_evidence(res_div, wrapper.activity_log)

    # Validate output schema
    assert "scenario_session_id" in evidence_pack
    assert "timestamp" in evidence_pack
    assert "selected_scenario_id" in evidence_pack
    assert "flow_activity_log" in evidence_pack
    assert "validation_report" in evidence_pack
    assert "boundary_integrity_verification" in evidence_pack
    assert "observed_results" in evidence_pack

    # Non-absolute results verification
    observed = evidence_pack["observed_results"]
    assert "total_workflow_tasks_completed" in observed
    assert "verification_latency_secs" in observed
    assert "estimated_baseline_reproducibility_percent" in observed

    # Validate file persistence
    assert evidence_file.exists()
    with open(evidence_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["scenario_session_id"] == "session_test_evidence"
    assert loaded["boundary_integrity_verification"]["sage_runtime_untouched"] is True
