import json
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


def test_verify_render_chatgpt_action_requires_credentials(tmp_path, monkeypatch):
    monkeypatch.delenv("SAGE_API_KEYS", raising=False)
    try:
        verify_render_chatgpt_action("https://mock-render-url.onrender.com", target_root=tmp_path)
    except ValueError as exc:
        assert "API key" in str(exc)
    else:
        raise AssertionError("live verification must fail closed when credentials are absent")


def test_verify_render_chatgpt_action_requires_successful_governed_response(tmp_path, monkeypatch):
    import httpx

    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload
            self.text = json.dumps(payload)

        def json(self):
            return self._payload

    def mock_get(url, *args, **kwargs):
        if "openapi.json" in url:
            return MockResponse(200, {"paths": {"/status": {}, "/ai/query/chatgpt": {}}})
        return MockResponse(200, {"status": "ok"})

    def mock_post(url, *args, **kwargs):
        return MockResponse(422, {"detail": "validation error"})

    monkeypatch.setattr(httpx, "get", mock_get)
    monkeypatch.setattr(httpx, "post", mock_post)

    evidence = verify_render_chatgpt_action(
        "https://mock-render-url.onrender.com",
        "test-key",
        target_root=tmp_path,
    )

    assert evidence["verification_passed"] is False
    assert evidence["action_configuration_status"] == "UNBRIDGED_HOST_SESSION"
    assert evidence["fail_closed"] is True


def test_verify_render_chatgpt_action_accepts_real_governed_receipt(tmp_path, monkeypatch):
    import httpx

    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload
            self.text = json.dumps(payload)

        def json(self):
            return self._payload

    def mock_get(url, *args, **kwargs):
        if "openapi.json" in url:
            return MockResponse(200, {"paths": {"/status": {}, "/ai/query/chatgpt": {}}})
        return MockResponse(200, {"status": "ok"})

    def mock_post(url, *args, **kwargs):
        return MockResponse(200, {"evidence": {"receipt_id": "LIVE-TEST"}, "response": "ok"})

    monkeypatch.setattr(httpx, "get", mock_get)
    monkeypatch.setattr(httpx, "post", mock_post)

    evidence = verify_render_chatgpt_action(
        "https://mock-render-url.onrender.com",
        "test-key",
        target_root=tmp_path,
    )

    assert evidence["verification_passed"] is True
    assert evidence["action_configuration_status"] == "CONNECTED_AND_GOVERNED"
    assert evidence["fail_closed"] is False
    assert (tmp_path / "evidence_capture" / "render_chatgpt_action_verification.json").exists()
