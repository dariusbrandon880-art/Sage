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


def test_activation_invalid_credentials_401(redirect_evidence_files, monkeypatch):
    """Verify that HTTP 401 invalid API key error is caught and logged as blocked evidence with exit code 0."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-invalid-key-for-testing")
    monkeypatch.setenv("SAGE_AUTH_SECRET", "fake-auth-secret")

    # Mock httpx.post to return a 401 Unauthorized response
    class MockResponse:
        status_code = 401
        text = '{"error": {"message": "Incorrect API key provided", "type": "invalid_request_error", "code": "invalid_api_key"}}'
        def json(self):
            return json.loads(self.text)

    import httpx
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: MockResponse())

    # Mock ChatGPTRuntimeAdapter
    from sage.experimental.act.continuity_control import ChatGPTRuntimeAdapter
    monkeypatch.setattr(ChatGPTRuntimeAdapter, "authenticate_handshake", lambda *args, **kwargs: {"status": "SUCCESS"})

    exit_codes = []
    monkeypatch.setattr(sys, "exit", lambda code: exit_codes.append(code))

    run_openai_activation()

    assert 0 in exit_codes
    evidence_file = redirect_evidence_files / "openai_runtime_live_connection.json"

    assert evidence_file.exists()

    with open(evidence_file, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["authentication_result"] == "BLOCKED_INVALID_CREDENTIALS"
    assert report["execution_result"]["completion_status"] == "BLOCKED"
    assert "401" in report["blocker_details"] or "invalid_api_key" in report["blocker_details"]
