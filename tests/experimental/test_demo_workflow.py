"""SAGE First Demonstration Workflow test suite."""

import os
import json
import pytest

from sage.experimental.act.demo_workflow import SAGEDemoWorkflowOrchestrator


def test_demo_workflow_execution_success():
    """Verify standard happy path of the SAGE demo workflow sequence."""
    orchestrator = SAGEDemoWorkflowOrchestrator(output_path="evidence_capture/demo_workflow_evidence.json")

    context_data = {
        "user_id": "usr_9921",
        "repository_path": "/app/workspace",
        "evaluation_target": "contracts.py",
    }

    # Run the entire sequence
    state = orchestrator.execute_demo_sequence(
        session_id="session_demo_9921",
        action_type="code_evaluation",
        user_id="usr_9921",
        approver="supervisor_charlie",
        signature="sig_demo_abc123",
        context_data=context_data,
    )

    assert state["session_id"] == "session_demo_9921"
    assert state["user_action"]["action_type"] == "code_evaluation"
    assert state["intake"]["status"] == "INTAKE_COMPLETE"
    assert state["context_evaluation"]["boundary_isolation_verified"] is True
    assert state["capability_analysis"]["split_brain_detected"] is True
    assert state["human_checkpoint"]["status"] == "APPROVED"
    assert state["evidence_receipt"]["assertion"] == "SAGE_ACTIVATION_RECEIPT_VALID"
    assert "state_checksum" in state

    # Export evidence and verify file structure
    path = orchestrator.export_demo_evidence("session_demo_9921")
    assert path == "evidence_capture/demo_workflow_evidence.json"
    assert os.path.exists(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["session_id"] == "session_demo_9921"
    assert data["demonstrator_output"]["divergence_visibility"]["divergence_detected"] is True


def test_demo_workflow_invalid_session_export():
    """Verify error on attempting to export a non-existent session workflow state."""
    orchestrator = SAGEDemoWorkflowOrchestrator()
    with pytest.raises(ValueError, match="Session 'session_non_existent' not found"):
        orchestrator.export_demo_evidence("session_non_existent")
