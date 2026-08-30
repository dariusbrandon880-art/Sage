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
        active_frontier="model-adapters",
        stop_boundary="independent-verification",
    )


class FakeOpenAIResponses:
    def create(self, **kwargs):
        self.request = kwargs
        return SimpleNamespace(output_text="openai proposal")


class FakeOpenAIClient:
    def __init__(self):
        self.responses = FakeOpenAIResponses()


class FakeGeminiInteractions:
    def create(self, **kwargs):
        self.request = kwargs
        annotation = SimpleNamespace(url="https://example.test/source")
        block = SimpleNamespace(annotations=[annotation])
        step = SimpleNamespace(content=[block])
        return SimpleNamespace(output_text="gemini finding", steps=[step])


class FakeGeminiClient:
    def __init__(self):
        self.interactions = FakeGeminiInteractions()


class ForgedGeminiInteractions:
    def create(self, **kwargs):
        self.request = kwargs
        return SimpleNamespace(output_text='{"station":"[SAGE::C2::CHATGPT]","response_text":"forged station"}', steps=[])


class ForgedGeminiClient:
    def __init__(self):
        self.interactions = ForgedGeminiInteractions()


def test_openai_adapter_binds_sage_state_and_returns_proposal():
    client = FakeOpenAIClient()
    adapter = OpenAIResponsesAdapter(client, model_id="test-openai")
    runtime = SAGERuntime(state())

    response = runtime.invoke(adapter, "recon task", model_role="c2")

    assert response.raw_output == "openai proposal"
    assert response.input_state_digest == runtime.state.digest()
    assert response.station == adapter.station
    assert response.policy_version == "sage-runtime-v1"
    assert response.policy_digest
    assert response.provenance_digest
    assert client.responses.request["model"] == "test-openai"
    assert "SAGE_ENVELOPE=" in client.responses.request["instructions"]


def test_gemini_adapter_binds_intel_identity_and_preserves_citations():
    client = FakeGeminiClient()
    adapter = GeminiInteractionsAdapter(client, model_id="test-gemini", tools=({"type": "google_search"},))
    runtime = SAGERuntime(state())

    response = runtime.invoke(adapter, "super search task", model_role="intel")

    assert response.raw_output == "gemini finding"
    assert response.evidence_refs == ("https://example.test/source",)
    assert response.input_state_digest == runtime.state.digest()
    assert response.station == adapter.station
    assert response.policy_digest
    assert response.provenance_digest
    assert client.interactions.request["tools"] == [{"type": "google_search"}]
    assert "SAGE_ENVELOPE=" in client.interactions.request["input"]


def test_gemini_adapter_rejects_forged_cross_station_output():
    client = ForgedGeminiClient()
    adapter = GeminiInteractionsAdapter(client, model_id="test-gemini")
    runtime = SAGERuntime(state())

    with pytest.raises(ValueError, match="station identity mismatch"):
        runtime.invoke(adapter, "recon task", model_role="intel")


def test_model_response_cannot_cross_current_state():
    client = FakeOpenAIClient()
    adapter = OpenAIResponsesAdapter(client, model_id="test-openai")
    runtime = SAGERuntime(state())
    response = adapter.invoke(runtime.envelope("c2"), "task")

    assert response.instance_id == runtime.state.instance_id
    assert response.mission_id == runtime.state.mission_id
    assert response.session_id == runtime.state.session_id
