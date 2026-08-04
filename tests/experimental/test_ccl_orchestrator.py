"""Test suite for SAGE Continuity Control Loop (SAGE-CCL) Operational Coordination Engine."""

import os
import ast
import json
import pytest
from sage.experimental.act.ccl_orchestrator import DeveloperWorkflowOrchestrator


def test_orchestrator_lifecycle_and_transitions():
    """Verify standard task registration and allowed/invalid state transitions."""
    orch = DeveloperWorkflowOrchestrator(session_id="session_test_lifecycle")

    # Ingest initialization event
    task = orch.ingest_event(
        "TASK_INIT",
        "task_lifecycle_01",
        {
            "objective_id": "obj_test_lifecycle",
            "assigned_agent": "agent_initiator",
            "initial_context": {"key": "initial_value"},
            "lineage_references": ["ref_01"]
        }
    )

    assert task["status"] == "INITIATED"
    assert task["assigned_agent"] == "agent_initiator"
    assert task["context"]["key"] == "initial_value"

    # Re-initialization should fail
    with pytest.raises(ValueError, match="already been initiated"):
        orch.ingest_event("TASK_INIT", "task_lifecycle_01", {})

    # Invalid transitions should be rejected (e.g. INITIATED -> COMPLETED)
    with pytest.raises(ValueError, match="Forbidden transition"):
        orch.ingest_event(
            "STATE_TRANSITION",
            "task_lifecycle_01",
            {"target_status": "COMPLETED", "comment": "Bypass!"}
        )

    # Valid transition (INITIATED -> ACTIVE)
    orch.ingest_event(
        "STATE_TRANSITION",
        "task_lifecycle_01",
        {"target_status": "ACTIVE", "comment": "Start working"}
    )
    assert orch.tasks["task_lifecycle_01"]["status"] == "ACTIVE"


def test_context_continuity_and_handoff():
    """Verify task context and lineage are preserved accurately across handoffs."""
    orch = DeveloperWorkflowOrchestrator(session_id="session_test_handoff")

    orch.ingest_event(
        "TASK_INIT",
        "task_handoff_01",
        {
            "objective_id": "obj_test_handoff",
            "assigned_agent": "agent_analyst",
            "initial_context": {"baseline_metric": 0.95}
        }
    )

    # Move to ACTIVE
    orch.ingest_event(
        "STATE_TRANSITION",
        "task_handoff_01",
        {"target_status": "ACTIVE"}
    )

    # Trigger handoff to reviewer with context updates
    orch.ingest_event(
        "AGENT_HANDOFF",
        "task_handoff_01",
        {
            "target_agent": "agent_reviewer",
            "handoff_context": {"updated_metric": 0.99},
            "reason": "Peer review needed."
        }
    )

    task = orch.tasks["task_handoff_01"]
    assert task["status"] == "HANDOFF"
    assert task["assigned_agent"] == "agent_reviewer"
    assert task["context"]["baseline_metric"] == 0.95
    assert task["context"]["updated_metric"] == 0.99
    assert task["context"]["last_handoff_by"] == "agent_analyst"


def test_human_authorization_visibility():
    """Verify human checkpoints correctly guard and block completion transitions."""
    orch = DeveloperWorkflowOrchestrator(session_id="session_test_auth")

    orch.ingest_event(
        "TASK_INIT",
        "task_auth_01",
        {
            "objective_id": "obj_test_auth",
            "assigned_agent": "agent_worker"
        }
    )

    orch.ingest_event(
        "STATE_TRANSITION",
        "task_auth_01",
        {"target_status": "ACTIVE"}
    )

    # Attempt transition to COMPLETED without approval should fail
    with pytest.raises(PermissionError, match="Cannot complete task.*without.*AUTHORIZED.*human checkpoint"):
        orch.ingest_event(
            "STATE_TRANSITION",
            "task_auth_01",
            {"target_status": "COMPLETED"}
        )

    # Ingest REJECTED human approval
    orch.ingest_event(
        "HUMAN_APPROVAL",
        "task_auth_01",
        {
            "supervisor_id": "human_supervisor_01",
            "decision": "REJECTED",
            "comments": "Insufficent context validation."
        }
    )

    # Transition to COMPLETED should still fail
    with pytest.raises(PermissionError, match="Cannot complete task.*without.*AUTHORIZED.*human checkpoint"):
        orch.ingest_event(
            "STATE_TRANSITION",
            "task_auth_01",
            {"target_status": "COMPLETED"}
        )

    # Ingest AUTHORIZED human approval
    orch.ingest_event(
        "HUMAN_APPROVAL",
        "task_auth_01",
        {
            "supervisor_id": "human_supervisor_01",
            "decision": "AUTHORIZED",
            "comments": "Context looks solid. Proceed."
        }
    )

    # Transition to COMPLETED succeeds now
    orch.ingest_event(
        "STATE_TRANSITION",
        "task_auth_01",
        {"target_status": "COMPLETED"}
    )
    assert orch.tasks["task_auth_01"]["status"] == "COMPLETED"


def test_continuity_records_and_evidence(tmp_path):
    """Verify that formal ContinuityControlRecords are produced with deterministic structures."""
    evidence_file = tmp_path / "ccl_evidence.json"
    orch = DeveloperWorkflowOrchestrator(session_id="session_test_evidence")

    orch.ingest_event(
        "TASK_INIT",
        "task_evidence_01",
        {
            "objective_id": "obj_test_evidence",
            "assigned_agent": "agent_jules",
            "initial_context": {"workspace": "sage/experimental"}
        }
    )

    orch.ingest_event(
        "STATE_TRANSITION",
        "task_evidence_01",
        {"target_status": "ACTIVE"}
    )

    orch.ingest_event(
        "HUMAN_APPROVAL",
        "task_evidence_01",
        {
            "supervisor_id": "human_supervisor_01",
            "decision": "AUTHORIZED",
            "comments": "Approved."
        }
    )

    orch.ingest_event(
        "STATE_TRANSITION",
        "task_evidence_01",
        {"target_status": "COMPLETED"}
    )

    # Export evidence
    evidence = orch.export_evidence(str(evidence_file))

    # Assert structural content
    assert evidence["execution_identifier"].startswith("ccl_run_")
    assert "task_evidence_01" in evidence["active_tasks"]

    # Assert ContinuityControlRecord validity
    ccl_record = evidence["continuity_control_records"]["task_evidence_01"]
    assert ccl_record["record_id"].startswith("CCL-REC-")
    assert ccl_record["task_state_snapshot"]["status"] == "COMPLETED"
    assert len(ccl_record["state_integrity"]["state_hash"]) == 64
    assert len(ccl_record["monotonic_sequence_history"]) == 4

    # Confirm correct JSON serialization
    assert evidence_file.exists()
    with open(evidence_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["execution_identifier"] == evidence["execution_identifier"]


def test_core_ast_isolation():
    """Verify SAGE One-Way Import Law: core production files must never import experimental modules."""
    protected_dirs = ["sage/runtime", "sage/core", "sage/acr", "sage/agents"]

    for root_dir in protected_dirs:
        if not os.path.exists(root_dir):
            continue

        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue

                filepath = os.path.join(dirpath, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read(), filename=filepath)
                    except SyntaxError:
                        continue

                for node in ast.walk(tree):
                    # Check for "import sage.experimental..."
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            assert "sage.experimental" not in alias.name, \
                                f"AST Isolation Violation in '{filepath}': Imports '{alias.name}'"

                    # Check for "from sage.experimental... import ..."
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            assert "sage.experimental" not in node.module, \
                                f"AST Isolation Violation in '{filepath}': From-imports '{node.module}'"
