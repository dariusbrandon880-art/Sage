"""Tests for SAGE FastAPI REST API server."""

import os
import tempfile
from fastapi.testclient import TestClient

# Mock the runtime's workspace path so the tests don't pollute the real workspace
tmp_dir_obj = tempfile.TemporaryDirectory()
tmpdir = tmp_dir_obj.name

from sage.api import app, runtime, validation  # noqa: E402

# Configure the global runtime to use the temporary directory
runtime.__init__(workspace_path=tmpdir)
validation.__init__(runtime.memory, runtime.archive)


def test_root_endpoint():
    """Test the root endpoint."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "SAGE Runtime online"


def test_health_endpoint():
    """Test the health endpoint."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "runtime": "active"}


def test_objective_endpoints():
    """Test setting and getting objectives."""
    with TestClient(app) as client:
        # Set objective
        response = client.post("/objective", json={"objective": "Test SAGE API Integration"})
        assert response.status_code == 200
        assert response.json()["status"] == "active"
        assert response.json()["objective"] == "Test SAGE API Integration"

        # Get objective
        response = client.get("/objective")
        assert response.status_code == 200
        assert response.json()["objective"] == "Test SAGE API Integration"


def test_task_endpoints():
    """Test setting and getting tasks."""
    with TestClient(app) as client:
        # Set task
        response = client.post("/task", json={"task": "Implement API integration tests"})
        assert response.status_code == 200
        assert response.json()["status"] == "active"
        assert response.json()["task"] == "Implement API integration tests"

        # Get task
        response = client.get("/task")
        assert response.status_code == 200
        assert response.json()["active_task"] == "Implement API integration tests"


def test_decision_endpoints():
    """Test recording, listing, and retrieving decisions."""
    with TestClient(app) as client:
        decision_data = {
            "decision_type": "architectural",
            "description": "Use FastAPI for core server",
            "rationale": "High performance and automatic documentation",
            "evidence": ["fastapi_vs_flask_benchmarks"],
        }

        # Record decision
        response = client.post("/decision", json=decision_data)
        assert response.status_code == 200
        decision_id = response.json()["decision_id"]
        assert decision_id is not None

        # List decisions
        response = client.get("/decisions")
        assert response.status_code == 200
        assert response.json()["count"] > 0

        # Get single decision
        response = client.get(f"/decision/{decision_id}")
        assert response.status_code == 200
        assert response.json()["description"] == "Use FastAPI for core server"


def test_memory_and_validation_and_archive_promotion_endpoints():
    """Test Memory, Validation, and Archive promotion endpoints end-to-end."""
    with TestClient(app) as client:
        # 1. Create Memory Object (Hypothesis)
        memory_data = {
            "object_type": "fact",
            "content": {"subject": "SAGE Runtime", "status": "integrated"},
            "tags": ["fact", "test"],
            "confidence": "hypothesis",
        }
        response = client.post("/memory", json=memory_data)
        assert response.status_code == 200
        memory_id = response.json()["memory_id"]
        assert memory_id is not None

        # Retrieve Memory
        response = client.get(f"/memory/{memory_id}")
        assert response.status_code == 200
        assert response.json()["object_type"] == "fact"
        assert response.json()["confidence"] == "hypothesis"

        # Search by tag
        response = client.get("/memory/search/tag/test")
        assert response.status_code == 200
        assert response.json()["count"] > 0

        # Search by type
        response = client.get("/memory/search/type/fact")
        assert response.status_code == 200
        assert response.json()["count"] > 0

        # 2. Validate Memory
        response = client.post("/validate", json={"memory_id": memory_id})
        assert response.status_code == 200
        assert response.json()["is_valid"] is True

        # 3. Promote to Validated
        response = client.post("/promote/validated", json={"memory_id": memory_id})
        assert response.status_code == 200

        # 4. Promote to Archive
        archive_data = {
            "memory_id": memory_id,
            "title": "Validated SAGE Integration Fact",
            "tags": ["archived_fact"],
        }
        response = client.post("/promote/archive", json=archive_data)
        assert response.status_code == 200
        archive_id = response.json()["archive_id"]
        assert archive_id is not None

        # Verify in archive list
        response = client.get("/archive")
        assert response.status_code == 200
        assert response.json()["count"] > 0

        # Retrieve single archive entry
        response = client.get(f"/archive/{archive_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Validated SAGE Integration Fact"

        # Search archive by title
        response = client.get("/archive/search/title/Validated")
        assert response.status_code == 200
        assert response.json()["count"] > 0


def test_blocker_endpoints():
    """Test adding and resolving blockers."""
    with TestClient(app) as client:
        # Add blocker
        response = client.post("/blocker", json={"blocker": "Database connection timeout"})
        assert response.status_code == 200

        # Check in task status
        response = client.get("/task")
        assert "Database connection timeout" in response.json()["blockers"]

        # Resolve blocker
        response = client.request(
            "DELETE", "/blocker", json={"blocker": "Database connection timeout"}
        )
        assert response.status_code == 200

        # Check resolved in task status
        response = client.get("/task")
        assert "Database connection timeout" not in response.json()["blockers"]


def test_checkpoint_endpoint():
    """Test the checkpoint creation endpoint."""
    with TestClient(app) as client:
        response = client.post("/checkpoint")
        assert response.status_code == 200
        assert "checkpoint_id" in response.json()


def test_handoff_and_restore_endpoints():
    """Test the handoff generation and session restoration endpoints."""
    with TestClient(app) as client:
        # First set some state
        client.post("/objective", json={"objective": "Test SAGE API Handoff"})
        client.post("/task", json={"task": "Verifying restore endpoint"})

        # Generate handoff
        response = client.post("/handoff")
        assert response.status_code == 200
        handoff_file = response.json()["handoff_file"]
        assert handoff_file is not None
        assert os.path.exists(handoff_file)

        # Clear/Modify the objective to verify it restores
        client.post("/objective", json={"objective": "Temporary wrong objective"})

        # Restore session
        response = client.post("/restore", json={"handoff_file": handoff_file})
        assert response.status_code == 200

        # Verify objective was restored
        response = client.get("/objective")
        assert response.status_code == 200
        assert response.json()["objective"] == "Test SAGE API Handoff"


def test_strategic_roadmap_endpoints():
    """Test REST API endpoints for all 5 strategic roadmap expansion layers."""
    with TestClient(app) as client:
        # 1. Capability Registry
        cap_data = {
            "id": "format_string",
            "name": "Formatter",
            "description": "Formats text fields",
            "permissions": ["text-processing"],
            "parameters": {"text": "string"},
        }
        res = client.post("/registry/capability", json=cap_data)
        assert res.status_code == 200
        assert res.json()["status"] == "success"

        # List
        res = client.get("/registry/capabilities")
        assert res.status_code == 200
        caps = res.json()["capabilities"]
        assert any(c["id"] == "format_string" for c in caps)

        # Invoke (unauthorized)
        res = client.post(
            "/registry/invoke", json={"id": "format_string", "args": {}, "scopes": ["user"]}
        )
        assert res.status_code == 403

        # Invoke (authorized)
        res = client.post(
            "/registry/invoke",
            json={"id": "format_string", "args": {"val": "test"}, "scopes": ["text-processing"]},
        )
        assert res.status_code == 200
        assert "success" in res.json()["status"]

        # 2. Intelligence Layer
        # Route context
        res = client.post("/intelligence/route", json={"text": "Refresh postgres migrations"})
        assert res.status_code == 200
        assert (
            res.json()["category"] == "default"
        )  # Categories not initialized in global runtime yet, matches default

        # Evaluate task
        eval_data = {
            "objective": "Complete SAGE",
            "task": "diagnose RAM issues",
            "context": {"ram": "99%"},
        }
        res = client.post("/intelligence/evaluate", json=eval_data)
        assert res.status_code == 200
        assert res.json()["recommended_action"] == "checkpoint"

        # 3. Automation Layer
        # Schedule
        res = client.post(
            "/automation/schedule", json={"name": "test_bg_job", "interval_seconds": 10}
        )
        assert res.status_code == 200
        assert "scheduled" in res.json()["message"]

        # Heal (no blockers)
        res = client.post("/automation/heal")
        assert res.status_code == 200
        assert res.json()["healed"] is False

        # 4. External Interfaces
        # Webhook register
        res = client.post(
            "/interfaces/webhook",
            json={"event_type": "checkpoint_created", "url": "https://callback.com"},
        )
        assert res.status_code == 200

        # Webhook trigger
        res = client.post(
            "/interfaces/webhook/trigger",
            json={"event_type": "checkpoint_created", "payload": {"foo": "bar"}},
        )
        assert res.status_code == 200
        assert res.json()["delivered_count"] == 1

        # OAuth token
        res = client.post(
            "/interfaces/oauth/token",
            json={"client_id": "test_client", "client_secret": "secret_abc"},
        )
        assert res.status_code == 200
        assert "access_token" in res.json()

        # 5. Business/Application Layer
        # Workspace Sandbox
        res = client.post(
            "/business/workspace", json={"client_id": "enterprise_corp", "quota_bytes": 1024}
        )
        assert res.status_code == 200
        assert res.json()["client_id"] == "enterprise_corp"

        # Compliance
        res = client.post(
            "/business/compliance", json={"decision_data": {"description": "Save", "evidence": []}}
        )
        assert res.status_code == 200
        assert res.json()["compliant"] is False  # Evidence missing
