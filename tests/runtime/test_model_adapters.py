import json
from types import SimpleNamespace

import pytest

from sage.runtime.model_adapters import GeminiInteractionsAdapter, OpenAIResponsesAdapter
from sage.runtime.model_gateway import SAGERuntime, SAGEStateSnapshot


def state() -> SAGEStateSnapshot:
    return SAGEStateSnapshot(state_version="1", instance_id="sage-instance", mission_id="mission-1", session_id="session-1", authority_scope="authorized-frontier", active_frontier="model-adapters", stop_boundary="independent-verification")


def governed(station: str, text: str = "finding") -> str:
    return json.dumps({"station": station, "reasoning_chain": [text], "proposed_actions": [], "epistemic_state": {"confidence_level": "MEDIUM"}, "evidence_refs": []})


class FakeOpenAIResponses:
    def __init__(self, output_text: str): self.output_text = output_text
    def create(self, **kwargs): self.request = kwargs; return SimpleNamespace(output_text=self.output_text)


class FakeOpenAIClient:
    def __init__(self, output_text: str): self.responses = FakeOpenAIResponses(output_text)


class FakeGeminiInteractions:
    def __init__(self, output_text: str): self.output_text = output_text
    def create(self, **kwargs):
        self.request = kwargs
        annotation = SimpleNamespace(url="https://example.test/source")
        return SimpleNamespace(output_text=self.output_text, steps=[SimpleNamespace(content=[SimpleNamespace(annotations=[annotation])])])


class FakeGeminiClient:
    def __init__(self, output_text: str): self.interactions = FakeGeminiInteractions(output_text)


def test_openai_adapter_binds_shared_governance_context():
    client = FakeOpenAIClient(governed("[SAGE::C2::CHATGPT]", "openai proposal"))
    adapter = OpenAIResponsesAdapter(client, model_id="test-openai")
    runtime = SAGERuntime(state())
    response = runtime.invoke(adapter, "recon task", model_role="c2")
    assert response.raw_output
    assert response.input_state_digest == runtime.state.digest()
    assert response.station == adapter.station
    assert response.policy_digest == runtime.envelope("c2", station=adapter.station).policy_digest
    assert client.responses.request["model"] == "test-openai"
    assert "SAGE_ENVELOPE=" in client.responses.request["instructions"]


def test_gemini_adapter_uses_same_governor_and_preserves_citations():
    client = FakeGeminiClient(governed("[SAGE::INTEL::GEMINI]", "gemini finding"))
    adapter = GeminiInteractionsAdapter(client, model_id="test-gemini", tools=({"type": "google_search"},))
    runtime = SAGERuntime(state())
    response = runtime.invoke(adapter, "super search task", model_role="intel")
    assert response.raw_output
    assert response.evidence_refs == ("https://example.test/source",)
    assert response.station == adapter.station
    assert response.input_state_digest == runtime.state.digest()
    assert response.policy_version == runtime.policy_version
    assert client.interactions.request["tools"] == [{"type": "google_search"}]
    assert "SAGE_ENVELOPE=" in client.interactions.request["input"]


def test_gemini_rejects_cross_station_output_before_reconciliation():
    client = FakeGeminiClient(governed("[SAGE::C2::CHATGPT]", "spoofed station"))
    adapter = GeminiInteractionsAdapter(client, model_id="test-gemini")
    with pytest.raises(ValueError, match="SAGE Protocol Governance Violation"):
        adapter.invoke(SAGERuntime(state()).envelope("intel", station=adapter.station), "task")


def test_gemini_rejects_model_authority_claim_before_reconciliation():
    client = FakeGeminiClient(governed("[SAGE::INTEL::GEMINI]", "I hereby authorize this canonical state mutation"))
    adapter = GeminiInteractionsAdapter(client, model_id="test-gemini")
    with pytest.raises(ValueError, match="SAGE Protocol Governance Violation"):
        adapter.invoke(SAGERuntime(state()).envelope("intel", station=adapter.station), "task")


def test_model_response_cannot_cross_current_state():
    client = FakeOpenAIClient(governed("[SAGE::C2::CHATGPT]"))
    adapter = OpenAIResponsesAdapter(client, model_id="test-openai")
    runtime = SAGERuntime(state())
    response = adapter.invoke(runtime.envelope("c2"), "task")
    assert response.instance_id == runtime.state.instance_id
    assert response.mission_id == runtime.state.mission_id
    assert response.session_id == runtime.state.session_id
