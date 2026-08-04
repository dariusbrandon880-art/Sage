"""Unit test suite for the SAGE Continuity Control Loop (SAGE-CCL) and sandboxed isolation rules."""

import os
import ast
import json
import time
import pytest
from pathlib import Path
from pydantic import ValidationError

from sage.experimental.act.continuity_control import (
    ContinuityControlRecord,
    ContinuityControlLoop
)
from sage.acr.session.session_state import SessionStateManager


def test_continuity_control_record_validation():
    """Verify that ContinuityControlRecord enforces correct format constraints."""
    # Standard valid inputs
    rec = ContinuityControlRecord(
        record_id="CCL-REC-20260804-f6b3d4e5-8888-4444-a999-cbcf00001111",
        session_id="session_f6b3d4e5",
        event_type="state_transition",
        timestamp=time.time(),
        action_taken="Ran build commands",
        decision_reasoning="Ensure build succeeded prior to feature addition"
    )
    assert rec.lifecycle_state == "PROPOSED"
    assert rec.workflow_friction == []
    assert rec.improvement_opportunities == []

    # Invalid record_id pattern (missing YYYYMMDD or invalid prefix)
    with pytest.raises(ValidationError, match="Invalid record_id format"):
        ContinuityControlRecord(
            record_id="REC-20260804-f6b3d4e5",
            session_id="session_f6b3d4e5",
            event_type="state_transition",
            timestamp=time.time(),
            action_taken="Ran build commands",
            decision_reasoning="Ensure build succeeded prior to feature addition"
        )

    # Invalid session_id pattern
    with pytest.raises(ValidationError, match="Invalid session_id format"):
        ContinuityControlRecord(
            record_id="CCL-REC-20260804-f6b3d4e5",
            session_id="sess_f6b3d4e5",  # Must be 'session_' or 'SES_'
            event_type="state_transition",
            timestamp=time.time(),
            action_taken="Ran build commands",
            decision_reasoning="Ensure build succeeded prior to feature addition"
        )


def test_continuity_control_loop_interception_and_enrichment(tmp_path):
    """Verify event capture, SessionStateManager enrichment, and record serialization."""
    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"

    # Set up SessionStateManager with a predefined session
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    active_sess = session_mgr.create_session(
        session_id="session_test_enrichment",
        active_objectives=["obj_validate_milestone_3", "obj_continuous_development"]
    )
    active_sess.add_completed_action("task_setup_env")
    active_sess.add_pending_action("task_run_verification")
    session_mgr.save_session(active_sess)

    # Initialize Continuity Control Loop
    ccl = ContinuityControlLoop(
        session_manager=session_mgr,
        storage_path=str(record_storage)
    )

    # Intercept event and check context enrichment
    record = ccl.intercept_event(
        event_type="boundary_intercept",
        action_taken="Implemented core telemetry tap",
        decision_reasoning="Fulfill Strategic Transition Directive requirements",
        evidence_payload={"test_run_success": True},
        workflow_friction=[{"type": "api_latency", "severity": "low"}],
        improvement_opportunities=["suggest automated test hooks"]
    )

    # Ensure record is constructed properly
    assert record.session_id == "session_test_enrichment"
    assert record.event_type == "boundary_intercept"
    assert record.action_taken == "Implemented core telemetry tap"
    assert "obj_validate_milestone_3" in record.evidence_payload["enriched_objectives"]
    assert "task_setup_env" in record.evidence_payload["session_completed_actions"]
    assert "task_run_verification" in record.evidence_payload["session_pending_actions"]
    assert record.workflow_friction[0]["type"] == "api_latency"
    assert record.improvement_opportunities[0] == "suggest automated test hooks"

    # Serialize record and verify file
    filepath = ccl.serialize_record(record)
    assert filepath.exists()

    with open(filepath, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    assert loaded_data["record_id"] == record.record_id
    assert loaded_data["lifecycle_state"] == "PROPOSED"


def test_continuity_control_chronological_and_recovered_validation(tmp_path):
    """Verify adversarial validation of chronological order and recovered state rules."""
    record_storage = tmp_path / "records"
    ccl = ContinuityControlLoop(storage_path=str(record_storage))

    # Create and serialize an initial valid record
    rec1 = ccl.intercept_event(
        event_type="checkpoint",
        action_taken="Saved state 1",
        decision_reasoning="Normal checkpointing"
    )
    # Force mock a older timestamp on rec1
    rec1.timestamp = 1000.0
    ccl.serialize_record(rec1)

    # Create rec2 that is newer
    rec2 = ccl.intercept_event(
        event_type="checkpoint",
        action_taken="Saved state 2",
        decision_reasoning="Normal checkpointing"
    )
    rec2.timestamp = 2000.0
    assert ccl.validate_record(rec2) is True

    # Create rec3 that violates chronology (timestamp older than rec2)
    rec3 = ccl.intercept_event(
        event_type="checkpoint",
        action_taken="Saved state 3",
        decision_reasoning="Anachronistic checkpointing"
    )
    ccl.serialize_record(rec2)  # Save rec2
    rec3.timestamp = 1500.0    # Older than rec2 (2000.0) but saved after
    assert ccl.validate_record(rec3) is False

    # Verify recovered event validation
    valid_recovered = ContinuityControlRecord(
        record_id="CCL-REC-20260804-rec1",
        session_id="session_rec_99",
        event_type="recovered",
        timestamp=3000.0,
        action_taken="Restored session after failure",
        decision_reasoning="Recovery protocol",
        failure_context={"error": "db_crash"},
        recovery_path="rehydrated_last_checkpoint"
    )
    assert ccl.validate_record(valid_recovered) is True

    invalid_recovered = ContinuityControlRecord(
        record_id="CCL-REC-20260804-rec2",
        session_id="session_rec_99",
        event_type="recovered",
        timestamp=3100.0,
        action_taken="Restored session after failure",
        decision_reasoning="Recovery protocol",
        failure_context=None,  # Missing failure context
        recovery_path="rehydrated_last_checkpoint"
    )
    assert ccl.validate_record(invalid_recovered) is False


def test_continuity_control_human_approval(tmp_path):
    """Verify that human approval successfully promotes the record state."""
    record_storage = tmp_path / "records"
    ccl = ContinuityControlLoop(storage_path=str(record_storage))

    record = ccl.intercept_event(
        event_type="state_transition",
        action_taken="Created new core service",
        decision_reasoning="Scaling requirement"
    )
    ccl.serialize_record(record)

    # Approve record
    approved = ccl.human_approval(
        record_id=record.record_id,
        supervisor_id="supervisor_jules",
        signature="sig_jules_approved_9922",
        decision="APPROVED"
    )

    assert approved.lifecycle_state == "VALIDATED"
    assert "human_approval_record" in approved.evidence_payload
    assert approved.evidence_payload["human_approval_record"]["supervisor_id"] == "supervisor_jules"
    assert approved.evidence_payload["human_approval_record"]["signature"] == "sig_jules_approved_9922"

    # Reject record
    rejected = ccl.human_approval(
        record_id=record.record_id,
        supervisor_id="supervisor_jules",
        signature="sig_jules_rejected_9922",
        decision="REJECTED"
    )
    assert rejected.lifecycle_state == "REJECTED"


def test_one_way_import_isolation_enforcement():
    """Verify absolute enforcement of the One-Way Import Law for SAGE-CCL.

    No module in the frozen production/core namespace ('sage/acr/', 'sage/core/', etc.)
    is allowed to import from 'sage.experimental' or 'sage.experimental.act'.
    """
    root_path = Path(__file__).parent.parent.parent / "sage"
    assert root_path.exists(), f"Could not find SAGE source path at: {root_path}"

    for file_path in root_path.glob("**/*.py"):
        # Exclude files inside sage/experimental
        if "experimental" in file_path.parts:
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=str(file_path))
            except SyntaxError as e:
                pytest.fail(f"Syntax error while parsing {file_path}: {e}")

            for node in ast.walk(tree):
                # Check direct imports (e.g., 'import sage.experimental')
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "sage.experimental" not in alias.name, (
                            f"One-Way Import Law Violation inside production: '{file_path}' "
                            f"attempts to directly import '{alias.name}'"
                        )
                # Check from imports (e.g., 'from sage.experimental.act.continuity_control import ...')
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        assert "sage.experimental" not in node.module, (
                            f"One-Way Import Law Violation inside production: '{file_path}' "
                            f"attempts to import from module '{node.module}'"
                        )
