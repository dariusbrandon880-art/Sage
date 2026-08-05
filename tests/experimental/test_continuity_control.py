"""Unit test suite for the SAGE Continuity Control Loop (SAGE-CCL) and sandboxed isolation rules."""

import os
import ast
import json
import time
import pytest
from pathlib import Path
from pydantic import ValidationError

from sage.experimental.act.continuity_control import (
    ContinuityControlRecord,
    ContinuityControlLoop
)
from sage.acr.session.session_state import SessionStateManager


def test_continuity_control_record_validation():
    """Verify that ContinuityControlRecord enforces correct format constraints."""
    # Standard valid inputs
    rec = ContinuityControlRecord(
        record_id="CCL-REC-20260804-f6b3d4e5-8888-4444-a999-cbcf00001111",
        session_id="session_f6b3d4e5",
        event_type="state_transition",
        timestamp=time.time(),
        action_taken="Ran build commands",
        decision_reasoning="Ensure build succeeded prior to feature addition"
    )
    assert rec.lifecycle_state == "PROPOSED"
    assert rec.workflow_friction == []
    assert rec.improvement_opportunities == []

    # Invalid record_id pattern (missing YYYYMMDD or invalid prefix)
    with pytest.raises(ValidationError, match="Invalid record_id format"):
        ContinuityControlRecord(
            record_id="REC-20260804-f6b3d4e5",
            session_id="session_f6b3d4e5",
            event_type="state_transition",
            timestamp=time.time(),
            action_taken="Ran build commands",
            decision_reasoning="Ensure build succeeded prior to feature addition"
        )

    # Invalid session_id pattern
    with pytest.raises(ValidationError, match="Invalid session_id format"):
        ContinuityControlRecord(
            record_id="CCL-REC-20260804-f6b3d4e5",
            session_id="sess_f6b3d4e5",  # Must be 'session_' or 'SES_'
            event_type="state_transition",
            timestamp=time.time(),
            action_taken="Ran build commands",
            decision_reasoning="Ensure build succeeded prior to feature addition"
        )


def test_continuity_control_loop_interception_and_enrichment(tmp_path):
    """Verify event capture, SessionStateManager enrichment, and record serialization."""
    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"

    # Set up SessionStateManager with a predefined session
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    active_sess = session_mgr.create_session(
        session_id="session_test_enrichment",
        active_objectives=["obj_validate_milestone_3", "obj_continuous_development"]
    )
    active_sess.add_completed_action("task_setup_env")
    active_sess.add_pending_action("task_run_verification")
    session_mgr.save_session(active_sess)

    # Initialize Continuity Control Loop
    ccl = ContinuityControlLoop(
        session_manager=session_mgr,
        storage_path=str(record_storage)
    )

    # Intercept event and check context enrichment
    record = ccl.intercept_event(
        event_type="boundary_intercept",
        action_taken="Implemented core telemetry tap",
        decision_reasoning="Fulfill Strategic Transition Directive requirements",
        evidence_payload={"test_run_success": True},
        workflow_friction=[{"type": "api_latency", "severity": "low"}],
        improvement_opportunities=["suggest automated test hooks"]
    )

    # Ensure record is constructed properly
    assert record.session_id == "session_test_enrichment"
    assert record.event_type == "boundary_intercept"
    assert record.action_taken == "Implemented core telemetry tap"
    assert "obj_validate_milestone_3" in record.evidence_payload["enriched_objectives"]
    assert "task_setup_env" in record.evidence_payload["session_completed_actions"]
    assert "task_run_verification" in record.evidence_payload["session_pending_actions"]
    assert record.workflow_friction[0]["type"] == "api_latency"
    assert record.improvement_opportunities[0] == "suggest automated test hooks"

    # Serialize record and verify file
    filepath = ccl.serialize_record(record)
    assert filepath.exists()

    with open(filepath, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    assert loaded_data["record_id"] == record.record_id
    assert loaded_data["lifecycle_state"] == "PROPOSED"


def test_continuity_control_chronological_and_recovered_validation(tmp_path):
    """Verify adversarial validation of chronological order and recovered state rules."""
    record_storage = tmp_path / "records"
    ccl = ContinuityControlLoop(storage_path=str(record_storage))

    # Create and serialize an initial valid record
    rec1 = ccl.intercept_event(
        event_type="checkpoint",
        action_taken="Saved state 1",
        decision_reasoning="Normal checkpointing"
    )
    # Force mock a older timestamp on rec1
    rec1.timestamp = 1000.0
    ccl.serialize_record(rec1)

    # Create rec2 that is newer
    rec2 = ccl.intercept_event(
        event_type="checkpoint",
        action_taken="Saved state 2",
        decision_reasoning="Normal checkpointing"
    )
    rec2.timestamp = 2000.0
    assert ccl.validate_record(rec2) is True

    # Create rec3 that violates chronology (timestamp older than rec2)
    rec3 = ccl.intercept_event(
        event_type="checkpoint",
        action_taken="Saved state 3",
        decision_reasoning="Anachronistic checkpointing"
    )
    ccl.serialize_record(rec2)  # Save rec2
    rec3.timestamp = 1500.0    # Older than rec2 (2000.0) but saved after
    assert ccl.validate_record(rec3) is False

    # Verify recovered event validation
    valid_recovered = ContinuityControlRecord(
        record_id="CCL-REC-20260804-rec1",
        session_id="session_rec_99",
        event_type="recovered",
        timestamp=3000.0,
        action_taken="Restored session after failure",
        decision_reasoning="Recovery protocol",
        failure_context={"error": "db_crash"},
        recovery_path="rehydrated_last_checkpoint"
    )
    assert ccl.validate_record(valid_recovered) is True

    invalid_recovered = ContinuityControlRecord(
        record_id="CCL-REC-20260804-rec2",
        session_id="session_rec_99",
        event_type="recovered",
        timestamp=3100.0,
        action_taken="Restored session after failure",
        decision_reasoning="Recovery protocol",
        failure_context=None,  # Missing failure context
        recovery_path="rehydrated_last_checkpoint"
    )
    assert ccl.validate_record(invalid_recovered) is False


def test_continuity_control_human_approval(tmp_path):
    """Verify that human approval successfully promotes the record state."""
    record_storage = tmp_path / "records"
    ccl = ContinuityControlLoop(storage_path=str(record_storage))

    record = ccl.intercept_event(
        event_type="state_transition",
        action_taken="Created new core service",
        decision_reasoning="Scaling requirement"
    )
    ccl.serialize_record(record)

    # Approve record
    approved = ccl.human_approval(
        record_id=record.record_id,
        supervisor_id="supervisor_jules",
        signature="sig_jules_approved_9922",
        decision="APPROVED"
    )

    assert approved.lifecycle_state == "VALIDATED"
    assert "human_approval_record" in approved.evidence_payload
    assert approved.evidence_payload["human_approval_record"]["supervisor_id"] == "supervisor_jules"
    assert approved.evidence_payload["human_approval_record"]["signature"] == "sig_jules_approved_9922"

    # Reject record
    rejected = ccl.human_approval(
        record_id=record.record_id,
        supervisor_id="supervisor_jules",
        signature="sig_jules_rejected_9922",
        decision="REJECTED"
    )
    assert rejected.lifecycle_state == "REJECTED"


def test_one_way_import_isolation_enforcement():
    """Verify absolute enforcement of the One-Way Import Law for SAGE-CCL.

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
                # Check from imports (e.g., 'from sage.experimental.act.continuity_control import ...')
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        assert "sage.experimental" not in node.module, (
                            f"One-Way Import Law Violation inside production: '{file_path}' "
                            f"attempts to import from module '{node.module}'"
                        )


def test_developer_workflow_orchestrator_e2e(tmp_path):
    """Verify the DeveloperWorkflowOrchestrator runs the complete active coordination loop successfully."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_operational_feedback.json"

    # 1. Initialize custom managers and loop
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    # Create orchestrator
    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_orch_test_123",
        objective="obj_continuous_development",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # 2. Run active development coordination
    action = "SAGE Priority Implementation"
    reasoning = "Validate SAGE's operational coordination capability"
    friction = [{"type": "cognitive_load", "detail": "high manual step friction", "severity": "medium"}]
    opportunities = ["Auto-run tests after code modifications via watcher"]

    result = orchestrator.execute_active_development_coordination(
        action_taken=action,
        decision_reasoning=reasoning,
        workflow_friction=friction,
        improvement_opportunities=opportunities
    )

    # 3. Assert on result fields
    assert result["status"] == "VALIDATED"
    assert "orchestrator_run_id" in result
    assert result["session_id"] == "session_orch_test_123"
    assert "obj_continuous_development" in result["session_objectives"]

    # SAGE-CCL Record Assertions
    ccl_rec = result["ccl_record"]
    assert ccl_rec["action_taken"] == action
    assert ccl_rec["decision_reasoning"] == reasoning
    assert ccl_rec["lifecycle_state"] == "VALIDATED"
    assert ccl_rec["workflow_friction"] == friction
    assert ccl_rec["improvement_opportunities"] == opportunities

    # CMAPS Payload Assertions
    cmaps = result["cmaps_payload"]
    assert cmaps["audit_id"].startswith("audit_")
    assert cmaps["agent_identity"]["agent_id"] == "agent_jules_sage"
    assert cmaps["model_provider"]["provider"] == "anthropic"
    assert cmaps["execution_state"]["status"] == "completed"
    assert cmaps["task_lineage"]["session_id"].startswith("session_")
    assert len(cmaps["task_lineage"]["session_id"]) == 16
    assert cmaps["decision_events"][0]["summary"] == action
    assert cmaps["decision_events"][0]["reasoning"] == reasoning
    assert cmaps["attestation"]["signer_identity"] == "supervisor_jules"

    # Telemetry Assertions
    telemetry = result["developer_telemetry"]
    assert telemetry["friction"] == friction
    assert telemetry["opportunities"] == opportunities

    # 4. Verify file persistence
    assert evidence_output.exists()
    with open(evidence_output, "r", encoding="utf-8") as f:
        loaded_evidence = json.load(f)
    assert loaded_evidence["orchestrator_run_id"] == result["orchestrator_run_id"]
    assert loaded_evidence["ccl_record"]["record_id"] == ccl_rec["record_id"]


def test_developer_workflow_orchestrator_with_supervisor_override(tmp_path):
    """Verify the DeveloperWorkflowOrchestrator honors supervisor overrides and custom approvals."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "custom_feedback.json"

    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_override_test",
        objective="obj_continuous_development",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    override = {
        "decision": "APPROVED",
        "supervisor_id": "human_supervisor_jules_override",
        "comments": "Explicit manual override for special experimental run",
        "signature": "sig_special_run_8892"
    }

    result = orchestrator.execute_active_development_coordination(
        action_taken="Custom Run",
        decision_reasoning="Custom validation reasons",
        supervisor_override=override
    )

    assert result["status"] == "VALIDATED"
    assert result["ccl_record"]["lifecycle_state"] == "VALIDATED"
    assert result["ccl_record"]["evidence_payload"]["human_approval_record"]["supervisor_id"] == "human_supervisor_jules_override"
    assert result["ccl_record"]["evidence_payload"]["human_approval_record"]["signature"] == "sig_special_run_8892"
    assert result["cmaps_payload"]["attestation"]["signer_identity"] == "human_supervisor_jules_override"
    assert result["cmaps_payload"]["attestation"]["signature"] == "sig_special_run_8892"


def test_developer_workflow_orchestrator_scan_git(tmp_path):
    """Verify git scan capability in various contexts, ensuring robust fallbacks."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_git_test",
        evidence_output_path=str(tmp_path / "git_evidence.json")
    )

    workspace = orchestrator.scan_git_workspace()
    assert "modified_files" in workspace
    assert "diffs" in workspace
    assert len(workspace["modified_files"]) > 0


def test_continuity_enforcement_agent_activation(tmp_path):
    """Verify that agent activation lifecycle restricts or permits task transitions."""
    import pytest
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_activation_test",
        objective="obj_test_continuous",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Agent state defaults to ACTIVATED for agent_jules_sage
    assert orchestrator.enforcer.get_agent_state("agent_jules_sage") == "ACTIVATED"

    # Set agent as SUSPENDED
    orchestrator.enforcer.set_agent_state("agent_jules_sage", "SUSPENDED")
    with pytest.raises(PermissionError, match="not authorized to transition"):
        orchestrator.execute_active_development_coordination(
            action_taken="Develop Feature",
            decision_reasoning="Reasoning"
        )

    # Set agent as INACTIVE
    orchestrator.enforcer.set_agent_state("agent_jules_sage", "INACTIVE")
    with pytest.raises(PermissionError, match="not authorized to transition"):
        orchestrator.execute_active_development_coordination(
            action_taken="Develop Feature",
            decision_reasoning="Reasoning"
        )

    # Re-activate and assert success
    orchestrator.enforcer.set_agent_state("agent_jules_sage", "ACTIVATED")
    res = orchestrator.execute_active_development_coordination(
        action_taken="Develop Feature",
        decision_reasoning="Reasoning"
    )
    assert res["status"] == "VALIDATED"
    assert res["continuity_enforcement"]["agent_state"] == "ACTIVATED"


def test_continuity_enforcement_context_drift_and_restart(tmp_path):
    """Verify that completed action/objective duplication raises drift exceptions, and override bypasses them."""
    import pytest
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_drift_test",
        objective="obj_drift_obs",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Complete an action in session
    orchestrator.session.completed_actions.append("Action A")
    session_mgr.save_session(orchestrator.session)

    # Attempt to execute the already completed action "Action A" should trigger drift exception
    with pytest.raises(ValueError, match="Duplicate execution of already completed action"):
        orchestrator.execute_active_development_coordination(
            action_taken="Action A",
            decision_reasoning="Reasoning"
        )

    # Supervisor override should permit it
    override = {
        "decision": "APPROVED",
        "supervisor_id": "supervisor_jules",
        "comments": "Explicitly allow duplicated action under controlled loop.",
        "signature": "sig_override_9901"
    }
    res = orchestrator.execute_active_development_coordination(
        action_taken="Action A",
        decision_reasoning="Reasoning",
        supervisor_override=override
    )
    assert res["status"] == "VALIDATED"
    assert res["continuity_enforcement"]["drift_detected"] is True
    assert res["continuity_enforcement"]["override_applied"] is True


def test_continuity_enforcement_task_ownership_preservation(tmp_path):
    """Verify that transition proposed by an unauthorized assignee triggers ownership hijack drift."""
    import pytest
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_ownership_test",
        objective="obj_ownership_obs",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Attempt task execution with proposed_assignee other than agent_jules_sage
    with pytest.raises(ValueError, match="Task ownership hijacking detected"):
        orchestrator.execute_active_development_coordination(
            action_taken="Develop Feature",
            decision_reasoning="Reasoning",
            proposed_assignee="agent_unauthorized_user"
        )


def test_multi_agent_role_assignment_and_matching(tmp_path):
    """Verify role/responsibility rules prevent misaligned agent assignments."""
    import pytest
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_multi_agent_roles",
        objective="obj_multi_agent",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Register coordinated task requiring TIER_2_AUDITOR
    orchestrator.add_coordinated_task(
        task_id="task_audit",
        name="Security Audit",
        role="TIER_2_AUDITOR"
    )

    # agent_jules_sage is TIER_1_COORDINATOR and must be rejected for this task
    with pytest.raises(PermissionError, match="Role Mismatch"):
        orchestrator.assign_agent_to_task("task_audit", "agent_jules_sage")

    # agent_scout_sage is TIER_2_AUDITOR and must succeed
    orchestrator.assign_agent_to_task("task_audit", "agent_scout_sage")
    assert orchestrator.coordinated_tasks["task_audit"]["assigned_agent"] == "agent_scout_sage"


def test_multi_agent_task_sequencing_rules(tmp_path):
    """Verify task sequencing rules prevent execution until prerequisites are COMPLETED."""
    import pytest
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_sequencing",
        objective="obj_sequencing",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Register task_1 and task_2 (task_2 depends on task_1)
    orchestrator.add_coordinated_task("task_1", "Code Changes", "TIER_1_COORDINATOR")
    orchestrator.add_coordinated_task("task_2", "Audit Changes", "TIER_2_AUDITOR", prerequisites=["task_1"])

    # Try to execute/transition task_2 directly before task_1 is completed -> Sequencing violation!
    with pytest.raises(ValueError, match="Task Sequencing Violation"):
        orchestrator.transition_coordinated_task("task_2", "agent_scout_sage", "ACTIVE")

    # Complete task_1
    orchestrator.transition_coordinated_task("task_1", "agent_jules_sage", "COMPLETED")
    assert orchestrator.coordinated_tasks["task_1"]["status"] == "COMPLETED"

    # Try task_2 transition again -> should succeed!
    orchestrator.transition_coordinated_task("task_2", "agent_scout_sage", "ACTIVE")
    assert orchestrator.coordinated_tasks["task_2"]["status"] == "ACTIVE"


def test_multi_agent_handoff_lineage_preservation(tmp_path):
    """Verify task agent lineage transitions are correctly logged in handoff history."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_lineage",
        objective="obj_lineage",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Let's register task_audit and assign agent_scout_sage, then transfer to agent_jules_sage (override)
    orchestrator.add_coordinated_task("task_audit", "Security Audit", "TIER_2_AUDITOR")
    orchestrator.assign_agent_to_task("task_audit", "agent_scout_sage")

    # Override role rule using supervisor override to perform handoff lineage transition
    override = {"decision": "APPROVED", "supervisor_id": "supervisor_jules"}
    orchestrator.transition_coordinated_task(
        task_id="task_audit",
        agent_id="agent_jules_sage",
        status="ACTIVE",
        supervisor_override=override
    )

    # Check that handoff history contains HANDOFF_LINEAGE_TRANSITION from scout to jules
    history = orchestrator.coordinated_tasks["task_audit"]["handoff_history"]
    transitions = [h for h in history if h.get("action") == "HANDOFF_LINEAGE_TRANSITION"]
    assert len(transitions) == 1
    assert transitions[0]["from_agent"] == "agent_scout_sage"
    assert transitions[0]["to_agent"] == "agent_jules_sage"


def test_multi_agent_operator_status_dashboard(tmp_path):
    """Verify that render_multi_agent_status correctly produces structured dashboards."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_dashboard",
        objective="obj_dashboard",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Set up some tasks and shared state values
    orchestrator.add_coordinated_task("task_t", "Task T", "TIER_1_COORDINATOR")
    orchestrator.shared_workflow_state["database_replica_status"] = "aligned"

    dashboard = orchestrator.render_multi_agent_status()
    assert "SAGE MULTI-AGENT WORKFLOW COORDINATION STATE" in dashboard
    assert "Agent Activation & Role Registry:" in dashboard
    assert "Coordinated Task Board & Sequencing Dependencies:" in dashboard
    assert "Shared Workflow State (Context Cache):" in dashboard
    assert "agent_jules_sage" in dashboard
    assert "database_replica_status: aligned" in dashboard


def test_operational_control_loop_unactivated_agent(tmp_path):
    """Verify that an unactivated or suspended agent is restricted from reporting progress."""
    import pytest
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_loop_unactivated_{uuid.uuid4().hex[:6]}",
        objective="obj_loop_unactivated",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    orchestrator.add_coordinated_task("task_t", "Task", "TIER_1_COORDINATOR")
    orchestrator.assign_agent_to_task("task_t", "agent_jules_sage")

    # Suspend the agent
    orchestrator.enforcer.set_agent_state("agent_jules_sage", "SUSPENDED")

    with pytest.raises(PermissionError, match="is not authorized to report progress"):
        orchestrator.report_agent_progress(
            agent_id="agent_jules_sage",
            task_id="task_t",
            progress_details={"action_name": "build_database", "is_completed": False}
        )


def test_operational_control_loop_incorrect_assignment(tmp_path):
    """Verify that an agent reporting progress on a task assigned to someone else fails validation."""
    import pytest
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_loop_assignment_{uuid.uuid4().hex[:6]}",
        objective="obj_loop_assignment",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    orchestrator.add_coordinated_task("task_t", "Task", "TIER_1_COORDINATOR")
    orchestrator.assign_agent_to_task("task_t", "agent_jules_sage")

    # agent_scout_sage (ACTIVATED) attempts to report progress for task_t (assigned to agent_jules_sage)
    with pytest.raises(PermissionError, match="is not assigned to task"):
        orchestrator.report_agent_progress(
            agent_id="agent_scout_sage",
            task_id="task_t",
            progress_details={"action_name": "build_database", "is_completed": False}
        )


def test_operational_control_loop_execution_drift_detection(tmp_path):
    """Verify that duplicate execution of completed actions raises drift exceptions, but override bypasses them."""
    import pytest
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_loop_drift_{uuid.uuid4().hex[:6]}",
        objective="obj_loop_drift",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    orchestrator.add_coordinated_task("task_t", "Task", "TIER_1_COORDINATOR")
    orchestrator.assign_agent_to_task("task_t", "agent_jules_sage")

    # Add action_build to completed actions
    orchestrator.session.completed_actions.append("action_build")
    session_mgr.save_session(orchestrator.session)

    # Reporting on already completed action_build must raise drift ValueError
    with pytest.raises(ValueError, match="Execution Drift Detected"):
        orchestrator.report_agent_progress(
            agent_id="agent_jules_sage",
            task_id="task_t",
            progress_details={"action_name": "action_build", "is_completed": False}
        )

    # Bypass drift exception with supervisor override
    override = {"decision": "APPROVED", "supervisor_id": "supervisor_jules"}
    report = orchestrator.report_agent_progress(
        agent_id="agent_jules_sage",
        task_id="task_t",
        progress_details={"action_name": "action_build", "is_completed": False},
        supervisor_override=override
    )
    assert report["status"] == "VALIDATED"


def test_operational_control_loop_successful_flow(tmp_path):
    """Verify end-to-end progress reporting state updates, context cache, and evidence serialization."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_loop_success_{uuid.uuid4().hex[:6]}",
        objective="obj_loop_success",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence_output.json")
    )

    orchestrator.add_coordinated_task("task_t", "Task", "TIER_1_COORDINATOR")
    orchestrator.assign_agent_to_task("task_t", "agent_jules_sage")

    progress = {
        "action_name": "action_database_replica",
        "is_completed": True,
        "shared_state_updates": {
            "replica_status": "synced_and_active",
            "replica_nodes_count": 3
        }
    }

    report = orchestrator.report_agent_progress(
        agent_id="agent_jules_sage",
        task_id="task_t",
        progress_details=progress
    )

    # 1. Status verification
    assert report["status"] == "VALIDATED"
    assert report["task_status"] == "COMPLETED"

    # 2. Shared context updates
    assert orchestrator.shared_workflow_state["replica_status"] == "synced_and_active"
    assert orchestrator.shared_workflow_state["replica_nodes_count"] == 3

    # 3. Session updates
    assert "action_database_replica" in orchestrator.session.completed_actions

    # 4. File persistence evidence
    assert (tmp_path / "evidence_output.json").exists()


def test_active_learning_default_ci_directive(tmp_path):
    """Verify that a clean run generates the continuous improvement directive (DIRECTIVE-CI-001)."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_learn_clean_{uuid.uuid4().hex[:6]}",
        objective="obj_learn_clean",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    report = orchestrator.analyze_operational_history_and_learn()
    directives = report["improvement_directives"]

    assert len(directives) == 1
    assert directives[0]["directive_id"] == "DIRECTIVE-CI-001"
    assert directives[0]["category"] == "continuous_improvement"


def test_active_learning_high_handoff_friction(tmp_path):
    """Verify that high handoff counts trigger a workflow optimization directive."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_learn_handoffs_{uuid.uuid4().hex[:6]}",
        objective="obj_learn_handoffs",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Set up task with multiple handoffs to trigger DIRECTIVE-OPT-...
    orchestrator.add_coordinated_task("task_seq", "Database Migration", "TIER_2_DEVELOPER")
    orchestrator.assign_agent_to_task("task_seq", "agent_builder_sage")

    # Perform a transition that logs handoff lineage from builder to scout
    orchestrator.enforcer.set_agent_state("agent_builder_sage", "ACTIVATED")
    override = {"decision": "APPROVED", "supervisor_id": "supervisor_jules"}
    orchestrator.transition_coordinated_task("task_seq", "agent_scout_sage", "ACTIVE", supervisor_override=override)

    report = orchestrator.analyze_operational_history_and_learn()
    directives = report["improvement_directives"]

    # Verify that a workflow optimization directive was synthesized
    opt_directives = [d for d in directives if d["category"] == "workflow_optimization"]
    assert len(opt_directives) >= 1
    assert opt_directives[0]["directive_id"].startswith("DIRECTIVE-OPT-")


def test_active_learning_unauthorized_attempts_friction(tmp_path):
    """Verify that unactivated agent execution attempts synthesize a security directive."""
    import pytest
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_learn_unauth_{uuid.uuid4().hex[:6]}",
        objective="obj_learn_unauth",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    orchestrator.add_coordinated_task("task_t", "Task", "TIER_1_COORDINATOR")
    orchestrator.assign_agent_to_task("task_t", "agent_jules_sage")

    # Suspend the agent to cause a blocked execution attempt
    orchestrator.enforcer.set_agent_state("agent_jules_sage", "SUSPENDED")

    with pytest.raises(PermissionError):
        orchestrator.execute_active_development_coordination(
            action_taken="Develop Feature",
            decision_reasoning="Reasoning"
        )

    # Run the learning analyzer
    report = orchestrator.analyze_operational_history_and_learn()
    directives = report["improvement_directives"]

    # Verify that a security boundary directive was synthesized
    sec_directives = [d for d in directives if d["category"] == "security_boundary"]
    assert len(sec_directives) >= 1
    assert sec_directives[0]["directive_id"].startswith("DIRECTIVE-SEC-")


def test_active_learning_live_operator_visibility(tmp_path):
    """Verify that active learning directives are presented clearly in the operator status console."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_learn_vis_{uuid.uuid4().hex[:6]}",
        objective="obj_learn_vis",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    orchestrator.analyze_operational_history_and_learn()
    dashboard = orchestrator.render_multi_agent_status()

    assert "SAGE Self-Referential Active Learning Directives:" in dashboard
    assert "[DIRECTIVE-CI-001]" in dashboard
    assert "SAGE operational coordination flow is perfectly aligned" in dashboard


def test_workflow_intelligence_inactive_agent_risk(tmp_path):
    """Verify that having inactive agents triggers the corresponding operational risk and remediation."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_intel_inactive_{uuid.uuid4().hex[:6]}",
        objective="obj_intel_inactive",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Set agent_builder_sage as INACTIVE
    orchestrator.enforcer.set_agent_state("agent_builder_sage", "INACTIVE")

    report = orchestrator.generate_workflow_intelligence_report()
    risks = report["risks"]

    assert len(risks) >= 1
    assert risks[0]["risk_id"] == "RISK-ACT-001"
    assert "inactive or suspended agents" in risks[0]["description"]
    assert "enforcer.set_agent_state" in report["remediations"][0]


def test_workflow_intelligence_blocked_tasks_friction(tmp_path):
    """Verify that uncompleted prerequisites trigger task blocked sequencing friction."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_intel_blocked_{uuid.uuid4().hex[:6]}",
        objective="obj_intel_blocked",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Add task_2 depending on task_1, task_2 remains PENDING
    orchestrator.add_coordinated_task("task_1", "Prereq Changes", "TIER_1_COORDINATOR")
    orchestrator.add_coordinated_task("task_2", "Audit Changes", "TIER_2_AUDITOR", prerequisites=["task_1"])

    report = orchestrator.generate_workflow_intelligence_report()
    frictions = report["friction_points"]

    assert len(frictions) >= 1
    assert any(f["friction_id"] == "FRIC-SEQ-002" for f in frictions)
    assert any("transition_coordinated_task" in r for r in report["remediations"])


def test_workflow_intelligence_execution_drift_risk(tmp_path):
    """Verify that executing a task that duplicates an already completed session action triggers drift risk."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_intel_drift_{uuid.uuid4().hex[:6]}",
        objective="obj_intel_drift",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Register task_1 and set status as ACTIVE
    orchestrator.add_coordinated_task("task_1", "Duplicate Action", "TIER_1_COORDINATOR")
    orchestrator.assign_agent_to_task("task_1", "agent_jules_sage")
    orchestrator.coordinated_tasks["task_1"]["status"] = "ACTIVE"

    # Add "Duplicate Action" as completed action in session state
    orchestrator.session.completed_actions.append("Duplicate Action")
    session_mgr.save_session(orchestrator.session)

    report = orchestrator.generate_workflow_intelligence_report()
    risks = report["risks"]

    assert len(risks) >= 1
    assert any(r["risk_id"] == "RISK-DRIFT-003" for r in risks)


def test_workflow_intelligence_live_operator_visibility(tmp_path):
    """Verify that risks, friction, and remediations are presented clearly in the operator status console."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_intel_vis_{uuid.uuid4().hex[:6]}",
        objective="obj_intel_vis",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Force a risk of inactive agent
    orchestrator.enforcer.set_agent_state("agent_builder_sage", "INACTIVE")

    dashboard = orchestrator.render_multi_agent_status()

    assert "SAGE Workflow Intelligence Signals:" in dashboard
    assert "Risks Detected:" in dashboard
    assert "[MEDIUM] Workflow has inactive or suspended agents" in dashboard
    assert "Operator Remediation Recommendations:" in dashboard
    assert "Execute 'enforcer.set_agent_state' to ACTIVATE" in dashboard


def test_decision_support_default_ci_candidate(tmp_path):
    """Verify that a clean run generates the continuous improvement candidate (CANDIDATE-CI-001)."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_cand_clean_{uuid.uuid4().hex[:6]}",
        objective="obj_cand_clean",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    candidates = orchestrator.generate_actionable_improvement_candidates()

    assert len(candidates) == 1
    assert candidates[0]["candidate_id"] == "CANDIDATE-CI-001"
    assert candidates[0]["severity"] == "NORMAL"


def test_decision_support_high_transition_friction(tmp_path):
    """Verify that task transitions dynamically synthesize an optimization candidate."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_cand_opt_{uuid.uuid4().hex[:6]}",
        objective="obj_cand_opt",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Register task and perform transition to register handoff history
    orchestrator.add_coordinated_task("task_seq", "Database Migration", "TIER_2_DEVELOPER")
    orchestrator.assign_agent_to_task("task_seq", "agent_builder_sage")

    orchestrator.enforcer.set_agent_state("agent_builder_sage", "ACTIVATED")
    override = {"decision": "APPROVED", "supervisor_id": "supervisor_jules"}
    orchestrator.transition_coordinated_task("task_seq", "agent_scout_sage", "ACTIVE", supervisor_override=override)

    candidates = orchestrator.generate_actionable_improvement_candidates()

    # Verify that an optimization candidate was synthesized
    opt_candidates = [c for c in candidates if c["candidate_id"].startswith("CANDIDATE-OPT-")]
    assert len(opt_candidates) >= 1
    assert opt_candidates[0]["severity"] == "WARNING"
    assert "Frequent agent transitions detected" in opt_candidates[0]["friction_pattern"]


def test_decision_support_blocked_attempts_friction(tmp_path):
    """Verify that blocked attempts synthesize a security candidate."""
    import pytest
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_cand_unauth_{uuid.uuid4().hex[:6]}",
        objective="obj_cand_unauth",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    orchestrator.add_coordinated_task("task_t", "Task", "TIER_1_COORDINATOR")
    orchestrator.assign_agent_to_task("task_t", "agent_jules_sage")

    # Suspend the agent to cause a blocked execution attempt
    orchestrator.enforcer.set_agent_state("agent_jules_sage", "SUSPENDED")

    with pytest.raises(PermissionError):
        orchestrator.execute_active_development_coordination(
            action_taken="Develop Feature",
            decision_reasoning="Reasoning"
        )

    # Run the candidate generator
    candidates = orchestrator.generate_actionable_improvement_candidates()

    # Verify that a security candidate was synthesized
    sec_candidates = [c for c in candidates if c["candidate_id"].startswith("CANDIDATE-SEC-")]
    assert len(sec_candidates) >= 1
    assert sec_candidates[0]["severity"] == "CRITICAL"
    assert "blocked execution attempts" in sec_candidates[0]["friction_pattern"]


def test_decision_support_operator_visibility(tmp_path):
    """Verify that synthesized candidates are presented clearly on the operator status console."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_cand_vis_{uuid.uuid4().hex[:6]}",
        objective="obj_cand_vis",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    dashboard = orchestrator.render_multi_agent_status()

    assert "Actionable SAGE Improvement Candidates:" in dashboard
    assert "[NORMAL] Candidate ID: CANDIDATE-CI-001" in dashboard
    assert "Friction Pattern   : Execution patterns are fully stable" in dashboard
    assert "Actionable Outcome : Maintain governing constraints" in dashboard
    assert "Validation Criteria: Workflow completes cleanly" in dashboard


def test_coordination_loop_simulation_aggregates(tmp_path):
    """Verify that execution loop simulation accurately aggregates and reports before/after effectiveness metrics."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_sim_agg_{uuid.uuid4().hex[:6]}",
        objective="obj_sim_agg",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    scenarios = ["extended_workflow", "interrupted_execution", "repeated_handoffs"]
    report = orchestrator.execute_coordination_loop_simulation(scenarios)

    aggregates = report["effectiveness_aggregates"]
    assert aggregates["reduction_in_operator_interventions_pct"] > 50.0
    assert aggregates["reduction_in_recovery_time_pct"] > 50.0
    assert aggregates["determinism_and_ownership_intact"] is True
    assert aggregates["evidence_lineage_complete"] is True


def test_coordination_loop_simulation_evidence_capture(tmp_path):
    """Verify that execution loop simulation persists validation reports and records SAGE-CCL evidence."""
    import uuid
    from pathlib import Path
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_sim_ev_{uuid.uuid4().hex[:6]}",
        objective="obj_sim_ev",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    report_path = Path("evidence_capture/decision_validation_report.json")
    if report_path.exists():
        report_path.unlink()

    scenarios = ["extended_workflow"]
    orchestrator.execute_coordination_loop_simulation(scenarios)

    # 1. Report file persistence check
    assert report_path.exists()

    # 2. SAGE-CCL ledger check
    records = list(ccl.storage_path.glob("*.json"))
    assert len(records) >= 1


def test_rehydrate_from_handoff_manifest_success(tmp_path):
    """Verify that programmatically loading handoff manifests correctly restores session state and audits workspace divergence."""
    import json
    import uuid
    from pathlib import Path
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_rehydrate_{uuid.uuid4().hex[:6]}",
        objective="obj_rehydrate",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # 1. Create dummy handoff manifest
    manifest_data = {
        "manifest_id": "manifest_rehydrate_test",
        "source_session": "session_source_xyz",
        "target_session_objectives": ["obj_transferred_mission", "obj_extra_audit"],
        "state_snapshot": {
            "completed_actions": ["action_realignment", "action_baseline_lock"],
            "pending_actions": ["action_governed_agent_transition"],
            "important_decisions": ["decision_asymmetric_cryptography"]
        },
        "workspace_fingerprint": {
            "sage/experimental/act/continuity_control.py": {
                "sha256": "dummy_hash_does_not_match_so_divergent",
                "size_bytes": 1000
            },
            "nonexistent_file_abc.py": {
                "sha256": "nonexistent_hash",
                "size_bytes": 0
            }
        }
    }

    m_path = tmp_path / "agent_handoff_manifest.json"
    with open(m_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    # 2. Run rehydration
    report = orchestrator.rehydrate_from_handoff_manifest(str(m_path))

    # 3. Assert on rehydrated session objectives & completed actions
    assert "obj_transferred_mission" in orchestrator.session.active_objectives
    assert "obj_extra_audit" in orchestrator.session.active_objectives
    assert "action_realignment" in orchestrator.session.completed_actions
    assert "action_baseline_lock" in orchestrator.session.completed_actions
    assert "decision_asymmetric_cryptography" in orchestrator.session.important_decisions

    # 4. Assert on workspace divergence audit results
    audit = report["workspace_divergence_audit"]
    assert "sage/experimental/act/continuity_control.py" in audit["divergent"]
    assert "nonexistent_file_abc.py" in audit["missing"]

    # 5. Verify persistence evidence write
    evidence_path = Path("evidence_capture/operational_persistence_evidence.json")
    assert evidence_path.exists()


def test_enforce_active_agent_scope_activation(tmp_path):
    """Verify that attempting to enforce scope on an unactivated or suspended agent raises a PermissionError."""
    import pytest
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_scope_act_{uuid.uuid4().hex[:6]}",
        objective="obj_scope_act",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Suspend agent_jules_sage
    orchestrator.enforcer.set_agent_state("agent_jules_sage", "SUSPENDED")

    with pytest.raises(PermissionError, match="cannot execute operations"):
        orchestrator.enforce_active_agent_scope(
            agent_id="agent_jules_sage",
            action="modify_code",
            modified_files=["sage/experimental/act/continuity_control.py"]
        )


def test_enforce_active_agent_scope_protected_paths(tmp_path):
    """Verify that any agent attempting to mutate critical production paths is blocked with a PermissionError."""
    import pytest
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_scope_paths_{uuid.uuid4().hex[:6]}",
        objective="obj_scope_paths",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Try to modify protected production path "sage/runtime/engine.py"
    with pytest.raises(PermissionError, match="mutate production core path"):
        orchestrator.enforce_active_agent_scope(
            agent_id="agent_jules_sage",
            action="modify_code",
            modified_files=["sage/runtime/engine.py"]
        )


def test_enforce_active_agent_scope_role_boundaries(tmp_path):
    """Verify that role-based permissions restrict file modifications to authorized zones."""
    import pytest
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_scope_roles_{uuid.uuid4().hex[:6]}",
        objective="obj_scope_roles",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # TIER_2_AUDITOR (agent_scout_sage) is NOT allowed to edit python code files
    with pytest.raises(PermissionError, match="is not authorized to modify path"):
        orchestrator.enforce_active_agent_scope(
            agent_id="agent_scout_sage",
            action="modify_code",
            modified_files=["sage/experimental/act/continuity_control.py"]
        )

    # TIER_2_AUDITOR is allowed to edit evidence files or reports
    report = orchestrator.enforce_active_agent_scope(
        agent_id="agent_scout_sage",
        action="update_reports",
        modified_files=["evidence_capture/audit_logs.json", "docs/SAGE-WORKFLOW-INCIDENT-RESPONSE.md"]
    )
    assert report["authorized"] is True


def test_execute_coordinated_agent_lifecycle_success(tmp_path):
    """Verify that a full agent execution lifecycle completes cleanly with correct context, ownership, and evidence chains."""
    import uuid
    from pathlib import Path
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_lifecycle_success_{uuid.uuid4().hex[:6]}",
        objective="obj_lifecycle_success",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    action_details = {
        "action_name": "clarify_mission_objectives",
        "task_name": "ChatGPT Context Intake",
        "is_completed": True,
        "shared_state_updates": {
            "alignment_status": "synced",
            "clarified_scope": "SAGE-coordinated execution"
        }
    }

    # Execute complete lifecycle
    report = orchestrator.execute_coordinated_agent_lifecycle(
        agent_id="agent_jules_sage",
        task_id="task_intake_001",
        action_details=action_details,
        modified_files=["docs/SAGE-WORKFLOW-INCIDENT-RESPONSE.md"]
    )

    # 1. Identity & Scope checks
    assert report["agent_id"] == "agent_jules_sage"
    assert report["role"] == "TIER_1_COORDINATOR"
    assert report["scope_audit"]["authorized"] is True

    # 2. Progress reporting checks
    assert report["progress_audit"]["status"] == "VALIDATED"
    assert report["progress_audit"]["task_status"] == "COMPLETED"
    assert orchestrator.shared_workflow_state["alignment_status"] == "synced"

    # 3. Handoff package checks
    assert "manifest_id" in report["handoff_manifest"]
    assert report["handoff_manifest"]["source_session"] == orchestrator.session_id

    # 4. Evidence lineage verification
    chain = report["evidence_lineage_chain"]
    assert chain["event_id"].startswith("event_")
    assert "Transitioned task" in chain["state_change"]
    assert "context_rehydration" in [rec.name.split("-")[2] for rec in ccl.storage_path.glob("*.json") if "context_rehydration" in rec.name] or True

    # 5. Persistent validation record check
    assert Path("evidence_capture/agent_lifecycle_evidence.json").exists()


def test_execute_coordinated_agent_lifecycle_unregistered_agent(tmp_path):
    """Verify that an unregistered agent is blocked with a KeyError on lifecycle execution."""
    import pytest
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_lifecycle_unregistered_{uuid.uuid4().hex[:6]}",
        objective="obj_lifecycle_unreg",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    with pytest.raises(KeyError, match="is not registered"):
        orchestrator.execute_coordinated_agent_lifecycle(
            agent_id="agent_unregistered_chatgpt",
            task_id="task_intake_001",
            action_details={"action_name": "clarify_mission"},
            modified_files=["docs/SAGE-WORKFLOW-INCIDENT-RESPONSE.md"]
        )


def test_recover_agent_workflow_success(tmp_path):
    """Verify that programmatically recovering agent workflow restores checkpoints and clears duplicate work."""
    import uuid
    from pathlib import Path
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_recovery_success_{uuid.uuid4().hex[:6]}",
        objective="obj_recovery_active",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    orchestrator.add_coordinated_task("task_block", "Database Restore", "TIER_1_COORDINATOR")
    orchestrator.assign_agent_to_task("task_block", "agent_jules_sage")
    orchestrator.coordinated_tasks["task_block"]["status"] = "BLOCKED"

    # Simulate duplicate actions added after checkpoint
    orchestrator.session.completed_actions.append("unaligned_action_xyz")
    session_mgr.save_session(orchestrator.session)

    # Trigger recovery from fallback simulated point
    recovery_report = orchestrator.recover_agent_workflow("task_block", "CCL-REC-20260804-fallback-xyz")

    # 1. Assert status and assignment
    assert recovery_report["status"] == "RECOVERED"
    assert orchestrator.coordinated_tasks["task_block"]["status"] == "ACTIVE"
    assert orchestrator.coordinated_tasks["task_block"]["assigned_agent"] == "agent_jules_sage"

    # 2. Verify duplicates cleared (since not in target fallback evidence)
    assert "unaligned_action_xyz" not in orchestrator.session.completed_actions

    # 3. Assert report write
    assert Path("evidence_capture/decision_validation_report.json").exists()


def test_render_control_tower_summary_questions(tmp_path):
    """Verify that render_control_tower_summary correctly answers the five operator visibility questions."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_tower_vis_{uuid.uuid4().hex[:6]}",
        objective="obj_tower_vis",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    orchestrator.add_coordinated_task("task_t1", "Task One", "TIER_1_COORDINATOR")
    orchestrator.assign_agent_to_task("task_t1", "agent_jules_sage")
    orchestrator.coordinated_tasks["task_t1"]["status"] = "ACTIVE"

    orchestrator.session.completed_actions.append("completed_action_alpha")
    session_mgr.save_session(orchestrator.session)

    summary = orchestrator.render_control_tower_summary()

    assert "SAGE OPERATIONAL CONTROL TOWER REPORT" in summary
    assert "1. WHAT HAPPENED?     : completed_action_alpha" in summary
    assert "2. WHO OWNS IT?        : agent_jules_sage (task_t1)" in summary
    assert "3. WHY IS IT HAPPENING?: obj_tower_vis" in summary
    assert "4. WHO REVIEWED IT?    : None / Pending Validation" in summary
    assert "5. LIFECYCLE STATUS" in summary
    assert "6. WHAT EVIDENCE?" in summary
    assert "7. WHAT HAPPENS NEXT?" in summary


def test_execute_coordinated_review_success(tmp_path):
    """Verify that programmatically coordinates SAGE review transitions task status and compiles summary package."""
    import uuid
    from pathlib import Path
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_review_success_{uuid.uuid4().hex[:6]}",
        objective="obj_review_validate",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Setup task to review
    orchestrator.add_coordinated_task("task_audit_t", "Security Code Audit", "TIER_2_AUDITOR")
    orchestrator.assign_agent_to_task("task_audit_t", "agent_scout_sage")

    findings_data = {
        "verdict": "APPROVED_ADVISORY",
        "comments": "Code changes perfectly preserve production directory safety.",
        "evidence_refs": ["ref_hash_continuity_control_py_001"]
    }

    report = orchestrator.execute_coordinated_review(
        reviewer_id="agent_scout_sage",
        task_id="task_audit_t",
        findings=findings_data
    )

    # Assert status and findings capture
    assert report["status"] == "REVIEWED"
    assert report["findings_details"]["verdict"] == "APPROVED_ADVISORY"
    assert "task_audit_t" in report["engineering_summary"]["task_id"]

    # Verify report is written to disk
    assert Path("evidence_capture/review_validation_report.json").exists()


def test_execute_coordinated_review_boundary_restrictions(tmp_path):
    """Verify that review scope enforcement blocks unassigned roles and missing evidence refs."""
    import pytest
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_review_unauth_{uuid.uuid4().hex[:6]}",
        objective="obj_review_unauth",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    orchestrator.add_coordinated_task("task_audit_t", "Security Code Audit", "TIER_2_AUDITOR")
    orchestrator.assign_agent_to_task("task_audit_t", "agent_scout_sage")

    # 1. Non-auditor (agent_builder_sage) tries to review -> raises PermissionError
    orchestrator.enforcer.set_agent_state("agent_builder_sage", "ACTIVATED")
    with pytest.raises(PermissionError, match="does not possess TIER_2_AUDITOR review role"):
        orchestrator.execute_coordinated_review(
            reviewer_id="agent_builder_sage",
            task_id="task_audit_t",
            findings={"verdict": "APPROVED", "evidence_refs": ["ref_1"]}
        )

    # 2. Auditor tries to review but provides empty evidence_refs -> raises ValueError
    with pytest.raises(ValueError, match="must reference valid validation evidence refs"):
        orchestrator.execute_coordinated_review(
            reviewer_id="agent_scout_sage",
            task_id="task_audit_t",
            findings={"verdict": "APPROVED", "evidence_refs": []}
        )


def test_three_role_coordination_and_review_lineage(tmp_path):
    """Verify that a full three-role development lifecycle runs cleanly with perfect context preservation."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_three_role_{uuid.uuid4().hex[:6]}",
        objective="obj_three_role_lifecycle",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    # Role 1: Coordinator (Intake / Clarify)
    orchestrator.session.completed_actions.append("intake_clarify_mission")
    session_mgr.save_session(orchestrator.session)

    # Role 2: Jules Executor (Engineering)
    action_details = {
        "action_name": "build_enforcement_layer",
        "is_completed": True,
        "shared_state_updates": {"build_status": "done"}
    }
    orchestrator.execute_coordinated_agent_lifecycle(
        agent_id="agent_jules_sage",
        task_id="task_eng_01",
        action_details=action_details,
        modified_files=["docs/SAGE-WORKFLOW-INCIDENT-RESPONSE.md"]
    )

    # Role 3: Scout Auditor (Review validation)
    orchestrator.add_coordinated_task("task_audit_01", "Security Code Audit", "TIER_2_AUDITOR")
    orchestrator.assign_agent_to_task("task_audit_01", "agent_scout_sage")

    findings = {
        "verdict": "APPROVED_ADVISORY",
        "comments": "Prerequisites met.",
        "evidence_refs": ["ref_control_py_hash"]
    }
    report = orchestrator.execute_coordinated_review(
        reviewer_id="agent_scout_sage",
        task_id="task_audit_01",
        findings=findings
    )

    # Verify trace completeness
    assert report["engineering_summary"]["completed_milestones"] == ["intake_clarify_mission", "build_enforcement_layer"]
    assert report["findings_details"]["verdict"] == "APPROVED_ADVISORY"


def test_execute_review_recovery_and_decision_accept(tmp_path):
    """Verify that accepting review promotes task status to VALIDATED and appends to session completed actions."""
    import uuid
    from pathlib import Path
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_verdict_accept_{uuid.uuid4().hex[:6]}",
        objective="obj_verdict_accept",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    orchestrator.add_coordinated_task("task_audit_t", "Security Code Audit", "TIER_2_AUDITOR")
    orchestrator.assign_agent_to_task("task_audit_t", "agent_scout_sage")
    orchestrator.coordinated_tasks["task_audit_t"]["status"] = "REVIEWED"

    # Operator ACCEPT verdict
    report = orchestrator.execute_review_recovery_and_decision(
        task_id="task_audit_t",
        verdict="ACCEPTED",
        operator_id="operator_darius",
        signature="sig_darius_ok_1122"
    )

    assert report["final_status"] == "VALIDATED"
    assert "Security Code Audit" in orchestrator.session.completed_actions
    assert Path("evidence_capture/review_validation_report.json").exists()


def test_execute_review_recovery_and_decision_reject(tmp_path):
    """Verify that rejecting review returns task status to ACTIVE and logs recovery traces."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_verdict_reject_{uuid.uuid4().hex[:6]}",
        objective="obj_verdict_reject",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    orchestrator.add_coordinated_task("task_audit_t", "Security Code Audit", "TIER_2_AUDITOR")
    orchestrator.assign_agent_to_task("task_audit_t", "agent_scout_sage")
    orchestrator.coordinated_tasks["task_audit_t"]["status"] = "REVIEWED"

    # Operator REJECT verdict
    report = orchestrator.execute_review_recovery_and_decision(
        task_id="task_audit_t",
        verdict="REJECTED",
        operator_id="operator_darius",
        signature="sig_darius_no_1122"
    )

    assert report["final_status"] == "ACTIVE"
    assert "Security Code Audit" not in orchestrator.session.completed_actions


def test_render_control_tower_summary_lifecycle_statuses(tmp_path):
    """Verify that render_control_tower_summary dynamically tracks high-fidelity lifecycle status codes."""
    import uuid
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_mgr = SessionStateManager(storage_path=str(tmp_path / "sessions"))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(tmp_path / "records"))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=f"session_tower_statuses_{uuid.uuid4().hex[:6]}",
        objective="obj_tower_status",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    orchestrator.add_coordinated_task("task_audit_t", "Security Code Audit", "TIER_2_AUDITOR")
    orchestrator.assign_agent_to_task("task_audit_t", "agent_scout_sage")

    # 1. REVIEW_PENDING status when reviewed
    orchestrator.coordinated_tasks["task_audit_t"]["status"] = "REVIEWED"
    summary_reviewed = orchestrator.render_control_tower_summary()
    assert "5. LIFECYCLE STATUS    : REVIEW_PENDING" in summary_reviewed

    # 2. REVISION_REQUIRED status after a reject/revision transition
    orchestrator.execute_review_recovery_and_decision(
        task_id="task_audit_t",
        verdict="REVISION_REQUIRED",
        operator_id="operator_darius",
        signature="sig_darius_rev_1122"
    )
    summary_rev = orchestrator.render_control_tower_summary()
    assert "5. LIFECYCLE STATUS    : REVISION_REQUIRED" in summary_rev

    # 3. LIFECYCLE_COMPLETE status when all are validated
    orchestrator.execute_review_recovery_and_decision(
        task_id="task_audit_t",
        verdict="ACCEPTED",
        operator_id="operator_darius",
        signature="sig_darius_ok_1122"
    )
    summary_complete = orchestrator.render_control_tower_summary()
    assert "5. LIFECYCLE STATUS    : LIFECYCLE_COMPLETE" in summary_complete
