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


def test_sage_operational_intelligence_layer_integration(tmp_path):
    """Verify the end-to-end SAGE Operational Intelligence Layer (SAGE-OIL) capability.

    Validates:
    - Dynamic performance and context efficiency metrics computation.
    - SAGE Improvement Signal generation (Event -> Evidence -> Metric -> Signal).
    - Preservation and traceability of metrics in the unified evidence package.
    - Generation of discovery lane candidates in discovery_candidates_register.json.
    - High-fidelity ASCII Control Tower summary rendering.
    """
    from sage.experimental.act.continuity_control import (
        DeveloperWorkflowOrchestrator,
        ContinuityControlLoop,
        SAGEOperationalIntelligenceLayer,
        ContinuityControlRecord
    )
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_operational_feedback.json"
    discovery_register = tmp_path / "evidence" / "discovery_candidates_register.json"

    # 1. Initialize custom managers and loop
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    # Initialize session state with duplicated active/completed actions to trigger efficiency metrics
    session = session_mgr.create_session(
        session_id="session_oil_test",
        active_objectives=["obj_validate_oil_integration"]
    )
    session.add_completed_action("task_compile_source")
    # Add identical pending action (bypassing state safeguard) to simulate unnecessary reassessment
    session.pending_actions.append("task_compile_source")
    session_mgr.save_session(session)

    # Initialize orchestrator
    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_oil_test",
        objective="obj_validate_oil_integration",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    action = "SAGE Operational Intelligence Integration Validation"
    reasoning = "Test dynamic metrics computation, improvement signals, and Control Tower dashboards"
    friction = [{"type": "environmental_latency", "detail": "high setup and download latency", "severity": "medium"}]
    opportunities = ["Auto-cache local packages and mock network boundaries"]

    # 2. Run active development coordination loop
    result = orchestrator.execute_active_development_coordination(
        action_taken=action,
        decision_reasoning=reasoning,
        workflow_friction=friction,
        improvement_opportunities=opportunities
    )

    # 3. Assert on results structure and metrics
    assert "operational_intelligence" in result
    op_intel = result["operational_intelligence"]
    assert "metrics" in op_intel
    assert "learning_signals" in op_intel

    metrics = op_intel["metrics"]
    assert metrics["lifecycle_completion_rate"] == 1.0  # Approved/Validated
    assert metrics["recovery_success_rate"] == 1.0       # Standard clean run
    assert metrics["evidence_completeness"] == 1.0       # All required keys are populated
    assert metrics["decision_trace_completeness"] == 1.0 # Fully complete decision event
    assert metrics["workflow_state_accuracy"] == 1.0     # Clean status matching VALIDATED
    assert metrics["execution_cycle_duration"] > 0.0     # Non-trivial execution time

    # Context Efficiency Tracking checks
    assert metrics["context_preservation_score"] == 1.0
    assert metrics["unnecessary_reassessment_events"] == 1 # "task_compile_source" is duplicate
    assert metrics["repeated_execution_prevention"] is False
    assert metrics["state_restoration_success"] is True

    # 4. Validate Signal Generation Flow
    learning_signals = op_intel["learning_signals"]
    assert len(learning_signals) >= 2 # Observed friction signal + Unnecessary reassessments signal

    # Verify that the signals map to the original record and contain correct fields
    friction_sig = next(s for s in learning_signals if s["metric_category"] == "OPERATIONAL_EFFICIENCY")
    assert friction_sig["event_id"] == result["ccl_record"]["record_id"]
    assert friction_sig["metric_evaluation"]["observed_friction_type"] == "environmental_latency"
    assert "CANDIDATE-OIL-" in friction_sig["improvement_candidate"]["candidate_id"]
    assert friction_sig["discovery_lane_input"]["target_process"] == "workflow_coordination_environmental_latency"

    # Verify that discovery candidates are correctly saved in the persistent register
    oil = SAGEOperationalIntelligenceLayer(storage_path=record_storage)
    promoted_record = ContinuityControlRecord(**result["ccl_record"])
    from pydantic import BaseModel
    from sage.experimental.act.continuity_control import SAGEOperationalMetrics
    metrics_obj = SAGEOperationalMetrics(**metrics)

    custom_signals = oil.generate_learning_signals(
        record=promoted_record,
        metrics=metrics_obj,
        register_path=discovery_register
    )
    assert len(custom_signals) >= 2
    assert discovery_register.exists()
    with open(discovery_register, "r", encoding="utf-8") as f:
        register_data = json.load(f)
    assert len(register_data) >= 2
    assert any(c["candidate_id"].startswith("CANDIDATE-OIL-") for c in register_data)

    # 5. Verify high-fidelity ASCII Control Tower Console Dashboard rendering
    dashboard_str = orchestrator.render_control_tower_summary(result)
    assert "SAGE CONTROL TOWER - OPERATIONAL INTELLIGENCE VIEW" in dashboard_str
    assert "[Workflow Health]" in dashboard_str
    assert "1. WHAT HAPPENED?" in dashboard_str
    assert "2. WHO OWNS IT?" in dashboard_str
    assert "3. WHY IS IT HAPPENING?" in dashboard_str
    assert "4. WHAT EVIDENCE SUPPORTS IT?" in dashboard_str
    assert "5. WHAT HAPPENS NEXT?" in dashboard_str
    assert "BOTTLENECK INDICATORS:" in dashboard_str


def test_sage_continuous_execution_and_governance_loop(tmp_path):
    """Verify continuous execution, backlog queue integration, loop safety controls,

    checkpoint/rollback recovery, failure escalation protection, and drift detection.
    """
    from sage.experimental.act.continuity_control import (
        DeveloperWorkflowOrchestrator,
        ContinuityControlLoop,
        SAGEMissionTask
    )
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_feedback.json"

    # Setup session manager and orchestrator
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_continuous_test_99",
        objective="obj_continuous_development",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # -----------------
    # 1. Mission Queue Processing & Priorities
    # -----------------
    task_low = SAGEMissionTask(
        task_id="task_low_priority",
        objective_id="obj_continuous_development",
        priority_score=10.0,
        authorized=True,
        description="Low priority task"
    )
    task_high = SAGEMissionTask(
        task_id="task_high_priority",
        objective_id="obj_continuous_development",
        priority_score=90.0,
        authorized=True,
        description="High priority task"
    )
    task_unauthorized = SAGEMissionTask(
        task_id="task_unauthorized_99",
        objective_id="obj_continuous_development",
        priority_score=95.0,
        authorized=False,
        description="Unauthorized task"
    )

    orchestrator.mission_queue.add_task(task_low)
    orchestrator.mission_queue.add_task(task_high)
    orchestrator.mission_queue.add_task(task_unauthorized)

    # Next approved task should be high priority, not the unauthorized even though it has a higher score
    next_task = orchestrator.mission_queue.get_next_approved_task(orchestrator.session.active_objectives)
    assert next_task is not None
    assert next_task.task_id == "task_high_priority"

    # -----------------
    # 2. Runtime State Transitions & Manual Pause / Resume / Stop
    # -----------------
    assert orchestrator.loop_state["mode"] == "CONTINUOUS"

    # Test manual pause
    orchestrator.pause_mission_execution_loop()
    assert orchestrator.loop_state["mode"] == "MANUAL_INTERVENTION_PAUSED"

    # Attempt running should instantly exit
    res_paused = orchestrator.execute_autonomous_mission_loop(max_cycles=1)
    assert res_paused["status"] == "MANUAL_INTERVENTION_PAUSED"
    assert len(res_paused["executed_tasks"]) == 0

    # Test resume
    orchestrator.resume_mission_execution_loop()
    assert orchestrator.loop_state["mode"] == "CONTINUOUS"

    # Test emergency stop
    orchestrator.emergency_stop()
    assert orchestrator.loop_state["mode"] == "STOPPED"

    with pytest.raises(ValueError, match="Stopped loop cannot be resumed"):
        orchestrator.resume_mission_execution_loop()

    # Reset loop to CONTINUOUS for remaining tests
    orchestrator.loop_state["mode"] = "CONTINUOUS"
    orchestrator.save_loop_state()

    # -----------------
    # 3. Execution, Evidence Generation, and Learning Cycle
    # -----------------
    res_exec = orchestrator.execute_autonomous_mission_loop(max_cycles=1)
    assert res_exec["status"] == "CONTINUOUS"
    assert "task_high_priority" in res_exec["executed_tasks"]

    # Verify task was completed
    t_high = orchestrator.mission_queue.get_task("task_high_priority")
    assert t_high.status == "COMPLETED"
    assert "task_high_priority" in orchestrator.session.completed_actions

    # Verify evidence generation
    assert evidence_output.exists()
    with open(evidence_output, "r", encoding="utf-8") as f:
        evidence_data = json.load(f)
    assert evidence_data["cmaps_payload"]["task_lineage"]["current_task_id"] == "task_high_priority"

    # -----------------
    # 4. Checkpoint & Rollback
    # -----------------
    checkpoint_id = orchestrator.loop_state["last_checkpoint_id"]
    assert checkpoint_id is not None

    # Mutate active objectives of session (simulation of context corruption)
    orchestrator.session.active_objectives = ["obj_corrupted_state"]
    orchestrator.session_manager.save_session(orchestrator.session)

    # Rollback to checkpoint
    orchestrator.rollback_to_checkpoint(checkpoint_id)
    assert "obj_continuous_development" in orchestrator.session.active_objectives
    assert "obj_corrupted_state" not in orchestrator.session.active_objectives

    # -----------------
    # 5. Failure Escalation Protection
    # -----------------
    # Add failing tasks with high priority so they are selected first
    f1 = SAGEMissionTask(task_id="task_fail_1", objective_id="obj_continuous_development", priority_score=100.0, authorized=True, description="Inject fail 1")
    f2 = SAGEMissionTask(task_id="task_fail_2", objective_id="obj_continuous_development", priority_score=100.0, authorized=True, description="Inject fail 2")
    f3 = SAGEMissionTask(task_id="task_fail_3", objective_id="obj_continuous_development", priority_score=100.0, authorized=True, description="Inject fail 3")
    orchestrator.mission_queue.add_task(f1)
    orchestrator.mission_queue.add_task(f2)
    orchestrator.mission_queue.add_task(f3)

    # Run loop to execute failing tasks
    res_fails = orchestrator.execute_autonomous_mission_loop(max_cycles=3)
    assert res_fails["status"] == "MANUAL_INTERVENTION_PAUSED" # Safety freeze triggered!
    assert res_fails["consecutive_failures"] == 2
    assert orchestrator.mission_queue.get_task("task_fail_1").status == "FAILED"
    assert orchestrator.mission_queue.get_task("task_fail_2").status == "PENDING"

    # Reset mode and failures for remaining checks
    orchestrator.loop_state["mode"] = "CONTINUOUS"
    orchestrator.loop_state["consecutive_failures"] = 0
    orchestrator.save_loop_state()

    # -----------------
    # 6. Discovery-to-Engineering Handoff
    # -----------------
    # Seed discovery candidates register
    discovery_reg = tmp_path / "discovery_register.json"
    cand = {
        "candidate_id": "CANDIDATE-OIL-TEST99",
        "description": "Optimize pre-compilation caches",
        "validation_criteria": "Reduces startup time",
        "priority": "HIGH"
    }
    with open(discovery_reg, "w", encoding="utf-8") as f:
        json.dump([cand], f)

    # Override target register file path in OIL to point to our temp file
    import unittest.mock as mock
    with mock.patch("sage.experimental.act.continuity_control.Path") as mock_path:
        # Let's make Path("evidence_capture/discovery_candidates_register.json") return our mocked register file
        mock_path.side_effect = lambda *args: discovery_reg if "discovery_candidates_register.json" in str(args) else Path(*args)

        task_hand = orchestrator.handoff_discovery_candidate_to_mission("CANDIDATE-OIL-TEST99")
        assert task_hand.task_id == "task_impr_CANDIDATE-OIL-TEST99"
        assert task_hand.priority_score == 80.0
        assert task_hand.lane == "optimization"
        assert task_hand.authorized is True

    # -----------------
    # 7. External Workspace Drift Detection
    # -----------------
    with mock.patch.object(orchestrator, "scan_git_workspace") as mock_scan:
        mock_scan.return_value = {
            "modified_files": ["sage/runtime/engine.py"],
            "diffs": {"sage/runtime/engine.py": "mutation in core engine"}
        }

        is_drift = orchestrator.detect_external_workspace_drift()
        assert is_drift is True
        assert orchestrator.loop_state["mode"] == "MANUAL_INTERVENTION_PAUSED"


def test_sage_operational_loop_and_queue_intelligence(tmp_path):
    """Verify queue intelligence, dependency awareness, duplicate suppression,

    archival, completed work pattern analysis, ranked scoring, and Control Tower display.
    """
    from sage.experimental.act.continuity_control import (
        DeveloperWorkflowOrchestrator,
        ContinuityControlLoop,
        SAGEMissionTask,
        SAGEOperationalIntelligenceLayer
    )
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_feedback.json"

    # Setup session manager and orchestrator
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_intel_test_99",
        objective="obj_continuous_development",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # -----------------
    # 1. Dependency Awareness & Blocked Task Detection
    # -----------------
    task_b = SAGEMissionTask(
        task_id="task_independent_b",
        objective_id="obj_continuous_development",
        priority_score=80.0,
        authorized=True,
        description="Independent Task B"
    )
    task_a = SAGEMissionTask(
        task_id="task_dependent_a",
        objective_id="obj_continuous_development",
        priority_score=90.0,
        authorized=True,
        description="Dependent Task A",
        depends_on=["task_independent_b"]
    )

    orchestrator.mission_queue.add_task(task_a)
    orchestrator.mission_queue.add_task(task_b)

    # Check that task_a is automatically identified as blocked
    orchestrator.mission_queue.update_dependency_states()
    t_a = orchestrator.mission_queue.get_task("task_dependent_a")
    assert t_a.is_blocked is True
    assert t_a.status == "BLOCKED"

    # Check next approved task - even though task_a has higher priority (90.0), task_b (80.0) should be selected because task_a is blocked
    next_task = orchestrator.mission_queue.get_next_approved_task(orchestrator.session.active_objectives)
    assert next_task is not None
    assert next_task.task_id == "task_independent_b"

    # -----------------
    # 2. Duplicate Candidate Suppression
    # -----------------
    task_b_dup = SAGEMissionTask(
        task_id="task_independent_b",
        objective_id="obj_continuous_development",
        priority_score=10.0,
        authorized=True,
        description="Duplicate Task B"
    )
    orchestrator.mission_queue.add_task(task_b_dup)

    # Priority should remain the original 80.0, not overwritten/duplicated
    assert orchestrator.mission_queue.get_task("task_independent_b").priority_score == 80.0

    # -----------------
    # 3. Completed Task Archival & Queue Metrics
    # -----------------
    # Run the loop to complete task_b
    res_b = orchestrator.execute_autonomous_mission_loop(max_cycles=1)
    assert "task_independent_b" in res_b["executed_tasks"]

    # Verify task_b completed successfully and task_a is automatically unblocked!
    assert orchestrator.mission_queue.get_task("task_independent_b").status == "COMPLETED"

    orchestrator.mission_queue.update_dependency_states()
    t_a_after = orchestrator.mission_queue.get_task("task_dependent_a")
    assert t_a_after.is_blocked is False
    assert t_a_after.status == "PENDING"

    # Archive completed tasks
    orchestrator.mission_queue.archive_completed_tasks()
    assert orchestrator.mission_queue.get_task("task_independent_b").is_archived is True
    # task_independent_b should be excluded from list_tasks()
    active_task_ids = [t.task_id for t in orchestrator.mission_queue.list_tasks()]
    assert "task_independent_b" not in active_task_ids
    assert "task_dependent_a" in active_task_ids

    # Check queue metrics
    q_metrics = orchestrator.mission_queue.get_queue_metrics()
    assert q_metrics["completed_count"] == 1
    assert q_metrics["archived_count"] == 1
    assert q_metrics["throughput_count"] == 1

    # -----------------
    # 4. Pattern Detection, Ranked Scoring, & Discovery Generation
    # -----------------
    oil = SAGEOperationalIntelligenceLayer(storage_path=record_storage)
    candidates = oil.analyze_completed_work_and_generate_candidates()

    assert len(candidates) > 0
    best_cand = candidates[0]
    assert "CANDIDATE-OIL-" in best_cand["candidate_id"]
    # Verify prioritization score computation is within expected boundaries (e.g. around 7.7)
    assert best_cand["prioritization_score"] >= 5.0
    assert best_cand["recommendation_confidence"] > 0.0

    # -----------------
    # 5. Control Tower Maturity & Reporting
    # -----------------
    # Create final package and render dashboard
    feedback_file = Path(orchestrator.evidence_output_path)
    if feedback_file.exists():
        with open(feedback_file, "r", encoding="utf-8") as f:
            evidence_pack = json.load(f)

        dashboard_str = orchestrator.render_control_tower_summary(evidence_pack)
        assert "SAGE CONTROL TOWER - OPERATIONAL INTELLIGENCE VIEW" in dashboard_str
        assert "[Active Execution State]" in dashboard_str
        assert "MISSION QUEUE HEALTH & THROUGHPUT" in dashboard_str
        assert "Queue Throughput" in dashboard_str
        assert "Improvement Velocity" in dashboard_str
        assert "RECENT COMPLETED WORK:" in dashboard_str


def test_sage_coordinated_loop_endurance_simulation(tmp_path):
    """Verify long-running endurance simulation runs, multi-cycle compounding,

    and JSON report serialization on disk.
    """
    from sage.experimental.act.continuity_control import (
        DeveloperWorkflowOrchestrator,
        ContinuityControlLoop,
        SAGEMissionTask
    )
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_feedback.json"

    # Setup session manager and orchestrator
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_endurance_test_99",
        objective="obj_continuous_development",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # 1. Add some tasks
    t1 = SAGEMissionTask(task_id="task_sim_1", objective_id="obj_continuous_development", priority_score=80.0, authorized=True, description="Endurance Sim Task 1")
    t2 = SAGEMissionTask(task_id="task_sim_2", objective_id="obj_continuous_development", priority_score=70.0, authorized=True, description="Endurance Sim Task 2")
    orchestrator.mission_queue.add_task(t1)
    orchestrator.mission_queue.add_task(t2)

    # 2. Run multi-cycle endurance simulation
    report = orchestrator.execute_endurance_simulation_run(cycles=3)

    # Assert report structure
    assert report["total_cycles"] == 3
    assert report["recovery_success_rate"] == 1.0
    assert report["compounding_duration_reduction_percent"] > 0.0
    assert len(report["history"]) == 3

    # Assert compounding curve: Cycle 1 duration should be greater than Cycle 3 duration due to compounding velocity simulation
    history_cycle_1 = report["history"][0]
    history_cycle_3 = report["history"][2]
    assert history_cycle_1["duration_secs"] > history_cycle_3["duration_secs"]

    # Verify report is written to disk
    report_file = Path("evidence_capture/operational_endurance_report.json")
    assert report_file.exists()

    with open(report_file, "r", encoding="utf-8") as f:
        serialized_report = json.load(f)
    assert serialized_report["total_cycles"] == 3
    assert serialized_report["compounding_duration_reduction_percent"] > 0.0

    # Verify additional compounding evidence files are written to disk
    learning_file = Path("evidence_capture/operational_learning_report.json")
    assert learning_file.exists()
    with open(learning_file, "r", encoding="utf-8") as f:
        l_rep = json.load(f)
    assert l_rep["learning_compounding_rate_percent"] > 0.0

    recommendation_file = Path("evidence_capture/recommendation_quality_report.json")
    assert recommendation_file.exists()
    with open(recommendation_file, "r", encoding="utf-8") as f:
        r_rep = json.load(f)
    assert r_rep["average_recommendation_confidence"] == 0.95

    queue_file = Path("evidence_capture/queue_intelligence_report.json")
    assert queue_file.exists()

    # Verify agent bridge and context restoration evidence reports are written to disk
    bridge_file = Path("evidence_capture/agent_bridge_validation_report.json")
    assert bridge_file.exists()
    with open(bridge_file, "r", encoding="utf-8") as f:
        b_rep = json.load(f)
    assert b_rep["verification_status"] == "VALIDATED"

    restoration_file = Path("evidence_capture/context_restoration_report.json")
    assert restoration_file.exists()
    with open(restoration_file, "r", encoding="utf-8") as f:
        re_rep = json.load(f)
    assert re_rep["state_restoration_accuracy_percent"] == 100.0

    trace_file = Path("evidence_capture/execution_trace_report.json")
    assert trace_file.exists()

    lineage_file = Path("evidence_capture/evidence_lineage_report.json")
    assert lineage_file.exists()


def test_sage_escalation_rules_lifecycle(tmp_path):
    """Verify consecutive failure retries, warning loop pauses, critical freezes,

    incident report log generation, and operator overrides.
    """
    from sage.experimental.act.continuity_control import (
        DeveloperWorkflowOrchestrator,
        ContinuityControlLoop,
        SAGEMissionTask
    )
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_feedback.json"

    # Setup session manager and orchestrator
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_escalation_test_99",
        objective="obj_continuous_development",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # 1. Test NORMAL escalation (retry loop)
    task_normal_fail = SAGEMissionTask(
        task_id="task_fail_transient",
        objective_id="obj_continuous_development",
        priority_score=100.0,
        authorized=True,
        description="Transient fail task"
    )
    orchestrator.mission_queue.add_task(task_normal_fail)

    # First attempt: should fail, log NORMAL, and remain PENDING for retry
    res_1 = orchestrator.execute_autonomous_mission_loop(max_cycles=1)
    assert res_1["status"] == "CONTINUOUS"

    t_normal = orchestrator.mission_queue.get_task("task_fail_transient")
    assert t_normal.status == "PENDING"
    assert orchestrator.loop_state["task_retries"]["task_fail_transient"] == 1

    # Verify NORMAL incident report registered
    assert len(orchestrator.loop_state["incidents"]) == 1
    assert orchestrator.loop_state["incidents"][0]["severity"] == "NORMAL"

    # Second attempt: should fail again, exhaust retries, log WARNING, and pause the loop
    res_2 = orchestrator.execute_autonomous_mission_loop(max_cycles=1)
    assert res_2["status"] == "MANUAL_INTERVENTION_PAUSED"

    t_warning = orchestrator.mission_queue.get_task("task_fail_transient")
    assert t_warning.status == "FAILED"
    assert orchestrator.loop_state["task_retries"]["task_fail_transient"] == 2

    # Verify WARNING incident report registered
    assert len(orchestrator.loop_state["incidents"]) == 2
    assert orchestrator.loop_state["incidents"][1]["severity"] == "WARNING"

    # 2. Test CRITICAL escalation (instant freeze and state checkpoint preservation)
    orchestrator.loop_state["mode"] = "CONTINUOUS"
    orchestrator.save_loop_state()

    task_critical_fail = SAGEMissionTask(
        task_id="task_fail_critical_violation",
        objective_id="obj_continuous_development",
        priority_score=150.0,
        authorized=True,
        description="Critical unrecoverable task"
    )
    orchestrator.mission_queue.add_task(task_critical_fail)

    # Execution should instantly stop (freeze), logging a CRITICAL incident and saving a checkpoint
    res_3 = orchestrator.execute_autonomous_mission_loop(max_cycles=1)
    assert res_3["status"] == "STOPPED"

    t_critical = orchestrator.mission_queue.get_task("task_fail_critical_violation")
    assert t_critical.status == "FAILED"

    # Verify CRITICAL incident report registered
    assert len(orchestrator.loop_state["incidents"]) == 3
    assert orchestrator.loop_state["incidents"][2]["severity"] == "CRITICAL"
    assert orchestrator.loop_state["incidents"][2]["authority_requirement"] == "OPERATOR_SIGN_OFF"

    # Verify critical checkpoint was saved
    checkpoints = orchestrator.checkpoint_manager.list_all()
    assert len(checkpoints) > 0
    assert any("CRITICAL_FREEZE" in str(cp.validation_status) for cp in checkpoints)

    # 3. Test Operator Override / Recovery Safety Gates
    with pytest.raises(ValueError, match="Stopped loop cannot be resumed"):
        orchestrator.resume_mission_execution_loop()

    # Manual supervisor override: override status back to CONTINUOUS and reset failures
    orchestrator.loop_state["mode"] = "CONTINUOUS"
    orchestrator.loop_state["consecutive_failures"] = 0
    orchestrator.save_loop_state()

    orchestrator.resume_mission_execution_loop()
    assert orchestrator.loop_state["mode"] == "CONTINUOUS"
    assert orchestrator.loop_state["consecutive_failures"] == 0


def test_external_agent_connection_bridge(tmp_path):
    """Verify SAGE ChatGPT Runtime Connector context retrieval, output updates, and Google Workspace sync."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_feedback.json"

    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_bridge_test_01",
        objective="obj_continuous_development",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # 1. Retrieve context as external agent
    context = orchestrator.retrieve_external_agent_context("agent_chatgpt")
    assert context["session_id"] == "session_bridge_test_01"
    assert "obj_continuous_development" in context["active_objectives"]
    assert "protected_workspaces" in context

    # Verify authorization check
    with pytest.raises(PermissionError, match="Unauthorized agent access attempt"):
        orchestrator.retrieve_external_agent_context("agent_unauthorized")

    # 2. Submit external agent output linked with Google account
    out_payload = {
        "action_taken": "ChatGPT Coordinate Developer loop",
        "decision_reasoning": "Restore session baseline state and request Jules build",
        "completed_action": "task_rehydrate_context"
    }

    result = orchestrator.submit_external_agent_output(
        agent_id="agent_chatgpt",
        output_data=out_payload,
        google_account="operator_jules@gmail.com"
    )

    assert result["status"] == "VALIDATED"
    assert "task_rehydrate_context" in orchestrator.session.completed_actions
    assert "google_workspace_sync_status" in result
    assert result["google_workspace_sync_status"]["google_account"] == "operator_jules@gmail.com"


def test_sage_managed_agent_operating_loop(tmp_path):
    """Verify SAGE Agent Operating Loop, Context Injection path, permission validation, and search integration."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_feedback.json"

    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_operating_test_02",
        objective="obj_continuous_development",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # 1. Request agent context package (injecting preceding operational solutions)
    context_pkg = orchestrator.request_agent_context_package("agent_jules_sage")
    assert context_pkg["agent_id"] == "agent_jules_sage"
    assert context_pkg["role_parameters"]["role"] == "SENIOR_SOFTWARE_ENGINEER"
    assert "injected_operational_solutions" in context_pkg
    assert len(context_pkg["injected_operational_solutions"]) > 0

    # 2. Submit intelligence assisted response
    resp_payload = {
        "action_taken": "Jules optimized pre-compilation cache speed",
        "decision_reasoning": "Resolve identified performance latency bottleneck",
        "completed_action": "task_optimize_cache"
    }

    result = orchestrator.submit_intelligence_assisted_agent_response(
        agent_id="agent_jules_sage",
        result_package=resp_payload
    )

    assert result["status"] == "VALIDATED"
    assert "task_optimize_cache" in orchestrator.session.completed_actions

    # Verify unauthorized permission error
    with pytest.raises(PermissionError, match="Unauthorized submission"):
         orchestrator.submit_intelligence_assisted_agent_response("agent_rogue", resp_payload)


def test_chatgpt_runtime_authentication(tmp_path):
    """Verify live ChatGPT runtime authentication handshakes and identity resolutions."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ChatGPTRuntimeAdapter
    import unittest.mock as mock

    orchestrator = DeveloperWorkflowOrchestrator(session_id="session_auth_test_11")

    # Configure variables matching environment configuration
    with mock.patch.dict(os.environ, {
        "SAGE_AGENT_ID": "chatgpt-runtime-agent",
        "SAGE_AUTH_SECRET": "safe_secret_99"
    }):
        adapter = ChatGPTRuntimeAdapter(orchestrator)

        # Valid handshake
        identity = adapter.authenticate_handshake("chatgpt-runtime-agent", "safe_secret_99")
        assert identity["agent_id"] == "chatgpt-runtime-agent"
        assert identity["provider"] == "openai"
        assert identity["status"] == "authenticated"

        # Invalid agent_id rejected
        with pytest.raises(PermissionError, match="Unknown agent ID"):
            adapter.authenticate_handshake("invalid-agent", "safe_secret_99")

        # Invalid secret credentials rejected
        with pytest.raises(PermissionError, match="Invalid credentials/secret"):
            adapter.authenticate_handshake("chatgpt-runtime-agent", "wrong_secret")


def test_chatgpt_runtime_governed_execution(tmp_path):
    """Verify live ChatGPT runtime context retrieval, task execution, result submissions, and evidence logs."""
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ChatGPTRuntimeAdapter
    import unittest.mock as mock

    orchestrator = DeveloperWorkflowOrchestrator(session_id="session_exec_test_12")

    with mock.patch.dict(os.environ, {
        "SAGE_AGENT_ID": "chatgpt-runtime-agent",
        "SAGE_AUTH_SECRET": "safe_secret_99"
    }):
        adapter = ChatGPTRuntimeAdapter(orchestrator)

        # Execute governed task
        result = adapter.execute_governed_task(
            agent_id="chatgpt-runtime-agent",
            task_id="task_rt_verify_loop",
            secret="safe_secret_99"
        )

        assert result["identity"]["status"] == "authenticated"
        assert result["response"] == "Optimized SAGE continuous execution loop speed successfully."
        assert result["validation"]["status"] == "VALIDATED"

        # Verify evidence proof generated on disk
        report_file = Path("evidence_capture/chatgpt_runtime_connection_report.json")
        assert report_file.exists()

        with open(report_file, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        assert report_data["connection_success"] is True
        assert report_data["authentication_result"] == "SUCCESS"
        assert report_data["validation_status"] == "VALIDATED"

        # Verify final activation report generated on disk
        activation_file = Path("evidence_capture/chatgpt_live_runtime_final_activation.json")
        assert activation_file.exists()

        with open(activation_file, "r", encoding="utf-8") as f:
            act_data = json.load(f)
        assert "EVAL-RT-" in act_data["evaluation_id"]
        assert act_data["agent_id"] == "chatgpt-runtime-agent"
        assert act_data["authentication_result"] == "SUCCESS"
        assert act_data["context_retrieval_result"]["current_task_boundary"] == "task_rt_verify_loop"
        assert act_data["execution_result"]["completion_status"] == "SUCCESS"
        assert act_data["validation_result"]["status"] == "VALIDATED"
