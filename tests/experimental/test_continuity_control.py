"""Unit and Integration Tests for SAGE-CCL (Continuity Control Loop)."""

import os
import shutil
import tempfile
import pytest
import re
from sage.experimental.act.continuity_control import (
    ContinuityControlRecord,
    ContinuityControlLoop,
)


@pytest.fixture
def temp_stage_dir():
    """Fixture to provide a clean, temporary staging directory for testing SAGE-CCL."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


def test_record_generation_and_serialization(temp_stage_dir):
    """Verify that SAGE-CCL correctly generates, serializes, and stages records."""
    ccl = ContinuityControlLoop(stage_dir=temp_stage_dir)
    session_id = "session_abcdef01"
    event_type = "state_transition"
    action = "Update SAGE index schema validation rules"
    reasoning = "Enforce stricter model provider consistency rules in CMAPS"
    evidence = {
        "artifact_path": "Main Archive/INDEX.md",
        "sha256_checksum": "a" * 64,
        "git_commit": "b" * 40,
    }

    # Generate record
    record = ccl.capture_event(
        session_id=session_id,
        event_type=event_type,
        action=action,
        reasoning=reasoning,
        evidence=evidence,
    )

    assert isinstance(record, ContinuityControlRecord)
    assert record.session_id == session_id
    assert record.event_type == event_type
    assert record.action_taken == action
    assert record.decision_reasoning == reasoning
    assert record.lifecycle_state == "PROPOSED"
    assert re.match(r"^CCL-REC-[0-9]{8}-[a-fA-F0-9\-]{36}$", record.record_id)

    # Stage record
    ccl.stage_record(record)

    # Check file exists
    expected_file = os.path.join(temp_stage_dir, f"{record.record_id}.json")
    assert os.path.exists(expected_file)


def test_invalid_session_id_format(temp_stage_dir):
    """Verify that SAGE-CCL rejects invalid session_id formats."""
    ccl = ContinuityControlLoop(stage_dir=temp_stage_dir)
    with pytest.raises(ValueError, match="Invalid session_id format"):
        ccl.capture_event(
            session_id="invalid_session_id",
            event_type="test",
            action="test",
            reasoning="test",
            evidence={},
        )


def test_read_only_integrity_checks(temp_stage_dir):
    """Verify that verify_record_integrity performs robust read-only validation."""
    ccl = ContinuityControlLoop(stage_dir=temp_stage_dir)
    session_id = "session_99998888"
    record = ccl.capture_event(
        session_id=session_id,
        event_type="boundary_intercept",
        action="Intercept drift in simulation boundary",
        reasoning="Recover gracefully using cached checkpoint state",
        evidence={"run_id": "run_test123"},
    )
    ccl.stage_record(record)

    # Validate correct record
    res = ccl.verify_record_integrity(record.record_id)
    assert res["record_id"] == record.record_id
    assert res["status"] == "VERIFIED_STABLE"
    assert res["lifecycle_state"] == "PROPOSED"

    # Try non-existent record ID
    with pytest.raises(ValueError, match="not found"):
        ccl.verify_record_integrity("CCL-REC-20260728-nonexistent")


def test_lifecycle_classifications_and_promotion(temp_stage_dir):
    """Verify record lifecycle starts at PROPOSED and transitions to VALIDATED on operator sign-off."""
    ccl = ContinuityControlLoop(stage_dir=temp_stage_dir)
    session_id = "session_77777777"
    record = ccl.capture_event(
        session_id=session_id,
        event_type="evidence_capture",
        action="Generate deployment evidence package for Render",
        reasoning="Satisfy external auditability requirements for launch",
        evidence={"health": "green"},
    )
    ccl.stage_record(record)

    # Reject promotion without valid signature
    with pytest.raises(ValueError, match="Cannot promote record to VALIDATED without a valid human operator signature"):
        ccl.promote_record(record.record_id, signature="invalid_sig")

    with pytest.raises(ValueError, match="Cannot promote record to VALIDATED without a valid human operator signature"):
        ccl.promote_record(record.record_id, signature=None)

    # Correct promotion
    promoted = ccl.promote_record(record.record_id, signature="sig_operator_key_999")
    assert promoted.lifecycle_state == "VALIDATED"
    assert promoted.evidence_payload["operator_signature"] == "sig_operator_key_999"

    # Confirm storage has been updated
    verify_res = ccl.verify_record_integrity(record.record_id)
    assert verify_res["lifecycle_state"] == "VALIDATED"


def test_causality_and_lineage_reconstruction(temp_stage_dir):
    """Verify that session records can be sorted chronologically and reconstructed into causal lineage graphs."""
    ccl = ContinuityControlLoop(stage_dir=temp_stage_dir)
    session_id = "session_0000aaaa"

    # Create multiple events in order
    r1 = ccl.capture_event(
        session_id=session_id,
        event_type="state_transition",
        action="Action 1",
        reasoning="Reason 1",
        evidence={"step": 1},
    )
    ccl.stage_record(r1)

    r2 = ccl.capture_event(
        session_id=session_id,
        event_type="boundary_intercept",
        action="Action 2",
        reasoning="Reason 2",
        evidence={"step": 2},
        failure_context={"error": "BoundaryLimitExceeded"},
        recovery_path="Restore to Checkpoint 1",
    )
    ccl.stage_record(r2)

    # Reconstruct lineage
    lineage = ccl.reconstruct_lineage(session_id=session_id)
    assert lineage["session_id"] == session_id
    assert lineage["total_records"] == 2
    assert lineage["audit_ready"] is True

    chain = lineage["chronological_lineage"]
    assert chain[0]["action"] == "Action 1"
    assert chain[1]["action"] == "Action 2"
    assert "failure" in chain[1]
    assert chain[1]["failure"]["error"] == "BoundaryLimitExceeded"
    assert chain[1]["recovery"] == "Restore to Checkpoint 1"


def test_one_way_import_isolation_enforcement():
    """Strictly assert that core production modules do not import the experimental continuity control loop."""
    production_dirs = ["sage/runtime", "sage/core", "sage/acr"]
    experimental_import_pattern = re.compile(r"sage\.experimental\.act")

    for p_dir in production_dirs:
        if not os.path.exists(p_dir):
            continue
        for root, _, files in os.walk(p_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r") as f:
                        content = f.read()
                    if experimental_import_pattern.search(content):
                        pytest.fail(
                            f"One-Way Import Law Violation: Production file '{filepath}' "
                            f"imports from experimental 'sage.experimental.act'."
                        )
