"""Adversarial contract tests for the governed Google/Gemini MCP bridge."""

from fastapi.testclient import TestClient

from sage.google_gemini_bridge_app import app
from sage.google_gemini_mcp import MCP_PROTOCOL_VERSION


def rpc(client: TestClient, method: str, params=None, *, headers=None):
    request_headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "mcp-protocol-version": MCP_PROTOCOL_VERSION,
    }
    request_headers.update(headers or {})
    return client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}},
        headers=request_headers,
    )


def test_discovery_advertises_governed_bridge(monkeypatch):
    monkeypatch.setenv("SAGE_GOOGLE_MCP_ALLOW_ANONYMOUS", "true")
    with TestClient(app) as client:
        response = rpc(client, "server/discover", headers={"mcp-protocol-version": ""})
        assert response.status_code == 200
        payload = response.json()["result"]
        assert MCP_PROTOCOL_VERSION in payload["supportedVersions"]
        assert payload["capabilities"] == {"tools": {}}
        assert "canonical governed system" in payload["instructions"]


def test_tools_list_is_deterministic_and_read_write_boundary_is_explicit(monkeypatch):
    monkeypatch.setenv("SAGE_GOOGLE_MCP_ALLOW_ANONYMOUS", "true")
    with TestClient(app) as client:
        first = rpc(client, "tools/list").json()["result"]["tools"]
        second = rpc(client, "tools/list").json()["result"]["tools"]
        assert first == second
        names = {tool["name"] for tool in first}
        assert names == {
            "sage_context",
            "sage_search",
            "sage_submit_research_candidate",
            "sage_capability_surface",
        }
        assert next(t for t in first if t["name"] == "sage_context")["annotations"]["readOnlyHint"] is True
        assert next(t for t in first if t["name"] == "sage_submit_research_candidate")["annotations"]["readOnlyHint"] is False


def test_context_is_bounded_and_contains_governance_posture(monkeypatch):
    monkeypatch.setenv("SAGE_GOOGLE_MCP_ALLOW_ANONYMOUS", "true")
    with TestClient(app) as client:
        response = rpc(client, "tools/call", {"name": "sage_context", "arguments": {}})
        assert response.status_code == 200
        context = response.json()["result"]["structuredContent"]
        assert context["identity"] == "SAGE"
        assert context["governance"] == "ACTIVE"
        assert "authority_model" in context
        assert "private_reasoning" not in str(context).lower()


def test_search_requires_exactly_one_selector(monkeypatch):
    monkeypatch.setenv("SAGE_GOOGLE_MCP_ALLOW_ANONYMOUS", "true")
    with TestClient(app) as client:
        response = rpc(client, "tools/call", {"name": "sage_search", "arguments": {}})
        assert response.status_code == 200
        assert response.json()["result"]["isError"] is True

        response = rpc(
            client,
            "tools/call",
            {"name": "sage_search", "arguments": {"tag": "google", "object_type": "fact"}},
        )
        assert response.status_code == 200
        assert response.json()["result"]["isError"] is True


def test_google_research_candidate_is_hypothesis_only(monkeypatch):
    monkeypatch.setenv("SAGE_GOOGLE_MCP_ALLOW_ANONYMOUS", "true")
    with TestClient(app) as client:
        response = rpc(
            client,
            "tools/call",
            {
                "name": "sage_submit_research_candidate",
                "arguments": {
                    "title": "Gemini MCP finding",
                    "finding": "External finding remains candidate knowledge.",
                    "source": "google-research:test",
                    "tags": ["inventor-stage"],
                    "context_id": "google-test-001",
                },
            },
        )
        assert response.status_code == 200
        result = response.json()["result"]["structuredContent"]
        assert result["confidence"] == "hypothesis"
        assert result["promotion_status"] == "CANDIDATE"
        assert result["authority_granted"] is False
        memory_id = result["memory_id"]

        memory = client.get(f"/memory/{memory_id}")
        assert memory.status_code == 200
        body = memory.json()
        assert body["confidence"] == "hypothesis"
        assert body["content"]["promotion_status"] == "CANDIDATE"
        assert body["content"]["authority_granted"] is False


def test_protocol_mismatch_fails_closed(monkeypatch):
    monkeypatch.setenv("SAGE_GOOGLE_MCP_ALLOW_ANONYMOUS", "true")
    with TestClient(app) as client:
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers={"content-type": "application/json", "mcp-protocol-version": "2025-11-25"},
        )
        assert response.status_code == 400
        assert response.json()["error"]["message"] == "Unsupported protocol version"


def test_missing_auth_fails_closed(monkeypatch):
    monkeypatch.delenv("SAGE_GOOGLE_MCP_API_KEY", raising=False)
    monkeypatch.setenv("SAGE_GOOGLE_MCP_ALLOW_ANONYMOUS", "false")
    monkeypatch.setenv("SAGE_REQUIRE_AUTH", "false")
    with TestClient(app) as client:
        response = rpc(client, "tools/list")
        assert response.status_code == 401
