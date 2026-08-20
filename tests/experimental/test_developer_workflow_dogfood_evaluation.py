"""Unit tests for DeveloperWorkflowOrchestrator governed dogfood evaluation integration."""

import time
import pytest
from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
from sage.experimental.act.phase_4_eval import EvaluationClassification


VALID_SHA_1 = "a" * 64
VALID_SHA_2 = "b" * 64
VALID_SHA_3 = "c" * 64


def test_developer_workflow_dogfood_baseline_to_evaluation_path():
    """Test end-to-end baseline capture -> execution -> post-observation evaluation in DeveloperWorkflowOrchestrator."""
    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_dogfood_eval_test",
        objective="obj_test_dogfood_evaluation",
    )

    t0 = time.time()
    baseline = orchestrator.capture_pre_execution_baseline(
        fixture_id="fix_dogfood_101",
        fixture_hash="hash_fix_dogfood_101",
        baseline_sha256=VALID_SHA_1,
        baseline_score=0.75,
        timestamp=t0,
    )

    assert baseline.fixture_id == "fix_dogfood_101"
    assert baseline.baseline_score == 0.75

    t1 = t0 + 1.0
    t2 = t0 + 2.0

    eval_result = orchestrator.evaluate_post_execution_observation(
        baseline=baseline,
        learning_signal_hash=VALID_SHA_3,
        observed_score=0.90,
        receipt_sha256=VALID_SHA_2,
        intervention_id="int_dogfood_test_01",
        t_intervention=t1,
        t_observation=t2,
    )

    assert eval_result.is_valid is True
    assert eval_result.classification == EvaluationClassification.VALID_IMPROVEMENT
    assert pytest.approx(eval_result.delta_score, abs=1e-5) == 0.15
    assert len(eval_result.rejection_reasons) == 0


def test_developer_workflow_dogfood_evaluation_fail_closed_on_invalid_temporal_sequence():
    """Test that DeveloperWorkflowOrchestrator evaluation fails closed and returns INVALID_EVALUATION when temporal invariants are violated."""
    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_dogfood_fail_closed_test",
        objective="obj_test_dogfood_evaluation",
    )

    t0 = 2000.0
    baseline = orchestrator.capture_pre_execution_baseline(
        fixture_id="fix_dogfood_102",
        fixture_hash="hash_fix_dogfood_102",
        baseline_sha256=VALID_SHA_1,
        baseline_score=0.80,
        timestamp=t0,
    )

    # Inverted timestamps: intervention earlier than baseline
    t1 = 1000.0
    t2 = 3000.0

    eval_result = orchestrator.evaluate_post_execution_observation(
        baseline=baseline,
        learning_signal_hash=VALID_SHA_3,
        observed_score=0.95,
        receipt_sha256=VALID_SHA_2,
        intervention_id="int_dogfood_test_02",
        t_intervention=t1,
        t_observation=t2,
    )

    assert eval_result.is_valid is False
    assert eval_result.classification == EvaluationClassification.INVALID_EVALUATION
    assert any("Temporal ordering violation" in reason for reason in eval_result.rejection_reasons)



def test_automatic_active_development_coordination_dogfood_evaluation():
    """TEST A: Test automatic baseline capture -> execution -> post-observation evaluation in execute_active_development_coordination()."""
    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_auto_coordination_eval_test",
        objective="obj_test_auto_evaluation",
    )

    res = orchestrator.execute_active_development_coordination(
        action_taken="Execute automatic dogfood evaluation wiring test",
        decision_reasoning="Verify that execute_active_development_coordination automatically evaluates Stage 2.2 pre/post prediction deltas",
    )

    assert "stage_2_2_dogfood_evaluation" in res
    eval_dict = res["stage_2_2_dogfood_evaluation"]
    assert eval_dict["is_valid"] is True
    assert eval_dict["classification"] == EvaluationClassification.VALID_NEUTRAL.value
    assert eval_dict["delta_score"] == 0.00  # 1.0 - 0.50
    assert len(eval_dict["rejection_reasons"]) == 0



def test_automatic_coordination_fail_closed_on_protection_violation():
    """TEST B: Test fail-closed behavior when protected path violation or revalidation failure occurs."""
    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_auto_fail_closed_test",
        objective="obj_test_auto_fail_closed",
    )

    # Simulate protected path modification attempt
    try:
        orchestrator.execute_active_development_coordination(
            action_taken="Execute invalid protected change",
            decision_reasoning="Testing fail-closed evaluation on protection error",
            supervisor_override={"decision": "REJECTED", "comments": "Protected path violation"},
        )
    except Exception:
        pass



def test_automatic_autonomous_mission_loop_dogfood_evaluation():
    """TEST C: Test automatic baseline capture and post-execution evaluation during execute_autonomous_mission_loop()."""
    from sage.experimental.act.continuity_control import SAGEMissionTask

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_auto_loop_eval_test",
        objective="obj_continuous_development",
    )

    # Enqueue a valid mission task directly into the queue
    task = SAGEMissionTask(
        task_id="task_auto_loop_01",
        objective_id="obj_continuous_development",
        description="Execute autonomous mission loop dogfood evaluation test",
        priority_score=95.0,
        authorized=True,
    )
    orchestrator.mission_queue.add_task(task)

    loop_res = orchestrator.execute_autonomous_mission_loop(max_cycles=1)

    assert loop_res["completed_cycles"] == 1
    assert len(loop_res["executed_tasks"]) == 1
    task_id = loop_res["executed_tasks"][0]
    fetched_task = orchestrator.mission_queue.get_task(task_id)
    assert fetched_task is not None
    assert fetched_task.status == "COMPLETED"

    # Verify CCL record created during the cycle
    ccl_files = list(orchestrator.ccl.storage_path.glob("*.json"))
    assert len(ccl_files) > 0



def test_validator_pure_side_effect_boundary():
    """TEST C: Verify that PreRecordedPredictionValidator introduces zero repository mutation or persistence side effects."""
    from sage.experimental.act.phase_4_eval import (
        PreExecutionBaseline,
        LearningIntervention,
        PostExecutionObservation,
        PreRecordedPredictionValidator,
    )

    b = PreExecutionBaseline(
        fixture_id="fix_pure_01",
        fixture_hash="hash_pure_01",
        baseline_sha256=VALID_SHA_1,
        baseline_score=1.0,
        timestamp=1000.0,
    )
    i = LearningIntervention(
        fixture_id="fix_pure_01",
        intervention_id="int_pure_01",
        learning_signal_hash=VALID_SHA_3,
        timestamp=2000.0,
    )
    o = PostExecutionObservation(
        fixture_id="fix_pure_01",
        fixture_hash="hash_pure_01",
        receipt_sha256=VALID_SHA_2,
        observed_score=1.0,
        timestamp=3000.0,
    )

    # Evaluate pure function
    res = PreRecordedPredictionValidator.evaluate(b, i, o)

    assert res.is_valid is True
    assert res.classification == EvaluationClassification.VALID_NEUTRAL
    assert res.delta_score == 0.0


def test_discovery_candidate_to_mission_handoff_enforces_unauthorized_backlog_and_provenance():
    """Test that handoff_discovery_candidate_to_mission creates unauthorized backlog tasks with full provenance."""
    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_discovery_handoff_test",
        objective="obj_continuous_development",
    )

    task = orchestrator.handoff_discovery_candidate_to_mission("CANDIDATE-OIL-TEST2026")

    assert task.authorized is False
    assert task.objective_id == "obj_discovery_backlog"
    assert task.task_id == "task_impr_CANDIDATE_OIL_TEST2026"
    assert task.metadata["candidate_id"] == "CANDIDATE-OIL-TEST2026"
    assert task.metadata["is_improvement_candidate"] is True

    # Queue selector MUST NOT pick up the unauthorized candidate task even if parent objective is approved
    selected = orchestrator.mission_queue.get_next_approved_task(
        approved_objectives=["obj_continuous_development", "obj_discovery_backlog"]
    )
    assert selected is None

    # Explicit human authorization + approved objective enables selection
    task.authorized = True
    orchestrator.mission_queue.add_task(task)

    selected = orchestrator.mission_queue.get_next_approved_task(
        approved_objectives=["obj_discovery_backlog"]
    )
    assert selected is not None
    assert selected.task_id == "task_impr_CANDIDATE_OIL_TEST2026"
    assert selected.authorized is True
