"""Focused Test Suite for SAGE-CCL-OPS Control Loop Integration.

Tests the full 9-stage target chain:
MISSION INTAKE -> PREFLIGHT VALIDATION -> AUTHORIZED EXECUTION -> CONTINUITY STATE
-> DOMAIN OBSERVATION -> EVIDENCE CAPTURE -> VERIFIED RESULT -> PROGRESSION UPDATE -> LONGITUDINAL MEMORY

Plus process restart reconstruction, duplicate prevention, unauthorized rejection, and fail-closed behavior.
"""

import json
import pytest
from pathlib import Path

from sage.experimental.ccl_ops import SAGEGovernedControlLoop
from sage.experimental.act.continuity_control import SAGEMissionTask


@pytest.fixture
def tmp_ccl_ops_dir(tmp_path):
    """Fixture providing temporary directories for SAGE-CCL-OPS storage and evidence."""
    s_dir = tmp_path / "ccl_ops_data"
    e_dir = tmp_path / "ccl_ops_evidence"
    s_dir.mkdir(parents=True, exist_ok=True)
    e_dir.mkdir(parents=True, exist_ok=True)
    return s_dir, e_dir


def test_ccl_ops_full_chain_execution(tmp_ccl_ops_dir):
    """Verify that SAGEGovernedControlLoop completes the full 9-stage operating chain cleanly."""
    s_dir, e_dir = tmp_ccl_ops_dir
    session_id = "session_ccl_ops_test_001"

    loop = SAGEGovernedControlLoop(
        session_id=session_id,
        objective="obj_test_full_chain",
        storage_path=str(s_dir),
        evidence_dir=str(e_dir)
    )

    res = loop.run_governed_mission_cycle(
        mission_id="mission_ops_001",
        proposal_name="Full Operating Chain Proof Mission",
        priority_score=95.0,
        domain_observation_data={
            "domain": "sports_rce",
            "prediction_id": "pred_rce_test_001",
            "selection": "HOME_WIN",
            "predicted_probability": 0.70
        }
    )

    assert res["status"] == "SUCCESS"
    assert res["mission_id"] == "mission_ops_001"
    assert res["checkpoints"]["pre_execution"].startswith("chk_")
    assert res["checkpoints"]["post_execution"].startswith("chk_")
    assert res["receipts"]["intake"]["next_state"] == "INTAKE"
    assert res["receipts"]["preflight"]["next_state"] == "PREFLIGHT_VALIDATED"
    assert res["receipts"]["outcome"]["next_state"] == "OUTCOME_CLASSIFIED"
    assert res["ccl_record_id"].startswith("CCL-REC-")
    assert res["flight_record_id"].startswith("REC-")


def test_ccl_ops_process_restart_recovery(tmp_ccl_ops_dir):
    """Prove that Process B can rehydrate state, identify current frontier, and preserve authorization after Process A completes work."""
    s_dir, e_dir = tmp_ccl_ops_dir
    session_id = "session_ccl_ops_restart_001"

    # --- PROCESS A ---
    loop_a = SAGEGovernedControlLoop(
        session_id=session_id,
        objective="obj_test_restart",
        storage_path=str(s_dir),
        evidence_dir=str(e_dir)
    )
    res_a = loop_a.run_governed_mission_cycle(
        mission_id="mission_ops_step_1",
        proposal_name="Step 1 Mission",
        priority_score=90.0,
        domain_observation_data={"domain": "system_telemetry", "status": "STEP_1_DONE"}
    )
    assert res_a["status"] == "SUCCESS"

    # Enqueue a second pending task
    task_2 = SAGEMissionTask(
        task_id="task_mission_ops_step_2",
        objective_id="obj_test_restart",
        priority_score=80.0,
        authorized=True,
        description="Step 2 Mission"
    )
    loop_a.orchestrator.mission_queue.add_task(task_2)

    # Terminate Process A
    del loop_a

    # --- PROCESS B: Fresh instance ---
    loop_b = SAGEGovernedControlLoop(
        session_id=session_id,
        objective="obj_test_restart",
        storage_path=str(s_dir),
        evidence_dir=str(e_dir)
    )

    recon = loop_b.reconstruct_operational_state()

    assert recon["status"] == "RECONSTRUCTED"
    assert recon["session_id"] == session_id

    # Verify answers to 4 core questions
    assert "task_mission_ops_step_1" in recon["what_has_been_verified"]["completed_task_ids"]
    assert "task_mission_ops_step_2" in recon["what_remains"]["pending_authorized_task_ids"]
    assert recon["what_am_i_authorized_to_do_next"]["next_authorized_task_id"] == "task_mission_ops_step_2"
    assert recon["what_am_i_authorized_to_do_next"]["authorization_status"] == "AUTHORIZED"


def test_ccl_ops_duplicate_and_completed_non_reexecution(tmp_ccl_ops_dir):
    """Ensure completed missions are never accidentally re-executed upon restart."""
    s_dir, e_dir = tmp_ccl_ops_dir
    session_id = "session_ccl_ops_no_reexec_001"

    loop = SAGEGovernedControlLoop(
        session_id=session_id,
        objective="obj_test_no_reexec",
        storage_path=str(s_dir),
        evidence_dir=str(e_dir)
    )

    loop.run_governed_mission_cycle(
        mission_id="mission_once_only",
        proposal_name="Run Once Mission",
        priority_score=100.0,
        domain_observation_data={"domain": "system_telemetry", "status": "DONE"}
    )

    # Rehydrate in fresh process
    loop_restart = SAGEGovernedControlLoop(
        session_id=session_id,
        objective="obj_test_no_reexec",
        storage_path=str(s_dir),
        evidence_dir=str(e_dir)
    )

    recon = loop_restart.reconstruct_operational_state()
    assert "task_mission_once_only" in recon["what_has_been_verified"]["completed_task_ids"]
    assert recon["what_am_i_authorized_to_do_next"]["next_authorized_task_id"] is None
    assert recon["what_am_i_authorized_to_do_next"]["authorization_status"] == "QUEUE_EXHAUSTED"


def test_ccl_ops_unauthorized_rejection(tmp_ccl_ops_dir):
    """Ensure invalid or unauthorized mission enqueues fail closed."""
    s_dir, e_dir = tmp_ccl_ops_dir
    session_id = "session_ccl_ops_unauth_001"

    loop = SAGEGovernedControlLoop(
        session_id=session_id,
        objective="obj_test_unauth",
        storage_path=str(s_dir),
        evidence_dir=str(e_dir)
    )

    from sage.mission_control import ExperimentalMissionState
    unauth_state = ExperimentalMissionState(
        mission_id="mission_unauth_001",
        name="Unauthorized Attempt",
        current_state="MISSION_PROPOSED",  # NOT EXECUTION_AUTHORIZED!
        prerequisites={}
    )

    with pytest.raises(PermissionError, match="Cannot enqueue mission state"):
        loop.orchestrator.enqueue_authorized_mission_state(unauth_state)


def test_ccl_ops_fail_closed_corrupted_state(tmp_ccl_ops_dir):
    """Ensure corrupted checkpoints fail closed during operational state reconstruction."""
    s_dir, e_dir = tmp_ccl_ops_dir
    session_id = "session_ccl_ops_corrupt_001"

    loop = SAGEGovernedControlLoop(
        session_id=session_id,
        objective="obj_test_corrupt",
        storage_path=str(s_dir),
        evidence_dir=str(e_dir)
    )

    # Create a checkpoint
    chk = loop.orchestrator.checkpoint_manager.create_checkpoint(
        current_sage_state=loop.session.model_dump(),
        active_goals=["obj_test_corrupt"],
        recent_decisions=[],
        validation_status={"status": "INITIAL"}
    )

    # Corrupt the checkpoint file
    corrupt_path = s_dir / "ccl" / "checkpoints" / f"{chk.id}.json"
    with open(corrupt_path, "w") as f:
        f.write("{ INVALID JSON DATA ...")

    loop_restart = SAGEGovernedControlLoop(
        session_id=session_id,
        objective="obj_test_corrupt",
        storage_path=str(s_dir),
        evidence_dir=str(e_dir)
    )

    with pytest.raises(ValueError, match="Corrupted checkpoint detected"):
        loop_restart.reconstruct_operational_state()
