"""Integration tests for SAGE 2 Universal Connectors and Operational Loop."""

import pytest
import tempfile
from pathlib import Path
from sage.runtime import SageRuntime
from sage.integration import (
    ConnectorRegistry,
    GitLabConnector,
    SlackConnector,
    LinearConnector,
    ConnectorStatus,
)


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_sage2_connector_registration(temp_workspace):
    """Verify that SAGE 2 universal connectors register and audit connection states correctly."""
    runtime = SageRuntime(str(temp_workspace))
    registry = ConnectorRegistry(runtime)

    gitlab = GitLabConnector(runtime)
    slack = SlackConnector(runtime)
    linear = LinearConnector(runtime)

    registry.register(gitlab)
    registry.register(slack)
    registry.register(linear)

    assert registry.get_connector("gitlab") == gitlab
    assert registry.get_connector("slack") == slack
    assert registry.get_connector("linear") == linear

    # Verify connection checking without keys (should default to NOT CONFIGURED)
    report = registry.get_registry_report()
    assert report["gitlab"]["status"] == ConnectorStatus.NOT_CONFIGURED
    assert report["slack"]["status"] == ConnectorStatus.NOT_CONFIGURED
    assert report["linear"]["status"] == ConnectorStatus.NOT_CONFIGURED


def test_sage2_connector_connection_with_mock_keys(temp_workspace):
    """Verify connectors dynamically identify configuration keys and set active status."""
    runtime = SageRuntime(str(temp_workspace))
    runtime.config["GITLAB_PRIVATE_TOKEN"] = "mock-gitlab-token"
    runtime.config["SLACK_BOT_TOKEN"] = "mock-slack-token"
    runtime.config["LINEAR_API_KEY"] = "mock-linear-key"

    registry = ConnectorRegistry(runtime)
    registry.register(GitLabConnector(runtime))
    registry.register(SlackConnector(runtime))
    registry.register(LinearConnector(runtime))

    report = registry.get_registry_report()
    assert report["gitlab"]["status"] == ConnectorStatus.CONNECTED
    assert report["slack"]["status"] == ConnectorStatus.CONNECTED
    assert report["linear"]["status"] == ConnectorStatus.CONNECTED


def test_sage2_connector_operational_loop_ingest(temp_workspace):
    """Verify that universal connectors route raw payloads cleanly through SAGERuntime's Continuity Bridge."""
    runtime = SageRuntime(str(temp_workspace))
    runtime.set_objective("Operational Loop Test")

    gitlab = GitLabConnector(runtime)
    slack = SlackConnector(runtime)

    # 1. Ingest GitLab Push Event
    gitlab_payload = {
        "event_name": "push",
        "project": {"name": "SAGE Engine"},
        "user_name": "Jules",
        "commits": [{"message": "Fix API bugs"}],
    }
    result_gl = gitlab.ingest_payload(gitlab_payload)
    assert result_gl["status"] == "success"
    assert "session_id" in result_gl

    # Verify memory contains the gitlab push interaction
    memories = runtime.memory.list_all()
    gl_mems = [m for m in memories if "gitlab" in m.tags]
    assert len(gl_mems) == 1
    assert gl_mems[0].content["user_name"] == "Jules"

    # 2. Ingest Slack message
    slack_payload = {
        "channel_id": "engineering",
        "text": "Completed the integration of PR #15",
    }
    result_slack = slack.ingest_payload(slack_payload)
    assert result_slack["status"] == "success"

    # Verify memory contains the slack message
    memories = runtime.memory.list_all()
    slack_mems = [m for m in memories if "slack" in m.tags]
    assert len(slack_mems) == 1
    assert slack_mems[0].content["text"] == "Completed the integration of PR #15"
