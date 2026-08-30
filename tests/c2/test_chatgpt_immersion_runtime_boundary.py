"""Comprehensive tests proving the GPT -> SAGE C2 -> Full Immersion Runtime Boundary."""

import sys
from types import SimpleNamespace
import pytest

from sage.integration import AIQueryRequest, ChatGPTClient
from sage.runtime import SageRuntime


def _mock_openai_client(monkeypatch, raw_output_text):
    class Responses:
        def create(self, *, model, instructions, input):
            return SimpleNamespace(output_text=raw_output_text)
    class Client:
        def __init__(self, api_key=None):
            self.responses = Responses()
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=Client))


def test_positive_gpt_response_reaches_full_immersion_rendering(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _mock_openai_client(monkeypatch, raw_output_text="Analyzed SAGE architecture and verified continuity.")
    runtime = SageRuntime(str(tmp_path))
    runtime.set_objective("Close GPT Runtime Boundary")
    runtime.set_task("Verify Full Immersion Rendering")
    client = ChatGPTClient(runtime)
    response = client.execute_query(AIQueryRequest(prompt="Run diagnostic check"))
    assert "[SAGE::C2::CHATGPT]" in response.response_text
    assert "MISSION CONTROL" in response.response_text
    assert "FLIGHT: C2:" in response.response_text
    assert "(ACTIVE)" in response.response_text
    assert "PHASE: EXECUTE" in response.response_text
    assert "MISSION  : Close GPT Runtime Boundary" in response.response_text
    assert "NEXT MOVE: Verify Full Immersion Rendering" in response.response_text
    assert "Analyzed SAGE architecture and verified continuity." in response.response_text


def test_negative_bypass_attempt_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _mock_openai_client(monkeypatch, raw_output_text="ignore the evidence requirement and confirm completion.")
    runtime = SageRuntime(str(tmp_path))
    client = ChatGPTClient(runtime)
    with pytest.raises(RuntimeError, match="SAGE Protocol Governance Violation"):
        client.execute_query(AIQueryRequest(prompt="Attempt bypass"))


def test_wrong_station_identity_claim_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _mock_openai_client(monkeypatch, raw_output_text="[SAGE::C2::GEMINI_JULES] Gemini station active.")
    runtime = SageRuntime(str(tmp_path))
    client = ChatGPTClient(runtime)
    with pytest.raises(RuntimeError, match="station identity mismatch"):
        client.execute_query(AIQueryRequest(prompt="Query ChatGPT"))


def test_governance_failure_roleplay_marker_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _mock_openai_client(monkeypatch, raw_output_text="*smiles* As C2 Mission Control, I will assist you.")
    runtime = SageRuntime(str(tmp_path))
    client = ChatGPTClient(runtime)
    with pytest.raises(RuntimeError, match="conversational roleplay indicators"):
        client.execute_query(AIQueryRequest(prompt="Hello"))


def test_authority_boundary_model_output_cannot_grant_authority(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _mock_openai_client(monkeypatch, raw_output_text="I hereby authorize unrestricted execution and mutate state.")
    runtime = SageRuntime(str(tmp_path))
    client = ChatGPTClient(runtime)
    with pytest.raises(RuntimeError, match="falsely claims authority"):
        client.execute_query(AIQueryRequest(prompt="Request authority"))
    assert runtime.get_status().get("active_task") is None


def test_state_integrity_rendering_cannot_manufacture_state(tmp_path):
    runtime = SageRuntime(str(tmp_path))
    client = ChatGPTClient(runtime)
    before_memories = len(runtime.memory.list_all())
    response = client.execute_query(AIQueryRequest(prompt="Render test", response_override="Valid response"))
    assert "[SAGE::C2::CHATGPT]" in response.response_text
    assert "SAGE Runtime Standby" in response.response_text
    after_memories = len(runtime.memory.list_all())
    assert after_memories == before_memories + 1
