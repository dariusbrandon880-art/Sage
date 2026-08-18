"""Unit test suite for SAGE Stage 2 — Controlled Self-Application Workflow Control Loop."""

import pytest
from sage.experimental.workflow_control import (
    SAGEWorkflowControlLoop,
    WorkflowExecutionRequest,
    WorkflowExecutionResult,
)
from sage.experimental.flight_record import SAGEFlightRecordManager


def test_1_complete_eight_stage_workflow_progression_execution(tmp_path):
    ledger_path = tmp_path / "flight_ledger.json"
    manager = SAGEFlightRecordManager(flight_ledger_path=ledger_path)
    control_loop = SAGEWorkflowControlLoop(flight_manager=manager)

    req = WorkflowExecutionRequest(
        mission_id="mission_stage2_001",
        objective="Validate Stage 2 controlled self-application flight",
        assigned_agent="agent_jules_sage",
        priority_score=90.0,
        task_payload={"target_files": ["sage/experimental/workflow_control.py"]},
    )

    result = control_loop.execute_governed_cycle(req)

    assert isinstance(result, WorkflowExecutionResult)
    assert result.mission_id == "mission_stage2_001"
    assert result.final_stage == "OUTCOME_CLASSIFIED"
    assert result.pfc_decision_outcome == "APPROVED"
    assert len(result.progression_receipts) == 8
    assert result.next_decision_state["decision"] == "HOLD_HUMAN_DECISION_REQUIRED"
    assert result.next_decision_state["self_authorization_permitted"] is False
    assert len(result.integrity_hash) == 64
    assert ledger_path.exists()


def test_2_authority_gate_blocks_unauthorized_agent(tmp_path):
    control_loop = SAGEWorkflowControlLoop()

    req = WorkflowExecutionRequest(
        mission_id="mission_unauth_agent",
        objective="Attempt unauth agent execution",
        assigned_agent="unauthorized_agent",
        priority_score=90.0,
    )

    with pytest.raises(ValueError, match="Transition Rejected: Failed validation gate for target state 'HANDOFF_READY'"):
        control_loop.execute_governed_cycle(req)


def test_3_failed_verification_stops_progression(tmp_path):
    control_loop = SAGEWorkflowControlLoop()

    req = WorkflowExecutionRequest(
        mission_id="mission_test_fail",
        objective="Failing test execution",
        priority_score=90.0,
    )

    def failing_test_func():
        return False, {"passed": 0, "failed": 5, "errors": 1}

    with pytest.raises(ValueError, match="WORKFLOW_TEST_VALIDATION_FAILED"):
        control_loop.execute_governed_cycle(req, test_executor_func=failing_test_func)


def test_4_recoverable_execution_receipt_chain(tmp_path):
    ledger_path = tmp_path / "flight_ledger.json"
    manager = SAGEFlightRecordManager(flight_ledger_path=ledger_path)
    control_loop = SAGEWorkflowControlLoop(flight_manager=manager)

    req = WorkflowExecutionRequest(
        mission_id="mission_chain_001",
        objective="Chain verification",
        priority_score=85.0,
    )

    result = control_loop.execute_governed_cycle(req)

    stages = [r["next_state"] for r in result.progression_receipts]
    expected_stages = [
        "INTAKE",
        "PRIORITIZED",
        "PREFLIGHT_VALIDATED",
        "HANDOFF_READY",
        "HANDOFF_EMITTED",
        "EXECUTION_RESULT_RECEIVED",
        "EVIDENCE_VALIDATED",
        "OUTCOME_CLASSIFIED",
    ]
    assert stages == expected_stages


def test_5_restart_rehydration_preserves_flight_record(tmp_path):
    ledger_path = tmp_path / "flight_ledger.json"
    manager = SAGEFlightRecordManager(flight_ledger_path=ledger_path)
    control_loop = SAGEWorkflowControlLoop(flight_manager=manager)

    req = WorkflowExecutionRequest(
        mission_id="mission_restart_001",
        objective="Restart test",
        priority_score=88.0,
    )

    original_result = control_loop.execute_governed_cycle(req)

    # Rehydrate in new manager instance from persisted file
    restarted_manager = SAGEFlightRecordManager(flight_ledger_path=ledger_path)
    flight_rec = restarted_manager._load_json_list(ledger_path)[0]

    assert flight_rec["record_id"] == original_result.execution_id
    assert flight_rec["mission_id"] == original_result.mission_id
    assert flight_rec["result_status"] == "SUCCESS"


def test_6_next_decision_state_blocks_self_authorization():
    control_loop = SAGEWorkflowControlLoop()
    req = WorkflowExecutionRequest(
        mission_id="mission_self_auth_block",
        objective="Self auth check",
        priority_score=95.0,
    )

    result = control_loop.execute_governed_cycle(req)

    next_state = result.next_decision_state
    assert next_state["decision"] == "HOLD_HUMAN_DECISION_REQUIRED"
    assert next_state["authorized_next_action"] is None
    assert next_state["self_authorization_permitted"] is False
