"""SAGE-ACT Milestone 2 Lineage Mapping and Validation test suite."""

import pytest
import os
import ast
from pathlib import Path
from datetime import datetime, timedelta, timezone

from sage.experimental.act.contracts import (
    SessionTaskTreeLinker,
    TaskDecisionBinder,
    PreMutationSafetyGates,
)
from sage.acr.session.session_state import SessionState
from sage.agents.models import AgentTask, AgentTaskState
from sage.models import DecisionEntry, DecisionType


class MockSessionStateManager:
    """Mock state manager for SessionState retrievals."""

    def __init__(self):
        self.sessions = {}

    def retrieve_session(self, session_id: str):
        return self.sessions.get(session_id)


class MockAgentTaskRouter:
    """Mock router for AgentTask retrievals."""

    def __init__(self):
        self.tasks = {}


class MockDecisionTracker:
    """Mock tracker for DecisionEntry retrievals."""

    def __init__(self):
        self.decisions = {}

    def list_all(self):
        return list(self.decisions.values())


def test_session_state_consumption_and_anomalies():
    """Verify that existing SessionState structures can be consumed and analyzed safely."""
    session_mgr = MockSessionStateManager()
    task_router = MockAgentTaskRouter()

    session_id = "session_milestone2_ok"
    session = SessionState(
        session_id=session_id,
        active_objectives=["obj_validate_scaffold"],
        completed_actions=["task_M2_scaffold"],
        pending_actions=["task_M2_review"],
    )
    session_mgr.sessions[session_id] = session

    # Add a correctly aligned completed task
    task_1 = AgentTask(
        task_id="task_M2_scaffold",
        objective_id="obj_validate_scaffold",
        title="task_M2_scaffold",  # matches title list in completed_actions
        assigned_agent_id="agent_jules",
        state=AgentTaskState.COMPLETED,
    )
    task_router.tasks["task_M2_scaffold"] = task_1

    # Add an uncompleted task
    task_2 = AgentTask(
        task_id="task_M2_review",
        objective_id="obj_validate_scaffold",
        title="task_M2_review",
        assigned_agent_id="agent_jules",
        state=AgentTaskState.EXECUTING,
    )
    task_router.tasks["task_M2_review"] = task_2

    linker = SessionTaskTreeLinker()

    # Verify successful trace
    report = linker.validate_session_and_tasks(
        session_id=session_id,
        task_ids=["task_M2_scaffold", "task_M2_review"],
        session_manager=session_mgr,
        task_router=task_router,
    )

    assert report["session_id"] == session_id
    assert report["valid_continuity"] is True
    assert len(report["anomalies"]) == 0
    assert report["validation_status"] == "CONTINUITY_TRUTH_REPORT_COMPILED"

    # Verify action consistency mismatch anomaly (e.g. COMPLETED task missing from completed_actions)
    session.completed_actions = ["some_other_completed_action"]  # break alignment completely
    report_mismatch = linker.validate_session_and_tasks(
        session_id=session_id,
        task_ids=["task_M2_scaffold"],
        session_manager=session_mgr,
        task_router=task_router,
    )
    assert report_mismatch["valid_continuity"] is False
    assert any(a["type"] == "action_consistency_mismatch" for a in report_mismatch["anomalies"])


def test_decision_entry_mapping_and_causality():
    """Verify that existing DecisionEntry structures can be mapped, checking causality and agent alignment."""
    task_router = MockAgentTaskRouter()
    dec_tracker = MockDecisionTracker()

    task_id = "task_verify"
    now_tz = datetime.now(timezone.utc)

    # Setup task with assigned agent
    task_router.tasks[task_id] = AgentTask(
        task_id=task_id,
        objective_id="obj_validate",
        title="Lineage verification",
        created_at=now_tz.isoformat(),
        assigned_agent_id="agent_jules",
    )

    # Setup decision made 10 minutes later, referencing the assigned agent ID in its rationale
    dec_id = "decision_ok"
    dec_tracker.decisions[dec_id] = DecisionEntry(
        id=dec_id,
        decision_type=DecisionType.ARCHITECTURAL,
        description="Lineage mapped",
        rationale="Mapping is read-only and safe for agent_jules",
        timestamp=now_tz + timedelta(minutes=10),
        outcome="APPROVED",
    )

    binder = TaskDecisionBinder()
    report = binder.validate_task_and_decisions(
        task_id=task_id,
        decision_ids=[dec_id],
        task_router=task_router,
        decision_tracker=dec_tracker,
    )

    assert report["task_id"] == task_id
    assert report["valid_causality"] is True
    assert len(report["anomalies"]) == 0

    # Verify agent ownership mismatch anomaly (assigned task agent is not mentioned)
    task_router.tasks[task_id].assigned_agent_id = "agent_unauthorized"
    report_agent_mismatch = binder.validate_task_and_decisions(
        task_id=task_id,
        decision_ids=[dec_id],
        task_router=task_router,
        decision_tracker=dec_tracker,
    )
    assert report_agent_mismatch["valid_causality"] is False
    assert any(a["type"] == "agent_ownership_mismatch" for a in report_agent_mismatch["anomalies"])


def test_pre_mutation_safety_validators():
    """Verify that PreMutationSafetyGates simulation reports findings without mutative side-effects."""
    gates = PreMutationSafetyGates()

    # 1. Path Mutation Isolation Check
    f_isolated = gates.validate_path_isolation("sage/experimental/act/contracts.py")
    assert f_isolated["is_isolated"] is True
    assert f_isolated["code"] == "PATH_ISOLATED"

    f_protected = gates.validate_path_isolation("sage/core/spek.py")
    assert f_protected["is_isolated"] is False
    assert f_protected["code"] == "PROTECTED_NAMESPACE_VIOLATION"

    # 2. Nonce Freshness Validation
    f_fresh = gates.validate_nonce_freshness("nonce_fresh_12345", ["nonce_replayed"])
    assert f_fresh["is_fresh"] is True
    assert f_fresh["code"] == "NONCE_FRESH"

    f_replay = gates.validate_nonce_freshness("nonce_replayed", ["nonce_replayed"])
    assert f_replay["is_fresh"] is False
    assert f_replay["code"] == "NONCE_REPLAY"

    # 3. Cyclic Lineage Detection
    dag_dependency = {
        "task_1": ["task_2"],
        "task_2": ["task_3"],
        "task_3": []
    }
    f_dag = gates.validate_acyclic_hierarchy(dag_dependency)
    assert f_dag["is_acyclic"] is True
    assert f_dag["code"] == "HIERARCHY_ACYCLIC"

    cyclic_dependency = {
        "task_1": ["task_2"],
        "task_2": ["task_3"],
        "task_3": ["task_1"]  # Circular cycle!
    }
    f_cycle = gates.validate_acyclic_hierarchy(cyclic_dependency)
    assert f_cycle["is_acyclic"] is False
    assert f_cycle["code"] == "CYCLE_DETECTED"


def test_one_way_import_isolation_enforcement():
    """Verify absolute enforcement of the One-Way Import Law.

    No module in the frozen production/core namespace ('sage/acr/', 'sage/core/', etc.)
    is allowed to import from 'sage.experimental' or 'sage.experimental.act'.
    """
    root_path = Path(__file__).parent.parent.parent / "sage"
    assert root_path.exists(), f"Could not find SAGE source path at: {root_path}"

    for file_path in root_path.glob("**/*.py"):
        # Exclude files inside sage/experimental
        if "experimental" in file_path.parts:
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=str(file_path))
            except SyntaxError as e:
                pytest.fail(f"Syntax error while parsing {file_path}: {e}")

            for node in ast.walk(tree):
                # Check direct imports (e.g., 'import sage.experimental')
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "sage.experimental" not in alias.name, (
                            f"One-Way Import Law Violation inside production: '{file_path}' "
                            f"attempts to directly import '{alias.name}'"
                        )
                # Check from imports (e.g., 'from sage.experimental.act import SessionTaskTreeLinker')
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        assert "sage.experimental" not in node.module, (
                            f"One-Way Import Law Violation inside production: '{file_path}' "
                            f"attempts to import from module '{node.module}'"
                        )
