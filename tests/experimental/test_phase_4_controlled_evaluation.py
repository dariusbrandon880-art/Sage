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

    # Validate Scenario B
    sc_b = package["workflows"][1]
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


def test_phase_4_execution_report_exists_and_conforms():
    """Verify that the SAGE-PHASE-4-CONTROLLED-EVALUATION-EXECUTION-REPORT.md document exists and conforms."""
    root_dir = Path(__file__).parent.parent.parent
    report_path = root_dir / "docs" / "SAGE-PHASE-4-CONTROLLED-EVALUATION-EXECUTION-REPORT.md"

    assert report_path.exists(), "The SAGE Phase 4 Execution Report must exist under docs/"
    content = report_path.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID and Classification
    assert "SAGE-PHASE-4-EXECUTION-2026-08-02" in content
    assert "Strategic Evaluation & Validation Report" in content
    assert "Validated Experimental Record" in content

    # Verify Key Required return headers
    assert "SAGE Phase 4 Controlled Evaluation Execution Report" in content
    assert "Execution Status" in content
    assert "Selected Workflow Expansion" in content
    assert "Evaluation Scenarios" in content
    assert "Components Reused" in content
    assert "New Components Added" in content
    assert "Evidence Generated" in content
    assert "Metrics Captured" in content
    assert "Governance Results" in content
    assert "Failure Validation" in content
    assert "Tests" in content
    assert "Regression Status" in content
    assert "Observed Advantages" in content
    assert "Observed Limitations" in content
    assert "Evidence Location" in content
    assert "Promotion Readiness" in content
    assert "Next Human Authorization Point" in content

    # Verify specific metrics categories
    assert "efficiency" in content_lower
    assert "continuity" in content_lower
    assert "governance" in content_lower
    assert "evidence" in content_lower


def test_phase_4_execution_report_is_indexed_correctly():
    """Verify that the Phase 4 Execution Report is registered in Main Archive/INDEX.md as VALIDATED."""
    root_dir = Path(__file__).parent.parent.parent
    index_file = root_dir / "Main Archive" / "INDEX.md"

    assert index_file.exists(), "Index file must exist in Main Archive/"
    content = index_file.read_text(encoding="utf-8")

    # Assert correct link format and state
    assert "../docs/SAGE-PHASE-4-CONTROLLED-EVALUATION-EXECUTION-REPORT.md" in content
    assert "[State: VALIDATED]" in content


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
