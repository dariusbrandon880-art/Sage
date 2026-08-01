"""SAGE Experimental Capability Enforcement Hypervisor Tests."""

import pytest
from sage.experimental.agents.models import AgentCommunicationEnvelope
from sage.experimental.agents.registry import AgentIdentityRegistry
from sage.experimental.agents.validation import AgentHandoffValidator
from sage.experimental.act.enforcement import CapabilityEnforcementHypervisor


@pytest.fixture
def active_hypervisor():
    """Fixture providing an active, default-seeded hypervisor."""
    registry = AgentIdentityRegistry(seed_defaults=True)
    validator = AgentHandoffValidator(registry)
    return CapabilityEnforcementHypervisor(validator)


def test_enforce_handoff_gate_success(active_hypervisor):
    """Verify that handoff gate permits authorized capabilities with valid, approved passports."""
    # 1. Prepare and register a valid, human-approved Capability Passport
    passport = {
        "capability_id": "cap_sdr_sim_engine",
        "name": "SDR Simulation Engine",
        "purpose": "Simulate and validate multi-agent tasks.",
        "lifecycle_state": "validated",
        "validation_strategy": "Run isolated playbooks.",
        "evidence_path": "docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        "dependencies": [],
        "human_signoff": {
            "signer": "supervisor_v1",
            "timestamp": "2026-07-30T12:00:00Z",
            "approved": True,
        },
    }
    active_hypervisor.register_passport(passport)

    # 2. Build communication envelope
    envelope = AgentCommunicationEnvelope(
        mission_id="mission_val_001",
        sender_identity="ChatGPT",
        receiver_identity="Jules",
        task_objective="Execute sandbox simulation run.",
        authorized_capability="cap_sdr_sim_engine",
        constraints=["no-code-mutation"],
        expected_artifact="evidence_capture/sdr_exp_002.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )

    execution_res = {"status": "SUCCESS"}

    # 3. enforce gate
    trace = active_hypervisor.enforce_handoff_gate(
        envelope=envelope,
        execution_result=execution_res,
        human_approved=True,
    )

    assert trace["status"] == "AUTHORIZED_EXECUTION"
    assert trace["capability_id"] == "cap_sdr_sim_engine"
    assert trace["enforcement_telemetry"]["passport_verified"] is True


def test_enforce_handoff_gate_unpassported_fails(active_hypervisor):
    """Verify that handoff gate blocks unregistered capabilities immediately."""
    envelope = AgentCommunicationEnvelope(
        mission_id="mission_val_001",
        sender_identity="ChatGPT",
        receiver_identity="Jules",
        task_objective="Execute unpassported task.",
        authorized_capability="cap_unregistered_feature",
        constraints=[],
        expected_artifact="evidence_capture/sdr_exp_002.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )

    with pytest.raises(ValueError, match="lacks a registered Capability Passport"):
        active_hypervisor.enforce_handoff_gate(envelope, {}, human_approved=True)


def test_enforce_handoff_gate_unapproved_passport_fails(active_hypervisor):
    """Verify that handoff gate blocks registered capabilities if they lack active human approval."""
    # Register passport with approved = False
    unapproved_passport = {
        "capability_id": "cap_sdr_sim_engine",
        "name": "SDR Simulation Engine",
        "purpose": "Simulate and validate multi-agent tasks.",
        "lifecycle_state": "proposed",
        "validation_strategy": "Run isolated playbooks.",
        "evidence_path": "docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        "dependencies": [],
        "human_signoff": {
            "signer": "supervisor_v1",
            "timestamp": "2026-07-30T12:00:00Z",
            "approved": False,
        },
    }
    active_hypervisor.register_passport(unapproved_passport)

    envelope = AgentCommunicationEnvelope(
        mission_id="mission_val_001",
        sender_identity="ChatGPT",
        receiver_identity="Jules",
        task_objective="Execute simulation task.",
        authorized_capability="cap_sdr_sim_engine",
        constraints=[],
        expected_artifact="evidence_capture/sdr_exp_002.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )

    with pytest.raises(ValueError, match="is not human-approved"):
        active_hypervisor.enforce_handoff_gate(envelope, {}, human_approved=True)


def test_enforce_handoff_gate_underlying_validation_fails(active_hypervisor):
    """Verify that handoff gate bubbles up permission failures when receiver lacks required permissions."""
    passport = {
        "capability_id": "cap_sdr_sim_engine",
        "name": "SDR Simulation Engine",
        "purpose": "Simulate and validate multi-agent tasks.",
        "lifecycle_state": "validated",
        "validation_strategy": "Run isolated playbooks.",
        "evidence_path": "docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        "dependencies": [],
        "human_signoff": {
            "signer": "supervisor_v1",
            "timestamp": "2026-07-30T12:00:00Z",
            "approved": True,
        },
    }
    active_hypervisor.register_passport(passport)

    # Gemini lacks 'execute_sandbox' (cannot run cap_sdr_sim_engine)
    envelope = AgentCommunicationEnvelope(
        mission_id="mission_val_001",
        sender_identity="ChatGPT",
        receiver_identity="Gemini",
        task_objective="Execute sandbox simulation run.",
        authorized_capability="cap_sdr_sim_engine",
        constraints=[],
        expected_artifact="evidence_capture/sdr_exp_002.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )

    with pytest.raises(ValueError, match="Receiver 'Gemini' lacks required permission"):
        active_hypervisor.enforce_handoff_gate(envelope, {}, human_approved=True)
