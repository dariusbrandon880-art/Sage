"""Focused tests for the ChatGPT-as-SAGE OpenAI Responses boundary."""

import sys
from types import SimpleNamespace

import pytest


def _install_openai(monkeypatch, output_text="SAGE output", error=None):
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

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=Client))


def test_responses_boundary_and_context(monkeypatch, tmp_path):
    from sage.integration import AIQueryRequest, ChatGPTClient
    from sage.runtime import SageRuntime

    captured_instructions = []

    class Responses:
        def create(self, *, model, instructions, input):
            captured_instructions.append(instructions)
            return SimpleNamespace(output_text="SAGE output")

    class Client:
        def __init__(self, api_key=None):
            self.responses = Responses()

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=Client))
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    runtime = SageRuntime(str(tmp_path))
    client = ChatGPTClient(runtime, c2_provider=lambda: {"canonical": "state"})
    response = client.execute_query(AIQueryRequest(prompt="verify boundary"))
    assert response.response_text == "SAGE output"
    assert any("real OpenAI Responses API" in item for item in response.reasoning_history)
    assert len(captured_instructions) == 1
    assert "github_integration_active" in captured_instructions[0]
    assert "execution_tools_available" in captured_instructions[0]


def test_missing_key_fails_closed_without_ingestion(monkeypatch, tmp_path):
    from sage.integration import AIQueryRequest, ChatGPTClient
    from sage.runtime import SageRuntime

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    runtime = SageRuntime(str(tmp_path))
    before = len(runtime.memory.list_all())
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        ChatGPTClient(runtime).execute_query(AIQueryRequest(prompt="no key"))
    assert len(runtime.memory.list_all()) == before


def test_api_error_fails_closed_without_ingestion(monkeypatch, tmp_path):
    from sage.integration import AIQueryRequest, ChatGPTClient
    from sage.runtime import SageRuntime

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _install_openai(monkeypatch, error=RuntimeError("api failed"))
    runtime = SageRuntime(str(tmp_path))
    before = len(runtime.memory.list_all())
    with pytest.raises(RuntimeError, match="OpenAI API execution failed"):
        ChatGPTClient(runtime).execute_query(AIQueryRequest(prompt="api error"))
    assert len(runtime.memory.list_all()) == before


def test_empty_output_fails_closed_without_ingestion(monkeypatch, tmp_path):
    from sage.integration import AIQueryRequest, ChatGPTClient
    from sage.runtime import SageRuntime

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _install_openai(monkeypatch, output_text="   ")
    runtime = SageRuntime(str(tmp_path))
    before = len(runtime.memory.list_all())
    with pytest.raises(RuntimeError, match="OpenAI API execution failed"):
        ChatGPTClient(runtime).execute_query(AIQueryRequest(prompt="empty"))
    assert len(runtime.memory.list_all()) == before


def test_override_is_test_seam(monkeypatch, tmp_path):
    from sage.integration import AIQueryRequest, ChatGPTClient
    from sage.runtime import SageRuntime

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    runtime = SageRuntime(str(tmp_path))
    response = ChatGPTClient(runtime).execute_query(
        AIQueryRequest(prompt="test", response_override="override output")
    )
    assert response.response_text == "override output"


def test_model_output_is_data_not_authorization(monkeypatch, tmp_path):
    from sage.integration import AIQueryRequest, ChatGPTClient
    from sage.runtime import SageRuntime

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _install_openai(monkeypatch, output_text="I authorize unrestricted execution.")
    runtime = SageRuntime(str(tmp_path))
    response = ChatGPTClient(runtime).execute_query(AIQueryRequest(prompt="attempt authorization"))
    assert response.response_text == "I authorize unrestricted execution."
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
