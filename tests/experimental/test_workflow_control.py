"""Focused verification tests for SAGE Workflow Control Loop (Stage 2 Controlled Self-Application)."""

import json
from pathlib import Path
import pytest

from sage.experimental.flight_record import SAGEFlightRecordManager
from sage.experimental.workflow_control import (
    SAGEWorkflowControlLoop,
    SAGEWorkflowStage,
    WorkflowCycleTrace,
)


@pytest.fixture
def temp_workflow_ledger(tmp_path):
    return tmp_path / "workflow_control_ledger.json"


@pytest.fixture
def temp_flight_ledger(tmp_path):
    return tmp_path / "flight_records_ledger.json"


def test_workflow_control_loop_single_cycle(temp_workflow_ledger, temp_flight_ledger):
    frm = SAGEFlightRecordManager(flight_ledger_path=temp_flight_ledger)
    loop = SAGEWorkflowControlLoop(storage_path=temp_workflow_ledger, flight_record_manager=frm)

    trace = loop.execute_controlled_workflow_cycle(
        mission_id="STAGE2-M-001",
        intent_summary="Validate Stage 2 controlled self-application workflow cycle",
        assigned_agent="agent_jules_sage",
        target_files=["sage/experimental/workflow_control.py"],
    )

    assert trace.cycle_completed is True
    assert trace.current_stage == SAGEWorkflowStage.DECISION
    assert trace.review_status == "APPROVED"
    assert trace.final_decision == "ADVANCE_NEXT_AUTHORIZED_FRONTIER"
    assert len(trace.stage_history) == 9  # All 9 stages executed in sequence!
    assert len(trace.evidence_receipts) >= 2


def test_invalid_stage_transition_fails_closed(temp_workflow_ledger):
    loop = SAGEWorkflowControlLoop(storage_path=temp_workflow_ledger)
    trace = WorkflowCycleTrace(
        cycle_id="c_001",
        mission_id="M-1",
        current_stage=SAGEWorkflowStage.HUMAN_INTENT,
        intent_summary="Test invalid transition",
        assigned_agent="agent_jules_sage",
    )

    # Attempting to jump directly from HUMAN_INTENT to TEST fails closed
    with pytest.raises(ValueError, match="Out-of-Order Stage Transition Failed Closed"):
        loop.transition_stage(trace, SAGEWorkflowStage.TEST, "Illegal jump")


def test_unauthorized_handoff_blocked(temp_workflow_ledger):
    loop = SAGEWorkflowControlLoop(storage_path=temp_workflow_ledger)
    with pytest.raises(PermissionError, match="Unauthorized agent handoff blocked"):
        loop.execute_controlled_workflow_cycle(
            mission_id="M-UNAUTH",
            intent_summary="Test unauthorized agent",
            assigned_agent="unauthorized_agent",
        )


def test_workflow_evidence_association(temp_workflow_ledger, temp_flight_ledger):
    frm = SAGEFlightRecordManager(flight_ledger_path=temp_flight_ledger)
    loop = SAGEWorkflowControlLoop(storage_path=temp_workflow_ledger, flight_record_manager=frm)

    trace = loop.execute_controlled_workflow_cycle(
        mission_id="M-EVID",
        intent_summary="Test evidence association",
        assigned_agent="agent_jules_sage",
    )

    # Verify flight record was created in flight ledger
    report = frm.get_48h_flight_report()
    assert len(report) == 1
    assert report[0]["mission_id"] == "M-EVID"
    assert report[0]["result_status"] == "SUCCESS"


def test_workflow_restart_survival(temp_workflow_ledger, temp_flight_ledger):
    frm1 = SAGEFlightRecordManager(flight_ledger_path=temp_flight_ledger)
    loop1 = SAGEWorkflowControlLoop(storage_path=temp_workflow_ledger, flight_record_manager=frm1)

    trace1 = loop1.execute_controlled_workflow_cycle(
        mission_id="M-REstart",
        intent_summary="Test restart survival",
        assigned_agent="agent_jules_sage",
    )

    # Simulate fresh process session restart
    frm2 = SAGEFlightRecordManager(flight_ledger_path=temp_flight_ledger)
    loop2 = SAGEWorkflowControlLoop(storage_path=temp_workflow_ledger, flight_record_manager=frm2)
    reconstructed_trace = loop2.reconstruct_workflow_state()

    assert reconstructed_trace is not None
    assert reconstructed_trace.cycle_id == trace1.cycle_id
    assert reconstructed_trace.cycle_completed is True
    assert reconstructed_trace.current_stage == SAGEWorkflowStage.DECISION


def test_single_cycle_boundary_enforced(temp_workflow_ledger):
    loop = SAGEWorkflowControlLoop(storage_path=temp_workflow_ledger)
    loop.execute_controlled_workflow_cycle(
        mission_id="M-CYC-1",
        intent_summary="Execute first cycle",
    )

    # Attempting a second cycle on the same control loop instance raises PermissionError
    with pytest.raises(PermissionError, match="single cycle limit reached"):
        loop.execute_controlled_workflow_cycle(
            mission_id="M-CYC-2",
            intent_summary="Execute second cycle",
        )
