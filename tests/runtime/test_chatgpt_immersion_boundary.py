"""Adversarial verification suite for ChatGPT immersion and runtime boundary."""

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
    SAGEProtocolGovernor,
    SAGERuntime,
)
from sage.runtime.model_adapters import OpenAIResponsesAdapter, _system_instructions


def test_system_instructions_auto_injects_immersion_projection():
    immersion = ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission="Adversarial Verification Mission",
        phase=ExecutionPhase.EXECUTE,
        flight_id="F4",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="CHATGPT-RUNTIME-BOUNDARY",
        gate="Zero bypass verification",
        next_move="Execute adversarial test suite",
    )
    snapshot = SAGEStateSnapshot(
        state_version="1.0",
        instance_id="inst_001",
        mission_id="miss_001",
        session_id="sess_001",
        authority_scope="READ_ONLY",
        active_frontier="CHATGPT-RUNTIME-BOUNDARY",
        stop_boundary="PREFLIGHT_FAIL",
        immersion_state=immersion,
    )
    envelope = SAGERuntimeEnvelope.from_state(snapshot, model_role="C2_CONTROLLER")

    instructions = _system_instructions(envelope)
    assert "CANONICAL IMMERSION PROJECTION BOUNDARY (MANDATORY):" in instructions
    assert "[SAGE::C2::CHATGPT]" in instructions
    assert "SAGE MISSION CONTROL HUD" in instructions
    assert "FRONTIER : CHATGPT-RUNTIME-BOUNDARY" in instructions


def test_invalid_immersion_state_fails_closed():
    with pytest.raises(ValueError, match="station_identity cannot be empty"):
        ImmersionState(
            station_identity="",
            mission="Fail closed test",
            phase=ExecutionPhase.EXECUTE,
            flight_id="F1",
            flight_status=FlightStatus.ACTIVE,
            trust_status=TrustStatus.VERIFIED,
            frontier="FRONTIER_TEST",
            gate="Gate test",
            next_move="Next move test",
        )


def test_protocol_governor_rejects_state_mutation_and_bypass_claims():
    raw_output_mutation = (
        '{"station": "[SAGE::C2::CHATGPT]", "reasoning_chain": ["I am mutating canonical state directly and promoting this capability autonomously."]}'
    )
    res = SAGEProtocolGovernor.validate_and_parse(raw_output_mutation)
    assert len(res.violations) > 0
    assert any("unauthorized direct state mutation" in v for v in res.violations)


def test_runtime_reconcile_rejects_stale_or_mismatched_digests():
    snapshot_a = SAGEStateSnapshot(
        state_version="1.0",
        instance_id="inst_001",
        mission_id="miss_001",
        session_id="sess_001",
        authority_scope="READ_ONLY",
        active_frontier="FRONTIER_A",
        stop_boundary="STOP",
    )
    runtime = SAGERuntime(snapshot_a)

    mock_response = MagicMock()
    mock_response.instance_id = "inst_001"
    mock_response.mission_id = "miss_001"
    mock_response.session_id = "sess_001"
    mock_response.input_state_digest = "stale_or_invalid_digest"

    with pytest.raises(ValueError, match="input state digest mismatch"):
        runtime.reconcile(mock_response)
