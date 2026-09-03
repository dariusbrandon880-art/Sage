"""Unit tests for Custom GPT / OpenAI Action authentication and flexible request body parsing."""

from fastapi.testclient import TestClient
import pytest

from sage.api import app, lifecycle_mgr


@pytest.fixture
def client():
    return TestClient(app)


def test_bearer_authorization_header_authenticates_protected_routes(client, monkeypatch):
    monkeypatch.setenv("SAGE_REQUIRE_AUTH", "true")
    api_key = "sage-test-bearer-key-2026"
    monkeypatch.setenv("SAGE_API_KEYS", api_key)
    lifecycle_mgr.load_api_keys_from_environment()

    # 1. Unauthenticated fails with 401
    resp_unauth = client.get("/system-frame")
    assert resp_unauth.status_code == 401

    # 2. x-api-key header authenticates
    resp_x_key = client.get("/system-frame", headers={"x-api-key": api_key})
    assert resp_x_key.status_code == 200

    # 3. Authorization: Bearer header authenticates Custom GPT Actions
    resp_bearer = client.get("/system-frame", headers={"Authorization": f"Bearer {api_key}"})
    assert resp_bearer.status_code == 200


def test_flexible_payload_keys_parsed_on_ai_query_and_render_endpoints(client):
    # 1. AIQueryRequest accepts query instead of prompt
    from sage.integration import AIQueryRequest
    req1 = AIQueryRequest.model_validate({"query": "Hello SAGE runtime"})
    assert req1.get_prompt() == "Hello SAGE runtime"

    # 2. ChatRenderRequest accepts content instead of prompt
    from sage.c2.chatgpt_controller import ChatRenderRequest
    req2 = ChatRenderRequest.model_validate({"content": "Render C2 status"})
    assert req2.get_prompt() == "Render C2 status"

    # 3. ChatRenderRequest accepts message instead of prompt
    req3 = ChatRenderRequest.model_validate({"message": "Show active task"})
    assert req3.get_prompt() == "Show active task"
