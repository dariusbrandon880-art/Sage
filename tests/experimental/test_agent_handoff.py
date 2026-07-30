"""SAGE Experimental Agent Handoff Validation Tests."""

import pytest
from sage.experimental.agents import (
    AgentCommunicationEnvelope,
    AgentIdentityRegistry,
    AgentHandoffValidator,
)


def test_valid_agent_handoff():
    """Verify that a valid agent communication envelope successfully passes validation."""
    registry = AgentIdentityRegistry()
    validator = AgentHandoffValidator(registry)

    # Valid handoff ChatGPT -> Jules
    envelope = AgentCommunicationEnvelope(
        mission_id="mission_sdr_002",
        sender_identity="chatgpt-coordinator",
        receiver_identity="jules-engineer",
        task_objective="Execute the sandbox test simulation.",
        authorized_capability="cap_cmaps_validation",
        constraints=["Only execute within safe sandbox enclaves"],
        expected_artifact="artifacts/sdr_test_results.json",
        evidence_reference="evidence_capture/sdr_exp_002_receipt.json",
        review_status="HUMAN_APPROVAL_REQUIRED",
    )

    result = validator.validate_handoff(envelope)
    assert result["validation_status"] == "APPROVED_BY_VALIDATOR"


def test_invalid_sender_identity():
    """Verify that validation fails if the sender identity is unknown."""
    registry = AgentIdentityRegistry()
    validator = AgentHandoffValidator(registry)

    envelope = AgentCommunicationEnvelope(
        mission_id="mission_sdr_002",
        sender_identity="unknown-agent",
        receiver_identity="jules-engineer",
        task_objective="Execute sandbox test.",
        authorized_capability="cap_cmaps_validation",
        constraints=[],
        expected_artifact="artifacts/res.json",
        evidence_reference="evidence_capture/rec.json",
        review_status="HUMAN_APPROVAL_REQUIRED",
    )

    with pytest.raises(ValueError, match="Sender 'unknown-agent' is not registered"):
        validator.validate_handoff(envelope)


def test_invalid_receiver_identity():
    """Verify that validation fails if the receiver identity is unknown."""
    registry = AgentIdentityRegistry()
    validator = AgentHandoffValidator(registry)

    envelope = AgentCommunicationEnvelope(
        mission_id="mission_sdr_002",
        sender_identity="chatgpt-coordinator",
        receiver_identity="unknown-agent",
        task_objective="Execute sandbox test.",
        authorized_capability="cap_cmaps_validation",
        constraints=[],
        expected_artifact="artifacts/res.json",
        evidence_reference="evidence_capture/rec.json",
        review_status="HUMAN_APPROVAL_REQUIRED",
    )

    with pytest.raises(ValueError, match="Receiver 'unknown-agent' is not registered"):
        validator.validate_handoff(envelope)


def test_disallowed_capability():
    """Verify that validation fails if the sender lacks permission for the capability."""
    registry = AgentIdentityRegistry()
    validator = AgentHandoffValidator(registry)

    envelope = AgentCommunicationEnvelope(
        mission_id="mission_sdr_002",
        sender_identity="jules-engineer",
        receiver_identity="chatgpt-coordinator",
        task_objective="Request coordinate.",
        # jules-engineer has cap_cmaps_validation but lacks simulate_handoff
        authorized_capability="simulate_handoff",
        constraints=[],
        expected_artifact="artifacts/res.json",
        evidence_reference="evidence_capture/rec.json",
        review_status="HUMAN_APPROVAL_REQUIRED",
    )

    with pytest.raises(ValueError, match="lacks permission for capability"):
        validator.validate_handoff(envelope)


def test_protected_directory_path_rejected():
    """Verify that any handoff referencing a protected folder pattern is rejected."""
    registry = AgentIdentityRegistry()
    validator = AgentHandoffValidator(registry)

    protected_paths = [
        "sage/runtime/config.py",
        "sage/core/kernel.py",
        "sage/acr/serialization.py",
        "sage/agents/reporting.py",
    ]

    for protected_path in protected_paths:
        envelope = AgentCommunicationEnvelope(
            mission_id="mission_sdr_002",
            sender_identity="chatgpt-coordinator",
            receiver_identity="jules-engineer",
            task_objective="Execute sandbox test.",
            authorized_capability="cap_cmaps_validation",
            constraints=[],
            expected_artifact=protected_path,
            evidence_reference="evidence_capture/rec.json",
            review_status="HUMAN_APPROVAL_REQUIRED",
        )

        with pytest.raises(ValueError, match="Access to protected directory pattern"):
            validator.validate_handoff(envelope)


def test_missing_evidence_reference():
    """Verify that validation fails if the evidence reference is blank."""
    registry = AgentIdentityRegistry()
    validator = AgentHandoffValidator(registry)

    envelope = AgentCommunicationEnvelope(
        mission_id="mission_sdr_002",
        sender_identity="chatgpt-coordinator",
        receiver_identity="jules-engineer",
        task_objective="Execute sandbox test.",
        authorized_capability="cap_cmaps_validation",
        constraints=[],
        expected_artifact="artifacts/res.json",
        evidence_reference="   ",
        review_status="HUMAN_APPROVAL_REQUIRED",
    )

    with pytest.raises(ValueError, match="Missing required field 'evidence_reference'"):
        validator.validate_handoff(envelope)


def test_missing_human_review_status():
    """Verify that validation fails if the review status is not set to HUMAN_APPROVAL_REQUIRED."""
    registry = AgentIdentityRegistry()
    validator = AgentHandoffValidator(registry)

    envelope = AgentCommunicationEnvelope(
        mission_id="mission_sdr_002",
        sender_identity="chatgpt-coordinator",
        receiver_identity="jules-engineer",
        task_objective="Execute sandbox test.",
        authorized_capability="cap_cmaps_validation",
        constraints=[],
        expected_artifact="artifacts/res.json",
        evidence_reference="evidence_capture/rec.json",
        review_status="AUTOMATED_BYPASS_ATTEMPT",
    )

    with pytest.raises(ValueError, match="review_status must be set to 'HUMAN_APPROVAL_REQUIRED'"):
        validator.validate_handoff(envelope)
