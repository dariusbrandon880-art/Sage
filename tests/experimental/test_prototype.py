import pytest
from sage.experimental.act.prototype import PrototypeOrchestratorRunner, PrototypeMetricsCollector

def test_prototype_metrics_collector():
    """Verify that PrototypeMetricsCollector registers and outputs all four metric domains correctly."""
    collector = PrototypeMetricsCollector()
    summary = collector.get_summary()

    # Check that all domains exist in the summary
    assert "efficiency" in summary
    assert "continuity" in summary
    assert "governance" in summary
    assert "quality" in summary

    # Record test metrics
    collector.record_efficiency(assisted_duration=1.5, restoration_time=0.1, acceleration_ratio=80.0)
    collector.record_continuity(context_recovered=True, restored_count=5, reconstruction_avoided=True, refs_preserved=3)
    collector.record_governance(checks_completed=4, approval_points=2, unauthorized_blocked=1, boundary_maintained=True)
    collector.record_quality(completeness=1.0, traceability=True, clarity="EXCELLENT", eval_score=9.5)

    updated = collector.get_summary()
    assert updated["efficiency"]["sage_assisted_workflow_duration_sec"] == 1.5
    assert updated["continuity"]["previous_decisions_restored_count"] == 5
    assert updated["governance"]["validation_checks_completed"] == 4
    assert updated["quality"]["review_clarity_rating"] == "EXCELLENT"


def test_prototype_orchestrator_runner_success_flow():
    """Verify that PrototypeOrchestratorRunner executes the success flow perfectly."""
    runner = PrototypeOrchestratorRunner(session_id="session_demonstration_01")
    assert runner.state == "initialized"

    human_obj = "Compile all governance specifications and generate a synchronization report."
    evidence_pack = runner.execute_workflow(
        human_objective=human_obj,
        historical_context_id="context_historical_baseline_01"
    )

    # State should now be pending approval
    assert runner.state == "pending_human_approval"

    # Confirm required top-level keys are present in evidence package
    assert "execution_identity" in evidence_pack
    assert "session_id" in evidence_pack
    assert "intake_record" in evidence_pack
    assert "agent_participation_records" in evidence_pack
    assert "validation_results" in evidence_pack
    assert "receipt_lineage" in evidence_pack
    assert "decision_checkpoints" in evidence_pack
    assert "output_artifact_reference" in evidence_pack
    assert "metrics_record" in evidence_pack

    # Confirm correct agent participation roles are recorded
    participation = evidence_pack["agent_participation_records"]
    roles = {record["role"] for record in participation}
    assert "Coordinator" in roles
    assert "Research" in roles
    assert "Engineering" in roles
    assert "Reviewer" in roles
    assert "Documentation" in roles

    # Confirm validation checks status
    assert len(evidence_pack["validation_results"]) == 4
    for check in evidence_pack["validation_results"]:
        assert check["status"] == "PASSED"

    # Try triggering human checkpoint gate with valid signature
    assert runner.trigger_human_checkpoint(signature="sig_human_supervisor_01_approved") is True
    assert runner.state == "completed_and_frozen"
    assert "human_approval_checkpoint" in runner.evidence_package
    assert runner.evidence_package["human_approval_checkpoint"]["status"] == "APPROVED_BY_HUMAN"


def test_prototype_orchestrator_runner_invalid_signature():
    """Verify that PrototypeOrchestratorRunner rejects invalid supervisor signatures."""
    runner = PrototypeOrchestratorRunner(session_id="session_demonstration_02")
    runner.execute_workflow(human_objective="Some task objective")

    with pytest.raises(ValueError, match="Invalid human supervisor signature key"):
        runner.trigger_human_checkpoint(signature="")

    with pytest.raises(ValueError, match="Invalid human supervisor signature key"):
        runner.trigger_human_checkpoint(signature="short")


def test_prototype_orchestrator_runner_invalid_state_transition():
    """Verify that PrototypeOrchestratorRunner raises value error on out-of-order transitions."""
    runner = PrototypeOrchestratorRunner(session_id="session_demonstration_03")
    with pytest.raises(ValueError, match="cannot trigger human checkpoint"):
        runner.trigger_human_checkpoint(signature="sig_supervisor_01")
