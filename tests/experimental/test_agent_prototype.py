"""Unit and Integration Tests for SAGE Governed Agent Prototype."""

import pytest
from sage.experimental.act.prototype import (
    PrototypeMetricsCollector,
    PrototypeOrchestratorRunner,
    DemoInterface,
)


def test_prototype_metrics_collector():
    """Verify that metrics are recorded and retrieved correctly."""
    collector = PrototypeMetricsCollector()
    collector.record_metrics(
        duration=1.23456,
        contexts=5,
        duplicates=1,
        checks=7,
        evidence_score=1.0,
        checkpoints=1,
        failures=0,
    )
    report = collector.get_report()
    assert report["execution_duration_sec"] == 1.2346
    assert report["context_recovered_keys"] == 5
    assert report["duplicate_work_prevented_count"] == 1
    assert report["validation_checks_passed_count"] == 7
    assert report["evidence_completeness_score"] == 1.0
    assert report["human_review_checkpoints_hit"] == 1
    assert report["failure_conditions_encountered_count"] == 0


def test_prototype_orchestrator_success_path():
    """Verify the success path of the governed agent prototype simulation."""
    runner = PrototypeOrchestratorRunner()
    assert runner.state == "PROPOSED"

    # Run simulation
    evidence = runner.run_simulation("Summarize recent SAGE architectural decision records.")
    assert runner.state == "PAUSED_AT_GATE"
    assert evidence["review_status"] == "PENDING_HUMAN_APPROVAL"
    assert len(evidence["receipts"]) == 4

    # Ensure receipts are chained
    for i, receipt in enumerate(evidence["receipts"]):
        if i == 0:
            assert receipt["previous_hash"] == "0" * 64
        else:
            assert receipt["previous_hash"] == evidence["receipts"][i - 1]["current_hash"]

    # Record Human Decision
    final_state = runner.record_human_decision("APPROVED")
    assert runner.state == "COMPLETED"
    assert final_state["review_status"] == "HUMAN_APPROVED"


def test_prototype_orchestrator_rejection_path():
    """Verify the rejection path of the governed agent prototype simulation."""
    runner = PrototypeOrchestratorRunner()
    runner.run_simulation("Summarize duplicate files.")
    assert runner.state == "PAUSED_AT_GATE"

    final_state = runner.record_human_decision("REJECTED")
    assert runner.state == "REJECTED"
    assert final_state["review_status"] == "HUMAN_REJECTED"


def test_prototype_orchestrator_invalid_transition():
    """Verify lifecycle violation checks are properly enforced."""
    runner = PrototypeOrchestratorRunner()
    with pytest.raises(ValueError, match="Lifecycle Violation"):
        runner.record_human_decision("APPROVED")


def test_demo_interface_execution():
    """Verify that the demo interface returns a valid, formatted report."""
    demo = DemoInterface()
    report = demo.run_demo("Retrieve SAGE context summary", auto_approve=True)
    assert "SAGE Governed Agent Prototype Run Report" in report
    assert "Chained Receipt Provenance Lineage" in report
    assert "agent_coordinator_chatgpt" in report


# ==========================================
# PHASE 2: VALIDATION AND SCENARIO EXPANSION
# ==========================================

def test_scenario_a_context_restoration():
    """Verify SCENARIO_A: Context Restoration execution and recovery of references."""
    runner = PrototypeOrchestratorRunner()
    evidence = runner.run_validation_scenario(
        scenario_id="SCENARIO_A",
        human_objective="Recover 2-5 year strategic planning contexts."
    )
    assert evidence["scenario_id"] == "SCENARIO_A"
    assert evidence["metrics"]["context_recovered_keys"] == 5
    assert len(evidence["receipts"]) == 4


def test_scenario_b_research_acceleration():
    """Verify SCENARIO_B: Research Acceleration and task delegation checkpoints."""
    runner = PrototypeOrchestratorRunner()
    evidence = runner.run_validation_scenario(
        scenario_id="SCENARIO_B",
        human_objective="Accelerate background research on SAML IDPs."
    )
    assert evidence["scenario_id"] == "SCENARIO_B"
    assert len(evidence["receipts"]) == 4


def test_scenario_c_engineering_workflow_support():
    """Verify SCENARIO_C: Engineering Workflow Support and validation outputs."""
    runner = PrototypeOrchestratorRunner()
    evidence = runner.run_validation_scenario(
        scenario_id="SCENARIO_C",
        human_objective="Investigate repository preflight test issues."
    )
    assert evidence["scenario_id"] == "SCENARIO_C"
    assert len(evidence["receipts"]) == 4


# ==========================================
# PHASE 2: FAILURE TESTING AND REJECTIONS
# ==========================================

def test_failure_invalid_agent_identity():
    """Verify correct fail-closed blocking of invalid agent identities."""
    runner = PrototypeOrchestratorRunner()
    with pytest.raises(ValueError, match="Invalid identity format"):
        runner.run_validation_scenario(
            scenario_id="SCENARIO_A",
            human_objective="Standard objective",
            inject_failure="invalid_agent_identity"
        )
    assert runner.state == "REJECT_CLOSED"
    assert runner.metrics_collector.get_report()["failure_conditions_encountered_count"] == 1


def test_failure_permission_violation_attempt():
    """Verify correct fail-closed blocking of unauthorized capability token requests."""
    runner = PrototypeOrchestratorRunner()
    with pytest.raises(PermissionError, match="Unauthorized capability format"):
        runner.run_validation_scenario(
            scenario_id="SCENARIO_A",
            human_objective="Standard objective",
            inject_failure="permission_violation_attempt"
        )
    assert runner.state == "REJECT_CLOSED"


def test_failure_missing_evidence():
    """Verify correct fail-closed blocking of envelopes with missing evidence/timestamps."""
    runner = PrototypeOrchestratorRunner()
    with pytest.raises(ValueError, match="Missing evidence chains"):
        runner.run_validation_scenario(
            scenario_id="SCENARIO_A",
            human_objective="Standard objective",
            inject_failure="missing_evidence"
        )
    assert runner.state == "REJECT_CLOSED"


def test_failure_duplicate_knowledge_detection():
    """Verify correct fail-closed blocking on duplicate knowledge detection."""
    runner = PrototypeOrchestratorRunner()
    with pytest.raises(ValueError, match="Duplicate work detected"):
        runner.run_validation_scenario(
            scenario_id="SCENARIO_A",
            human_objective="Standard objective",
            inject_failure="duplicate_knowledge_detection"
        )
    assert runner.state == "REJECT_CLOSED"
    assert runner.metrics_collector.get_report()["duplicate_work_prevented_count"] == 1


def test_failure_boundary_violation_attempt():
    """Verify correct fail-closed blocking on illegal core write attempts."""
    runner = PrototypeOrchestratorRunner()
    with pytest.raises(PermissionError, match="Boundary violation"):
        runner.run_validation_scenario(
            scenario_id="SCENARIO_A",
            human_objective="Standard objective",
            inject_failure="boundary_violation_attempt"
        )
    assert runner.state == "REJECT_CLOSED"
