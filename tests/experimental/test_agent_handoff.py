"""SAGE-ACT Milestone 7: SAGE Experimental Agent Communication Bridge Verification Tests."""

import pytest
from datetime import datetime, timezone
from sage.experimental.agents import (
    AgentIdentity,
    AgentIdentityRegistry,
    AgentCommunicationEnvelope,
    AgentHandoffValidator,
)


def test_valid_agent_handoff_sequence():
    """Verify that a standard coordinator-to-executor handoff with valid fields succeeds."""
    registry = AgentIdentityRegistry()
    validator = AgentHandoffValidator(registry)

    # ChatGPT (Coordinator) hands off task to Jules (Executor)
    envelope = AgentCommunicationEnvelope(
        sender_id="agent_chatgpt",
        receiver_id="agent_jules",
        capability_id="coordinate_workflow",
        evidence_reference="ref_sdr_crc_001",
        human_review_status="APPROVED",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        execution_trace_reference="session_f5c4b3a2",
    )

    assert validator.validate_handoff(envelope) is True


def test_invalid_identity_rejection():
    """Verify that an unregistered/malicious agent identity is rejected."""
    registry = AgentIdentityRegistry()
    validator = AgentHandoffValidator(registry)

    # Malicious anonymous agent tries to send
    envelope = AgentCommunicationEnvelope(
        sender_id="agent_anonymous_malicious",
        receiver_id="agent_jules",
        capability_id="write_code",
        evidence_reference="ref_malicious_001",
        human_review_status="APPROVED",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        execution_trace_reference="session_bad",
    )

    with pytest.raises(ValueError, match="Unauthorized or unregistered agent identity"):
        validator.validate_handoff(envelope)


def test_unauthorized_capability_rejection():
    """Verify that an agent attempting an unauthorized capability is rejected."""
    registry = AgentIdentityRegistry()
    validator = AgentHandoffValidator(registry)

    # Executor (Jules) tries to execute coordinate_workflow (not in his list)
    envelope = AgentCommunicationEnvelope(
        sender_id="agent_jules",
        receiver_id="agent_chatgpt",
        capability_id="coordinate_workflow",
        evidence_reference="ref_jules_01",
        human_review_status="APPROVED",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        execution_trace_reference="session_f5c4b3a2",
    )

    with pytest.raises(ValueError, match="is not authorized to execute capability"):
        validator.validate_handoff(envelope)


def test_missing_evidence_rejection():
    """Verify that a handoff lacking required evidence references is rejected."""
    registry = AgentIdentityRegistry()
    validator = AgentHandoffValidator(registry)

    # Empty evidence_reference
    envelope = AgentCommunicationEnvelope(
        sender_id="agent_chatgpt",
        receiver_id="agent_jules",
        capability_id="coordinate_workflow",
        evidence_reference=" ",
        human_review_status="APPROVED",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        execution_trace_reference="session_f5c4b3a2",
    )

    with pytest.raises(ValueError, match="Missing required evidence reference in envelope"):
        validator.validate_handoff(envelope)


def test_missing_human_review_rejection():
    """Verify that handoffs with pending human review status are blocked."""
    registry = AgentIdentityRegistry()
    validator = AgentHandoffValidator(registry)

    # PENDING human_review_status
    envelope = AgentCommunicationEnvelope(
        sender_id="agent_chatgpt",
        receiver_id="agent_jules",
        capability_id="coordinate_workflow",
        evidence_reference="ref_001",
        human_review_status="PENDING",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        execution_trace_reference="session_f5c4b3a2",
    )

    with pytest.raises(ValueError, match="Capability promotion requires explicit human review"):
        validator.validate_handoff(envelope)


def test_protected_boundary_path_rejection():
    """Verify that handoffs targeting modifications inside protected enclaves are rejected."""
    registry = AgentIdentityRegistry()
    validator = AgentHandoffValidator(registry)

    envelope = AgentCommunicationEnvelope(
        sender_id="agent_chatgpt",
        receiver_id="agent_jules",
        capability_id="coordinate_workflow",
        evidence_reference="ref_001",
        human_review_status="APPROVED",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        execution_trace_reference="session_f5c4b3a2",
    )

    # Simulated targets inside core enclaves
    unauthorized_paths = ["sage/core/spek.py", "sage/runtime/engine.py"]
    for path in unauthorized_paths:
        with pytest.raises(PermissionError, match="Autonomous handoff attempted to write to protected core enclave path"):
            validator.validate_handoff(envelope, target_paths=[path])


def test_chronological_monotonicity_enforcement():
    """Verify that sequential handoffs enforce monotonic timestamp dispatch order."""
    registry = AgentIdentityRegistry()
    validator = AgentHandoffValidator(registry)

    # 1. Monotonic order (succeeds)
    e1 = AgentCommunicationEnvelope(
        "agent_chatgpt", "agent_jules", "coordinate_workflow", "ref_01", "APPROVED", "2026-07-31T10:00:00Z", "trace_1"
    )
    e2 = AgentCommunicationEnvelope(
        "agent_jules", "agent_claude", "write_code", "ref_02", "APPROVED", "2026-07-31T10:05:00Z", "trace_1"
    )

    assert validator.validate_sequence_chronology([e1, e2]) is True

    # 2. Out of order (backdated timestamp)
    e3 = AgentCommunicationEnvelope(
        "agent_claude", "agent_gemini", "analyze_trace", "ref_03", "APPROVED", "2026-07-31T09:59:00Z", "trace_1"
    )

    with pytest.raises(ValueError, match="Chronological discontinuity"):
        validator.validate_sequence_chronology([e1, e2, e3])
