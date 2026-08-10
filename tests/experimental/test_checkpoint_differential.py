"""Focused differential test suite for SAGE CheckpointManager and DeveloperWorkflowOrchestrator."""

import json
from pathlib import Path
import pytest

from sage.acr.session.checkpoint import CheckpointManager, ContinuityCheckpoint
from sage.acr.session.session_state import SessionState
from sage.experimental.act.continuity_control import (
    DeveloperWorkflowOrchestrator,
    ContinuityControlLoop,
    SessionStateManager,
    SAGEMissionTask
)


def test_checkpoint_differential_analysis(tmp_path):
    """Differential Test proving whether SAGE Checkpoint Manager has an emergent effect or stronger existing capability.

    Case A: Execution without Checkpoint Consumption.
    Case B: Checkpoint Operation Alone (Save & Reload).
    Case C: Execution + Checkpoint + Consumer Continuation.
    Negative Path: Real failure + Rollback Recovery.
    """
    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_feedback.json"

    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    # Setup orchestrator
    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_diff_test",
        objective="obj_diff_test",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # --- CASE A: Execution without Checkpoint Consumption ---
    task_a = SAGEMissionTask(
        task_id="task_a_execution",
        objective_id="obj_diff_test",
        priority_score=50.0,
        authorized=True,
        description="Task A execution"
    )
    orchestrator.mission_queue.add_task(task_a)

    # Execute orchestrator loop once
    res_exec = orchestrator.execute_autonomous_mission_loop(max_cycles=1)
    assert "task_a_execution" in orchestrator.session.completed_actions
    assert task_a.status == "COMPLETED"

    checkpoint_id_a = orchestrator.loop_state["last_checkpoint_id"]
    assert checkpoint_id_a is not None

    # Save Case A metrics
    state_a = orchestrator.session.model_dump()

    # --- CASE B: Checkpoint Operation Alone (Save & Reload) ---
    checkpoint = orchestrator.checkpoint_manager.retrieve_checkpoint(checkpoint_id_a)
    assert checkpoint is not None
    assert checkpoint.current_sage_state["completed_actions"] == ["task_a_execution"]

    # Verify reload on an independent process/instance of orchestrator
    orchestrator_b = DeveloperWorkflowOrchestrator(
        session_id="session_diff_test_b",
        objective="obj_diff_test",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )
    # Rehydrate session state manually from retrieved checkpoint
    orchestrator_b.session = SessionState(**checkpoint.current_sage_state)
    assert orchestrator_b.session.completed_actions == ["task_a_execution"]

    # --- CASE C: Execution + Checkpoint + Consumer Continuation ---
    # Mutate / Corrupt state to simulate dynamic failure/drift
    orchestrator.session.completed_actions = ["task_a_execution", "corrupted_action"]
    orchestrator.session_manager.save_session(orchestrator.session)

    # Consumer (Orchestrator Rollback) restores the clean state
    orchestrator.rollback_to_checkpoint(checkpoint_id_a)
    assert "corrupted_action" not in orchestrator.session.completed_actions
    assert orchestrator.session.completed_actions == ["task_a_execution"]

    # Run continuation task under reloaded state
    task_c = SAGEMissionTask(
        task_id="task_c_execution",
        objective_id="obj_diff_test",
        priority_score=60.0,
        authorized=True,
        description="Task C execution"
    )
    orchestrator.mission_queue.add_task(task_c)
    orchestrator.execute_autonomous_mission_loop(max_cycles=1)

    assert "task_c_execution" in orchestrator.session.completed_actions
    assert task_c.status == "COMPLETED"

    # Terminal state comparison
    state_c = orchestrator.session.model_dump()
    assert "task_c_execution" in state_c["completed_actions"]
    assert "task_a_execution" in state_c["completed_actions"]

    # CLASSIFICATION PROOF:
    # Restoring checkpoint state dynamically resets the session state correctly,
    # but does NOT create a new execution paradigm or different continuation behavior
    # beyond standard rollback recovery of the session fields.
    # Therefore, this represents a STRONGER EXISTING CAPABILITY, NOT an emergent capability.


def test_failure_recovery_differential(tmp_path):
    """Test standard execution failure and rollback path."""
    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_feedback.json"

    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_fail_test",
        objective="obj_fail_test",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # Pre-populate with a successful task and get its checkpoint
    task_good = SAGEMissionTask(
        task_id="task_good_execution",
        objective_id="obj_fail_test",
        priority_score=80.0,
        authorized=True,
        description="Successful task"
    )
    orchestrator.mission_queue.add_task(task_good)
    orchestrator.execute_autonomous_mission_loop(max_cycles=1)

    good_chk_id = orchestrator.loop_state["last_checkpoint_id"]
    assert good_chk_id is not None

    # Add a failing task
    task_fail = SAGEMissionTask(
        task_id="task_fail_execution",
        objective_id="obj_fail_test",
        priority_score=90.0,
        authorized=True,
        description="Inject fail"
    )
    orchestrator.mission_queue.add_task(task_fail)

    # Run loop - expect failure
    orchestrator.execute_autonomous_mission_loop(max_cycles=1)
    assert task_fail.status == "FAILED"
    assert orchestrator.loop_state["consecutive_failures"] == 1

    # Rollback to good state
    orchestrator.rollback_to_checkpoint(good_chk_id)
    assert orchestrator.session.completed_actions == ["task_good_execution"]
    # Verify that the corrupted / failed action is excluded
    assert "task_fail_execution" not in orchestrator.session.completed_actions
