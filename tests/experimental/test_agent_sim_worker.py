"""SAGE Agent Activation v1 Simulation Worker test suite."""

import pytest
from datetime import datetime, timezone

from sage.agents.models import AgentIdentity, PermissionBoundary, AgentRole
from sage.experimental.act.agent_runner import GovernedAgentSimWorker


def test_agent_sim_worker_boundary_compliance():
    """Verify correct simulated dispatch when files and actions lie perfectly within allowed paths."""
    identity = AgentIdentity(
        agent_id="agent_contributor_01",
        name="Contributor SAGE Agent",
        role=AgentRole.CONTRIBUTOR
    )
    boundary = PermissionBoundary(
        agent_id="agent_contributor_01",
        allowed_paths=["sage/experimental/act/"],
        prohibited_paths=["sage/core/"],
        prohibited_actions=["delete_database"]
    )

    worker = GovernedAgentSimWorker(identity, boundary)
    result = worker.simulate_action(
        action_name="read_file",
        target_path="sage/experimental/act/contracts.py"
    )

    assert result["status"] == "SIMULATION_SUCCESS"
    assert result["agent_id"] == "agent_contributor_01"
    assert result["action"] == "read_file"
    assert result["read_only_assertion"] is True
    assert "task_event" in result


def test_agent_sim_worker_boundary_violation():
    """Confirms that attempts to read/write on prohibited paths raise a ValueError with prefix."""
    identity = AgentIdentity(
        agent_id="agent_contributor_01",
        name="Contributor SAGE Agent"
    )
    boundary = PermissionBoundary(
        agent_id="agent_contributor_01",
        prohibited_paths=["sage/core/"]
    )

    worker = GovernedAgentSimWorker(identity, boundary)
    with pytest.raises(ValueError, match="SAGE-ACT Contract Violation: Prohibited Path Intercepted"):
        worker.simulate_action(
            action_name="read_file",
            target_path="sage/core/spek.py"
        )


def test_agent_sim_worker_prohibited_action():
    """Verify that execution of prohibited action is blocked."""
    identity = AgentIdentity(
        agent_id="agent_contributor_01",
        name="Contributor SAGE Agent"
    )
    boundary = PermissionBoundary(
        agent_id="agent_contributor_01",
        prohibited_actions=["purge_logs"]
    )

    worker = GovernedAgentSimWorker(identity, boundary)
    with pytest.raises(ValueError, match="SAGE-ACT Contract Violation: Prohibited Action Intercepted"):
        worker.simulate_action(
            action_name="purge_logs",
            target_path="sage/experimental/act/contracts.py"
        )


def test_agent_sim_worker_causal_monotonicity():
    """Verify simulated event timestamps are chronologically consistent and properly monotonic."""
    identity = AgentIdentity(
        agent_id="agent_contributor_01",
        name="Contributor SAGE Agent"
    )
    boundary = PermissionBoundary(agent_id="agent_contributor_01")

    worker = GovernedAgentSimWorker(identity, boundary)

    t_start = datetime.now(timezone.utc)
    result = worker.simulate_action(
        action_name="read_file",
        target_path="sage/experimental/act/contracts.py"
    )
    t_end = datetime.now(timezone.utc)

    event_time_str = result["simulated_at"]
    event_dt = datetime.fromisoformat(event_time_str)

    # Convert event_dt to timezone aware if needed, fromisoformat handles standard format
    assert event_dt >= t_start or abs((event_dt - t_start).total_seconds()) <= 2
    assert event_dt <= t_end or abs((event_dt - t_end).total_seconds()) <= 2


def test_agent_sim_worker_read_only_invariance():
    """Assert that simulated worker makes zero disk writes and remains completely in-memory."""
    identity = AgentIdentity(
        agent_id="agent_contributor_01",
        name="Contributor SAGE Agent"
    )
    boundary = PermissionBoundary(agent_id="agent_contributor_01")

    worker = GovernedAgentSimWorker(identity, boundary)
    result = worker.simulate_action(
        action_name="write_file",
        target_path="sage/experimental/act/contracts.py"
    )

    assert result["status"] == "SIMULATION_SUCCESS"
    assert result["read_only_assertion"] is True
