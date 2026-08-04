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


def test_operator_status_dashboard_formatting(tmp_path):
    """Verify the ASCII status dashboard is generated with correct section titles and session values."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_dash_test_123",
        evidence_output_path=str(tmp_path / "dash_evidence.json")
    )

    dashboard = orchestrator.render_coordination_status()
    assert "SAGE CO-ORDINATION & ACTIVATION STATUS DASHBOARD" in dashboard
    assert "Active Session: session_dash_test_123" in dashboard
    assert "Agent & Task Assignment Info" in dashboard
    assert "Workspace Track & Guard Status" in dashboard
    assert "SAGE-CCL Ledger Stats" in dashboard


def test_prepare_handoff_manifest(tmp_path):
    """Verify that prepare_agent_handoff successfully generates a compliant JSON handoff manifest."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator

    output_manifest = tmp_path / "agent_handoff_manifest.json"
    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_handoff_test",
        evidence_output_path=str(tmp_path / "feedback.json")
    )

    # Run handoff preparation
    manifest = orchestrator.prepare_agent_handoff(output_path=str(output_manifest))

    # Assert on manifest structures
    assert manifest["source_session"] == "session_handoff_test"
    assert "manifest_id" in manifest
    assert "timestamp" in manifest
    assert "workspace_fingerprint" in manifest
    assert "coordination_telemetry" in manifest
    assert manifest["coordination_telemetry"]["assigned_agent"] == "agent_jules_sage"
    assert "rehydration_token" in manifest["coordination_telemetry"]

    # Verify JSON file structure
    assert output_manifest.exists()
    with open(output_manifest, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["manifest_id"] == manifest["manifest_id"]
    assert loaded["source_session"] == "session_handoff_test"


def test_agent_activation_lifecycle(tmp_path):
    """Verify that agent activation states transition properly along their expected lifecycle."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    session_mgr = SessionStateManager(storage_path=str(session_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_act_test",
        objective="obj_continuous_development"
    )
    # Patch session storage for orchestrator
    orchestrator.session_manager = session_mgr
    orchestrator.session = session_mgr.create_session(
        session_id="session_act_test",
        active_objectives=["obj_continuous_development"]
    )

    # 1. Initialize Activation State
    agent_id = "agent_jules_sage"
    task_id = "task_active_development"
    state = orchestrator.initialize_agent_activation(
        agent_id=agent_id,
        assigned_task_id=task_id,
        authorized_scope=["sage/experimental/"]
    )
    assert state.agent_id == agent_id
    assert state.assigned_task_id == task_id
    assert state.lifecycle_state == "INITIATED"
    assert "sage/experimental/" in state.authorized_scope_prefixes

    # 2. Authorize Activation State
    authorized_state = orchestrator.authorize_agent_activation(
        agent_id=agent_id,
        supervisor_id="supervisor_jules",
        signature="sig_jules_auth_88"
    )
    assert authorized_state.lifecycle_state == "ACTIVE"
    assert authorized_state.human_authorization_signature == "sig_jules_auth_88"

    # 3. Complete Activation State
    completed_state = orchestrator.complete_agent_activation(agent_id=agent_id)
    assert completed_state.lifecycle_state == "COMPLETED"


def test_active_agent_scope_enforcement(tmp_path):
    """Verify that SAGE actively enforces authorized boundaries and blocks violations."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    session_mgr = SessionStateManager(storage_path=str(session_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_enforce_test",
        objective="obj_continuous_development"
    )
    orchestrator.session_manager = session_mgr
    orchestrator.session = session_mgr.create_session(
        session_id="session_enforce_test",
        active_objectives=["obj_continuous_development"]
    )

    agent_id = "agent_jules_sage"
    task_id = "task_active_development"

    # Set up INITIATED state (should fail enforcement because not ACTIVE yet)
    orchestrator.initialize_agent_activation(
        agent_id=agent_id,
        assigned_task_id=task_id,
        authorized_scope=["sage/experimental/"]
    )
    res_initiated = orchestrator.enforce_active_agent_scope(agent_id, ["sage/experimental/act/continuity_control.py"])
    assert res_initiated["is_allowed"] is False
    assert "Must be ACTIVE to execute" in res_initiated["reason"]

    # Authorize agent to ACTIVE
    orchestrator.authorize_agent_activation(agent_id, "supervisor_jules", "sig_jules_123")

    # Clean modification within scope -> ALLOW
    res_clean = orchestrator.enforce_active_agent_scope(agent_id, ["sage/experimental/act/continuity_control.py"])
    assert res_clean["is_allowed"] is True
    assert res_clean["action"] == "ALLOW_EXECUTION"

    # Out of scope modification -> BLOCK & transition to BLOCKED
    res_out_of_scope = orchestrator.enforce_active_agent_scope(agent_id, ["docs/INDEX.md"])
    assert res_out_of_scope["is_allowed"] is False
    assert "is outside the authorized scope" in res_out_of_scope["reason"]
    assert res_out_of_scope["action"] == "BLOCK_EXECUTION"

    # Re-verify that agent is now BLOCKED
    res_blocked_repeat = orchestrator.enforce_active_agent_scope(agent_id, ["sage/experimental/act/continuity_control.py"])
    assert res_blocked_repeat["is_allowed"] is False
    assert "is BLOCKED due to previous boundary violations" in res_blocked_repeat["reason"]


def test_active_agent_protected_namespace_enforcement(tmp_path):
    """Verify that SAGE actively blocks modifications to core protected namespaces even if initialized as ACTIVE."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    session_mgr = SessionStateManager(storage_path=str(session_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_protected_enforce_test",
        objective="obj_continuous_development"
    )
    orchestrator.session_manager = session_mgr
    orchestrator.session = session_mgr.create_session(
        session_id="session_protected_enforce_test",
        active_objectives=["obj_continuous_development"]
    )

    agent_id = "agent_jules_sage"
    task_id = "task_active_development"

    # Initialize and authorize with very broad scope prefix
    orchestrator.initialize_agent_activation(
        agent_id=agent_id,
        assigned_task_id=task_id,
        authorized_scope=["sage/"]
    )
    orchestrator.authorize_agent_activation(agent_id, "supervisor_jules", "sig_jules_456")

    # Attempt modifying a protected production namespace file -> BLOCK & transition to BLOCKED
    res_protected = orchestrator.enforce_active_agent_scope(agent_id, ["sage/runtime/engine.py"])
    assert res_protected["is_allowed"] is False
    assert "modification of protected core file" in res_protected["reason"]
    assert res_protected["action"] == "BLOCK_EXECUTION"


def test_record_agent_execution_step_allowed(tmp_path):
    """Verify that an aligned agent execution step is recorded successfully and logged in session metadata."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, AgentProgressUpdate
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    session_mgr = SessionStateManager(storage_path=str(session_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_exec_allowed_test",
        objective="obj_continuous_development"
    )
    orchestrator.session_manager = session_mgr
    orchestrator.session = session_mgr.create_session(
        session_id="session_exec_allowed_test",
        active_objectives=["obj_continuous_development"]
    )

    agent_id = "agent_jules_sage"
    task_id = "task_active_development"

    # Set up and authorize agent activation
    orchestrator.initialize_agent_activation(agent_id, task_id, ["sage/experimental/"])
    orchestrator.authorize_agent_activation(agent_id, "supervisor_jules", "sig_jules_9911")

    # Clean aligned step
    update = AgentProgressUpdate(
        agent_id=agent_id,
        step_id="step_01",
        action_taken="Wrote telemetry method inside experimental namespaces",
        objective_alignment="obj_continuous_development",
        modified_files=["sage/experimental/act/continuity_control.py"]
    )

    res = orchestrator.record_agent_execution_step(update)
    assert res["status"] == "ACTIVE"
    assert res["drift_detected"] is False
    assert res["action"] == "ALLOW_EXECUTION"

    # Verify session log
    exec_log = orchestrator.session.metadata.get("execution_log")
    assert exec_log is not None
    assert len(exec_log) == 1
    assert exec_log[0]["step_id"] == "step_01"
    assert exec_log[0]["status"] == "ALIGNED"


def test_record_agent_execution_step_blocked_by_drift(tmp_path):
    """Verify that an execution step with objective drift is blocked and transitions the agent to BLOCKED."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, AgentProgressUpdate
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    session_mgr = SessionStateManager(storage_path=str(session_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_exec_drift_test",
        objective="obj_continuous_development"
    )
    orchestrator.session_manager = session_mgr
    orchestrator.session = session_mgr.create_session(
        session_id="session_exec_drift_test",
        active_objectives=["obj_continuous_development"]
    )

    agent_id = "agent_jules_sage"
    task_id = "task_active_development"

    orchestrator.initialize_agent_activation(agent_id, task_id, ["sage/experimental/"])
    orchestrator.authorize_agent_activation(agent_id, "supervisor_jules", "sig_jules_9911")

    # Drifting step (claiming alignment to an unassigned objective)
    update = AgentProgressUpdate(
        agent_id=agent_id,
        step_id="step_drift",
        action_taken="Modifying server configurations",
        objective_alignment="obj_unauthorized_server_maintenance"
    )

    res = orchestrator.record_agent_execution_step(update)
    assert res["status"] == "BLOCKED"
    assert res["drift_detected"] is True
    assert "Objective Drift" in res["reason"]

    # Re-verify agent status is now BLOCKED
    act_dict = orchestrator.session.metadata.get("agent_activation")
    assert act_dict["lifecycle_state"] == "BLOCKED"


def test_record_agent_execution_step_blocked_by_security(tmp_path):
    """Verify that execution containing unauthorized api directives is actively blocked."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, AgentProgressUpdate
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    session_mgr = SessionStateManager(storage_path=str(session_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_exec_sec_test",
        objective="obj_continuous_development"
    )
    orchestrator.session_manager = session_mgr
    orchestrator.session = session_mgr.create_session(
        session_id="session_exec_sec_test",
        active_objectives=["obj_continuous_development"]
    )

    agent_id = "agent_jules_sage"
    task_id = "task_active_development"

    orchestrator.initialize_agent_activation(agent_id, task_id, ["sage/experimental/"])
    orchestrator.authorize_agent_activation(agent_id, "supervisor_jules", "sig_jules_9911")

    # Unauthorized action string
    update = AgentProgressUpdate(
        agent_id=agent_id,
        step_id="step_sec_fail",
        action_taken="Executing bypass_policies command",
        objective_alignment="obj_continuous_development"
    )

    res = orchestrator.record_agent_execution_step(update)
    assert res["status"] == "BLOCKED"
    assert res["drift_detected"] is True
    assert "Security Drift" in res["reason"]


def test_workflow_intelligence_healthy(tmp_path):
    """Verify that a normal active agent with no friction produces a HEALTHY status report."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    session_mgr = SessionStateManager(storage_path=str(session_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_intel_healthy_test",
        objective="obj_continuous_development"
    )
    orchestrator.session_manager = session_mgr
    orchestrator.session = session_mgr.create_session(
        session_id="session_intel_healthy_test",
        active_objectives=["obj_continuous_development"]
    )

    agent_id = "agent_jules_sage"
    task_id = "task_active_development"

    # Activate agent
    orchestrator.initialize_agent_activation(agent_id, task_id, ["sage/experimental/"])
    orchestrator.authorize_agent_activation(agent_id, "supervisor_jules", "sig_jules_9911")

    # Mock git workspace to be empty/clean for isolated test
    orchestrator.scan_git_workspace = lambda: {"modified_files": [], "diffs": {}}

    # Generate Report
    report = orchestrator.generate_workflow_intelligence_report()
    assert report["workflow_status"] == "HEALTHY"
    assert report["health_score"] >= 90.0
    assert len(report["blocked_conditions"]) == 0


def test_workflow_intelligence_degraded(tmp_path):
    """Verify that uninitialized agent results in a DEGRADED status report with signals."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    session_mgr = SessionStateManager(storage_path=str(session_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_intel_degraded_test",
        objective="obj_continuous_development"
    )
    orchestrator.session_manager = session_mgr
    orchestrator.session = session_mgr.create_session(
        session_id="session_intel_degraded_test",
        active_objectives=["obj_continuous_development"]
    )

    # Mock git workspace to be empty/clean for isolated test
    orchestrator.scan_git_workspace = lambda: {"modified_files": [], "diffs": {}}

    # Do not activate agent -> NO_AGENT_ACTIVE -> DEGRADED
    report = orchestrator.generate_workflow_intelligence_report()
    assert report["workflow_status"] == "DEGRADED"
    assert report["health_score"] < 90.0
    assert any(sig["signal_type"] == "NO_AGENT_ACTIVE" for sig in report["actionable_operator_signals"])


def test_workflow_intelligence_blocked(tmp_path):
    """Verify that a blocked agent results in a BLOCKED workflow report with critical override signals."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    session_mgr = SessionStateManager(storage_path=str(session_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_intel_blocked_test",
        objective="obj_continuous_development"
    )
    orchestrator.session_manager = session_mgr
    orchestrator.session = session_mgr.create_session(
        session_id="session_intel_blocked_test",
        active_objectives=["obj_continuous_development"]
    )

    agent_id = "agent_jules_sage"
    task_id = "task_active_development"

    orchestrator.initialize_agent_activation(agent_id, task_id, ["sage/experimental/"])
    orchestrator.authorize_agent_activation(agent_id, "supervisor_jules", "sig_jules_9911")

    # Force block the agent via scope violation
    orchestrator.enforce_active_agent_scope(agent_id, ["docs/INDEX.md"])

    # Mock git workspace to be empty/clean for isolated test
    orchestrator.scan_git_workspace = lambda: {"modified_files": [], "diffs": {}}

    # Generate Report
    report = orchestrator.generate_workflow_intelligence_report()
    assert report["workflow_status"] == "BLOCKED"
    assert report["health_score"] < 60.0
    assert len(report["blocked_conditions"]) == 1
    assert any(sig["signal_type"] == "SUPERVISOR_OVERRIDE_REQUIRED" for sig in report["actionable_operator_signals"])


def test_rehydrate_from_handoff_manifest_success(tmp_path):
    """Verify that SAGE programmatically restores session objectives and agent activation from handoff manifest."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    manifest_file = tmp_path / "manifest.json"

    session_mgr = SessionStateManager(storage_path=str(session_storage))

    # 1. Create a dummy manifest
    manifest_data = {
        "manifest_id": "manifest_test_rehydrate",
        "timestamp": "2026-08-04T12:00:00Z",
        "source_session": "session_rehydrated_99",
        "target_session_objectives": ["obj_persistent_continuity", "obj_continuous_development"],
        "state_snapshot": {
            "completed_actions": ["task_setup_persistence"],
            "pending_actions": ["task_verify_rehydration"],
            "important_decisions": []
        },
        "agent_activation_state": {
            "agent_id": "agent_jules_sage",
            "session_id": "session_rehydrated_99",
            "assigned_task_id": "task_active_development",
            "lifecycle_state": "ACTIVE",
            "authorized_scope_prefixes": ["sage/experimental/"],
            "human_authorization_signature": "sig_supervisor_jules_11"
        },
        "workspace_fingerprint": {}
    }

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    # 2. Run Rehydration
    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_dummy",
        objective="obj_temporary"
    )
    orchestrator.session_manager = session_mgr
    orchestrator.ccl.storage_path = record_storage

    report = orchestrator.rehydrate_from_handoff_manifest(str(manifest_file))

    # 3. Assert on restored state
    assert report["rehydrated_session_id"] == "session_rehydrated_99"
    assert "obj_persistent_continuity" in report["target_objectives"]
    assert report["agent_activation_state"]["agent_id"] == "agent_jules_sage"
    assert report["agent_activation_state"]["lifecycle_state"] == "ACTIVE"

    # Verify session is fully rehydrated in SessionStateManager
    rehydrated_session = session_mgr.retrieve_session("session_rehydrated_99")
    assert rehydrated_session is not None
    assert "obj_persistent_continuity" in rehydrated_session.active_objectives
    assert "task_setup_persistence" in rehydrated_session.completed_actions


def test_rehydrate_from_handoff_manifest_divergence(tmp_path):
    """Verify SAGE actively detects workspace state divergence and flags missing/modified files."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    manifest_file = tmp_path / "manifest.json"
    dummy_file = tmp_path / "dummy_experimental.py"

    # Create dummy workspace file with custom content
    dummy_file.write_text("print('original state')", encoding="utf-8")

    session_mgr = SessionStateManager(storage_path=str(session_storage))

    # Manifest specifying dummy_file but with divergent size/checksum, and a missing file
    manifest_data = {
        "manifest_id": "manifest_test_divergence",
        "timestamp": "2026-08-04T12:00:00Z",
        "source_session": "session_divergence_99",
        "target_session_objectives": ["obj_continuous_development"],
        "state_snapshot": {},
        "agent_activation_state": None,
        "workspace_fingerprint": {
            str(dummy_file): {
                "sha256": "wrong_hash_to_trigger_divergence",
                "size_bytes": 9999
            },
            "missing_experimental_file.py": {
                "sha256": "any_hash",
                "size_bytes": 42
            }
        }
    }

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_dummy",
        objective="obj_temporary"
    )
    orchestrator.session_manager = session_mgr
    orchestrator.ccl.storage_path = record_storage

    report = orchestrator.rehydrate_from_handoff_manifest(str(manifest_file))

    # Assert on divergence audit findings
    audit = report["divergence_audit"]
    assert audit["divergence_detected"] is True
    assert audit["divergent_files_count"] == 1
    assert str(dummy_file) in audit["divergent_files"]
    assert audit["missing_files_count"] == 1
    assert "missing_experimental_file.py" in audit["missing_files"]


def test_promote_discovery_candidate_success(tmp_path):
    """Verify that SAGE programmatically synthesizes, validates, and records discovery candidates."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"

    session_mgr = SessionStateManager(storage_path=str(session_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_discovery_test_1",
        objective="obj_continuous_development"
    )
    orchestrator.session_manager = session_mgr
    orchestrator.ccl.storage_path = record_storage
    orchestrator.session = session_mgr.create_session(
        session_id="session_discovery_test_1",
        active_objectives=["obj_continuous_development"]
    )

    # Promote Discovery Candidate
    candidate = orchestrator.promote_discovery_candidate(
        opportunity_type="OPERATIONAL_EFFICIENCY",
        pattern_observed="Repeated git command invokes are relatively slow in sandboxes",
        research_validation_criteria="Implement high-fidelity workspace memory cache to bypass shell executions"
    )

    assert candidate["candidate_id"].startswith("DISC-CAN-")
    assert candidate["opportunity_type"] == "OPERATIONAL_EFFICIENCY"
    assert candidate["pattern_observed"] == "Repeated git command invokes are relatively slow in sandboxes"
    assert candidate["lifecycle_state"] == "PROPOSED"

    # Verify session has the candidate
    stored_candidates = orchestrator.session.metadata.get("discovery_candidates")
    assert stored_candidates is not None
    assert len(stored_candidates) == 1
    assert stored_candidates[0]["candidate_id"] == candidate["candidate_id"]


def test_rehydrate_preserves_discovery_candidates(tmp_path):
    """Verify that loading a handoff manifest containing discovery candidates correctly rehydrates those candidates into session metadata."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    manifest_file = tmp_path / "manifest.json"

    session_mgr = SessionStateManager(storage_path=str(session_storage))

    # Create manifest with discovery candidates
    manifest_data = {
        "manifest_id": "manifest_test_discovery_rehydrate",
        "timestamp": "2026-08-04T12:00:00Z",
        "source_session": "session_rehydrated_discovery",
        "target_session_objectives": ["obj_continuous_development"],
        "state_snapshot": {},
        "agent_activation_state": None,
        "discovery_candidates": [
            {
                "candidate_id": "DISC-CAN-ABCDE12345",
                "opportunity_type": "TEST_INTEGRITY",
                "pattern_observed": "Pre-commit tests could be automatically triggered",
                "research_validation_criteria": "Integrate git pre-commit hooks programmatically",
                "lifecycle_state": "PROPOSED",
                "timestamp": 1234567.8
            }
        ],
        "workspace_fingerprint": {}
    }

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_dummy",
        objective="obj_temporary"
    )
    orchestrator.session_manager = session_mgr
    orchestrator.ccl.storage_path = record_storage

    report = orchestrator.rehydrate_from_handoff_manifest(str(manifest_file))

    # Verify candidates are present in rehydrated session
    rehydrated_session = session_mgr.retrieve_session("session_rehydrated_discovery")
    assert rehydrated_session is not None
    candidates = rehydrated_session.metadata.get("discovery_candidates")
    assert candidates is not None
    assert len(candidates) == 1
    assert candidates[0]["candidate_id"] == "DISC-CAN-ABCDE12345"


def test_discovery_candidate_prioritization_and_ranking(tmp_path):
    """Verify that SAGE programmatically evaluates, scores, and ranks registered discovery candidates."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"

    session_mgr = SessionStateManager(storage_path=str(session_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_discovery_priority_test",
        objective="obj_continuous_development"
    )
    orchestrator.session_manager = session_mgr
    orchestrator.ccl.storage_path = record_storage
    orchestrator.session = session_mgr.create_session(
        session_id="session_discovery_priority_test",
        active_objectives=["obj_continuous_development"]
    )

    # 1. Promote multiple candidates of varying metrics
    orchestrator.promote_discovery_candidate(
        opportunity_type="OPERATIONAL_EFFICIENCY",
        pattern_observed="Low impact item",
        research_validation_criteria="Simple fix",
        operational_impact=3.0,
        frequency_score=2.0
    )
    orchestrator.promote_discovery_candidate(
        opportunity_type="TEST_INTEGRITY",
        pattern_observed="High impact item",
        research_validation_criteria="Complex fix",
        operational_impact=9.0,
        frequency_score=8.0
    )

    # Mock clean workflow status for standard ranking
    orchestrator.generate_workflow_intelligence_report = lambda: {
        "workflow_status": "HEALTHY",
        "health_score": 100.0,
        "blocked_conditions": [],
        "actionable_operator_signals": []
    }

    prioritized = orchestrator.generate_prioritized_candidates()
    assert len(prioritized) == 2
    # Verify descending rank order (high priority first)
    assert prioritized[0]["pattern_observed"] == "High impact item"
    assert prioritized[0]["priority_score"] == 8.5
    assert prioritized[1]["pattern_observed"] == "Low impact item"
    assert prioritized[1]["priority_score"] == 2.5


def test_discovery_candidate_blocked_boost(tmp_path):
    """Verify that BLOCKED workflow state dynamically elevates security/test candidate priorities."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"

    session_mgr = SessionStateManager(storage_path=str(session_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_discovery_boost_test",
        objective="obj_continuous_development"
    )
    orchestrator.session_manager = session_mgr
    orchestrator.ccl.storage_path = record_storage
    orchestrator.session = session_mgr.create_session(
        session_id="session_discovery_boost_test",
        active_objectives=["obj_continuous_development"]
    )

    # Promote a TEST_INTEGRITY candidate
    orchestrator.promote_discovery_candidate(
        opportunity_type="TEST_INTEGRITY",
        pattern_observed="Hook tests",
        research_validation_criteria="criteria",
        operational_impact=6.0,
        frequency_score=5.0
    )

    # Mock BLOCKED workflow report to trigger the automatic boost
    orchestrator.generate_workflow_intelligence_report = lambda: {
        "workflow_status": "BLOCKED",
        "health_score": 20.0,
        "blocked_conditions": ["Agent blocked"],
        "actionable_operator_signals": []
    }

    prioritized = orchestrator.generate_prioritized_candidates()
    assert len(prioritized) == 1
    # Check that scores have been boosted
    assert prioritized[0]["operational_impact"] == 8.0  # +2.0
    assert prioritized[0]["frequency_score"] == 6.5  # +1.5
    assert prioritized[0]["priority_score"] == 7.25  # (8.0 + 6.5) / 2.0
    assert prioritized[0]["risk_level"] == "CRITICAL"
    assert prioritized[0]["validation_readiness"] == "HIGH"
