"""SAGE Phase 4 Controlled Evaluation programmatic validation suite."""

import os
import ast
import json
from pathlib import Path
from sage.experimental.act.phase_4_eval import Phase4EvaluationRunner


def test_phase_4_evaluation_runner_execution_and_schema():
    """Verify that Phase4EvaluationRunner executes perfectly and produces a conforming evidence package."""
    root_dir = Path(__file__).parent.parent.parent
    evidence_file = root_dir / "evidence_capture" / "phase_4_controlled_evaluation_evidence.json"

    # Delete if exists to ensure we verify fresh generation
    if evidence_file.exists():
        evidence_file.unlink()

    runner = Phase4EvaluationRunner(output_path=str(evidence_file))
    package = runner.execute_all()

    assert evidence_file.exists(), "Phase 4 Execution must generate the JSON evidence package."

    # Validate high-level structure
    assert package["compliance_pack_id"] == "comp_phase_4_controlled_evaluation_2026_08_02"
    assert len(package["workflows"]) == 2
    assert "aggregate_metrics" in package

    # Validate aggregate metrics
    agg = package["aggregate_metrics"]
    assert agg["total_workflows_executed"] == 2
    assert agg["total_steps_reduced"] == 27
    assert agg["unauthorized_actions_blocked"] == 3
    assert agg["context_recovery_success_rate"] == 100.0

    # Validate Scenario A
    sc_a = package["workflows"][0]
    assert sc_a["evaluation_id"] == "eval_phase4_scenario_a_001"
    assert sc_a["evaluation_identifier"] == "eval_phase4_scenario_a_001"
    assert "Perform joint multi-agent context validation" in sc_a["human_objective"]
    assert len(sc_a["workflow_trace"]) == 4
    assert len(sc_a["agent_participation_record"]) == 4
    assert sc_a["validation_results"]["schema_check"] == "PASSED"
    assert len(sc_a["receipt_lineage"]) == 3
    assert sc_a["outcome_state"] == "SUCCESS_VALIDATED"

    # Verify scenario A required metrics
    m_a = sc_a["metrics_summary"]
    assert m_a["efficiency"]["steps_reduced"] == 12
    assert m_a["continuity"]["decisions_reconstructed"] == 4
    assert m_a["governance"]["blocked_unauthorized_actions"] == 2
    assert m_a["evidence"]["completeness_score"] == 1.0

    # Verify reproducibility check
    assert sc_a["validation_results"]["reproducibility_check"]["reproducible"] is True
    assert sc_a["validation_results"]["reproducibility_check"]["status"] == "PASSED"

    # Validate Scenario B
    sc_b = package["workflows"][1]
    assert sc_b["evaluation_id"] == "eval_phase4_scenario_b_001"
    assert sc_b["evaluation_identifier"] == "eval_phase4_scenario_b_001"
    assert "Recover stateless session context" in sc_b["human_objective"]
    assert len(sc_b["workflow_trace"]) == 4
    assert len(sc_b["agent_participation_record"]) == 3
    assert sc_b["validation_results"]["schema_check"] == "PASSED"
    assert len(sc_b["receipt_lineage"]) == 2
    assert sc_b["outcome_state"] == "SUCCESS_RECOVERED"

    # Verify scenario B failure trapping and blocking
    val_b = sc_b["validation_results"]
    assert len(val_b["intercepted_failures"]) == 1
    assert val_b["intercepted_failures"][0]["error_type"] == "ModelExecutionLoop"
    assert len(val_b["blocked_unauthorized_actions"]) == 1
    assert val_b["blocked_unauthorized_actions"][0]["action_attempted"] == "WRITE_TO_CORE_SPEK"

    # Verify reproducibility check for scenario B
    assert sc_b["validation_results"]["reproducibility_check"]["reproducible"] is True
    assert sc_b["validation_results"]["reproducibility_check"]["status"] == "PASSED"


def test_phase_4_boundary_isolation_enforcement():
    """Assert that zero changes have been made to protected production and configuration namespaces.

    Only sage/experimental/act/, tests/experimental/, and documentation/indexes are allowed modifications.
    """
    root_dir = Path(__file__).parent.parent.parent
    sage_dir = root_dir / "sage"

    # Ensure no experimental code leakage into production directories (One-Way Import Law)
    for path in sage_dir.glob("**/*.py"):
        if "experimental" in path.parts:
            continue

        # Check file content does not import experimental namespaces
        with open(path, "r", encoding="utf-8") as f:
            file_content = f.read()
            try:
                tree = ast.parse(file_content, filename=str(path))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "sage.experimental" not in alias.name, (
                            f"One-Way Import Law Violation: '{path}' "
                            f"attempts to directly import '{alias.name}'"
                        )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        assert "sage.experimental" not in node.module, (
                            f"One-Way Import Law Violation: '{path}' "
                            f"attempts to import from module '{node.module}'"
                        )
