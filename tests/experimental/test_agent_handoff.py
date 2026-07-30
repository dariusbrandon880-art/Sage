"""SAGE Multi-Agent Handoff and Communication Bridge Tests."""

import pytest
import time
from datetime import datetime
from sage.experimental.agents.models import (
    AgentIdentity,
    AgentCommunicationEnvelope,
    HandoffEvidenceRecord,
)
from sage.experimental.agents.registry import AgentIdentityRegistry
from sage.experimental.agents.validation import AgentHandoffValidator


def test_agent_registry_seed_defaults():
    """Verify that the identity registry is seeded with standard SAGE agent identities."""
    registry = AgentIdentityRegistry(seed_defaults=True)

    # ChatGPT: Coordinator
    chatgpt = registry.get_agent("ChatGPT")
    assert chatgpt is not None
    assert chatgpt.role == "Coordinator"
    assert "coordinate_missions" in chatgpt.permissions
    assert "mutate_code" in chatgpt.restrictions

    # Jules: Engineering Executor
    jules = registry.get_agent("Jules")
    assert jules is not None
    assert jules.role == "Engineering Executor"
    assert "execute_sandbox" in jules.permissions
    assert "direct_review" in jules.restrictions

    # Claude: Adversarial Reviewer
    claude = registry.get_agent("Claude")
    assert claude is not None
    assert claude.role == "Adversarial Reviewer"
    assert "adversarial_audit" in claude.permissions
    assert "mutate_code" in claude.restrictions

    # Gemini: Independent Analyst
    gemini = registry.get_agent("Gemini")
    assert gemini is not None
    assert gemini.role == "Independent Analyst"
    assert "analyze_metrics" in gemini.permissions
    assert "execute_sandbox" in gemini.restrictions


def test_register_duplicate_agent():
    """Verify that registering duplicate agents throws a ValueError."""
    registry = AgentIdentityRegistry(seed_defaults=False)
    identity = AgentIdentity(agent_id="ChatGPT", role="Coordinator")
    registry.register_agent(identity)

    with pytest.raises(ValueError, match="already registered"):
        registry.register_agent(identity)


def test_register_invalid_agent_id():
    """Verify that registering an empty agent_id throws a ValueError."""
    registry = AgentIdentityRegistry(seed_defaults=False)
    identity = AgentIdentity(agent_id="", role="Coordinator")
    with pytest.raises(ValueError, match="agent_id must be a non-empty string"):
        registry.register_agent(identity)


def test_valid_agent_handoff_validation():
    """Verify a successful multi-agent handoff validation with human approval."""
    registry = AgentIdentityRegistry(seed_defaults=True)
    validator = AgentHandoffValidator(registry)

    # ChatGPT delegating to Jules to execute sandbox task
    envelope = AgentCommunicationEnvelope(
        mission_id="mission_sdr_001",
        sender_identity="ChatGPT",
        receiver_identity="Jules",
        task_objective="Execute first controlled dry-run of SDR validator.",
        authorized_capability="cap_sdr_sim_engine",
        constraints=["read-only-scratch"],
        expected_artifact="evidence_capture/sdr_exp_001_evidence_package.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )

    execution_res = {
        "status": "SUCCESS",
        "output_written": True,
        "payload_checksum": "a1b2c3d4e5f6g7h8",
    }

    # Execute and validate handoff
    evidence_record = validator.validate_and_execute_handoff(
        envelope=envelope,
        execution_result=execution_res,
        human_approved=True,
    )

    assert isinstance(evidence_record, HandoffEvidenceRecord)
    assert evidence_record.envelope["sender_identity"] == "ChatGPT"
    assert evidence_record.envelope["receiver_identity"] == "Jules"
    assert evidence_record.artifact_reference == "evidence_capture/sdr_exp_001_evidence_package.json"
    assert evidence_record.review_status == "approved"
    assert "timestamp" in evidence_record.to_dict()


def test_handoff_unregistered_agent():
    """Verify handoff validation fails if either sender or receiver is unregistered."""
    registry = AgentIdentityRegistry(seed_defaults=True)
    validator = AgentHandoffValidator(registry)

    envelope = AgentCommunicationEnvelope(
        mission_id="mission_sdr_001",
        sender_identity="UnknownAgent",
        receiver_identity="Jules",
        task_objective="Execute sandbox task.",
        authorized_capability="cap_sdr_sim_engine",
        constraints=[],
        expected_artifact="evidence_capture/sdr_exp_001.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )

    with pytest.raises(ValueError, match="Sender identity 'UnknownAgent' is not registered"):
        validator.validate_and_execute_handoff(envelope, {}, human_approved=False)


def test_handoff_lacks_capability_permission():
    """Verify validation fails if receiver lacks permission for the authorized capability."""
    registry = AgentIdentityRegistry(seed_defaults=True)
    validator = AgentHandoffValidator(registry)

    # ChatGPT delegating 'cap_sdr_sim_engine' to Gemini (Gemini lacks 'execute_sandbox' permission)
    envelope = AgentCommunicationEnvelope(
        mission_id="mission_sdr_001",
        sender_identity="ChatGPT",
        receiver_identity="Gemini",
        task_objective="Execute sandbox task.",
        authorized_capability="cap_sdr_sim_engine",
        constraints=[],
        expected_artifact="evidence_capture/sdr_exp_001.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )

    with pytest.raises(ValueError, match="Receiver 'Gemini' lacks required permission"):
        validator.validate_and_execute_handoff(envelope, {}, human_approved=False)


def test_handoff_violates_constraint():
    """Verify validation fails if receiver's permissions violate an envelope constraint."""
    registry = AgentIdentityRegistry(seed_defaults=True)
    validator = AgentHandoffValidator(registry)

    # ChatGPT delegating to an agent that has mutate_code permission, violating 'no-code-mutation'
    # Jules doesn't have mutate_code. Let's register a custom agent that does.
    custom_agent = AgentIdentity(
        agent_id="MutatorAgent",
        role="CodeModifier",
        permissions=["mutate_code", "execute_sandbox"],
    )
    registry.register_agent(custom_agent)

    envelope = AgentCommunicationEnvelope(
        mission_id="mission_sdr_001",
        sender_identity="ChatGPT",
        receiver_identity="MutatorAgent",
        task_objective="Modify file.",
        authorized_capability="cap_sdr_sim_engine",
        constraints=["no-code-mutation"],
        expected_artifact="evidence_capture/sdr_exp_001.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )

    with pytest.raises(ValueError, match="violates the 'no-code-mutation' task constraint"):
        validator.validate_and_execute_handoff(envelope, {}, human_approved=False)


def test_handoff_invalid_artifact_and_reference():
    """Verify validation fails if artifact format or reference prefix is invalid."""
    registry = AgentIdentityRegistry(seed_defaults=True)
    validator = AgentHandoffValidator(registry)

    # Invalid artifact format (not .json or .md)
    envelope = AgentCommunicationEnvelope(
        mission_id="mission_sdr_001",
        sender_identity="ChatGPT",
        receiver_identity="Jules",
        task_objective="Execute sandbox.",
        authorized_capability="cap_sdr_sim_engine",
        constraints=[],
        expected_artifact="invalid_format.txt",
        evidence_reference="docs/spec.md",
        review_status="pending",
    )

    with pytest.raises(ValueError, match="Invalid expected_artifact format"):
        validator.validate_and_execute_handoff(envelope, {}, human_approved=False)

    # Invalid evidence reference prefix
    envelope2 = AgentCommunicationEnvelope(
        mission_id="mission_sdr_001",
        sender_identity="ChatGPT",
        receiver_identity="Jules",
        task_objective="Execute sandbox.",
        authorized_capability="cap_sdr_sim_engine",
        constraints=[],
        expected_artifact="evidence_capture/sdr_exp_001.json",
        evidence_reference="tmp/invalid_ref.md",
        review_status="pending",
    )

    with pytest.raises(ValueError, match="Evidence reference must point to docs/ or evidence_capture/"):
        validator.validate_and_execute_handoff(envelope2, {}, human_approved=False)


def test_handoff_human_approval_authority():
    """Verify human_approved parameter correctly determines final review_status."""
    registry = AgentIdentityRegistry(seed_defaults=True)
    validator = AgentHandoffValidator(registry)

    envelope = AgentCommunicationEnvelope(
        mission_id="mission_sdr_001",
        sender_identity="ChatGPT",
        receiver_identity="Jules",
        task_objective="Execute sandbox task.",
        authorized_capability="cap_sdr_sim_engine",
        constraints=[],
        expected_artifact="evidence_capture/sdr_exp_001.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )

    # Case A: Human Approved is False -> review_status remains "pending"
    evidence_pending = validator.validate_and_execute_handoff(
        envelope, {}, human_approved=False
    )
    assert evidence_pending.review_status == "pending"

    # Case B: Human Approved is True -> review_status becomes "approved"
    evidence_approved = validator.validate_and_execute_handoff(
        envelope, {}, human_approved=True
    )
    assert evidence_approved.review_status == "approved"


def test_sequential_multi_agent_handoff_chain():
    """Verify a complete sequential handoff chain with monotonically increasing timestamps."""
    registry = AgentIdentityRegistry(seed_defaults=True)
    validator = AgentHandoffValidator(registry)

    mission_id = "mission_sdr_002_test"
    constraints = ["no-code-mutation"]

    # 1. ChatGPT -> Jules
    env_1 = AgentCommunicationEnvelope(
        mission_id=mission_id,
        sender_identity="ChatGPT",
        receiver_identity="Jules",
        task_objective="Sandbox run.",
        authorized_capability="cap_sdr_sim_engine",
        constraints=constraints,
        expected_artifact="evidence_capture/sdr_exp_002_jules_output.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )
    time.sleep(0.01)
    record_1 = validator.validate_and_execute_handoff(env_1, {}, human_approved=True)

    # 2. Jules -> Claude
    env_2 = AgentCommunicationEnvelope(
        mission_id=mission_id,
        sender_identity="Jules",
        receiver_identity="Claude",
        task_objective="Audit run.",
        authorized_capability="cap_adversarial_audit",
        constraints=constraints,
        expected_artifact="evidence_capture/sdr_exp_002_claude_audit.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )
    time.sleep(0.01)
    record_2 = validator.validate_and_execute_handoff(env_2, {}, human_approved=True)

    # 3. Claude -> Gemini
    env_3 = AgentCommunicationEnvelope(
        mission_id=mission_id,
        sender_identity="Claude",
        receiver_identity="Gemini",
        task_objective="Metrics compilation.",
        authorized_capability="cap_metrics_compilation",
        constraints=constraints,
        expected_artifact="evidence_capture/sdr_exp_002_gemini_metrics.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )
    time.sleep(0.01)
    record_3 = validator.validate_and_execute_handoff(env_3, {}, human_approved=True)

    # Check timestamps are monotonically increasing
    t1 = datetime.fromisoformat(record_1.timestamp)
    t2 = datetime.fromisoformat(record_2.timestamp)
    t3 = datetime.fromisoformat(record_3.timestamp)

    assert t1 < t2 < t3
    assert record_1.envelope["constraints"] == ["no-code-mutation"]
    assert record_2.envelope["constraints"] == ["no-code-mutation"]
    assert record_3.envelope["constraints"] == ["no-code-mutation"]


def test_agent_permission_boundaries():
    """Verify distinct permission boundaries are strictly enforced across models."""
    registry = AgentIdentityRegistry(seed_defaults=True)
    validator = AgentHandoffValidator(registry)

    # Jules can execute sandbox
    env_jules = AgentCommunicationEnvelope(
        mission_id="mission_test",
        sender_identity="ChatGPT",
        receiver_identity="Jules",
        task_objective="Sandbox run.",
        authorized_capability="cap_sdr_sim_engine",
        constraints=[],
        expected_artifact="evidence_capture/sdr_exp_001.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )
    record_jules = validator.validate_and_execute_handoff(env_jules, {}, human_approved=True)
    assert record_jules.review_status == "approved"

    # Claude cannot execute sandbox
    env_claude = AgentCommunicationEnvelope(
        mission_id="mission_test",
        sender_identity="ChatGPT",
        receiver_identity="Claude",
        task_objective="Sandbox run.",
        authorized_capability="cap_sdr_sim_engine",
        constraints=[],
        expected_artifact="evidence_capture/sdr_exp_001.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )
    with pytest.raises(ValueError, match="lacks required permission 'execute_sandbox'"):
        validator.validate_and_execute_handoff(env_claude, {}, human_approved=True)
