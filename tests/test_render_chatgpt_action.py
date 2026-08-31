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


def test_verify_render_chatgpt_action_mocked(tmp_path, monkeypatch):
    import httpx
    def mock_get(url, *args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                if "openapi.json" in url:
                    return {"paths": {"/status": {}}}
                return {"status": "ok"}
            @property
            def text(self):
                return '{"status": "ok"}'
        return MockResponse()

    def mock_post(url, *args, **kwargs):
        class MockResponse:
            status_code = 200
            @property
            def text(self):
                return '{"response": "ok"}'
        return MockResponse()

    monkeypatch.setattr(httpx, "get", mock_get)
    monkeypatch.setattr(httpx, "post", mock_post)

    evidence = verify_render_chatgpt_action("http://mock-render-url.onrender.com", "test-key", target_root=tmp_path)

    assert evidence["verification_passed"] is True
    assert evidence["action_configuration_status"] == "CONNECTED_AND_GOVERNED"
    assert (tmp_path / "evidence_capture" / "render_chatgpt_action_verification.json").exists()
