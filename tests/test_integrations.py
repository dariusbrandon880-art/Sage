"""Tests for Phase 2 Integration layers: ChatGPT, Gemini, GitHub, Google Workspace."""

import pytest
from fastapi.testclient import TestClient

from sage.api import app


@pytest.fixture
def api_client():
    """Returns a FastAPI TestClient configured for SAGE."""
    return TestClient(app)


def test_service_diagnostics_endpoint(api_client):
    """Test SAGE Service Layer diagnostics endpoint returns correct metadata."""
    response = api_client.get("/service/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "diagnostics" in data
    assert "memory_size" in data["diagnostics"]
    assert "archive_size" in data["diagnostics"]


def test_chatgpt_context_endpoints(api_client):
    """Test ChatGPT integration endpoints: context, lookup, reason, and sync."""
    # 1. Context query
    response = api_client.post("/integration/chatgpt/context", json={"query": "architecture"})
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "active_objective" in data
    assert "relevant_memories" in data

    # 2. Validated lookup
    response = api_client.post("/integration/chatgpt/lookup", json={"query": "database"})
    assert response.status_code == 200
    data = response.json()
    assert "archive_results" in data
    assert "validated_memory_results" in data

    # 3. Record reasoning
    reason_payload = {
        "decision_type": "architectural",
        "description": "Expose integration layers",
        "rationale": "Allows external client systems to sync",
        "evidence": ["client_requirements"],
        "reasoning_trace": ["Step 1: Check requirements", "Step 2: Define endpoints"],
    }
    response = api_client.post("/integration/chatgpt/reason", json=reason_payload)
    assert response.status_code == 200
    data = response.json()
    assert "decision_id" in data
    assert data["status"] == "recorded"

    # 4. Sync context
    sync_payload = {
        "session_id": "session_chatgpt_test",
        "chat_context": {"messages_count": 14, "thread_id": "thread_abc"},
    }
    response = api_client.post("/integration/chatgpt/sync", json=sync_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_gemini_integration_endpoints(api_client):
    """Test Gemini/Jules integration endpoints: repository awareness and feedback loops."""
    # 1. Repository metadata
    response = api_client.get("/integration/gemini/repository")
    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "SAGE-ACR"
    assert "modules" in data

    # 2. Active developer context
    response = api_client.get("/integration/gemini/context")
    assert response.status_code == 200
    data = response.json()
    assert "objective" in data
    assert "task" in data

    # 3. Register execution feedback (Success)
    feedback_payload = {
        "task_id": "task_jules_01",
        "code_changes": "def hello(): pass",
        "test_output": "All 15 tests passed.",
        "success": True,
    }
    response = api_client.post("/integration/gemini/feedback", json=feedback_payload)
    assert response.status_code == 200
    data = response.json()
    assert "feedback_id" in data
    assert "blockers" in data

    # 4. Register execution feedback (Failure - registers blocker)
    failed_feedback_payload = {
        "task_id": "task_jules_02",
        "code_changes": "def buggy(): raise Exception()",
        "test_output": "AssertionError: expected True got False",
        "success": False,
    }
    response = api_client.post("/integration/gemini/feedback", json=failed_feedback_payload)
    assert response.status_code == 200
    data = response.json()
    assert "feedback_id" in data
    assert any("task_jules_02" in b for b in data["blockers"])


def test_github_integration_endpoints(api_client):
    """Test GitHub sync: commit hook, pull request event, and action runners."""
    # 1. Commit hooks
    commit_payload = {
        "commit_hash": "a1b2c3d4e5f6",
        "author": "engineer-jules",
        "message": "fix: resolve memory storage persistence race",
        "changed_files": ["sage/memory/storage.py"],
    }
    response = api_client.post("/integration/github/commit", json=commit_payload)
    assert response.status_code == 200
    data = response.json()
    assert "memory_id" in data
    assert data["status"] == "indexed"

    # 2. Pull Request merged (triggers search and archive promotions)
    pr_payload = {
        "pr_number": 42,
        "title": "Merge integration endpoints into core",
        "author": "engineer-jules",
        "state": "merged",
        "body": "This merges all integration layers.",
        "merged_at": "2026-07-21T12:00:00Z",
    }
    response = api_client.post("/integration/github/pull-request", json=pr_payload)
    assert response.status_code == 200
    data = response.json()
    assert "memory_id" in data
    assert data["pr_state"] == "merged"

    # 3. Actions and CI failures
    ci_payload = {
        "run_id": "88776655",
        "workflow_name": "SAGE Unit Tests CI",
        "status": "failed",
        "failure_log": "ImportError",
    }
    response = api_client.post("/integration/github/ci-run", json=ci_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert any("SAGE Unit Tests CI" in b for b in data["blockers"])


def test_google_workspace_integration_endpoints(api_client):
    """Test Google Workspace indexing, ADR linkages, and reference querying."""
    # 1. Index new document
    doc_payload = {
        "doc_url": "https://docs.google.com/document/d/1abc/edit",
        "doc_type": "ADR",
        "title": "ADR-005: Decoupled Integration Layer",
        "tags": ["integration", "phase2", "decoupled"],
        "decision_id": "decision_123",
    }
    response = api_client.post("/integration/workspace/index", json=doc_payload)
    assert response.status_code == 200
    data = response.json()
    assert "memory_id" in data
    assert data["status"] == "indexed"

    # 2. Query documents
    response = api_client.get("/integration/workspace/documents?doc_type=ADR")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert len(data["documents"]) >= 1
    assert data["documents"][0]["content"]["title"] == "ADR-005: Decoupled Integration Layer"
