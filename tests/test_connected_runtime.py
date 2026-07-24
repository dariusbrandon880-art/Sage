"""Comprehensive end-to-end integration tests for SAGE 2 connected runtime operations."""

import tempfile

import pytest
from fastapi.testclient import TestClient

from sage.acr.continuity_integration import RecoveryWorkflow, StateCalibrationSync
from sage.acr.skal import (
    process_incoming_payload,
    promote_skal_payload,
)
from sage.acr.state_transition import StateTransitionEngine, STPState
from sage.models import KnowledgeState
from sage.runtime import SAGERuntime


@pytest.fixture
def temp_runtime():
    """Create a clean SAGE runtime instance using a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runtime = SAGERuntime(workspace_path=tmpdir)
        runtime.start()
        yield runtime
        runtime.stop()


def test_e2e_successful_pipeline_flow(temp_runtime):
    """Test the entire integrated loop: SKAL Intake -> Validation -> Governance Promotion -> Master Archive."""
    # S0 State Setup
    temp_runtime.set_objective("Launch Mars Colony")
    temp_runtime.set_task("Calibrate thrusters")

    stp = StateTransitionEngine(temp_runtime)

    # 1. Begin mutation transaction
    tx_id = stp.begin_mutation("Approved propulsion validation report")
    transition = stp.transitions[tx_id]
    assert transition.stage == STPState.DELTA
    assert transition.from_state["current_objective"] == "Launch Mars Colony"
    assert transition.from_state["active_task"] == "Calibrate thrusters"

    # 2. Intake: Process incoming validated report
    payload_data = {
        "source": "ci-propulsion-tests",
        "timestamp": "2026-03-31T20:15:00Z",
        "commit_identifier": "prop-777",
        "validation_results": {"thruster_ratio": 1.05},
        "evidence_references": ["link-to-telemetry-1"],
        "confidence_metadata": {"reps": 10},
    }
    intake_res = process_incoming_payload("validation_report", payload_data, temp_runtime)
    memory_id = intake_res["memory_id"]

    # 3. Register evidence in transaction
    stp.register_evidence(tx_id, memory_id)
    assert transition.stage == STPState.EVIDENCE
    assert memory_id in transition.evidence_ids

    # 4. Validate transition
    is_valid = stp.validate_transition(tx_id)
    assert is_valid is True
    assert transition.stage == STPState.VALIDATION

    # 5. Commit transition
    stp.commit_transition(tx_id)
    assert transition.stage == STPState.S1
    assert transition.to_state["current_objective"] == "Launch Mars Colony"

    # 6. Governance & Promotion
    promote_res = promote_skal_payload(
        memory_id=memory_id,
        approved=True,
        approver="Jules",
        runtime=temp_runtime,
    )
    assert promote_res["status"] == "success"
    assert promote_res["destination"] == "Master Archive"

    # Verify promoted ArchiveEntry exists
    archive_id = promote_res["archive_id"]
    archive_entry = temp_runtime.archive.retrieve_entry(archive_id)
    assert archive_entry is not None
    assert archive_entry.knowledge_state == KnowledgeState.ARCHIVED


def test_e2e_pipeline_validation_failure_and_stp_rollback(temp_runtime):
    """Test that a validation failure triggers automatic STP rollback to restore S0 and delete evidence."""
    # S0 State Setup
    temp_runtime.set_objective("Launch Mars Colony")
    temp_runtime.set_task("Verify life support systems")

    # Ingest a valid initial MemoryObject to ensure it exists
    valid_payload = {
        "source": "ci-life-support",
        "timestamp": "2026-03-31T20:15:00Z",
        "commit_identifier": "life-001",
        "validation_results": {"o2_levels": "nominal"},
        "evidence_references": ["link-to-sensor-logs"],
        "confidence_metadata": {"score": 1.0},
    }
    valid_intake = process_incoming_payload("validation_report", valid_payload, temp_runtime)
    valid_mem_id = valid_intake["memory_id"]

    stp = StateTransitionEngine(temp_runtime)

    # 1. Begin mutation transaction
    tx_id = stp.begin_mutation("Faulty life support report transition")

    # Change runtime active state to simulate task mutation (Delta)
    temp_runtime.set_task("MUTATED TASK THAT SHOULD ROLLBACK")

    # 2. Intake: Ingest a memory report that passes schema but fails the validation rules (missing evidence references!)
    # We pass an empty list [] which is valid for schema, but fails Quality Substance validation
    bad_payload = {
        "source": "flawed-sensor",
        "timestamp": "2026-03-31T20:15:00Z",
        "commit_identifier": "life-999",
        "validation_results": {"o2_levels": "critical-leak"},
        "evidence_references": [],  # Empty list triggers validation fail!
        "confidence_metadata": {"error": "uncalibrated"},
    }
    bad_intake = process_incoming_payload("validation_report", bad_payload, temp_runtime)
    bad_mem_id = bad_intake["memory_id"]

    # 3. Register evidence in transaction
    stp.register_evidence(tx_id, bad_mem_id)
    assert bad_mem_id in stp.transitions[tx_id].evidence_ids

    # 4. Validate transition (This should fail ValidationSystem rules due to missing/empty evidence_references)
    is_valid = stp.validate_transition(tx_id)
    assert is_valid is False  # Fails!

    # 5. Verify Rollback: S0 stable state restored
    assert (
        temp_runtime.current_state.active_task == "Verify life support systems"
    )  # Restored from MUTATED TASK

    # Verify bad evidence object was deleted from memory store
    assert temp_runtime.memory.retrieve(bad_mem_id) is None

    # Verify valid initial memory object was NOT deleted or affected
    assert temp_runtime.memory.retrieve(valid_mem_id) is not None


def test_state_calibration_sync_and_reconciliation(temp_runtime):
    """Test StateCalibrationSync reconciles state drift and links."""
    # Set task
    temp_runtime.set_task("Fix cabin lock")

    calibrator = StateCalibrationSync(temp_runtime)

    # 1. Active task alignment calibration
    res = calibrator.calibrate_all()
    assert "active_task_context_alignment" in res["reconciled_keys"]

    context = temp_runtime.context_tracker.get_current_context()
    assert "task:Fix cabin lock" in context.unresolved_items

    # 2. Reconcile Decision Tracker evidence links pointing to archived memories
    # Store evidence memory
    mem_id = "reconcile_ev_1"
    from sage.models import MemoryObject

    obj = MemoryObject(
        id=mem_id,
        object_type="fact",
        content={"cabin": "sealed"},
        tags=["cabin"],
    )
    temp_runtime.memory.store(obj)

    # Record decision referencing that evidence ID
    temp_runtime.decisions.record_decision(
        decision_type="technical",
        description="Decision on cabin",
        rationale="Proof of seal",
        evidence=[mem_id],
        decision_id="dec_cabin_1",
    )

    # Promote evidence memory to Master Archive
    promote_skal_payload(
        memory_id=process_incoming_payload(
            "validation_report",
            {
                "source": "api-reconcile",
                "timestamp": "2026-03-31T22:00:00Z",
                "commit_identifier": "rec-111",
                "validation_results": {"sealed": True},
                "evidence_references": ["ref-1"],
                "confidence_metadata": {},
            },
            temp_runtime,
        )["memory_id"],
        approved=True,
        approver="Jules",
        runtime=temp_runtime,
    )

    # Now we promote the original reconciliation memory manually to test target replacement
    temp_runtime.validation.promote_to_validated(mem_id)
    temp_runtime.validation.promote_to_archive(mem_id, title="Cabin Sealed Spec")

    # Run calibrator to repair link
    res2 = calibrator.calibrate_all()
    assert res2["fixed_decision_links"] >= 1

    dec = temp_runtime.decisions.retrieve_decision("dec_cabin_1")
    assert f"archive_{mem_id}" in dec.evidence


def test_recovery_workflow_rehydration(temp_runtime):
    """Test RecoveryWorkflow session repair and snapshot recovery."""
    temp_runtime.set_objective("Objective Recovery")

    # Create dummy session state JSON directly on disk without index registration
    storage_path = temp_runtime.session_manager.storage_path
    session_id = "session_orphaned_999"
    filepath = storage_path / f"{session_id}.json"

    with open(filepath, "w") as f:
        f.write('{"session_id": "session_orphaned_999", "active_objectives": ["Launch Satellite"]}')

    # Run repair workflow
    workflow = RecoveryWorkflow(temp_runtime)
    repaired = workflow.repair_corrupted_sessions()
    assert repaired == 1
    assert session_id in temp_runtime.session_manager.sessions


def test_rest_api_connected_pipeline_happy_path():
    """Test SAGE-SKAL REST connected pipeline endpoint happy path."""
    from sage.api import app, runtime, validation

    with tempfile.TemporaryDirectory() as tmpdir:
        # Override global runtime
        runtime.__init__(workspace_path=tmpdir)
        runtime.start()
        validation.__init__(runtime.memory, runtime.archive)

        with TestClient(app) as client:
            payload = {
                "payload_type": "validation_report",
                "payload_data": {
                    "source": "e2e-pipeline-tests",
                    "timestamp": "2026-03-31T20:15:00Z",
                    "commit identifier": "e2e-111",
                    "validation results": {"e2e_passed": True},
                    "evidence references": ["run-id-e2e"],
                    "confidence metadata": {"reliability": 1.0},
                },
                "approved": True,
                "approver": "Jules",
                "is_research": False,
            }
            response = client.post("/tools/skal/pipeline", json=payload)
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "success"
            assert "transaction_id" in data
            assert data["promotion"]["destination"] == "Master Archive"
            assert "archive_id" in data["promotion"]


def test_rest_api_connected_pipeline_validation_failure_rollback():
    """Test SAGE-SKAL REST connected pipeline handles validation failure with full STP rollback."""
    from sage.api import app, runtime, validation

    with tempfile.TemporaryDirectory() as tmpdir:
        # Override global runtime
        runtime.__init__(workspace_path=tmpdir)
        runtime.start()
        validation.__init__(runtime.memory, runtime.archive)

        # S0 setup
        runtime.set_objective("E2E Rollback Objective")
        runtime.set_task("Original E2E Task")

        with TestClient(app) as client:
            # We pass empty list [] for "evidence references" to pass schema validation but fail ValidationSystem rules
            payload = {
                "payload_type": "validation_report",
                "payload_data": {
                    "source": "faulty-e2e",
                    "timestamp": "2026-03-31T20:15:00Z",
                    "commit identifier": "e2e-failed",
                    "validation results": {"passed": False},
                    "evidence references": [],  # Empty list triggers validation fail!
                    "confidence metadata": {"score": 0.0},
                },
                "approved": True,
                "approver": "Jules",
                "is_research": False,
            }
            response = client.post("/tools/skal/pipeline", json=payload)
            assert response.status_code == 400
            assert "SAGE E2E Pipeline failed validation" in response.json()["detail"]

            # Verify STP Rollback restored S0 stable state (original objective & task values)
            assert runtime.current_state.current_objective == "E2E Rollback Objective"
            assert runtime.current_state.active_task == "Original E2E Task"

            # Verify no temporary memory object remains in the memory store
            assert len(runtime.memory.list_all()) == 0
