"""Comprehensive Test Suite for Governed Autonomous Mission Continuity.

Validates process interruption survival, durable rehydration, checkpoint integrity,
duplicate mission prevention, completed mission non-reexecution, pending task rediscovery,
authorization preservation, fail-closed corrupted checkpoint handling, and deterministic next-frontier selection.
"""

import json
import pytest
from pathlib import Path

from sage.experimental.act.continuity_control import (
    DeveloperWorkflowOrchestrator,
    SAGEMissionTask,
    ContinuityControlLoop,
)
from sage.mission_control import ExperimentalMissionState
from sage.acr.session.session_state import SessionStateManager


@pytest.fixture
def tmp_ccl_dir(tmp_path):
    """Fixture providing a clean temporary directory for SAGE-CCL persistent storage."""
    d = tmp_path / "sage_ccl_test"
    d.mkdir(parents=True, exist_ok=True)
    return d


def test_mission_continuity_process_interruption_and_restart(tmp_ccl_dir):
    """Prove that an authorized mission survives process termination and can be rehydrated and continued from fresh process memory."""
    session_id = "session_continuity_restart_001"
    objective = "obj_autonomous_mission_continuity"

    # --- PROCESS 1: Propose, authorize, enqueue, run cycle 1 ---
    ccl1 = ContinuityControlLoop(
        session_manager=SessionStateManager(storage_path=str(tmp_ccl_dir / "sessions")),
        storage_path=str(tmp_ccl_dir)
    )
    orch1 = DeveloperWorkflowOrchestrator(
        session_id=session_id,
        objective=objective,
        ccl=ccl1,
        evidence_output_path=str(tmp_ccl_dir / "evidence_1.json")
    )

    mstate = ExperimentalMissionState(
        mission_id="mission_001",
        name="Continuity Test Mission",
        current_state="EXECUTION_AUTHORIZED",
        prerequisites={"operator_signature_obtained": True},
        metadata={
            "task_id": "task_mission_001_step_1",
            "objective_id": objective,
            "priority_score": 95.0,
            "target_files": ["sage/experimental/act/continuity_control.py"]
        }
    )
    task1 = orch1.enqueue_authorized_mission_state(mstate)
    assert task1.authorized is True

    # Also enqueue Step 2
    task2 = SAGEMissionTask(
        task_id="task_mission_001_step_2",
        objective_id=objective,
        priority_score=90.0,
        authorized=True,
        description="Continuity Step 2 Workload",
        metadata={"target_files": ["sage/experimental/act/continuity_control.py"]}
    )
    orch1.mission_queue.add_task(task2)

    # Run cycle 1 (executes step 1)
    res1 = orch1.execute_autonomous_mission_loop(max_cycles=1)
    assert res1["completed_cycles"] == 1
    assert "task_mission_001_step_1" in res1["executed_tasks"]

    # SIMULATE PROCESS INTERRUPT / RESTART: drop orch1, create completely fresh orch2
    del orch1
    del ccl1

    # --- PROCESS 2: Reinitialize from disk ---
    ccl2 = ContinuityControlLoop(
        session_manager=SessionStateManager(storage_path=str(tmp_ccl_dir / "sessions")),
        storage_path=str(tmp_ccl_dir)
    )
    orch2 = DeveloperWorkflowOrchestrator(
        session_id=session_id,
        objective=objective,
        ccl=ccl2,
        evidence_output_path=str(tmp_ccl_dir / "evidence_2.json")
    )

    # Reconstruct mission state without conversation memory
    recon = orch2.reconstruct_mission_state()

    assert recon["status"] == "RECONSTRUCTED"
    assert recon["session_id"] == session_id

    # 1. WHAT WAS I DOING?
    assert recon["what_was_i_doing"]["active_task_id"] in ["task_mission_001_step_1", "task_mission_001_step_2"]

    # 2. WHAT HAS BEEN VERIFIED?
    assert "task_mission_001_step_1" in recon["what_has_been_verified"]["completed_task_ids"]
    assert recon["what_has_been_verified"]["completed_tasks_count"] >= 1
    assert recon["what_has_been_verified"]["verified_checkpoints_count"] >= 1

    # 3. WHAT REMAINS?
    assert "task_mission_001_step_2" in recon["what_remains"]["pending_authorized_task_ids"]

    # 4. WHAT AM I AUTHORIZED TO DO NEXT?
    assert recon["what_am_i_authorized_to_do_next"]["next_authorized_task_id"] == "task_mission_001_step_2"
    assert recon["what_am_i_authorized_to_do_next"]["authorization_status"] == "AUTHORIZED"

    # Continue execution in Process 2 from exact verified frontier
    res2 = orch2.execute_autonomous_mission_loop(max_cycles=1)
    assert res2["completed_cycles"] == 1
    assert "task_mission_001_step_2" in res2["executed_tasks"]

    # Re-verify after step 2 completion
    recon_final = orch2.reconstruct_mission_state()
    assert "task_mission_001_step_2" in recon_final["what_has_been_verified"]["completed_task_ids"]
    assert recon_final["what_am_i_authorized_to_do_next"]["authorization_status"] == "QUEUE_EXHAUSTED"


def test_completed_mission_non_reexecution(tmp_ccl_dir):
    """Ensure completed tasks are never accidentally re-executed upon restart."""
    session_id = "session_non_reexec_001"
    objective = "obj_autonomous_mission_continuity"

    ccl = ContinuityControlLoop(
        session_manager=SessionStateManager(storage_path=str(tmp_ccl_dir / "sessions")),
        storage_path=str(tmp_ccl_dir)
    )
    orch = DeveloperWorkflowOrchestrator(
        session_id=session_id,
        objective=objective,
        ccl=ccl
    )

    task = SAGEMissionTask(
        task_id="task_completed_once",
        objective_id=objective,
        priority_score=100.0,
        authorized=True,
        description="Single execution task",
        metadata={"target_files": ["sage/experimental/act/continuity_control.py"]}
    )
    orch.mission_queue.add_task(task)

    # Complete task
    res1 = orch.execute_autonomous_mission_loop(max_cycles=1)
    assert "task_completed_once" in res1["executed_tasks"]

    # Fresh process restart
    orch_restart = DeveloperWorkflowOrchestrator(
        session_id=session_id,
        objective=objective,
        ccl=ContinuityControlLoop(
            session_manager=SessionStateManager(storage_path=str(tmp_ccl_dir / "sessions")),
            storage_path=str(tmp_ccl_dir)
        )
    )

    recon = orch_restart.reconstruct_mission_state()
    assert "task_completed_once" in recon["what_has_been_verified"]["completed_task_ids"]
    assert recon["what_am_i_authorized_to_do_next"]["next_authorized_task_id"] is None

    # Run loop again - queue must be exhausted, no re-execution
    res2 = orch_restart.execute_autonomous_mission_loop(max_cycles=5)
    assert res2["completed_cycles"] == 0
    assert res2["terminal_reason"] == "QUEUE_EXHAUSTED"
    assert "task_completed_once" not in res2["executed_tasks"]


def test_authorization_preservation_and_unauthorized_rejection(tmp_ccl_dir):
    """Ensure unauthorized or pending tasks without authorization are rejected and remain unexecuted."""
    session_id = "session_unauthorized_001"
    objective = "obj_autonomous_mission_continuity"

    orch = DeveloperWorkflowOrchestrator(
        session_id=session_id,
        objective=objective,
        ccl=ContinuityControlLoop(
            session_manager=SessionStateManager(storage_path=str(tmp_ccl_dir / "sessions")),
            storage_path=str(tmp_ccl_dir)
        )
    )

    unauth_task = SAGEMissionTask(
        task_id="task_unauthorized_stealth",
        objective_id=objective,
        priority_score=999.0,
        authorized=False,  # NOT AUTHORIZED!
        description="Unauthorized task injection"
    )
    orch.mission_queue.add_task(unauth_task)

    recon = orch.reconstruct_mission_state()
    assert recon["what_am_i_authorized_to_do_next"]["next_authorized_task_id"] is None
    assert recon["what_am_i_authorized_to_do_next"]["authorization_status"] == "QUEUE_EXHAUSTED"

    res = orch.execute_autonomous_mission_loop(max_cycles=1)
    assert res["completed_cycles"] == 0
    assert res["terminal_reason"] == "QUEUE_EXHAUSTED"
    assert "task_unauthorized_stealth" not in res["executed_tasks"]


def test_fail_closed_on_corrupted_checkpoint(tmp_ccl_dir):
    """Ensure corrupted or tampered checkpoint files cause rehydration to fail closed."""
    session_id = "session_corrupt_chk_001"
    objective = "obj_autonomous_mission_continuity"

    ccl = ContinuityControlLoop(
        session_manager=SessionStateManager(storage_path=str(tmp_ccl_dir / "sessions")),
        storage_path=str(tmp_ccl_dir)
    )
    orch = DeveloperWorkflowOrchestrator(
        session_id=session_id,
        objective=objective,
        ccl=ccl
    )

    # Create a valid checkpoint
    chk = orch.checkpoint_manager.create_checkpoint(
        current_sage_state=orch.session.model_dump(),
        active_goals=[objective],
        recent_decisions=[],
        validation_status={"status": "INITIAL"}
    )

    # Corrupt the checkpoint file on disk
    corrupt_file = tmp_ccl_dir / "checkpoints" / f"{chk.id}.json"
    with open(corrupt_file, "w") as f:
        f.write("{ INVALID JSON payload ...")

    # Reconstruct should raise ValueError due to corruption
    orch_restart = DeveloperWorkflowOrchestrator(
        session_id=session_id,
        objective=objective,
        ccl=ContinuityControlLoop(
            session_manager=SessionStateManager(storage_path=str(tmp_ccl_dir / "sessions")),
            storage_path=str(tmp_ccl_dir)
        )
    )

    with pytest.raises(ValueError, match="Corrupted checkpoint detected"):
        orch_restart.reconstruct_mission_state()

    # Loop mode must be updated to MANUAL_INTERVENTION_PAUSED
    assert orch_restart.loop_state["mode"] == "MANUAL_INTERVENTION_PAUSED"


def test_deterministic_next_frontier_selection_across_priorities(tmp_ccl_dir):
    """Verify that next frontier selection is strictly deterministic based on priority score and timestamp across restarts."""
    session_id = "session_frontier_priority_001"
    objective = "obj_autonomous_mission_continuity"

    orch = DeveloperWorkflowOrchestrator(
        session_id=session_id,
        objective=objective,
        ccl=ContinuityControlLoop(
            session_manager=SessionStateManager(storage_path=str(tmp_ccl_dir / "sessions")),
            storage_path=str(tmp_ccl_dir)
        )
    )

    task_low = SAGEMissionTask(
        task_id="task_priority_50",
        objective_id=objective,
        priority_score=50.0,
        authorized=True,
        description="Low priority"
    )
    task_high = SAGEMissionTask(
        task_id="task_priority_90",
        objective_id=objective,
        priority_score=90.0,
        authorized=True,
        description="High priority"
    )
    task_med = SAGEMissionTask(
        task_id="task_priority_75",
        objective_id=objective,
        priority_score=75.0,
        authorized=True,
        description="Medium priority"
    )

    orch.mission_queue.add_task(task_low)
    orch.mission_queue.add_task(task_high)
    orch.mission_queue.add_task(task_med)

    # Process restart
    orch_restart = DeveloperWorkflowOrchestrator(
        session_id=session_id,
        objective=objective,
        ccl=ContinuityControlLoop(
            session_manager=SessionStateManager(storage_path=str(tmp_ccl_dir / "sessions")),
            storage_path=str(tmp_ccl_dir)
        )
    )

    recon = orch_restart.reconstruct_mission_state()
    # High priority task (score 90) must be selected as next authorized frontier
    assert recon["what_am_i_authorized_to_do_next"]["next_authorized_task_id"] == "task_priority_90"
