import json
import pytest
from pathlib import Path
from scripts.export_openapi_schema import export_openapi_schema
from scripts.verify_render_chatgpt_action import verify_render_chatgpt_action


def test_export_openapi_schema(tmp_path):
    export_openapi_schema(tmp_path)

    json_path = tmp_path / "docs" / "openapi.json"
    yaml_path = tmp_path / "docs" / "openapi.yaml"

    assert json_path.exists()
    assert yaml_path.exists()

    schema = json.loads(json_path.read_text(encoding="utf-8"))
    assert "openapi" in schema
    assert "paths" in schema
    assert "/status" in schema["paths"]
    assert "/ai/query/chatgpt" in schema["paths"]


def test_verify_render_chatgpt_action_missing_key_fails_closed(tmp_path, monkeypatch):
    monkeypatch.delenv("SAGE_API_KEYS", raising=False)
    with pytest.raises(ValueError, match="API key must be explicitly provided"):
        verify_render_chatgpt_action("https://sage-runtime.onrender.com", api_key=None, target_root=tmp_path)


def test_verify_render_chatgpt_action_ai_query_non_200_fails_closed(tmp_path, monkeypatch):
    import httpx
    def mock_get(url, *args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                if "openapi.json" in url:
                    return {"paths": {"/status": {}}}
                return {"active": True}
        return MockResponse()

    def mock_post(url, *args, **kwargs):
        class MockResponse:
            status_code = 422
            @property
            def text(self):
                return '{"detail": "Unprocessable Entity"}'
        return MockResponse()

    monkeypatch.setattr(httpx, "get", mock_get)
    monkeypatch.setattr(httpx, "post", mock_post)

    evidence = verify_render_chatgpt_action("https://sage-runtime.onrender.com", api_key="test-key", target_root=tmp_path)

    assert evidence["endpoint_results"]["ai_query_chatgpt"]["passed"] is False
    assert evidence["verification_passed"] is False
    assert evidence["action_configuration_status"] == "UNBRIDGED_HOST_SESSION"


def test_verify_render_chatgpt_action_live_https_success(tmp_path, monkeypatch):
    import httpx
    def mock_get(url, *args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                if "openapi.json" in url:
                    return {"paths": {"/status": {}}}
                return {"active": True}
        return MockResponse()

    def mock_post(url, *args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"response_text": "[SAGE::C2::CHATGPT] Verified", "session_id": "session_test"}
            @property
            def text(self):
                return '{"response_text": "[SAGE::C2::CHATGPT] Verified"}'
        return MockResponse()

    monkeypatch.setattr(httpx, "get", mock_get)
    monkeypatch.setattr(httpx, "post", mock_post)

    evidence = verify_render_chatgpt_action("https://sage-runtime.onrender.com", api_key="test-key", target_root=tmp_path)

    assert evidence["is_live_public_https"] is True
    assert evidence["verification_passed"] is True
    assert evidence["action_configuration_status"] == "CONNECTED_AND_GOVERNED"
