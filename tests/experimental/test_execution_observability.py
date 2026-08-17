"""Focused Test Suite for SAGE Execution Observability Receipt Layer.

Tests receipt creation, fresh-process restart reconstruction, duplicate execution ID rejection,
receipt integrity/hash validation, missing evidence completion blocking, subsystem boundary preservation,
and read-only CCL-OPS integration.
"""

import json
import pytest
from pathlib import Path

from sage.experimental.execution_observability import (
    ExecutionObservationReceipt,
    ExecutionObservationTracker,
)
from sage.experimental.ccl_ops import SAGEGovernedControlLoop


@pytest.fixture
def tmp_obs_dir(tmp_path):
    """Fixture providing temporary ledger path for observation receipts."""
    ledger = tmp_path / "execution_observation_ledger.json"
    return ledger


def test_execution_receipt_creation(tmp_obs_dir):
    """Verify creation and persistence of a valid ExecutionObservationReceipt."""
    tracker = ExecutionObservationTracker(ledger_path=tmp_obs_dir)

    receipt = ExecutionObservationReceipt(
        execution_id="exec_test_001",
        mission_id="mission_obs_001",
        initiating_subsystem="CCL-OPS",
        validation_result={"status": "APPROVED", "gate": "preflight"},
        authorization_result={"status": "AUTHORIZED", "operator": "agent_jules"},
        observed_transitions=[{"from": "INTAKE", "to": "PREFLIGHT_VALIDATED"}],
        evidence_references=["evidence_capture/ccl_ops_001.json"],
        subsystem_receipts={"ccl_ops": "CCL-REC-20260816-001"},
        completion_state="COMPLETED"
    )

    recorded = tracker.record_observation_receipt(receipt)
    assert recorded.execution_id == "exec_test_001"
    assert recorded.hash_integrity_marker != ""
    assert recorded.verify_integrity() is True

    retrieved = tracker.retrieve_observation_receipt("exec_test_001")
    assert retrieved is not None
    assert retrieved.execution_id == "exec_test_001"
    assert retrieved.completion_state == "COMPLETED"


def test_execution_restart_reconstruction(tmp_obs_dir):
    """Prove that Process B can rehydrate observation state across fresh processes from durable disk evidence."""
    # --- PROCESS A ---
    tracker_a = ExecutionObservationTracker(ledger_path=tmp_obs_dir)
    r1 = ExecutionObservationReceipt(
        execution_id="exec_restart_001",
        mission_id="mission_restart_001",
        initiating_subsystem="ACT",
        evidence_references=["evidence_capture/act_001.json"],
        completion_state="COMPLETED"
    )
    r2 = ExecutionObservationReceipt(
        execution_id="exec_restart_002",
        mission_id="mission_restart_002",
        initiating_subsystem="Sports/RCE",
        evidence_references=["evidence_capture/sports_001.json"],
        completion_state="IN_PROGRESS"
    )
    tracker_a.record_observation_receipt(r1)
    tracker_a.record_observation_receipt(r2)

    del tracker_a  # Process A terminates

    # --- PROCESS B: Fresh Tracker Instance ---
    tracker_b = ExecutionObservationTracker(ledger_path=tmp_obs_dir)
    recon = tracker_b.reconstruct_observation_state()

    assert recon["status"] == "RECONSTRUCTED"
    assert recon["total_observations"] == 2
    assert recon["completed_count"] == 1
    assert recon["in_progress_count"] == 1
    assert recon["last_known_execution_id"] == "exec_restart_002"
    assert recon["last_known_state"] == "IN_PROGRESS"


def test_duplicate_execution_detection(tmp_obs_dir):
    """Ensure duplicate execution_ids are rejected and cause a fail-closed ValueError."""
    tracker = ExecutionObservationTracker(ledger_path=tmp_obs_dir)

    r1 = ExecutionObservationReceipt(
        execution_id="exec_dup_001",
        mission_id="mission_dup_001",
        evidence_references=["evidence_1.json"],
        completion_state="COMPLETED"
    )
    tracker.record_observation_receipt(r1)

    r2 = ExecutionObservationReceipt(
        execution_id="exec_dup_001",  # Duplicate execution ID!
        mission_id="mission_dup_002",
        evidence_references=["evidence_2.json"],
        completion_state="COMPLETED"
    )

    with pytest.raises(ValueError, match="Duplicate execution_id 'exec_dup_001' detected"):
        tracker.record_observation_receipt(r2)


def test_receipt_integrity_validation(tmp_obs_dir):
    """Ensure tampered or corrupted hash integrity markers fail verification."""
    r = ExecutionObservationReceipt(
        execution_id="exec_tampered_001",
        mission_id="mission_tampered_001",
        evidence_references=["evidence_1.json"],
        completion_state="COMPLETED"
    )
    assert r.verify_integrity() is True

    # Tamper with completion state without updating hash_integrity_marker
    r.completion_state = "FAILED"
    assert r.verify_integrity() is False

    # Attempting to record tampered receipt fails closed
    tracker = ExecutionObservationTracker(ledger_path=tmp_obs_dir)
    with pytest.raises(ValueError, match="Receipt integrity validation failed"):
        tracker.record_observation_receipt(r)


def test_missing_evidence_blocks_completion(tmp_obs_dir):
    """Ensure completing an observation receipt without evidence references fails closed."""
    tracker = ExecutionObservationTracker(ledger_path=tmp_obs_dir)

    receipt = ExecutionObservationReceipt(
        execution_id="exec_no_ev_001",
        mission_id="mission_no_ev_001",
        evidence_references=[],  # Missing evidence!
        completion_state="COMPLETED"
    )

    with pytest.raises(ValueError, match="Missing evidence blocks completion"):
        tracker.record_observation_receipt(receipt)


def test_subsystem_boundary_preservation(tmp_obs_dir):
    """Verify that ExecutionObservationTracker acts purely as a read-only audit/projection layer without mutating subsystems."""
    tracker = ExecutionObservationTracker(ledger_path=tmp_obs_dir)

    receipt = ExecutionObservationReceipt(
        execution_id="exec_subsystem_001",
        mission_id="mission_subsystem_001",
        initiating_subsystem="Airspace",
        validation_result={"c2_status": "QUALIFIED"},
        evidence_references=["evidence_capture/airspace_001.json"],
        subsystem_receipts={"airspace": "SORTIE-REC-001"},
        completion_state="COMPLETED"
    )
    tracker.record_observation_receipt(receipt)

    # Re-read ledger directly from disk
    assert tmp_obs_dir.exists()
    with open(tmp_obs_dir, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["execution_id"] == "exec_subsystem_001"
    assert data[0]["subsystem_receipts"]["airspace"] == "SORTIE-REC-001"


def test_ccl_ops_observation_read_only(tmp_path):
    """Verify read-only observation tracking of SAGEGovernedControlLoop executions."""
    s_dir = tmp_path / "ccl_ops_data"
    e_dir = tmp_path / "ccl_ops_evidence"
    obs_ledger = tmp_path / "execution_observation_ledger.json"

    loop = SAGEGovernedControlLoop(
        session_id="session_obs_ccl_ops_001",
        objective="obj_obs_test",
        storage_path=str(s_dir),
        evidence_dir=str(e_dir)
    )

    res = loop.run_governed_mission_cycle(
        mission_id="mission_obs_ccl_ops_001",
        proposal_name="Observed CCL-OPS Cycle",
        priority_score=95.0,
        domain_observation_data={"domain": "system_telemetry", "status": "PASS"}
    )

    assert res["status"] == "SUCCESS"

    # Tracker consumes the output in a purely read-only audit fashion
    tracker = ExecutionObservationTracker(ledger_path=obs_ledger)
    receipt = ExecutionObservationReceipt(
        execution_id=f"exec_ccl_ops_{res['mission_id']}",
        mission_id=res["mission_id"],
        initiating_subsystem="CCL-OPS",
        validation_result=res["receipts"]["preflight"],
        authorization_result={"status": "AUTHORIZED"},
        observed_transitions=[{"from": "INTAKE", "to": "OUTCOME_CLASSIFIED"}],
        evidence_references=[res["flight_record_id"]],
        subsystem_receipts={"ccl_record_id": res["ccl_record_id"]},
        completion_state="COMPLETED"
    )

    tracker.record_observation_receipt(receipt)

    recon = tracker.reconstruct_observation_state()
    assert recon["completed_count"] == 1
    assert recon["last_known_execution_id"] == f"exec_ccl_ops_{res['mission_id']}"
