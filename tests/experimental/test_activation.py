"""SAGE Activation Layer Foundation test suite."""

import pytest
from datetime import datetime, timezone

from sage.experimental.act.activation import (
    ActivationEntryPoint,
    ContextIntakeBridge,
    ValidatedCapabilityConnector,
    HumanAuthorizationCheckpoint,
    EvidenceReceiptGenerator,
)


def test_activation_workflow_success():
    """Verify standard happy path SAGE activation workflow sequence."""
    runner = ActivationEntryPoint()

    context_data = {
        "user_id": "usr_9921",
        "repository_path": "/app/workspace",
        "evaluation_target": "contracts.py",
    }

    # Execute workflow sequence: User Action -> Intake -> Validation -> Checkpoint -> Receipt
    receipt = runner.execute_workflow(
        action_type="code_evaluation",
        context_data=context_data,
        task_ids=["task_001_intake", "task_002_review"],
        decision_ids=["decision_001_approve", "proposal_002_merge"],
        approver="supervisor_charlie",
        signature="sig_7e2a9b3c4f",
    )

    assert receipt["assertion"] == "SAGE_ACTIVATION_RECEIPT_VALID"
    assert receipt["action_type"] == "code_evaluation"
    assert receipt["session_id"].startswith("session_")
    assert "verification_hash" in receipt

    payload = receipt["payload"]
    assert payload["intake"]["status"] == "intake_complete"
    assert payload["validation"]["link_status"] == "INTERFACE_VERIFIED"
    assert payload["authorization"]["checkpoint_status"] == "APPROVED"
    assert payload["authorization"]["authorized_by"] == "supervisor_charlie"


def test_activation_invalid_intake():
    """Verify error on empty action_type during intake."""
    bridge = ContextIntakeBridge()
    with pytest.raises(ValueError, match="Action type cannot be empty"):
        bridge.ingest_action(action_type="", context_data={})


def test_activation_invalid_lineage():
    """Verify contract lineage-mapping failure on malformed session_id format."""
    connector = ValidatedCapabilityConnector()
    with pytest.raises(ValueError, match="Invalid session_id format"):
        connector.validate_capability_lineage(
            session_id="bad_sess_prefix",  # Must start with session_
            task_ids=["task_01"],
        )


def test_activation_invalid_human_checkpoint():
    """Verify rejection of human checkpoint with missing authorization details."""
    checkpoint = HumanAuthorizationCheckpoint()
    with pytest.raises(ValueError, match="Human authorization requires a valid approver and signature"):
        checkpoint.authorize_action("session_1234", "Run test", approver="", signature="sig")

    with pytest.raises(ValueError, match="Human authorization requires a valid approver and signature"):
        checkpoint.authorize_action("session_1234", "Run test", approver="admin", signature="")


def test_activation_receipt_integrity():
    """Verify that any modification of payload content invalidates the verification hash."""
    bridge = ContextIntakeBridge()
    connector = ValidatedCapabilityConnector()
    checkpoint = HumanAuthorizationCheckpoint()
    generator = EvidenceReceiptGenerator()

    intake = bridge.ingest_action("audit_run", {"session_id": "session_8888"})
    validation = connector.validate_capability_lineage("session_8888", ["task_01"])
    auth = checkpoint.authorize_action("session_8888", "Run audit", "supervisor_alice", "sig_123")

    receipt = generator.generate_receipt(intake, validation, auth)
    initial_hash = receipt["verification_hash"]

    # If the payload is tampered with, regenerating receipt results in a different verification hash
    receipt["payload"]["intake"]["context_data"]["tampered"] = True
    new_receipt = generator.generate_receipt(receipt["payload"]["intake"], receipt["payload"]["validation"], receipt["payload"]["authorization"])
    assert new_receipt["verification_hash"] != initial_hash


def test_activation_cmaps_payload_validation():
    """Verify CMAPS v1.0 validation within the Activation Entry Point."""
    runner = ActivationEntryPoint()

    # Generate a valid CMAPS payload
    payload = {
        "audit_id": "audit_12345678901234567890123456789012",
        "timestamp": "2026-03-31T12:00:00Z",
        "agent_identity": {
            "agent_id": "agent_test_runner",
            "name": "Test Runner",
            "role": "QA Agent",
            "governance_tier": "tier_1",
        },
        "model_provider": {
            "provider": "openai",
            "model_name": "gpt-4o",
            "temperature": 0.0,
        },
        "execution_state": {
            "run_id": "run_12345678901234567890",
            "status": "active",
            "step_counter": 1,
            "started_at": "2026-03-31T12:00:00Z",
            "updated_at": "2026-03-31T12:00:00Z",
        },
        "task_lineage": {
            "session_id": "session_12345678",
            "current_task_id": "task_verify_activation",
            "subtask_ids": [],
        },
        "decision_events": [],
        "failure_events": [],
        "recovery_checkpoints": [],
        "evidence_relationships": [],
        "attestation": {
            "nonce": "nonce_123",
            "signature": "sig_456",
            "signer_identity": "signer_789",
        },
    }

    receipt = runner.execute_workflow(
        action_type="audit_run",
        context_data={"session_id": "session_12345678"},
        task_ids=["task_verify_activation"],
        decision_ids=None,
        approver="supervisor_bob",
        signature="sig_abc",
        audit_payload=payload,
    )

    assert receipt["assertion"] == "SAGE_ACTIVATION_RECEIPT_VALID"
    assert receipt["payload"]["validation"]["cmaps_validation"] == "SUCCESS"
