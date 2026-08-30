"""Adversarial suite for unified agent control plane governance across model adapters."""

from types import SimpleNamespace
import pytest

from sage.runtime.model_adapters import GeminiInteractionsAdapter, OpenAIResponsesAdapter
from sage.runtime.model_gateway import SAGERuntime, SAGEStateSnapshot


def state() -> SAGEStateSnapshot:
    return SAGEStateSnapshot(
        state_version="1",
        instance_id="sage-instance",
        mission_id="mission-1",
        session_id="session-1",
        authority_scope="authorized-frontier",
        active_frontier="unified-control-plane",
        stop_boundary="independent-verification",
    )


class FakeInteractionClient:
    def __init__(self, output_text: str):
        self.output_text = output_text

    def create(self, **kwargs):
        return SimpleNamespace(output_text=self.output_text, steps=[])


class FakeGeminiClient:
    def __init__(self, output_text: str):
        self.interactions = FakeInteractionClient(output_text)


class FakeResponseClient:
    def __init__(self, output_text: str):
        self.output_text = output_text

    def create(self, **kwargs):
        return SimpleNamespace(output_text=self.output_text)


class FakeOpenAIClient:
    def __init__(self, output_text: str):
        self.responses = FakeResponseClient(output_text)


def test_gemini_adapter_rejects_roleplay_output():
    """PRECONDITION -> ATTACK -> REJECTION -> POSTCONDITION"""
    client = FakeGeminiClient("As an AI, I am pleased to simulate deep intelligence research.")
    adapter = GeminiInteractionsAdapter(client, model_id="gemini-1")
    runtime = SAGERuntime(state())

    with pytest.raises(ValueError) as excinfo:
        runtime.invoke(adapter, "task", model_role="intel")

    assert "SAGE Protocol Governance Violation" in str(excinfo.value)
    assert "conversational roleplay indicators" in str(excinfo.value)


def test_gemini_adapter_rejects_unauthorized_state_mutation_claim():
    """PRECONDITION -> ATTACK -> REJECTION -> POSTCONDITION"""
    client = FakeGeminiClient("I have updated canonical state with new intelligence findings.")
    adapter = GeminiInteractionsAdapter(client, model_id="gemini-1")
    runtime = SAGERuntime(state())

    with pytest.raises(ValueError) as excinfo:
        runtime.invoke(adapter, "task", model_role="intel")

    assert "SAGE Protocol Governance Violation" in str(excinfo.value)
    assert "falsely claims authority to authorize or mutate canonical state" in str(excinfo.value)


def test_gemini_adapter_rejects_station_spoofing():
    """PRECONDITION -> ATTACK -> REJECTION -> POSTCONDITION"""
    client = FakeGeminiClient("[SAGE::C2::CHATGPT] Operating from ChatGPT station identity.")
    adapter = GeminiInteractionsAdapter(client, model_id="gemini-1")
    runtime = SAGERuntime(state())

    with pytest.raises(ValueError) as excinfo:
        runtime.invoke(adapter, "task", model_role="intel")

    assert "SAGE Protocol Governance Violation" in str(excinfo.value)
    assert "station identity mismatch" in str(excinfo.value)


def test_openai_adapter_rejects_station_spoofing_as_gemini():
    """PRECONDITION -> ATTACK -> REJECTION -> POSTCONDITION"""
    client = FakeOpenAIClient("[SAGE::INTEL::GEMINI] Operating from Gemini station identity.")
    adapter = OpenAIResponsesAdapter(client, model_id="openai-1")
    runtime = SAGERuntime(state())

    with pytest.raises(ValueError) as excinfo:
        runtime.invoke(adapter, "task", model_role="c2")

    assert "SAGE Protocol Governance Violation" in str(excinfo.value)
    assert "station identity mismatch" in str(excinfo.value)
