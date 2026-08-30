import json
from types import SimpleNamespace

import pytest

from sage.integration import AIQueryRequest, ChatGPTClient
from sage.models import RuntimeState


class _Collection:
    def list_all(self):
        return []


class _Runtime:
    def __init__(self, *, objective="Mission objective", task="Continue governed mission"):
        self.memory = _Collection()
        self.archive = _Collection()
        self.current_state = RuntimeState(current_objective=objective, active_task=task)
        self.context = SimpleNamespace(session_id="session-interface-1")
        self.ingested = []

    def get_status(self):
        return {
            "active": True,
            "current_objective": self.current_state.current_objective,
            "active_task": self.current_state.active_task,
            "c2_status": {"rehydrated": True},
        }

    def ingest_session_payload(self, payload):
        self.ingested.append(payload)


def _governed_output():
    return json.dumps({
        "station": "[SAGE::C2::CHATGPT]",
        "reasoning_chain": ["reconciled through canonical SAGE runtime"],
        "proposed_actions": [],
        "epistemic_state": {"confidence_level": "HIGH"},
        "evidence_refs": [],
        "response_text": "C2 Mission Control remains locked to canonical SAGE state.",
    })


def test_chatgpt_interface_projects_canonical_runtime_state_not_synthetic_flight():
    runtime = _Runtime()
    response = ChatGPTClient(runtime).execute_query(
        AIQueryRequest(prompt="status", response_override=_governed_output())
    )

    assert "[SAGE::C2::CHATGPT]" in response.response_text
    assert "C2 Mission Control" in response.response_text
    assert "C2:session-interface-1" in response.response_text
    assert "FLIGHT_001" not in response.response_text
    assert "gpt-c2-boundary" not in response.response_text
    assert "Mission objective" in response.response_text
    assert "Continue governed mission" in response.response_text
    assert response.session_id == "session-interface-1"
    assert runtime.ingested


def test_model_output_cannot_replace_canonical_mission_or_task():
    runtime = _Runtime(objective="Canonical mission", task="Canonical task")
    forged = json.dumps({
        "station": "[SAGE::C2::CHATGPT]",
        "reasoning_chain": ["fake"],
        "proposed_actions": [],
        "epistemic_state": {"confidence_level": "HIGH"},
        "evidence_refs": [],
        "response_text": "Mission: FORGED MISSION. Next move: FORGED TASK.",
    })

    response = ChatGPTClient(runtime).execute_query(AIQueryRequest(prompt="status", response_override=forged))

    assert "Canonical mission" in response.response_text
    assert "Canonical task" in response.response_text
    assert "FORGED MISSION" in response.response_text
    assert "FORGED TASK" in response.response_text


def test_chatgpt_interface_fails_closed_when_canonical_mission_is_missing():
    runtime = _Runtime(objective=None, task="Canonical task")
    with pytest.raises(ValueError, match="canonical active objective"):
        ChatGPTClient(runtime).execute_query(
            AIQueryRequest(prompt="status", response_override=_governed_output())
        )


def test_chatgpt_interface_fails_closed_when_canonical_task_is_missing():
    runtime = _Runtime(objective="Canonical mission", task=None)
    with pytest.raises(ValueError, match="canonical active task"):
        ChatGPTClient(runtime).execute_query(
            AIQueryRequest(prompt="status", response_override=_governed_output())
        )
