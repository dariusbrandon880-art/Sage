"""Unit and integration tests for SAGE Command Center v1."""

import tempfile
from fastapi.testclient import TestClient

from sage.runtime.engine import SageRuntime
from sage.command_center import CommandCenter
from sage.api import app


def test_command_center_modular_helpers():
    """Verify that the CommandCenter class behaves correctly with a clean, isolated local runtime."""
    with tempfile.TemporaryDirectory() as tmpdir:
        local_runtime = SageRuntime(workspace_path=tmpdir)
        local_runtime.start()

        cmd_center = CommandCenter(local_runtime)
        payload = cmd_center.get_visibility_payload()

        assert "timestamp" in payload
        assert "current_system_view" in payload
        assert "archive_view" in payload
        assert "runtime_view" in payload
        assert "continuity_view" in payload

        # View 1: Current System View checks
        sys_view = payload["current_system_view"]
        assert sys_view["runtime_status"] in ["active", "inactive"]
        assert "current_milestone" in sys_view
        assert sys_view["active_task"] is not None
        assert sys_view["blockers"] == []
        assert sys_view["last_checkpoint"] is not None

        # View 2: Archive View checks
        arch_view = payload["archive_view"]
        assert arch_view["master_archive_status"] == "available"
        assert isinstance(arch_view["latest_reports"], list)
        assert isinstance(arch_view["recent_decisions"], list)
        assert isinstance(arch_view["recent_operational_records"], list)

        # View 3: Runtime View checks
        rt_view = payload["runtime_view"]
        assert rt_view["health_status"]["status"] == "healthy"
        assert rt_view["api_status"]["status"] == "online"
        assert "OpenAI / ChatGPT" in rt_view["active_connectors"]
        assert "Google AI / Gemini" in rt_view["active_connectors"]

        # View 4: Continuity View checks
        cont_view = payload["continuity_view"]
        assert "latest_session_state" in cont_view
        assert isinstance(cont_view["checkpoint_history"], list)


def test_command_center_endpoint_integration():
    """Verify the /command-center endpoint fetches the visibility payload correctly."""
    with TestClient(app) as client:
        # Set some objectives and tasks
        client.post("/objective", json={"objective": "Validate Command Center"})
        client.post("/task", json={"task": "Run endpoint integration tests"})

        # Query Command Center endpoint
        response = client.get("/command-center")
        assert response.status_code == 200
        data = response.json()

        assert "timestamp" in data
        assert "current_system_view" in data
        assert "archive_view" in data

        sys_view = data["current_system_view"]
        assert sys_view["active_task"] == "Run endpoint integration tests"

        cont_view = data["continuity_view"]
        assert cont_view["latest_session_state"]["current_objective"] == "Validate Command Center"
