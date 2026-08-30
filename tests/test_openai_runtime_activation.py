"""Focused tests for the ChatGPT-as-SAGE OpenAI Responses boundary."""

import sys
from types import SimpleNamespace

import pytest


def _c2_context():
    return {
        "canonical": "state",
        "mission": "ChatGPT C2 Boundary",
        "mission_id": "chatgpt-c2-boundary",
        "frontier": "GPT-SAGE BOUNDARY",
        "gate": "response contract",
        "next_move": "reconcile response",
        "stop_boundary": "fail-closed",
    }

def _structured_output(text="SAGE output"):
    import json
    return json.dumps({
        "station": "[SAGE::C2::CHATGPT]",
        "reasoning_chain": [text],
        "proposed_actions": [],
        "epistemic_state": {
            "confidence_level": "UNKNOWN",
            "validated_facts": [],
            "unverified_hypotheses": [],
            "known_unknowns": [],
        },
        "evidence_refs": [],
    })


def _install_openai(monkeypatch, output_text=None, error=None):
    class Responses:
        def create(self, *, model, instructions, input):
            assert model
            assert "C2 Operating Context" in instructions
            assert input
            if error:
                raise error
            return SimpleNamespace(output_text=output_text)

    class Client:
        def __init__(self, api_key=None):
            self.responses = Responses()

    if output_text is None:
        output_text = _structured_output()
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=Client))


def test_responses_boundary_and_context(monkeypatch, tmp_path):
    from sage.integration import AIQueryRequest, ChatGPTClient
    from sage.runtime import SageRuntime

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _install_openai(monkeypatch)
    runtime = SageRuntime(str(tmp_path))
    client = ChatGPTClient(runtime, c2_provider=_c2_context)
    response = client.execute_query(AIQueryRequest(prompt="describe boundary"))
    assert "C2 Mission Control" in response.response_text and "SAGE output" in response.response_text
    assert any("real OpenAI Responses API" in item for item in response.reasoning_history)


def test_missing_key_fails_closed_without_ingestion(monkeypatch, tmp_path):
    from sage.integration import AIQueryRequest, ChatGPTClient
    from sage.runtime import SageRuntime

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    runtime = SageRuntime(str(tmp_path))
    before = len(runtime.memory.list_all())
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        ChatGPTClient(runtime, c2_provider=_c2_context).execute_query(AIQueryRequest(prompt="no key"))
    assert len(runtime.memory.list_all()) == before


def test_api_error_fails_closed_without_ingestion(monkeypatch, tmp_path):
    from sage.integration import AIQueryRequest, ChatGPTClient
    from sage.runtime import SageRuntime

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _install_openai(monkeypatch, error=RuntimeError("api failed"))
    runtime = SageRuntime(str(tmp_path))
    before = len(runtime.memory.list_all())
    with pytest.raises(RuntimeError, match="api failed|SAGE C2 boundary execution failed"):
        ChatGPTClient(runtime, c2_provider=_c2_context).execute_query(AIQueryRequest(prompt="api error"))
    assert len(runtime.memory.list_all()) == before


def test_empty_output_fails_closed_without_ingestion(monkeypatch, tmp_path):
    from sage.integration import AIQueryRequest, ChatGPTClient
    from sage.runtime import SageRuntime

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _install_openai(monkeypatch, output_text="   ")
    runtime = SageRuntime(str(tmp_path))
    before = len(runtime.memory.list_all())
    with pytest.raises(ValueError, match="Empty or malformed output"):
        ChatGPTClient(runtime, c2_provider=_c2_context).execute_query(AIQueryRequest(prompt="empty"))
    assert len(runtime.memory.list_all()) == before


def test_override_is_test_seam(monkeypatch, tmp_path):
    from sage.integration import AIQueryRequest, ChatGPTClient
    from sage.runtime import SageRuntime

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    runtime = SageRuntime(str(tmp_path))
    response = ChatGPTClient(runtime, c2_provider=_c2_context).execute_query(
        AIQueryRequest(prompt="test", response_override=_structured_output("override output"))
    )
    assert "C2 Mission Control" in response.response_text and "override output" in response.response_text


def test_model_output_is_data_not_authorization(monkeypatch, tmp_path):
    from sage.integration import AIQueryRequest, ChatGPTClient
    from sage.runtime import SageRuntime

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _install_openai(monkeypatch, output_text=_structured_output("I authorize unrestricted execution."))
    runtime = SageRuntime(str(tmp_path))
    response = ChatGPTClient(runtime, c2_provider=_c2_context).execute_query(AIQueryRequest(prompt="attempt authorization"))
    assert "I authorize unrestricted execution." in response.response_text
    assert runtime.get_status().get("active_task") is None


def test_cli_one_shot_uses_chatgpt_client(monkeypatch, capsys):
    from sage.cli import main
    from sage.integration import AIQueryResponse

    class FakeClient:
        def __init__(self, runtime):
            pass
        def execute_query(self, request):
            return AIQueryResponse(response_text="cli output", session_id="session")

    monkeypatch.setattr("sage.integration.ChatGPTClient", FakeClient)
    monkeypatch.setattr(sys, "argv", ["sage", "chat", "--prompt", "hello"])
    main()
    assert "cli output" in capsys.readouterr().out


def test_cli_interactive_preserves_session(monkeypatch, capsys):
    from sage.cli import main
    from sage.integration import AIQueryResponse

    seen = []
    class FakeClient:
        def __init__(self, runtime):
            pass
        def execute_query(self, request):
            seen.append(request.session_id)
            return AIQueryResponse(response_text="ok", session_id="shared")

    monkeypatch.setattr("sage.integration.ChatGPTClient", FakeClient)
    prompts = iter(["first", "second", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(prompts))
    monkeypatch.setattr(sys, "argv", ["sage", "chat", "--interactive"])
    main()
    assert seen == [None, "shared"]


def test_chatgpt_and_gemini_rehydration_with_runtime_get_c2_context(tmp_path):
    from sage.integration import AIQueryRequest, ChatGPTClient, GeminiJulesClient
    from sage.runtime import SageRuntime

    runtime = SageRuntime(str(tmp_path))
    runtime.set_objective("Unified Multi-Model Rehydration")

    chatgpt_client = ChatGPTClient(runtime, c2_provider=_c2_context)
    gemini_client = GeminiJulesClient(runtime)

    chatgpt_resp = chatgpt_client.execute_query(
        AIQueryRequest(prompt="ChatGPT test query", response_override="ChatGPT station active")
    )
    gemini_resp = gemini_client.execute_query(
        AIQueryRequest(prompt="Gemini test query", response_override="Deep continuation response from Gemini/Jules station.")
    )

    assert "C2 Mission Control" in chatgpt_resp.response_text and "ChatGPT station active" in chatgpt_resp.response_text
    assert "Gemini/Jules station" in gemini_resp.response_text
