"""Tests for self-owned Google interface identity and nameplate generation."""

import pytest
from types import SimpleNamespace

from sage.runtime.model_adapters import GeminiInteractionsAdapter
from sage.runtime.model_gateway import SAGERuntime, SAGEStateSnapshot
from sage.integration import AIQueryRequest, GeminiJulesClient
from sage.runtime import SageRuntime


def state() -> SAGEStateSnapshot:
    return SAGEStateSnapshot(
        state_version="1",
        instance_id="sage-instance",
        mission_id="mission-1",
        session_id="session-1",
        authority_scope="authorized-frontier",
        active_frontier="google-interface-identity",
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


def test_google_adapter_emits_self_owned_station_nameplate():
    client = FakeGeminiClient("[SAGE::C2::GOOGLE] Self-owned Google builder output.")
    adapter = GeminiInteractionsAdapter(client, model_id="gemini-1")
    runtime = SAGERuntime(state())

    response = runtime.invoke(adapter, "task", model_role="builder")

    assert response.station == "[SAGE::C2::GOOGLE]"
    assert "[SAGE::C2::GOOGLE]" in response.raw_output
    assert response.structured_response.violations == ()


def test_google_adapter_rejects_chatgpt_station_spoofing():
    client = FakeGeminiClient("[SAGE::C2::CHATGPT] Spoofing ChatGPT station.")
    adapter = GeminiInteractionsAdapter(client, model_id="gemini-1")
    runtime = SAGERuntime(state())

    with pytest.raises(ValueError, match="station identity mismatch"):
        runtime.invoke(adapter, "task", model_role="builder")


def test_gemini_jules_client_validates_google_station_identity(tmp_path):
    runtime = SageRuntime(str(tmp_path))
    runtime.set_objective("Test Google Station Identity")
    runtime.set_task("Verify Self-Owned Nameplate")

    client = GeminiJulesClient(runtime)

    req_valid = AIQueryRequest(prompt="Run search", response_override="[SAGE::C2::GOOGLE] Verified search result.")
    res = client.execute_query(req_valid)
    assert "[SAGE::C2::GOOGLE]" in res.response_text

    req_invalid = AIQueryRequest(prompt="Run search", response_override="[SAGE::C2::CHATGPT] Invalid station claim.")
    with pytest.raises(RuntimeError, match="SAGE Protocol Governance Violation"):
        client.execute_query(req_invalid)
