"""SAGE-ACT Milestone 2 Interface validation and Import isolation test suite."""

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
from sage.agents.models import AgentTask, AgentTaskState, TaskEvent
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


def test_session_task_tree_linker_valid_integration():
    """Verify standard valid linkage mapping and zero anomalies when fully aligned."""
    session_mgr = MockSessionStateManager()
    task_router = MockAgentTaskRouter()

    # 1. Setup existing SessionState
    session_id = "session_2026_ok"
    session = SessionState(
        session_id=session_id,
        active_objectives=["obj_kernel_deploy"],
    )
    session_mgr.sessions[session_id] = session

    # 2. Setup active AgentTasks
    task_1 = AgentTask(
        task_id="task_001_compile",
        objective_id="obj_kernel_deploy",
        title="Compile secure kernel",
        assigned_agent_id="agent_jules_enforcer",
        state=AgentTaskState.COMPLETED,
    )
    task_router.tasks["task_001_compile"] = task_1

    linker = SessionTaskTreeLinker()
    report = linker.validate_session_and_tasks(
        session_id=session_id,
        task_ids=["task_001_compile"],
        session_manager=session_mgr,
        task_router=task_router,
    )

    assert report["session_id"] == session_id
    assert report["valid_continuity"] is True
    assert len(report["anomalies"]) == 0
    assert report["validation_status"] == "CONTINUITY_TRUTH_REPORT_COMPILED"


def test_session_task_tree_linker_anomalies_and_orphans():
    """Verify that linker detects session_not_found, task_not_found, orphan_task, and mismatch anomalies."""
    session_mgr = MockSessionStateManager()
    task_router = MockAgentTaskRouter()

    # Setup mismatched active session
    session_id = "session_2026_mismatch"
    session = SessionState(
        session_id=session_id,
        active_objectives=["obj_prod_deploy"],
    )
    session_mgr.sessions[session_id] = session

    # Setup an orphan task (no agent) with objective mismatch
    task_router.tasks["task_orphan"] = AgentTask(
        task_id="task_orphan",
        objective_id="obj_unaligned_secret",
        title="Unassigned secret audit",
        assigned_agent_id=None,  # Orphan
        state=AgentTaskState.PENDING,
    )

    linker = SessionTaskTreeLinker()

    # 1. Test missing session anomaly
    report_no_session = linker.validate_session_and_tasks(
        session_id="session_unknown",
        task_ids=[],
        session_manager=session_mgr,
        task_router=task_router,
    )
    assert report_no_session["valid_continuity"] is False
    assert any(a["type"] == "session_not_found" for a in report_no_session["anomalies"])

    # 2. Test missing task and orphan task anomalies
    report_orphans = linker.validate_session_and_tasks(
        session_id=session_id,
        task_ids=["task_missing", "task_orphan"],
        session_manager=session_mgr,
        task_router=task_router,
    )
    assert report_orphans["valid_continuity"] is False
    anom_types = [a["type"] for a in report_orphans["anomalies"]]
    assert "task_not_found" in anom_types
    assert "orphan_task_no_agent" in anom_types
    assert "objective_alignment_mismatch" in anom_types


def test_session_task_tree_linker_missing_lineage_link():
    """Verify detection of missing lineage link where a task references a session but is omitted from list."""
    session_mgr = MockSessionStateManager()
    task_router = MockAgentTaskRouter()

    session_id = "session_missing_link_test"
    session = SessionState(
        session_id=session_id,
        active_objectives=["obj_audit"],
    )
    session_mgr.sessions[session_id] = session

    # Task is in router and references session_id in metadata, but is not passed in task_ids list
    task_router.tasks["task_unlisted"] = AgentTask(
        task_id="task_unlisted",
        objective_id="obj_audit",
        title="Audit compliance logs",
        assigned_agent_id="agent_jules",
        metadata={"session_id": session_id},
    )

    linker = SessionTaskTreeLinker()
    report = linker.validate_session_and_tasks(
        session_id=session_id,
        task_ids=[],  # Omitting task_unlisted
        session_manager=session_mgr,
        task_router=task_router,
    )

    assert report["valid_continuity"] is False
    assert any(a["type"] == "missing_lineage_link" for a in report["anomalies"])


def test_task_decision_binder_valid_integration():
    """Verify standard valid decision-to-task binding with perfect temporal order."""
    task_router = MockAgentTaskRouter()
    dec_tracker = MockDecisionTracker()

    task_id = "task_verify_contract"
    now_tz = datetime.now(timezone.utc)

    # Task created at time 'now'
    task_router.tasks[task_id] = AgentTask(
        task_id=task_id,
        objective_id="obj_deploy",
        title="Contract verification",
        created_at=now_tz.isoformat(),
        assigned_agent_id="agent_enforcer",
    )

    # Decision made 5 minutes later
    dec_id = "decision_approve_scaffold"
    dec_tracker.decisions[dec_id] = DecisionEntry(
        id=dec_id,
        decision_type=DecisionType.TECHNICAL,
        description="Approve read-only contracts",
        rationale="Milestone 2 interface safety verified",
        timestamp=now_tz + timedelta(minutes=5),
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
    assert report["validation_status"] == "DECISION_CAUSALITY_MAP_COMPILED"


def test_task_decision_binder_causality_violations():
    """Verify that binder detects task_not_found, decision_not_found, and temporal_causality_violations."""
    task_router = MockAgentTaskRouter()
    dec_tracker = MockDecisionTracker()

    task_id = "task_2026_audit"
    now_tz = datetime.now(timezone.utc)

    # Task created 'now'
    task_router.tasks[task_id] = AgentTask(
        task_id=task_id,
        objective_id="obj_audit",
        title="Compliance checking",
        created_at=now_tz.isoformat(),
        assigned_agent_id="agent_validator",
    )

    # Decision is marked as having occurred 10 minutes *before* the task was created
    dec_id = "decision_retroactive"
    dec_tracker.decisions[dec_id] = DecisionEntry(
        id=dec_id,
        decision_type=DecisionType.ARCHITECTURAL,
        description="Retroactive decision",
        rationale="Incorrectly logged timeline",
        timestamp=now_tz - timedelta(minutes=10),  # Causality violation!
    )

    binder = TaskDecisionBinder()

    # 1. Test task not found
    report_no_task = binder.validate_task_and_decisions(
        task_id="task_unknown",
        decision_ids=[],
        task_router=task_router,
        decision_tracker=dec_tracker,
    )
    assert report_no_task["valid_causality"] is False
    assert any(a["type"] == "task_not_found" for a in report_no_task["anomalies"])

    # 2. Test decision not found & causality violations
    report_violations = binder.validate_task_and_decisions(
        task_id=task_id,
        decision_ids=["decision_missing", dec_id],
        task_router=task_router,
        decision_tracker=dec_tracker,
    )
    assert report_violations["valid_causality"] is False
    anom_types = [a["type"] for a in report_violations["anomalies"]]
    assert "decision_not_found" in anom_types
    assert "temporal_causality_violation" in anom_types


def test_task_decision_binder_unlinked_decision_reference():
    """Verify detection of decision referencing task in evidence but omitted from list."""
    task_router = MockAgentTaskRouter()
    dec_tracker = MockDecisionTracker()

    task_id = "task_core"
    task_router.tasks[task_id] = AgentTask(
        task_id=task_id,
        objective_id="obj_core",
        title="Core tasks",
        assigned_agent_id="agent_jules",
    )

    # Decision contains task_id in evidence list, but is not passed in decision_ids list
    dec_id = "decision_unlinked_ref"
    dec_tracker.decisions[dec_id] = DecisionEntry(
        id=dec_id,
        decision_type=DecisionType.STRATEGIC,
        description="Strategic mapping",
        rationale="Derived from task outcomes",
        evidence=[task_id],
    )

    binder = TaskDecisionBinder()
    report = binder.validate_task_and_decisions(
        task_id=task_id,
        decision_ids=[],  # Omitting dec_id
        task_router=task_router,
        decision_tracker=dec_tracker,
    )

    assert report["valid_causality"] is False
    assert any(a["type"] == "unlinked_decision_reference" for a in report["anomalies"])


def test_pre_mutation_safety_gates_path_isolation():
    """Verify that path mutation isolation checks pass for sandbox paths and fail for core paths."""
    gates = PreMutationSafetyGates()

    # Valid sandbox paths succeed
    assert gates.validate_path_isolation("sage/experimental/act/contracts.py") is True
    assert gates.validate_path_isolation("tests/experimental/test_act_interface.py") is True
    assert gates.validate_path_isolation("sage_data/sessions/session_xyz.json") is True

    # Mutating core files directly fails-closed with ValueError
    with pytest.raises(ValueError, match="Mutating core protected namespace"):
        gates.validate_path_isolation("sage/core/spek.py")

    with pytest.raises(ValueError, match="Mutating core protected namespace"):
        gates.validate_path_isolation(".sage/config/runtime.json")

    with pytest.raises(ValueError, match="Mutating core protected namespace"):
        gates.validate_path_isolation("sage/acr/eas_receipts.py")


def test_pre_mutation_safety_gates_nonce_freshness():
    """Verify that nonce uniqueness check accepts fresh nonces and rejects duplicates."""
    gates = PreMutationSafetyGates()
    active_ledger = ["nonce_used_123", "nonce_used_456"]

    # Fresh unique nonces succeed
    assert gates.validate_nonce_freshness("nonce_fresh_789", active_ledger) is True

    # Replayed nonces fail-closed
    with pytest.raises(ValueError, match="Nonce replay detected"):
        gates.validate_nonce_freshness("nonce_used_123", active_ledger)

    # Malformed nonces fail-closed
    with pytest.raises(ValueError, match="malformed or too short"):
        gates.validate_nonce_freshness("short", active_ledger)


def test_pre_mutation_safety_gates_acyclic_hierarchy():
    """Verify that acyclic hierarchy validation passes on DAGs and rejects loops."""
    gates = PreMutationSafetyGates()

    # Valid DAG dependencies (A -> B, B -> C, A -> C) succeed
    dag_map = {
        "task_A": ["task_B", "task_C"],
        "task_B": ["task_C"],
        "task_C": [],
    }
    assert gates.validate_acyclic_hierarchy(dag_map) is True

    # Cyclic dependencies (A -> B, B -> C, C -> A) fail-closed
    cyclic_map = {
        "task_A": ["task_B"],
        "task_B": ["task_C"],
        "task_C": ["task_A"],  # Cycle!
    }
    with pytest.raises(ValueError, match="Circular dependency detected"):
        gates.validate_acyclic_hierarchy(cyclic_map)


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
