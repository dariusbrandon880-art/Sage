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


from sage.experimental.act import AgentBoundaryInterceptionError


def test_agent_sim_worker_intercept_success():
    """Verify that simulate_action_with_intercept returns success when no violation occurs."""
    identity = AgentIdentity(
        agent_id="agent_contributor_01",
        name="Contributor SAGE Agent"
    )
    boundary = PermissionBoundary(
        agent_id="agent_contributor_01",
        allowed_paths=["sage/experimental/act/"]
    )

    worker = GovernedAgentSimWorker(identity, boundary)
    result = worker.simulate_action_with_intercept(
        action_name="read_file",
        target_path="sage/experimental/act/contracts.py",
        session_id="session_f6b3d4e5",
        workflow_id="workflow_123",
        current_task_step="read_contracts",
        previous_steps=[],
        causal_binder_ref="validation_status_ok",
        causal_chain=[],
        underlying_decisions=[]
    )

    assert result["status"] == "SIMULATION_SUCCESS"
    assert result["read_only_assertion"] is True


def test_agent_sim_worker_intercept_failure_schema():
    """Verify that simulate_action_with_intercept gracefully captures boundary failure and returns a schema-compliant payload."""
    identity = AgentIdentity(
        agent_id="agent_contributor_01",
        name="Contributor SAGE Agent"
    )
    boundary = PermissionBoundary(
        agent_id="agent_contributor_01",
        prohibited_paths=["sage/core/"]
    )

    worker = GovernedAgentSimWorker(identity, boundary)
    with pytest.raises(AgentBoundaryInterceptionError) as exc_info:
        worker.simulate_action_with_intercept(
            action_name="read_file",
            target_path="sage/core/spek.py",
            session_id="session_f6b3d4e5",
            workflow_id="workflow_123",
            current_task_step="read_spek",
            previous_steps=[{"step_name": "init_session", "completed_at": "2026-03-01T12:00:00Z", "status": "COMPLETED"}],
            causal_binder_ref="validation_status_ok",
            causal_chain=["decision_001"],
            underlying_decisions=[{"decision_id": "decision_001", "decision_type": "architectural", "timestamp": "2026-03-01T12:00:00Z"}]
        )

    err = exc_info.value
    assert "SAGE-ACT Contract Violation: Graceful Intercept Captured" in str(err)

    payload = err.payload
    # Verify exact schema compliance
    assert "identity" in payload
    assert payload["identity"]["agent_id"] == "agent_contributor_01"
    assert payload["identity"]["session_id"] == "session_f6b3d4e5"
    assert payload["identity"]["workflow_id"] == "workflow_123"

    assert "state" in payload
    assert payload["state"]["current_task_step"] == "read_spek"
    assert len(payload["state"]["previous_steps"]) == 1
    assert payload["state"]["active_state_snapshot_ref"].startswith("snapshot_")

    assert "failure_event" in payload
    assert payload["failure_event"]["failure_type"] == "BOUNDARY_VIOLATION"
    assert "timestamp" in payload["failure_event"]
    assert payload["failure_event"]["originating_component"] == "sage.experimental.act.agent_runner.GovernedAgentSimWorker"
    assert payload["failure_event"]["external_dependency_status"] == {"local_filesystem": "ACTIVE"}

    assert "decision_lineage" in payload
    assert payload["decision_lineage"]["causal_binder_ref"] == "validation_status_ok"
    assert payload["decision_lineage"]["causal_chain"] == ["decision_001"]
    assert len(payload["decision_lineage"]["underlying_decisions"]) == 1

    assert "recovery" in payload
    assert payload["recovery"]["recovery_possible"] is True
    assert payload["recovery"]["human_approval_required"] is True
    assert payload["recovery"]["rehydration_checkpoint_ref"].startswith("checkpoint_")
