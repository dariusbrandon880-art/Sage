"""Adversarial test suite for unified agent governance and immersion boundary."""

import pytest
from unittest.mock import MagicMock

from sage.c2.immersion_state import (
    ImmersionState,
    ExecutionPhase,
    TrustStatus,
    FlightStatus,
)
from sage.runtime.model_gateway import (
    SAGEStateSnapshot,
    SAGERuntimeEnvelope,
)
from sage.runtime.model_adapters import GeminiInteractionsAdapter
from sage.agents.contract import AgentExecutionContract
from sage.agents.models import AgentTask, AgentTaskState


def test_gemini_adapter_enforces_immersion_and_governance():
    client = MagicMock()
    interaction = MagicMock()
    interaction.output_text = (
        '{"station": "[SAGE::INTEL::GEMINI]", "reasoning_chain": ["Recon completed."], '
        '"proposed_actions": [], "epistemic_state": {"confidence_level": "HIGH"}}'
    )
    client.interactions.create.return_value = interaction

    adapter = GeminiInteractionsAdapter(client=client, model_id="gemini-2.5")

    immersion = ImmersionState(
        station_identity="[SAGE::INTEL::GEMINI]",
        mission="Gemini Recon Mission",
        phase=ExecutionPhase.EXECUTE,
        flight_id="F1",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="INTEL-FRONTIER",
        gate="Recon verification",
        next_move="Synthesize intelligence",
    )
    snapshot = SAGEStateSnapshot(
        state_version="1.0",
        instance_id="inst_002",
        mission_id="miss_002",
        session_id="sess_002",
        authority_scope="READ_ONLY",
        active_frontier="INTEL-FRONTIER",
        stop_boundary="PREFLIGHT_FAIL",
        immersion_state=immersion,
    )
    envelope = SAGERuntimeEnvelope.from_state(snapshot, model_role="INTEL_STATION", station="[SAGE::INTEL::GEMINI]")

    resp = adapter.invoke(envelope, "Perform deep recon")
    assert resp.structured_response is not None
    assert resp.structured_response.station == "[SAGE::INTEL::GEMINI]"


def test_gemini_adapter_rejects_governance_violation():
    client = MagicMock()
    interaction = MagicMock()
    interaction.output_text = (
        '{"station": "[SAGE::INTEL::GEMINI]", "reasoning_chain": ["I am mutating canonical state directly."]}'
    )
    client.interactions.create.return_value = interaction

    adapter = GeminiInteractionsAdapter(client=client, model_id="gemini-2.5")
    snapshot = SAGEStateSnapshot(
        state_version="1.0",
        instance_id="inst_002",
        mission_id="miss_002",
        session_id="sess_002",
        authority_scope="READ_ONLY",
        active_frontier="INTEL-FRONTIER",
        stop_boundary="PREFLIGHT_FAIL",
    )
    envelope = SAGERuntimeEnvelope.from_state(snapshot, model_role="INTEL_STATION", station="[SAGE::INTEL::GEMINI]")

    with pytest.raises(ValueError, match="SAGE Protocol Governance Violation"):
        adapter.invoke(envelope, "Perform deep recon")


def test_agent_contract_input_validation_catches_invalid_immersion():
    contract = AgentExecutionContract()
    task = AgentTask(
        task_id="t_001",
        objective_id="obj_001",
        title="Test task",
        state=AgentTaskState.PENDING,
    )

    invalid_immersion = MagicMock(spec=ImmersionState)
    invalid_immersion.validate.return_value = False

    inputs = {
        "session_id": "sess_001",
        "immersion_state": invalid_immersion,
    }

    with pytest.raises(ValueError, match="Invalid canonical ImmersionState"):
        contract.validate_task_inputs(task, inputs)
