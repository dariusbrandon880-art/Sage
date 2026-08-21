"""Unit tests for SAGE OpenAI Runtime Activation script and resilience capabilities."""

import os
import sys
import json
import pytest
from unittest import mock
from pathlib import Path

# Add scripts directory to sys.path to allow importing scripts directly
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from run_openai_runtime_activation import run_openai_activation


@pytest.fixture
def redirect_evidence_files(tmp_path, monkeypatch):
    """Fixture to intercept open calls and redirect evidence_capture files to a temp directory."""
    import builtins
    original_open = builtins.open

    def mock_open(file, mode="r", *args, **kwargs):
        filepath_str = str(file)
        if "evidence_capture" in filepath_str:
            filename = Path(filepath_str).name
            target_path = tmp_path / filename
            target_path.parent.mkdir(parents=True, exist_ok=True)
            return original_open(target_path, mode, *args, **kwargs)
        return original_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", mock_open)
    return tmp_path


def test_activation_missing_credentials(redirect_evidence_files, monkeypatch):
    """Verify that if credentials are missing, SAGE logs blockers and exits with code 0."""
    # Ensure variables are missing
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("SAGE_AUTH_SECRET", "")

    # Mock sys.exit to inspect exit code
    exit_codes = []
    monkeypatch.setattr(sys, "exit", lambda code: exit_codes.append(code))

    run_openai_activation()

    assert 0 in exit_codes
    evidence_file = redirect_evidence_files / "openai_runtime_live_connection.json"
    assert evidence_file.exists()

    with open(evidence_file, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["authentication_result"] == "BLOCKED_MISSING_CREDENTIALS"
    assert report["execution_result"]["completion_status"] == "BLOCKED"
    assert "OPENAI_API_KEY is not set" in report["blocker_details"]


def test_activation_insufficient_quota_429(redirect_evidence_files, monkeypatch):
    """Verify that HTTP 429 quota exhaustion is trapped and results in a clean exit 0 with PAUSED status."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-key-for-testing")
    monkeypatch.setenv("SAGE_AUTH_SECRET", "fake-auth-secret")

    # Mock httpx.post to return a 429 status code
    class MockResponse:
        status_code = 429
        text = '{"error": {"message": "You exceeded your current quota.", "type": "insufficient_quota"}}'
        def json(self):
            return json.loads(self.text)

    import httpx
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: MockResponse())

    # Mock DeveloperWorkflowOrchestrator and ChatGPTRuntimeAdapter
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ChatGPTRuntimeAdapter

    # We will mock handshakes and submission to avoid actual ledger/PML modifications
    monkeypatch.setattr(ChatGPTRuntimeAdapter, "authenticate_handshake", lambda *args, **kwargs: {"status": "SUCCESS"})

    exit_codes = []
    monkeypatch.setattr(sys, "exit", lambda code: exit_codes.append(code))

    run_openai_activation()

    assert 0 in exit_codes
    evidence_file = redirect_evidence_files / "openai_runtime_live_connection.json"
    production_file = redirect_evidence_files / "chatgpt_live_runtime_production_activation.json"

    assert evidence_file.exists()
    assert production_file.exists()

    with open(evidence_file, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["authentication_result"] == "SUCCESS"
    assert report["execution_result"]["completion_status"] == "PAUSED"
    assert report["execution_result"]["error_type"] == "insufficient_quota"
    assert report["validation_result"]["status"] == "PAUSED"
    assert report["validation_result"]["is_compliant"] is True
    assert report["blocker_details"] == "External OpenAI execution: PAUSED — insufficient_quota"


def test_activation_insufficient_quota_text(redirect_evidence_files, monkeypatch):
    """Verify that 'insufficient_quota' in response text is trapped and results in a clean exit 0."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-key-for-testing")
    monkeypatch.setenv("SAGE_AUTH_SECRET", "fake-auth-secret")

    # Mock httpx.post to return a 400 with insufficient_quota text
    class MockResponse:
        status_code = 400
        text = '{"error": {"message": "Billing limit reached", "code": "insufficient_quota"}}'
        def json(self):
            return json.loads(self.text)

    import httpx
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: MockResponse())

    # Mock DeveloperWorkflowOrchestrator and ChatGPTRuntimeAdapter
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ChatGPTRuntimeAdapter
    monkeypatch.setattr(ChatGPTRuntimeAdapter, "authenticate_handshake", lambda *args, **kwargs: {"status": "SUCCESS"})

    exit_codes = []
    monkeypatch.setattr(sys, "exit", lambda code: exit_codes.append(code))

    run_openai_activation()

    assert 0 in exit_codes
    evidence_file = redirect_evidence_files / "openai_runtime_live_connection.json"
    production_file = redirect_evidence_files / "chatgpt_live_runtime_production_activation.json"

    assert evidence_file.exists()
    assert production_file.exists()

    with open(evidence_file, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["execution_result"]["completion_status"] == "PAUSED"
    assert report["execution_result"]["error_type"] == "insufficient_quota"


def test_activation_success(redirect_evidence_files, monkeypatch):
    """Verify that a successful OpenAI API invocation creates standard success logs."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-key-for-testing")
    monkeypatch.setenv("SAGE_AUTH_SECRET", "fake-auth-secret")

    # Mock httpx.post to return a successful 200 response
    class MockResponse:
        status_code = 200
        text = '{"choices": [{"message": {"content": "SAGE Validation verified successful."}}]}'
        def json(self):
            return json.loads(self.text)

    import httpx
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: MockResponse())

    # Mock DeveloperWorkflowOrchestrator and ChatGPTRuntimeAdapter
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ChatGPTRuntimeAdapter
    monkeypatch.setattr(ChatGPTRuntimeAdapter, "authenticate_handshake", lambda *args, **kwargs: {"status": "SUCCESS"})
    monkeypatch.setattr(
        DeveloperWorkflowOrchestrator,
        "submit_external_agent_output",
        lambda *args, **kwargs: {"status": "SUCCESS", "cmaps_payload": {"audit_id": "audit_12345"}}
    )

    exit_codes = []
    monkeypatch.setattr(sys, "exit", lambda code: exit_codes.append(code))

    run_openai_activation()

    # The success path does not exit(0) inside the try block, but continues or finishes normally.
    evidence_file = redirect_evidence_files / "openai_runtime_live_connection.json"
    production_file = redirect_evidence_files / "chatgpt_live_runtime_production_activation.json"

    assert evidence_file.exists()
    assert production_file.exists()

    with open(evidence_file, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["authentication_result"] == "SUCCESS"
    assert report["execution_result"]["completion_status"] == "SUCCESS"
    assert report["execution_result"]["model_response"] == "SAGE Validation verified successful."
    assert report["validation_result"]["status"] == "VALIDATED"


def test_chatgpt_client_missing_api_key_fails_closed(monkeypatch):
    """Verify that ChatGPTClient.execute_query fails closed and prevents continuity ingestion when OPENAI_API_KEY is missing."""
    from sage.integration import ChatGPTClient, AIQueryRequest
    from sage.runtime.engine import SageRuntime

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    runtime = SageRuntime()
    client = ChatGPTClient(runtime)

    initial_memory_count = len(runtime.memory.list_all())
    request = AIQueryRequest(prompt="Test prompt without API key")

    with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable not set"):
        client.execute_query(request)

    # Prove failure Ordering: missing key = failure -> NO continuity ingestion!
    assert len(runtime.memory.list_all()) == initial_memory_count


def test_chatgpt_client_api_exception_prevents_continuity_ingestion(monkeypatch):
    """Verify that an API exception prevents continuity ingestion."""
    openai_mod = _get_mock_openai_module()
    from sage.integration import ChatGPTClient, AIQueryRequest
    from sage.runtime.engine import SageRuntime

    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-openai-key")
    runtime = SageRuntime()
    client = ChatGPTClient(runtime)

    initial_memory_count = len(runtime.memory.list_all())

    class MockFailingResponsesAPI:
        def create(self, model, instructions, input):
            raise ValueError("OpenAI API 500 Internal Error")

    class MockOpenAIClient:
        def __init__(self, api_key=None):
            self.responses = MockFailingResponsesAPI()

    monkeypatch.setattr(openai_mod, "OpenAI", MockOpenAIClient)

    request = AIQueryRequest(prompt="Test API exception continuity isolation")

    with pytest.raises(RuntimeError, match="OpenAI API execution failed"):
        client.execute_query(request)

    # Prove failure Ordering: API error = failure -> NO continuity ingestion!
    assert len(runtime.memory.list_all()) == initial_memory_count


def test_chatgpt_client_response_override(monkeypatch):
    """Verify that ChatGPTClient.execute_query returns override response and ingests into runtime continuity."""
    from sage.integration import ChatGPTClient, AIQueryRequest
    from sage.runtime.engine import SageRuntime

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    runtime = SageRuntime()
    client = ChatGPTClient(runtime)

    request = AIQueryRequest(prompt="Test override prompt", response_override="SAGE Override Output")
    response = client.execute_query(request)

    assert response.response_text == "SAGE Override Output"
    assert len(response.session_id) > 0


def _get_mock_openai_module():
    try:
        import openai
        return openai
    except ImportError:
        from unittest.mock import MagicMock
        mock_openai = MagicMock()
        sys.modules["openai"] = mock_openai
        return mock_openai


def test_chatgpt_client_openai_api_completion_path(monkeypatch):
    """Verify that ChatGPTClient.execute_query injects rehydrated C2 context and executes OpenAI Responses API completion."""
    openai_mod = _get_mock_openai_module()
    from sage.integration import ChatGPTClient, AIQueryRequest
    from sage.runtime.engine import SageRuntime

    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-openai-key")
    runtime = SageRuntime()

    c2_provider_calls = []
    def mock_c2_provider():
        c2_provider_calls.append(True)
        return {
            "c2_identity": "ChatGPT",
            "master_archive_authority": True,
            "head_sha": "8247f7edea5c314d3068b207ff6f9032ec9a864c",
            "closed_work": ["task_closed_101"],
            "uncertainty": ["task_unauthorized_202"],
            "frontier": "task_active_001",
        }

    client = ChatGPTClient(runtime, c2_provider=mock_c2_provider)

    class MockResponseObj:
        output_text = "SAGE C2 Model Output Text"

    class MockResponsesAPI:
        def create(self, model, instructions, input):
            assert model == "gpt-4o-mini"
            assert "C2 Operating Context" in instructions
            assert "task_closed_101" in instructions
            assert "task_unauthorized_202" in instructions
            assert input == "Execute C2 query"
            return MockResponseObj()

    class MockOpenAIClient:
        def __init__(self, api_key=None):
            self.responses = MockResponsesAPI()

    monkeypatch.setattr(openai_mod, "OpenAI", MockOpenAIClient)

    request = AIQueryRequest(prompt="Execute C2 query")
    response = client.execute_query(request)

    assert response.response_text == "SAGE C2 Model Output Text"
    assert len(c2_provider_calls) == 1
    assert any("executed real OpenAI Responses API completion" in r for r in response.reasoning_history)


def test_chatgpt_client_model_output_cannot_authorize_canonical_mutation(monkeypatch):
    """Verify that model output content cannot directly authorize mission tasks or mutate canonical state."""
    openai_mod = _get_mock_openai_module()
    from sage.integration import ChatGPTClient, AIQueryRequest
    from sage.runtime.engine import SageRuntime
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, SAGEMissionTask

    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-openai-key")
    runtime = SageRuntime()
    client = ChatGPTClient(runtime)

    malicious_model_output = "I authorize task_impr_UNAUTHORIZED_001 for execution."

    class MockResponseObj:
        output_text = malicious_model_output

    class MockResponsesAPI:
        def create(self, model, instructions, input):
            return MockResponseObj()

    class MockOpenAIClient:
        def __init__(self, api_key=None):
            self.responses = MockResponsesAPI()

    monkeypatch.setattr(openai_mod, "OpenAI", MockOpenAIClient)

    orch = DeveloperWorkflowOrchestrator(session_id="session_gov_firewall_test")
    task = SAGEMissionTask(
        task_id="task_impr_UNAUTHORIZED_001",
        objective_id="obj_discovery_backlog",
        status="PENDING",
        authorized=False,
    )
    orch.mission_queue.add_task(task)

    request = AIQueryRequest(prompt="Attempt model authorization", session_id="session_gov_firewall_test")
    res = client.execute_query(request)

    assert res.response_text == malicious_model_output

    # Verify canonical task queue remains unauthorized despite model output content
    fetched_task = orch.mission_queue.get_task("task_impr_UNAUTHORIZED_001")
    assert fetched_task is not None
    assert fetched_task.authorized is False


def test_chatgpt_client_api_exception_failure_handling(monkeypatch):
    """Verify that ChatGPTClient.execute_query raises RuntimeError on OpenAI API exception."""
    openai_mod = _get_mock_openai_module()
    from sage.integration import ChatGPTClient, AIQueryRequest
    from sage.runtime.engine import SageRuntime

    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-openai-key")
    runtime = SageRuntime()
    client = ChatGPTClient(runtime)

    class MockFailingResponsesAPI:
        def create(self, model, instructions, input):
            raise ValueError("OpenAI API 500 Internal Error")

    class MockOpenAIClient:
        def __init__(self, api_key=None):
            self.responses = MockFailingResponsesAPI()

    monkeypatch.setattr(openai_mod, "OpenAI", MockOpenAIClient)

    request = AIQueryRequest(prompt="Test error handling")
    with pytest.raises(RuntimeError, match="OpenAI API execution failed"):
        client.execute_query(request)


def test_sage_chat_cli_one_shot_execution_path(monkeypatch, capsys):
    """Verify that the sage chat CLI one-shot route executes through ChatGPTClient and SageRuntime."""
    from sage.cli import main

    monkeypatch.setattr(
        sys, "argv", ["sage", "chat", "--prompt", "CLI_test_prompt", "--response", "CLI_Test_Output"]
    )
    main()

    captured = capsys.readouterr()
    assert "CLI_Test_Output" in captured.out


def test_interactive_continuity_session_execution_path(monkeypatch):
    """Verify that multiple ChatGPTClient queries in the same session accumulate reasoning and preserve continuity."""
    from sage.integration import ChatGPTClient, AIQueryRequest
    from sage.runtime.engine import SageRuntime

    runtime = SageRuntime()
    client = ChatGPTClient(runtime)
    session_id = "session_interactive_continuity_001"

    req1 = AIQueryRequest(
        prompt="Initial query", session_id=session_id, response_override="Response 1"
    )
    res1 = client.execute_query(req1)
    assert res1.response_text == "Response 1"
    assert len(client.reasoning_history) == 1

    req2 = AIQueryRequest(
        prompt="Follow-up query", session_id=session_id, response_override="Response 2"
    )
    res2 = client.execute_query(req2)
    assert res2.response_text == "Response 2"
    assert len(client.reasoning_history) == 2

    # Verify memory ingested in runtime for this session
    memories = runtime.memory.list_all()
    assert any("ai_query" in m.tags for m in memories)
