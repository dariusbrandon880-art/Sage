"""SAGE Demonstration Scenario Evaluation test suite."""

import os
import json
import pytest

from sage.experimental.act.demo_evaluation import SAGEDemoEvaluationManager


def test_demo_evaluation_success():
    """Verify that evaluating demonstration outputs successfully calculates correct metrics and packages results."""
    manager = SAGEDemoEvaluationManager(output_path="evidence_capture/demo_evaluation_evidence.json")

    mock_scenario_run = {
        "launcher_result": {
            "experience_result": {
                "workflow_payload": {
                    "human_checkpoint": {
                        "status": "APPROVED",
                    }
                }
            }
        }
    }

    eval_result = manager.evaluate_demonstration_outputs(
        scenario_id="scenario_stress_recovery",
        simulated_scenario_output=mock_scenario_run,
    )

    assert eval_result["scenario_id"] == "scenario_stress_recovery"
    assert "evaluation_checksum" in eval_result
    assert eval_result["evaluation_metrics"]["boundary_integrity_score"] == 100.0
    assert eval_result["evaluation_metrics"]["boundary_violations_prevented"] == 3
    assert eval_result["evaluation_metrics"]["divergence_recovery_status"] == "RECOVERED_SUCCESS"
    assert "SAGE EVALUATION SUMMARY" in eval_result["measurable_outcome_summary"]

    # Export evidence and verify file structure
    path = manager.export_evaluation_evidence()
    assert path == "evidence_capture/demo_evaluation_evidence.json"
    assert os.path.exists(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["scenario_id"] == "scenario_stress_recovery"
    assert data["readability_display"]["trace_readable_formatting"] == "enabled"


def test_demo_evaluation_unexecuted_export():
    """Verify error on attempting to export evaluation evidence before any run has executed."""
    manager = SAGEDemoEvaluationManager()
    with pytest.raises(ValueError, match="No evaluations have been run yet"):
        manager.export_experience_evidence = manager.export_evaluation_evidence()
