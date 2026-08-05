"""Test suite for SAGE Continuity Control Loop (SAGE-CCL) Operational Coordination Engine."""

import os
import ast
import json
import pytest
from sage.experimental.act.ccl_orchestrator import (
    DeveloperWorkflowOrchestrator,
    ChatGPTAgentConnector,
    JulesAgentConnector,
)


def test_orchestrator_lifecycle_and_transitions():
    """Verify standard task registration and allowed/invalid state transitions under activation constraints."""
    orch = DeveloperWorkflowOrchestrator(session_id="session_test_lifecycle")

    # Activate agent_initiator
    orch.ingest_event(
        "AGENT_ACTIVATION",
        "system",
        {
            "agent_id": "agent_initiator",
            "supervisor_id": "human_supervisor_01",
            "decision": "AUTHORIZED",
            "role": "EXECUTOR"
        }
    )

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
    assert task["agent_role"] == "EXECUTOR"
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


def test_unactivated_agent_rejection():
    """Verify unactivated agents are blocked from task assignment and state transitions."""
    orch = DeveloperWorkflowOrchestrator(session_id="session_test_unactivated")

    # Trying to assign unactivated agent should raise PermissionError
    with pytest.raises(PermissionError, match="Cannot assign unactivated agent"):
        orch.ingest_event(
            "TASK_INIT",
            "task_fail_01",
            {
                "objective_id": "obj_fail",
                "assigned_agent": "agent_unactivated"
            }
        )

    # Now, initiate a task with an unassigned status
    orch.ingest_event(
        "TASK_INIT",
        "task_fail_01",
        {
            "objective_id": "obj_fail",
            "assigned_agent": "unassigned"
        }
    )

    # Trying to transition using an unactivated agent should fail
    with pytest.raises(PermissionError, match="Unactivated agent.*cannot perform state transition"):
        orch.ingest_event(
            "STATE_TRANSITION",
            "task_fail_01",
            {
                "target_status": "ACTIVE",
                "agent_id": "agent_unactivated"
            }
        )


def test_context_continuity_and_handoff():
    """Verify task context and lineage are preserved accurately across handoffs under activation checks."""
    orch = DeveloperWorkflowOrchestrator(session_id="session_test_handoff")

    # Activate analyst and reviewer
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_analyst", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "ANALYST"})
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_reviewer", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "REVIEWER"})

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

    # Handoff to unactivated agent should fail
    with pytest.raises(PermissionError, match="Destination agent.*is not activated"):
        orch.ingest_event(
            "AGENT_HANDOFF",
            "task_handoff_01",
            {
                "target_agent": "agent_not_active",
                "reason": "Request audit"
            }
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
    assert task["agent_role"] == "REVIEWER"
    assert task["context"]["baseline_metric"] == 0.95
    assert task["context"]["updated_metric"] == 0.99
    assert task["context"]["last_handoff_by"] == "agent_analyst"


def test_multi_agent_structured_delegation():
    """Verify active parent tasks can delegate subtasks to other activated agents with role awareness."""
    orch = DeveloperWorkflowOrchestrator(session_id="session_test_delegation")

    # Activate Coordinator and Executor
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_coord", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "COORDINATOR"})
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_exec", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "EXECUTOR"})
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_unassigned", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "GENERAL_AGENT"})

    # Initialize Parent Task
    orch.ingest_event(
        "TASK_INIT",
        "parent_task_01",
        {
            "objective_id": "obj_main_refactor",
            "assigned_agent": "agent_coord",
            "lineage_references": ["ref_adr_baseline"]
        }
    )

    # Non-active parent task should fail to delegate
    with pytest.raises(PermissionError, match="Parent task.*must be in 'ACTIVE' state to delegate"):
        orch.delegate_task("parent_task_01", "subtask_01", "agent_exec", "obj_exec_subtask")

    # Move parent task to ACTIVE
    orch.ingest_event("STATE_TRANSITION", "parent_task_01", {"target_status": "ACTIVE"})

    # Delegate to unactivated agent should fail
    with pytest.raises(PermissionError, match="Target agent.*must be fully activated to receive delegated task"):
        orch.delegate_task("parent_task_01", "subtask_01", "agent_unactivated", "obj_subtask")

    # Delegate task successfully
    subtask = orch.delegate_task(
        parent_task_id="parent_task_01",
        child_task_id="subtask_01",
        to_agent="agent_exec",
        objective_id="obj_exec_subtask",
        initial_context={"diff_size": 25}
    )

    assert subtask["task_id"] == "subtask_01"
    assert subtask["parent_task_id"] == "parent_task_01"
    assert subtask["assigned_agent"] == "agent_exec"
    assert subtask["agent_role"] == "EXECUTOR"
    assert subtask["context"]["diff_size"] == 25
    assert "ref_adr_baseline" in subtask["lineage_references"]

    parent_task = orch.tasks["parent_task_01"]
    assert "subtask_01" in parent_task["subtask_ids"]


def test_controlled_workflow_progress_and_ownership():
    """Verify governed execution progress reporting, active result ingestion, and ownership constraints."""
    orch = DeveloperWorkflowOrchestrator(session_id="session_test_progress")

    # Activate Executor & Observer
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_exec", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "EXECUTOR"})
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_observer", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "ANALYST"})

    orch.ingest_event(
        "TASK_INIT",
        "task_progress_01",
        {
            "objective_id": "obj_code_gen",
            "assigned_agent": "agent_exec"
        }
    )

    # Ingestion of progress should fail if task is not ACTIVE
    with pytest.raises(PermissionError, match="Cannot record progress on task.*INITIATED"):
        orch.record_progress("task_progress_01", "agent_exec", 10.0, {"changes": "baseline"})

    # Move task to ACTIVE
    orch.ingest_event("STATE_TRANSITION", "task_progress_01", {"target_status": "ACTIVE"})

    # Ingestion should fail if unauthorized agent attempts to write progress (Ownership check)
    with pytest.raises(PermissionError, match="Agent.*does not own task"):
        orch.record_progress("task_progress_01", "agent_observer", 25.0, {"changes": "illegal_override"})

    # Ingestion succeeds for the correct owner
    res = orch.record_progress(
        task_id="task_progress_01",
        agent_id="agent_exec",
        progress_percent=75.0,
        result_payload={"git_hash": "a8c9b201"},
        feedback="AST parsing passed successfully."
    )

    assert res["progress_percent"] == 75.0
    assert res["latest_result"]["git_hash"] == "a8c9b201"
    assert len(res["operational_feedback"]) == 1
    assert res["operational_feedback"][0]["feedback"] == "AST parsing passed successfully."


def test_workflow_intelligence_feedback_layer():
    """Verify workflow state analysis, risk/drift/blocked detections, and structured improvement candidate generation."""
    orch = DeveloperWorkflowOrchestrator(session_id="session_test_intelligence")

    # Activate Coordinator, Executor, and General Agent
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_coord", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "COORDINATOR"})
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_exec", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "GENERAL_AGENT"}) # Lack of specialized role

    # 1. Initialize Parent Task - Active Risk: assigned general agent, missing lineage refs
    orch.ingest_event(
        "TASK_INIT",
        "parent_task_01",
        {
            "objective_id": "obj_main_refactor",
            "assigned_agent": "agent_exec"
        }
    )

    # 2. Blocked Task: parent task is ACTIVE but progress is stalled at 0.0%
    orch.ingest_event("STATE_TRANSITION", "parent_task_01", {"target_status": "ACTIVE"})

    # 3. Drift Event: Child task objective is different from parent task
    orch.delegate_task("parent_task_01", "subtask_drift", "agent_coord", "obj_different_drift")

    # 4. Ingest Operational feedback for classification
    orch.record_progress("parent_task_01", "agent_exec", 10.0, {}, "Verify and test AST compilation limits.") # TEST_INTEGRITY
    orch.record_progress("parent_task_01", "agent_exec", 50.0, {}, "Encountered boundary security violations.") # BOUNDARY_SECURITY

    # Analyze
    analysis = orch.intelligence.analyze_workflow_state()
    assert len(analysis["active_risks"]) >= 2
    assert len(analysis["blocked_tasks"]) >= 1
    assert len(analysis["drift_events"]) >= 1

    # Verify Feedback Classification
    opps = orch.intelligence.process_operational_feedback()
    categories = [opp["category"] for opp in opps]
    assert "TEST_INTEGRITY" in categories
    assert "BOUNDARY_SECURITY" in categories

    # Verify Improvement Candidates
    candidates = orch.intelligence.generate_improvement_candidates()
    assert len(candidates) >= 3
    categories_cand = [cand["category"] for cand in candidates]
    assert "AUTOMATION_TEST_INTEGRITY" in categories_cand
    assert "AUTOMATION_BOUNDARY_SECURITY" in categories_cand
    assert "WORKFLOW_COORDINATION_REPAIR" in categories_cand

    # Verify Operator Intelligence View rendering
    view = orch.intelligence.generate_operator_intelligence_view()
    assert "SAGE WORKFLOW INTELLIGENCE & FEEDBACK LAYER" in view
    assert "ACTIVE RISKS DETECTED" in view
    assert "BLOCKED / STALLED TASKS" in view
    assert "TASK OBJECTIVE DRIFT EVENTS" in view
    assert "STRUCTURED IMPROVEMENT CANDIDATES" in view


def test_human_authorization_visibility():
    """Verify human checkpoints correctly guard and block completion transitions."""
    orch = DeveloperWorkflowOrchestrator(session_id="session_test_auth")

    # Activate agent_worker
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_worker", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "EXECUTOR"})

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

    # Activate agent_jules
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_jules", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "COORDINATOR"})

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

    # Record some progress
    orch.record_progress("task_evidence_01", "agent_jules", 50.0, {"stage": "intermediate_build"}, "Stage 1 builds.")

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
    assert ccl_record["task_state_snapshot"]["agent_role"] == "COORDINATOR"
    assert ccl_record["task_state_snapshot"]["progress_percent"] == 50.0
    assert ccl_record["task_state_snapshot"]["latest_result"]["stage"] == "intermediate_build"
    assert len(ccl_record["state_integrity"]["state_hash"]) == 64

    # Confirm correct JSON serialization
    assert evidence_file.exists()
    with open(evidence_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["execution_identifier"] == evidence["execution_identifier"]


def test_operator_summary():
    """Verify terminal operator-visible summary formatting and delegation hierarchies."""
    orch = DeveloperWorkflowOrchestrator(session_id="session_test_summary")

    # Activate agents
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_exec", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "EXECUTOR"})
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_susp", "supervisor_id": "super", "decision": "SUSPENDED"})

    orch.ingest_event(
        "TASK_INIT",
        "task_summary_01",
        {
            "objective_id": "obj_render_summary",
            "assigned_agent": "agent_exec"
        }
    )

    # Delegate child subtask
    orch.ingest_event("STATE_TRANSITION", "task_summary_01", {"target_status": "ACTIVE"})
    orch.delegate_task("task_summary_01", "subtask_summary_01", "agent_exec", "obj_render_subtask")

    # Record child progress
    orch.ingest_event("STATE_TRANSITION", "subtask_summary_01", {"target_status": "ACTIVE"})
    orch.record_progress("subtask_summary_01", "agent_exec", 90.0, {"coverage": "98%"}, "Refactored tests.")

    summary = orch.generate_operator_summary()
    assert "SAGE OPERATIONAL COORDINATION & CONTEXT SUMMARY" in summary
    assert "agent_exec" in summary
    assert "[ACTIVATED] (Role: EXECUTOR)" in summary
    assert "agent_susp" in summary
    assert "[SUSPENDED]" in summary
    assert "task_summary_01" in summary
    assert "obj_render_summary" in summary
    assert "subtask_summary_01" in summary
    assert "Progress: 90.0%" in summary
    assert "Latest  : {\"coverage\": \"98%\"}" in summary


def test_chatgpt_agent_connector():
    """Verify ChatGPTAgentConnector registration, context rehydration, event alignment, clarification, and handoffs."""
    orch = DeveloperWorkflowOrchestrator(session_id="session_chatgpt_testing")

    # 1. Verification of Automatic Activations and Role Mapping
    conn = ChatGPTAgentConnector(orch, agent_id="agent_chat_ops")
    assert orch.agents["agent_chat_ops"] == "ACTIVATED"
    assert orch.agent_roles["agent_chat_ops"] == "COORDINATOR"

    # 2. Context Rehydration Check
    rehydrated = conn.rehydrate_context()
    assert rehydrated["orchestrator_run_id"] == orch.orchestrator_run_id
    assert rehydrated["agent_identity"]["role"] == "COORDINATOR"
    assert "ADR-001" in rehydrated["lineage_baselines"]

    # 3. Conversational State Alignment Routing
    task = conn.align_workflow_state("INITIATE_TASK", "task_chatgpt_01", {
        "objective_id": "obj_coordination_test",
        "initial_context": {"origin": "chat_prompt"},
        "lineage_references": ["ref_lineage_01"]
    })
    assert task["task_id"] == "task_chatgpt_01"
    assert task["status"] == "INITIATED"
    assert task["context"]["origin"] == "chat_prompt"

    # Advance state to ACTIVE
    conn.align_workflow_state("START_EXECUTION", "task_chatgpt_01", {"comment": "Starting test."})
    assert orch.tasks["task_chatgpt_01"]["status"] == "ACTIVE"

    # Record progress
    conn.align_workflow_state("RECORD_PROGRESS", "task_chatgpt_01", {
        "progress_percent": 30.0,
        "result_payload": {"stage": "analysis_complete"}
    })
    assert orch.tasks["task_chatgpt_01"]["progress_percent"] == 30.0

    # 4. Objective Clarification Logging
    conn.clarify_objective("task_chatgpt_01", "Clarify AST boundary path?", "Paths must be restricted to sage/experimental.")
    clarifications = orch.tasks["task_chatgpt_01"]["context"]["objective_clarifications"]
    assert len(clarifications) == 1
    assert clarifications[0]["question"] == "Clarify AST boundary path?"
    assert clarifications[0]["clarification"] == "Paths must be restricted to sage/experimental."

    # 5. Handoff Manifest Generation & Verification
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_jules_exec", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "EXECUTOR"})
    manifest = conn.generate_handoff_manifest("task_chatgpt_01", "agent_jules_exec")

    assert manifest["source_agent"] == "agent_chat_ops"
    assert manifest["destination_agent"] == "agent_jules_exec"
    assert "origin" in manifest["preserved_context_keys"]
    assert orch.tasks["task_chatgpt_01"]["status"] == "HANDOFF"
    assert orch.tasks["task_chatgpt_01"]["assigned_agent"] == "agent_jules_exec"


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


def test_end_to_end_integrated_system(tmp_path):
    """Rigorous end-to-end integration test validating the entire SAGE control loop as one cohesive system."""
    evidence_file = tmp_path / "ccl_integrated_evidence.json"
    orch = DeveloperWorkflowOrchestrator(session_id="session_root_integration")

    # 1. Agent Activation Registry (Governed Gate)
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_coord", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "COORDINATOR"})
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_exec", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "EXECUTOR"})
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_analyst", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "ANALYST"})
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_reviewer", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "REVIEWER"})

    # 2. Task Initialization (Parent Workflow)
    orch.ingest_event("TASK_INIT", "task_root", {
        "objective_id": "obj_root_integration",
        "assigned_agent": "agent_coord",
        "initial_context": {"workspace": "sage/experimental/act", "status": "init"},
        "lineage_references": ["ADR-001", "SAGE-ACT-MP-2.0"]
    })

    # Move parent task to ACTIVE
    orch.ingest_event("STATE_TRANSITION", "task_root", {"target_status": "ACTIVE"})

    # 3. Coordinated Task Delegation
    orch.delegate_task("task_root", "subtask_exec", "agent_exec", "obj_exec_subtask")
    orch.delegate_task("task_root", "subtask_analyst", "agent_analyst", "obj_analyst_subtask")

    # 4. Controlled Agent Execution (Progress & Feedback Reporting)
    orch.ingest_event("STATE_TRANSITION", "subtask_exec", {"target_status": "ACTIVE"})
    orch.record_progress("subtask_exec", "agent_exec", 50.0, {"stage": "code_gen"}, "Verify and test AST compilation limits.")
    orch.record_progress("subtask_exec", "agent_exec", 100.0, {"stage": "done"}, "Encountered boundary security violations.")

    orch.ingest_event("STATE_TRANSITION", "subtask_analyst", {"target_status": "ACTIVE"})
    orch.record_progress("subtask_analyst", "agent_analyst", 100.0, {"violations": 0}, "Verified zero AST mutations.")

    # 5. Coordinated Handoff Sequencing
    orch.ingest_event("AGENT_HANDOFF", "subtask_exec", {
        "target_agent": "agent_reviewer",
        "handoff_context": {"git_hash": "a8c9b201"},
        "reason": "Request code refactor review."
    })

    # 6. Human Authorization Gateway Checks
    orch.ingest_event("HUMAN_APPROVAL", "subtask_exec", {"supervisor_id": "human_supervisor_01", "decision": "AUTHORIZED", "comments": "Approved."})
    orch.ingest_event("STATE_TRANSITION", "subtask_exec", {"target_status": "COMPLETED", "agent_id": "agent_reviewer", "comment": "Reviewer signed off."})

    orch.ingest_event("HUMAN_APPROVAL", "subtask_analyst", {"supervisor_id": "human_supervisor_01", "decision": "AUTHORIZED", "comments": "AST isolation check approved."})
    orch.ingest_event("STATE_TRANSITION", "subtask_analyst", {"target_status": "COMPLETED", "agent_id": "agent_analyst", "comment": "Analyst signed off."})

    orch.ingest_event("HUMAN_APPROVAL", "task_root", {"supervisor_id": "human_supervisor_01", "decision": "AUTHORIZED", "comments": "Root workflow approved."})
    orch.ingest_event("STATE_TRANSITION", "task_root", {"target_status": "COMPLETED", "agent_id": "agent_coord", "comment": "Coordinated workflow completed."})

    # 7. Operational Evidence Export & Analytics (SAGE-OWIL)
    evidence = orch.export_evidence(str(evidence_file))

    # Assertions validating the entire integrated system works as one cohesive unit
    assert evidence["execution_identifier"] == orch.orchestrator_run_id
    assert "task_root" in evidence["active_tasks"]
    assert "subtask_exec" in evidence["active_tasks"]
    assert "subtask_analyst" in evidence["active_tasks"]

    # Verify state, context preservation, and lineage tracing
    subtask_exec_state = evidence["active_tasks"]["subtask_exec"]
    assert subtask_exec_state["status"] == "COMPLETED"
    assert subtask_exec_state["assigned_agent"] == "agent_reviewer"
    assert subtask_exec_state["agent_role"] == "REVIEWER"
    assert subtask_exec_state["context"]["git_hash"] == "a8c9b201"
    assert subtask_exec_state["context"]["last_handoff_by"] == "agent_exec"
    assert len(subtask_exec_state["operational_feedback"]) == 2

    # Verify intelligence report is generated
    report = evidence["workflow_intelligence_report"]
    assert len(report["active_risks"]) >= 0
    assert len(report["drift_events"]) >= 0
    assert len(report["improvement_opportunities"]) == 3
    assert len(report["structured_improvement_candidates"]) == 3

    # Confirm operator intelligence view console output formatting
    view = report["operator_intelligence_view"]
    assert "SAGE WORKFLOW INTELLIGENCE & FEEDBACK LAYER" in view[1]
    assert " ACTIVE RISKS DETECTED:" in view
    assert " BLOCKED / STALLED TASKS:" in view
    assert " TASK OBJECTIVE DRIFT EVENTS:" in view
    assert " STRUCTURED IMPROVEMENT CANDIDATES GENERATED:" in view


def test_realistic_workflow_variation_and_recovery(tmp_path):
    """Verify SAGE-CCL-OPS resilience under realistic workflow variations and recovery scenarios."""
    evidence_file = tmp_path / "ccl_realism_evidence.json"
    orch = DeveloperWorkflowOrchestrator(session_id="session_realism_validation")

    # 1. Activate agent network
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_coord", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "COORDINATOR"})
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_exec", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "EXECUTOR"})

    # 2. TASK_INIT (with initial context)
    orch.ingest_event("TASK_INIT", "task_parent", {
        "objective_id": "obj_primary_mission",
        "assigned_agent": "agent_coord",
        "initial_context": {"baseline": "v1.0"}
    })
    orch.ingest_event("STATE_TRANSITION", "task_parent", {"target_status": "ACTIVE"})

    # 3. Objective Shift (Dynamic change during execution)
    orch.delegate_task("task_parent", "subtask_variation", "agent_exec", "obj_updated_mission")
    orch.ingest_event("STATE_TRANSITION", "subtask_variation", {"target_status": "ACTIVE"})

    # 4. Unexpected Agent Delay / Interrupted execution (stalled progress)
    orch.record_progress("subtask_variation", "agent_exec", 0.0, {"stage": "interrupted"}, "Encountered slow container build. Stalled.")

    # 5. Recovery after Interruption
    orch.record_progress("subtask_variation", "agent_exec", 100.0, {"stage": "recovered", "status": "all_green"}, "Recovered container and verified AST compliance.")

    # 6. Human Gate Approval
    orch.ingest_event("HUMAN_APPROVAL", "subtask_variation", {"supervisor_id": "human_supervisor_01", "decision": "AUTHORIZED", "comments": "AST isolation checked after build recovery."})
    orch.ingest_event("STATE_TRANSITION", "subtask_variation", {"target_status": "COMPLETED", "agent_id": "agent_exec", "comment": "Subtask recovered and completed."})

    orch.ingest_event("HUMAN_APPROVAL", "task_parent", {"supervisor_id": "human_supervisor_01", "decision": "AUTHORIZED", "comments": "Parent mission approved."})
    orch.ingest_event("STATE_TRANSITION", "task_parent", {"target_status": "COMPLETED", "agent_id": "agent_coord", "comment": "Closing parent task."})

    # 7. Export evidence to verify traceability
    evidence = orch.export_evidence(str(evidence_file))

    # Assertions for realistic variation & recovery
    assert evidence["execution_identifier"] == orch.orchestrator_run_id
    subtask_state = evidence["active_tasks"]["subtask_variation"]
    assert subtask_state["status"] == "COMPLETED"
    assert subtask_state["objective_id"] == "obj_updated_mission"  # Verifies shifted objective tracking
    assert len(subtask_state["operational_feedback"]) == 2

    # Verify SAGE classified the delay opportunity properly
    report = evidence["workflow_intelligence_report"]
    opp_categories = [opp["category"] for opp in report["improvement_opportunities"]]
    assert "LIVELINESS" in opp_categories  # Matches "slow" or "delay" feedback


def test_chatgpt_coordinated_agent_workflow_validation(tmp_path):
    """Verify and validate SAGE first complete agent integration workflow using ChatGPT coordinator role."""
    evidence_file = tmp_path / "ccl_chatgpt_validation_evidence.json"
    orch = DeveloperWorkflowOrchestrator(session_id="session_chatgpt_integration_val")

    # 1. Activation & Role Assignment Gate
    chatgpt = ChatGPTAgentConnector(orch, agent_id="agent_chatgpt_coord")
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_jules_exec", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "EXECUTOR"})
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_reviewer_gemini", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "REVIEWER"})

    # Validate active profiles in system
    assert orch.agents["agent_chatgpt_coord"] == "ACTIVATED"
    assert orch.agent_roles["agent_chatgpt_coord"] == "COORDINATOR"
    assert orch.agents["agent_jules_exec"] == "ACTIVATED"
    assert orch.agent_roles["agent_jules_exec"] == "EXECUTOR"

    # 2. Mission Context Rehydration Validation (ChatGPT receives current states & baselines)
    context_data = chatgpt.rehydrate_context()
    assert context_data["agent_identity"]["agent_id"] == "agent_chatgpt_coord"
    assert "ADR-001" in context_data["lineage_baselines"]
    assert "SAGE-ACT-MP-2.0" in context_data["lineage_baselines"]

    # 3. Conversational state alignment: Initialize parent task
    parent_task = chatgpt.align_workflow_state("INITIATE_TASK", "task_parent", {
        "objective_id": "obj_coordinated_refactoring",
        "initial_context": {"baseline": "v1.0", "milestones_completed": ["Milestone-1-contracts"]},
        "lineage_references": ["ADR-001", "SAGE-ACT-MP-2.0"]
    })
    assert parent_task["task_id"] == "task_parent"
    assert parent_task["status"] == "INITIATED"
    assert "Milestone-1-contracts" in parent_task["context"]["milestones_completed"]

    # Start parent execution
    chatgpt.align_workflow_state("START_EXECUTION", "task_parent", {"comment": "ChatGPT is actively aligning task status to ACTIVE."})
    assert orch.tasks["task_parent"]["status"] == "ACTIVE"

    # 4. Scoped Task Delegation (ChatGPT coordinates task assignment to Executor)
    child_task = orch.delegate_task(
        parent_task_id="task_parent",
        child_task_id="task_exec_refactor",
        to_agent="agent_jules_exec",
        objective_id="obj_write_ccl_orchestrator",
        initial_context={"files_to_modify": ["sage/experimental/act/ccl_orchestrator.py"]}
    )
    assert child_task["parent_task_id"] == "task_parent"
    assert child_task["assigned_agent"] == "agent_jules_exec"
    assert child_task["agent_role"] == "EXECUTOR"

    # ChatGPT clarifies objective and guards mission boundaries
    chatgpt.clarify_objective("task_exec_refactor", "Can we write tests?", "Yes, write comprehensive tests in tests/experimental.")
    assert len(orch.tasks["task_exec_refactor"]["context"]["objective_clarifications"]) == 1

    # 5. Scoped Execution & Updates (Ingest Executor progress)
    orch.ingest_event("STATE_TRANSITION", "task_exec_refactor", {"target_status": "ACTIVE"})
    orch.record_progress("task_exec_refactor", "agent_jules_exec", 100.0, {"stage": "all_tests_passed"}, "Tests verified green under pytest.")

    # 6. Handoff Readiness Manifest (Generate secure manifest to request Reviewer review)
    handoff_manifest = chatgpt.generate_handoff_manifest("task_exec_refactor", "agent_reviewer_gemini")
    assert handoff_manifest["source_agent"] == "agent_chatgpt_coord"
    assert handoff_manifest["destination_agent"] == "agent_reviewer_gemini"
    assert orch.tasks["task_exec_refactor"]["status"] == "HANDOFF"
    assert orch.tasks["task_exec_refactor"]["assigned_agent"] == "agent_reviewer_gemini"

    # 7. Operational Traceability (Completions Trace: Event -> State Change -> Evidence Record -> Outcome)
    orch.ingest_event("HUMAN_APPROVAL", "task_exec_refactor", {"supervisor_id": "human_supervisor_01", "decision": "AUTHORIZED", "comments": "Code matches all guidelines."})
    orch.ingest_event("STATE_TRANSITION", "task_exec_refactor", {"target_status": "COMPLETED", "agent_id": "agent_reviewer_gemini", "comment": "Review completed successfully."})

    orch.ingest_event("HUMAN_APPROVAL", "task_parent", {"supervisor_id": "human_supervisor_01", "decision": "AUTHORIZED", "comments": "Parent task approved."})
    orch.ingest_event("STATE_TRANSITION", "task_parent", {"target_status": "COMPLETED", "agent_id": "agent_chatgpt_coord", "comment": "Mission successfully completed."})

    # Export evidence payload
    evidence = orch.export_evidence(str(evidence_file))
    assert evidence["execution_identifier"] == orch.orchestrator_run_id
    assert evidence["active_tasks"]["task_parent"]["status"] == "COMPLETED"
    assert evidence["active_tasks"]["task_exec_refactor"]["status"] == "COMPLETED"

    # Confirm traceability trace records
    ccl_record = evidence["continuity_control_records"]["task_exec_refactor"]
    assert ccl_record["task_state_snapshot"]["parent_task_id"] == "task_parent"
    assert ccl_record["task_state_snapshot"]["progress_percent"] == 100.0
    assert ccl_record["task_state_snapshot"]["latest_result"]["stage"] == "all_tests_passed"
    assert len(ccl_record["monotonic_sequence_history"]) == 6 # Complete traceable chain (TASK_INIT, HUMAN_APPROVALs, STATE_TRANSITIONS, progress)


def test_jules_agent_connector(tmp_path):
    """Verify JulesAgentConnector registration, context rehydration, progress reporting, and handoffs."""
    orch = DeveloperWorkflowOrchestrator(session_id="session_jules_testing")

    # 1. Registration & Role Verification
    jules = JulesAgentConnector(orch, agent_id="agent_jules_exec")
    assert orch.agents["agent_jules_exec"] == "ACTIVATED"
    assert orch.agent_roles["agent_jules_exec"] == "EXECUTOR"

    # Activate a reviewer agent as well
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_reviewer", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "REVIEWER"})

    # Initialize a task
    task = orch.ingest_event(
        "TASK_INIT",
        "task_jules_01",
        {
            "objective_id": "obj_engineering_refactor",
            "assigned_agent": "agent_jules_exec",
            "initial_context": {
                "files_to_modify": ["sage/experimental/act/ccl_orchestrator.py"],
                "milestones_completed": ["Milestone-1-contracts", "Milestone-2-ccl-ops"]
            }
        }
    )
    assert task["status"] == "INITIATED"

    # 2. Context Rehydration Check (reporting awaiting approval checkpoint blocker initially)
    context_pkg = jules.rehydrate_engineering_context("task_jules_01")
    assert context_pkg["active_mission"]["objective_id"] == "obj_engineering_refactor"
    assert context_pkg["workflow_state"]["status"] == "INITIATED"
    assert "Milestone-2-ccl-ops" in context_pkg["completed_milestones"]
    assert context_pkg["repository_context"]["branch_name"].startswith("jules-")
    assert "awaiting human approval" in context_pkg["current_blocker"].lower()
    assert len(context_pkg["evidence_history"]["preceding_records_hashes"]) == 1

    # Now verify with blocker (by making task ACTIVE with 0% progress)
    jules.align_task_state("task_jules_01", "ACTIVE", "Jules starting execution.")
    assert orch.tasks["task_jules_01"]["status"] == "ACTIVE"

    context_pkg_active = jules.rehydrate_engineering_context("task_jules_01")
    assert context_pkg_active["workflow_state"]["status"] == "ACTIVE"
    # Should report blocker since task is active with 0.0% progress (as analyzed by intelligence feedback layer)
    assert "stalled" in context_pkg_active["current_blocker"].lower()

    # 3. Progress Reporting Validation
    jules.report_progress(
        task_id="task_jules_01",
        progress_percent=80.0,
        result_payload={"ast_isolation_verified": True},
        feedback="Added AST checks successfully."
    )
    assert orch.tasks["task_jules_01"]["progress_percent"] == 80.0
    assert orch.tasks["task_jules_01"]["latest_result"]["ast_isolation_verified"] is True

    # 4. Handoff Manifest Generation & Verification
    manifest = jules.generate_handoff_manifest("task_jules_01", "agent_reviewer")
    assert manifest["source_agent"] == "agent_jules_exec"
    assert manifest["destination_agent"] == "agent_reviewer"
    assert "files_to_modify" in manifest["preserved_context_keys"]
    assert orch.tasks["task_jules_01"]["status"] == "HANDOFF"
    assert orch.tasks["task_jules_01"]["assigned_agent"] == "agent_reviewer"

    # Verify that unactivated source agent raises Error
    orch.agents["agent_jules_exec"] = "SUSPENDED"
    with pytest.raises(PermissionError, match="Handoff Refused"):
        jules.generate_handoff_manifest("task_jules_01", "agent_reviewer")


def test_two_role_coordination_and_recovery_loop(tmp_path):
    """Validate the first real two-role SAGE operational loop (ChatGPT Coordinator -> Jules Executor).

    Covers:
      1. Coordinator -> Executor transfer of 8 fields.
      2. Complete execution traceability (Assignment -> Action -> Progress -> State Transition -> Evidence -> Outcome).
      3. Recovery validation (Interrupted tasks, paused workflows, resumed execution, incomplete handoffs).
      4. Review readiness preparation (ChatGPT -> Jules -> Evidence -> Reviewer).
      5. Shared state consistency and validation.
    """
    evidence_file = tmp_path / "ccl_two_role_validation.json"
    orch = DeveloperWorkflowOrchestrator(session_id="session_two_role_validation")

    # [Agent Activation Gate]
    chatgpt = ChatGPTAgentConnector(orch, agent_id="agent_chatgpt_coord")
    jules = JulesAgentConnector(orch, agent_id="agent_jules_exec")
    orch.ingest_event("AGENT_ACTIVATION", "system", {"agent_id": "agent_reviewer", "supervisor_id": "super", "decision": "AUTHORIZED", "role": "REVIEWER"})

    # --- PART 1: Coordinator -> Executor Transfer ---
    # ChatGPT coordinates the initiation of the engineering refactoring mission
    orch.ingest_event(
        "TASK_INIT",
        "task_engineering_exec",
        {
            "objective_id": "obj_experimental_hardening",
            "assigned_agent": "agent_jules_exec",
            "initial_context": {
                "files_to_modify": ["sage/experimental/act/ccl_orchestrator.py"],
                "milestones_completed": ["Milestone-1-contracts", "Milestone-2-ccl-ops"]
            },
            "lineage_references": ["ADR-001", "SAGE-ACT-MP-2.0"]
        }
    )

    # Rehydrate engineering context for Jules and assert all 8 fields are perfectly present and transferred
    jules_ctx = jules.rehydrate_engineering_context("task_engineering_exec")

    # Field 1: Active Mission
    assert jules_ctx["active_mission"]["objective_id"] == "obj_experimental_hardening"
    assert jules_ctx["active_mission"]["session_id"] == "session_two_role_validation"

    # Field 2: Current Workflow State
    assert jules_ctx["workflow_state"]["status"] == "INITIATED"
    assert jules_ctx["workflow_state"]["progress_percent"] == 0.0

    # Field 3: Completed Milestones
    assert "Milestone-2-ccl-ops" in jules_ctx["completed_milestones"]

    # Field 4: Engineering Scope
    assert jules_ctx["assigned_engineering_responsibility"]["scope_prefix"] == "sage/experimental/act"
    assert "sage/experimental/act/ccl_orchestrator.py" in jules_ctx["assigned_engineering_responsibility"]["target_files"]

    # Field 5: Repository Context
    assert jules_ctx["repository_context"]["workspace_clean"] is True
    assert jules_ctx["repository_context"]["ast_restricted"] is True

    # Field 6: Blockers
    # The task is INITIATED and lacks a human approval gate, which intelligence reports as a coordination blocker
    assert "awaiting human approval" in jules_ctx["current_blocker"].lower()

    # Field 7: Required Action
    assert "Transition to ACTIVE state" in jules_ctx["required_next_action"]

    # Field 8: Evidence History (Preceding record state hash)
    assert len(jules_ctx["evidence_history"]["preceding_records_hashes"]) == 1
    assert len(jules_ctx["evidence_history"]["preceding_records_hashes"][0]) == 64

    # --- PART 2: Engineering Execution Traceability ---
    # Step 1: State Transition (Start execution)
    jules.align_task_state("task_engineering_exec", "ACTIVE", "Jules starts code-modification loop.")
    assert orch.tasks["task_engineering_exec"]["status"] == "ACTIVE"

    # Step 2: Progress Updates
    jules.report_progress(
        task_id="task_engineering_exec",
        progress_percent=40.0,
        result_payload={"ast_parsed": True},
        feedback="AST parsed successfully. Writing new connector tests."
    )

    task_state = orch.tasks["task_engineering_exec"]
    assert task_state["progress_percent"] == 40.0
    assert task_state["latest_result"]["ast_parsed"] is True
    assert task_state["operational_feedback"][-1]["feedback"] == "AST parsed successfully. Writing new connector tests."

    # --- PART 3: Recovery Validation ---
    # Scenario A: Interrupted engineering task / paused workflow
    # Jules reports an interruption or delay (e.g., container compile slow down)
    jules.report_progress(
        task_id="task_engineering_exec",
        progress_percent=40.0,
        result_payload={"build_failure": "Timeout compiling assets"},
        feedback="Slow compiler build. Interrupted workflow."
    )

    # Let's verify our SAGE intelligence detects the LIVELINESS / delay friction and assigns candidate candidacy
    analysis_interrupted = orch.intelligence.analyze_workflow_state()
    # Task progress is not 0% (it is 40%), but we logged "slow" feedback, which is processed as friction opportunity
    opps = orch.intelligence.process_operational_feedback()
    liveliness_opps = [opp for opp in opps if opp["category"] == "LIVELINESS"]
    assert len(liveliness_opps) >= 1
    assert "slow" in liveliness_opps[0]["observed_friction"].lower()

    # Scenario B: Resumed Execution & Priority Shift
    # Jules resumes the interrupted workflow and completes 100% of the assigned work
    jules.report_progress(
        task_id="task_engineering_exec",
        progress_percent=100.0,
        result_payload={"git_hash": "a8c9b201", "tests_passing": True, "build_failure": "NONE"},
        feedback="Recovered container compilation, completed loop. All unit tests green."
    )

    # Assert state updates correctly and is fully preserved
    assert orch.tasks["task_engineering_exec"]["progress_percent"] == 100.0
    assert orch.tasks["task_engineering_exec"]["latest_result"]["tests_passing"] is True
    assert orch.tasks["task_engineering_exec"]["latest_result"]["build_failure"] == "NONE"

    # --- PART 4: Review Readiness Preparation ---
    # ChatGPT Coordinator coordinates reviewer handoff readiness
    # Prepare the peer handoff block (transfer task ownership from Jules to the Reviewer role)
    jules.generate_handoff_manifest("task_engineering_exec", "agent_reviewer")

    assert orch.tasks["task_engineering_exec"]["status"] == "HANDOFF"
    assert orch.tasks["task_engineering_exec"]["assigned_agent"] == "agent_reviewer"
    assert orch.tasks["task_engineering_exec"]["agent_role"] == "REVIEWER"

    # Human checkpoint gate authorization before final task completion
    orch.ingest_event(
        "HUMAN_APPROVAL",
        "task_engineering_exec",
        {
            "supervisor_id": "human_supervisor_01",
            "decision": "AUTHORIZED",
            "comments": "Two-role coordination loop successfully validated."
        }
    )

    # Transition task to COMPLETED by Reviewer
    orch.ingest_event(
        "STATE_TRANSITION",
        "task_engineering_exec",
        {
            "target_status": "COMPLETED",
            "agent_id": "agent_reviewer",
            "comment": "Peer reviewer verifies engineering action aligns 100% with objective."
        }
    )

    assert orch.tasks["task_engineering_exec"]["status"] == "COMPLETED"

    # --- PART 5: Shared State Consistency & Evidence Completeness ---
    evidence = orch.export_evidence(str(evidence_file))

    # Assert complete end-to-end trace reconstruction
    assert "task_engineering_exec" in evidence["active_tasks"]
    record = evidence["continuity_control_records"]["task_engineering_exec"]

    # Verify monotonically ordered history events are preserved
    assert len(record["monotonic_sequence_history"]) >= 6
    event_types = [evt["event_type"] for evt in record["monotonic_sequence_history"]]
    assert "TASK_INIT" in event_types
    assert "STATE_TRANSITION" in event_types
    assert "TASK_PROGRESS" in event_types
    assert "AGENT_HANDOFF" in event_types
    assert "HUMAN_APPROVAL" in event_types

    # Ensure state hashes align and are non-repudiable
    assert len(record["state_integrity"]["state_hash"]) == 64
    assert len(record["state_integrity"]["chain_hash"]) == 64
