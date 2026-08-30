import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from sage.c2.chatgpt_sage_boundary import (
    execute_sage_bound_chatgpt,
    execute_sage_bound_chatgpt_from_legacy_runtime,
)
from sage.c2.immersion_state import ExecutionPhase, FlightStatus, ImmersionState, TrustStatus
from sage.runtime.model_gateway import SAGEStateSnapshot


@pytest.fixture
def states():
    runtime_state = SAGEStateSnapshot(
        state_version="test-v1",
        instance_id="instance-test",
        mission_id="mission-test",
        session_id="session-test",
        authority_scope="human-operator",
        active_frontier="GPT-SAGE BOUNDARY",
        stop_boundary="fail-closed",
    )
    immersion_state = ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission="GPT-SAGE Boundary",
        phase=ExecutionPhase.EXECUTE,
        flight_id="F1",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.UNVERIFIED,
        frontier="GPT-SAGE BOUNDARY",
        gate="response contract",
        next_move="verify",
    )
    return runtime_state, immersion_state


def structured_output():
    return json.dumps(
        {
            "station": "[SAGE::C2::CHATGPT]",
            "reasoning_chain": ["boundary candidate"],
            "proposed_actions": [],
            "epistemic_state": {
                "confidence_level": "UNKNOWN",
                "validated_facts": [],
                "unverified_hypotheses": [],
                "known_unknowns": [],
            },
            "evidence_refs": [],
        }
    )


def test_gpt_turn_crosses_governance_then_render(states):
    runtime_state, immersion_state = states
    result = execute_sage_bound_chatgpt(
        runtime_state=runtime_state,
        immersion_state=immersion_state,
        task="render governed response",
        response_override=structured_output(),
    )
    assert result.state_digest == runtime_state.digest()
    assert result.raw_output
    assert "[SAGE::C2::CHATGPT]" in result.rendered_output
    assert "C2 Mission Control" in result.rendered_output
    assert "GPT-SAGE Boundary" in result.rendered_output


def test_missing_station_fails_before_render(states):
    runtime_state, immersion_state = states
    bad = json.loads(structured_output())
    bad["station"] = "[SPOOFED]"
    with pytest.raises(RuntimeError, match="SAGE Protocol Governance Violation"):
        execute_sage_bound_chatgpt(
            runtime_state=runtime_state,
            immersion_state=immersion_state,
            task="spoof station",
            response_override=json.dumps(bad),
        )


def test_invalid_immersion_state_cannot_be_constructed():
    with pytest.raises(ValueError, match="mission cannot be empty"):
        ImmersionState(
            station_identity="[SAGE::C2::CHATGPT]",
            mission="",
            phase=ExecutionPhase.EXECUTE,
            flight_id="F1",
            flight_status=FlightStatus.ACTIVE,
            trust_status=TrustStatus.UNVERIFIED,
            frontier="GPT-SAGE BOUNDARY",
            gate="response contract",
            next_move="verify",
        )


def test_legacy_chatgpt_integration_contains_no_provider_call():
    source = Path("sage/integration.py").read_text()
    assert "openai.OpenAI" not in source
    assert "execute_sage_bound_chatgpt_from_legacy_runtime" in source


def test_legacy_runtime_hydrates_new_immersion_fields():
    runtime = SimpleNamespace(
        current_state=SimpleNamespace(current_objective="Legacy C2 Objective"),
        get_status=lambda: {
            "current_objective": "Canonical Objective",
            "active_task": "Continue governed task",
            "governance_status": "ACTIVE",
        },
    )
    result = execute_sage_bound_chatgpt_from_legacy_runtime(
        runtime=runtime,
        session_id="legacy-session",
        task="continue legacy caller through boundary",
        c2_context={
            "active_objective": "Canonical Objective",
            "active_task": "Continue governed task",
            "governance_status": "ACTIVE",
        },
        response_override=structured_output(),
    )
    assert result.state_digest
    assert "Canonical Objective" in result.rendered_output
    assert "Continue governed task" in result.rendered_output
