"""Integration and unit tests for SAGE Phase 2 Activation - Service, AI, and Tool integrations."""

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from sage.runtime import SAGERuntime
from sage.service import LifecycleManager
from sage.integration import (
    ChatGPTClient,
    GeminiJulesClient,
    ToolIntegrationManager,
    AIQueryRequest,
    GitHubEvent,
    GoogleWorkspaceArtifact
)
from sage.api import app


def test_service_lifecycle_and_diagnostics():
    """Test standard LifecycleManager start/stop and diagnostics reporting."""
    mgr = LifecycleManager()
    assert mgr.status == "STOPPED"

    # Startup
    start_res = mgr.startup()
    assert start_res["status"] == "RUNNING"
    assert mgr.status == "RUNNING"
    assert mgr.get_uptime() >= 0.0

    # Diagnostics
    diag = mgr.get_diagnostics()
    assert diag.status == "RUNNING"
    assert diag.diagnostics_passed is True
    assert diag.version == "1.0.0"

    # Auth boundary
    assert mgr.authorize("sage-default-key-2026") is True
    assert mgr.authorize("invalid-key") is False

    # Shutdown
    shutdown_res = mgr.shutdown()
    assert shutdown_res["status"] == "STOPPED"
    assert mgr.status == "STOPPED"


def test_ai_clients_and_context_retrieval():
    """Test ChatGPT and GeminiJules connector execution and context retrieval."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runtime = SAGERuntime(str(Path(tmpdir)))

        # Seed some data to memory
        from sage.models import MemoryObject, ConfidenceLevel
        obj = MemoryObject(
            object_type="fact",
            content={"message": "System v1 activation is successful"},
            tags=["continuity", "v1_activation"],
            confidence=ConfidenceLevel.VALIDATED
        )
        runtime.memory.store(obj)

        # Test ChatGPT client context lookup
        client = ChatGPTClient(runtime)
        context = client.retrieve_context("Tell me about v1_activation and continuity")
        assert len(context["matched_memories"]) > 0
        assert context["matched_memories"][0]["id"] == obj.id

        # Test Query
        req = AIQueryRequest(prompt="Continue the v1_activation work", session_id="session_test_1")
        res = client.execute_query(req)
        assert res.session_id == "session_test_1"
        assert len(res.referenced_memories) > 0
        assert obj.id in res.referenced_memories
        assert len(res.reasoning_history) > 0

        # Test Gemini Jules client
        gemini = GeminiJulesClient(runtime)
        res_gemini = gemini.execute_query(req)
        assert res_gemini.session_id == "session_test_1"
        assert len(res_gemini.reasoning_history) > 0


def test_engineering_tool_integrations():
    """Test tool index management of GitHub webhooks and Workspace document markers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runtime = SAGERuntime(str(Path(tmpdir)))
        tool_mgr = ToolIntegrationManager(runtime)

        # GitHub commit
        gh_event = GitHubEvent(
            event_type="commit",
            repository="dariusbrandon880-art/Sage",
            ref="refs/heads/main",
            author="Jules",
            payload={"message": "Initial activation of Phase 2 Service Layer"}
        )
        event_id = tool_mgr.index_github_event(gh_event)
        assert event_id == gh_event.event_id

        # Google Doc
        gw_doc = GoogleWorkspaceArtifact(
            doc_id="doc_v1_specs",
            title="SAGE Platform Spec Sheet",
            doc_type="doc",
            last_modified_by="dariusbrandon880-art",
            url="https://docs.google.com/document/d/doc_v1_specs",
            metadata={"description": "Detailed specs for platform activation"}
        )
        doc_id = tool_mgr.index_workspace_artifact(gw_doc)
        assert doc_id == "doc_v1_specs"

        # Test lookup relationships
        relationships = tool_mgr.get_relationship_index("activation")
        assert len(relationships["connected_github_events"]) == 1
        assert len(relationships["connected_workspace_artifacts"]) == 1


def test_api_integration_endpoints():
    """Test REST endpoints for new system layer and integrations."""
    with TestClient(app) as client:
        # 1. Service Diagnostics
        res = client.get("/service/diagnostics")
        assert res.status_code == 200
        assert "uptime_seconds" in res.json()

        # Test auth startup with valid key
        res = client.post("/service/startup", headers={"x-api-key": "sage-default-key-2026"})
        assert res.status_code == 200

        # Test auth shutdown with invalid key
        res = client.post("/service/shutdown", headers={"x-api-key": "bad-key"})
        assert res.status_code == 401

        # 2. AI endpoints
        ai_payload = {
            "prompt": "continuity of platform validation",
            "session_id": "api_session_1",
            "include_validated_memory": True,
            "include_knowledge_state": True
        }
        res = client.post("/ai/query/chatgpt", json=ai_payload)
        assert res.status_code == 200
        assert "response_text" in res.json()
        assert res.json()["session_id"] == "api_session_1"

        res = client.post("/ai/query/gemini-jules", json=ai_payload)
        assert res.status_code == 200
        assert "response_text" in res.json()

        # 3. Tool endpoints
        github_payload = {
            "event_type": "pull_request",
            "repository": "dariusbrandon880-art/Sage",
            "author": "Jules",
            "payload": {"message": "Merge Phase 2 changes"}
        }
        res = client.post("/tools/github/event", json=github_payload)
        assert res.status_code == 200
        assert "event_id" in res.json()

        gw_payload = {
            "doc_id": "spec_sheet",
            "title": "Phase 2 design spec",
            "doc_type": "doc",
            "last_modified_by": "Jules",
            "url": "https://google.com/spec_sheet"
        }
        res = client.post("/tools/workspace/artifact", json=gw_payload)
        assert res.status_code == 200
        assert res.json()["status"] == "indexed"

        res = client.get("/tools/index/relationships?query_tag=spec")
        assert res.status_code == 200
        assert len(res.json()["connected_workspace_artifacts"]) > 0

        # 4. Snapshot monitoring endpoints
        res = client.post("/snapshot")
        assert res.status_code == 200
        assert "snapshot_id" in res.json()

        res = client.get("/snapshots")
        assert res.status_code == 200
        assert "snapshots" in res.json()
