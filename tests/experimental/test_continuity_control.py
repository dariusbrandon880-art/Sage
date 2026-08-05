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
    assert "patterns" in op_intel
    assert "recommendations" in op_intel
    assert "optimization_trends" in op_intel

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

    # Pattern and Recommendation verification
    patterns = op_intel["patterns"]
    assert len(patterns) >= 1
    bottleneck_pattern = next(p for p in patterns if p["pattern_type"] == "bottleneck")
    assert "environmental_latency" in bottleneck_pattern["description"]
    assert bottleneck_pattern["frequency"] == 1

    recs = op_intel["recommendations"]
    assert len(recs) >= 1
    assert any("environmental_latency" in r["description"] for r in recs)
    bottleneck_rec = next(r for r in recs if "environmental_latency" in r["description"])
    assert bottleneck_rec["operational_impact"] == "MEDIUM"
    assert bottleneck_rec["confidence_level"] > 0.0
    assert bottleneck_rec["affected_stage"] == "execution"

    trends = op_intel["optimization_trends"]
    assert "cumulative_improvement_pct" in trends
    assert "execution_time_reduction_pct" in trends

    # 4. Validate Signal Generation Flow
    learning_signals = op_intel["learning_signals"]
    assert len(learning_signals) >= 3 # Observed friction, Unnecessary reassessments, and optimization recommendations

    # Verify that the signals map to the original record and contain correct fields
    friction_sig = next(s for s in learning_signals if s["metric_category"] == "OPERATIONAL_EFFICIENCY")
    assert friction_sig["event_id"] == result["ccl_record"]["record_id"]
    assert friction_sig["metric_evaluation"]["observed_friction_type"] == "environmental_latency"
    assert "CANDIDATE-OIL-" in friction_sig["improvement_candidate"]["candidate_id"]
    assert friction_sig["discovery_lane_input"]["target_process"] == "workflow_coordination_environmental_latency"

    # Verify that recommendation signal generates standard Candidate block
    opt_sig = next(s for s in learning_signals if s["metric_category"] == "WORKFLOW_OPTIMIZATION")
    assert opt_sig["improvement_candidate"]["candidate_id"].startswith("CANDIDATE-OPT-")
    assert opt_sig["improvement_candidate"]["is_promoted"] is False
    assert opt_sig["improvement_candidate"]["requires_approval"] is True

    # Verify that discovery candidates are correctly saved in the persistent register
    oil = SAGEOperationalIntelligenceLayer(storage_path=record_storage)
    promoted_record = ContinuityControlRecord(**result["ccl_record"])
    from pydantic import BaseModel
    from sage.experimental.act.continuity_control import SAGEOperationalMetrics
    metrics_obj = SAGEOperationalMetrics(**metrics)

    custom_signals = oil.generate_learning_signals(
        record=promoted_record,
        metrics=metrics_obj,
        register_path=discovery_register,
        recommendations=recs
    )
    assert len(custom_signals) >= 3
    assert discovery_register.exists()
    with open(discovery_register, "r", encoding="utf-8") as f:
        register_data = json.load(f)
    assert len(register_data) >= 3
    assert any(c["candidate_id"].startswith("CANDIDATE-OPT-") for c in register_data)

    # 5. Verify high-fidelity ASCII Control Tower Console Dashboard rendering
    dashboard_str = orchestrator.render_control_tower_summary(result)
    assert "SAGE CONTROL TOWER - OPERATIONAL INTELLIGENCE VIEW" in dashboard_str
    assert "[Workflow Health]" in dashboard_str
    assert "1. WHAT HAPPENED?" in dashboard_str
    assert "2. WHO OWNS IT?" in dashboard_str
    assert "3. WHY IS IT HAPPENING?" in dashboard_str
    assert "4. WHAT EVIDENCE SUPPORTS IT?" in dashboard_str
    assert "5. WHAT HAPPENS NEXT?" in dashboard_str
    assert "CONTINUOUS OPTIMIZATION DASHBOARD" in dashboard_str
    assert "RECURRING WORKFLOW PATTERNS IDENTIFIED" in dashboard_str
    assert "ADVISORY OPTIMIZATION OPPORTUNITIES" in dashboard_str
    assert "BOTTLENECK INDICATORS:" in dashboard_str


def test_real_workflow_optimization_cycle(tmp_path):
    """Verify that SAGE optimization intelligence creates measurable workflow improvement.

    Simulates a complete Real Optimization Cycle across consecutive workflow generations:
    - Run 1 (Baseline Generation): High latency, duplicate actions, and friction.
    - Run 2 (Optimization Execution): Low latency, clean context, and zero friction.
    - Validates:
      - Recommendation quality (operational stage, expected improvement, confidence accuracy).
      - Optimization effectiveness (measurable reductions in time, duplication, and cumulative trends).
      - Workflow learning quality (repeated workflows yield stronger patterns and higher confidence).
      - Control Tower dynamic improvement and comparative rendering.
    """
    from sage.experimental.act.continuity_control import (
        DeveloperWorkflowOrchestrator,
        ContinuityControlLoop
    )
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output_1 = tmp_path / "evidence" / "ccl_run_1.json"
    evidence_output_2 = tmp_path / "evidence" / "ccl_run_2.json"

    # Set up loop and managers
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    # --- RUN 1: Baseline Workflow Generation ---
    session_1 = session_mgr.create_session(
        session_id="session_cycle_run_1",
        active_objectives=["obj_optimization_cycle_test"]
    )
    session_1.add_completed_action("task_git_scan")
    # Force duplicate work to trigger redundant reassessment metrics
    session_1.pending_actions.append("task_git_scan")
    session_mgr.save_session(session_1)

    orchestrator_1 = DeveloperWorkflowOrchestrator(
        session_id="session_cycle_run_1",
        objective="obj_optimization_cycle_test",
        ccl=ccl,
        evidence_output_path=str(evidence_output_1)
    )

    result_1 = orchestrator_1.execute_active_development_coordination(
        action_taken="Run 1 Baseline execution with simulated friction",
        decision_reasoning="Establish operational baselines",
        workflow_friction=[{"type": "cognitive_load", "detail": "high manual step coordination", "severity": "medium"}],
        improvement_opportunities=["Automate step transitioning"]
    )

    # Validate baseline metrics
    metrics_1 = result_1["operational_intelligence"]["metrics"]
    assert metrics_1["unnecessary_reassessment_events"] == 1
    assert metrics_1["repeated_execution_prevention"] is False

    # Force serialize record_1 into history so Run 2 reads it as a baseline
    record_1_id = result_1["ccl_record"]["record_id"]
    record_1_file = record_storage / f"{record_1_id}.json"
    assert record_1_file.exists()

    # --- RUN 2: Optimized Workflow Generation ---
    # Create optimized session with no duplicate actions and zero friction
    session_2 = session_mgr.create_session(
        session_id="session_cycle_run_2",
        active_objectives=["obj_optimization_cycle_test"]
    )
    session_2.add_completed_action("task_git_scan")
    session_mgr.save_session(session_2)

    orchestrator_2 = DeveloperWorkflowOrchestrator(
        session_id="session_cycle_run_2",
        objective="obj_optimization_cycle_test",
        ccl=ccl,
        evidence_output_path=str(evidence_output_2)
    )

    # Let's execute Run 2 coordination cleanly
    result_2 = orchestrator_2.execute_active_development_coordination(
        action_taken="Run 2 Optimized execution with resolved friction",
        decision_reasoning="Apply and evaluate advisory recommendations",
        workflow_friction=[], # resolved
        improvement_opportunities=[]
    )

    # --- VALIDATION OF MEASURABLE ADVANTAGE ---
    op_intel_2 = result_2["operational_intelligence"]
    metrics_2 = op_intel_2["metrics"]
    trends_2 = op_intel_2["optimization_trends"]
    patterns_2 = op_intel_2["patterns"]
    recs_2 = op_intel_2["recommendations"]

    # 1. Recommendation Quality and Workflow Learning Quality
    assert len(patterns_2) >= 1
    cognitive_pattern = next(p for p in patterns_2 if "cognitive_load" in p["description"])
    assert cognitive_pattern["frequency"] == 1  # From Run 1
    assert len(cognitive_pattern["evidence_records"]) == 1
    assert record_1_id in cognitive_pattern["evidence_records"]

    # 2. Optimization Effectiveness
    # Reduction in duplicate actions should yield positive optimization metrics
    assert metrics_2["unnecessary_reassessment_events"] == 0
    assert metrics_2["repeated_execution_prevention"] is True
    assert trends_2["duplicate_work_reduction_pct"] > 0.0
    assert trends_2["cumulative_improvement_pct"] > 0.0

    # 3. Control Tower Improvement and Comparative view
    dashboard_2 = orchestrator_2.render_control_tower_summary(result_2)
    assert "CONTINUOUS OPTIMIZATION DASHBOARD" in dashboard_2
    assert "How are we improving?" in dashboard_2
    assert f"[Duplicate Work Reduc] :: +100.00%" in dashboard_2
    assert "[Cumulative Optimizer]" in dashboard_2


def test_external_agent_connection_bridge(tmp_path):
    """Verify SAGE state retrieval and write-back connection bridge for external agents.

    Validates:
    - SAGE Interface Contract: retrieve_external_agent_context retrieves mission state,
      workflow state, ownership, authorization boundaries, evidence history, and next required actions.
    - Write-Back Path: submit_external_agent_output validates agent permissions,
      updates session state, captures evidence via SAGE-CCL, and returns validated coordination results.
    """
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_bridge_feedback.json"

    # Set up loop and orchestrator
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_bridge_test",
        objective="obj_test_external_bridge",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # 1. Test Interface Contract (Retrieve Context)
    context = orchestrator.retrieve_external_agent_context()
    assert context["active_mission_state"]["session_id"] == "session_bridge_test"
    assert "obj_test_external_bridge" in context["active_mission_state"]["active_objectives"]
    assert context["ownership"]["assigned_agent"] == "agent_jules_sage"
    assert "sage/runtime/" in context["authorization_boundaries"]["protected_namespaces"]
    assert context["next_required_action"] == "Fulfill active objectives and record initial baseline coordination"

    # 2. Test Write-Back Path (Submit Agent Output)
    # Attempt unauthorized agent write-back (should fail)
    import pytest
    with pytest.raises(PermissionError, match="Unauthorized agent"):
        orchestrator.submit_external_agent_output(
            agent_id="agent_rogue_hacker",
            action_taken="Mutate core",
            decision_reasoning="Bypass"
        )

    # Submit valid agent output
    result = orchestrator.submit_external_agent_output(
        agent_id="agent_coord_chatgpt",
        action_taken="ChatGPT external session coordination complete",
        decision_reasoning="Link external agent sessions into durable SAGE state",
        completed_action="task_bridge_setup",
        pending_action="task_bridge_verify"
    )

    # Validate state update
    assert "task_bridge_setup" in orchestrator.session.completed_actions
    assert "task_bridge_verify" in orchestrator.session.pending_actions

    # Validate SAGE-CCL evidence generation
    assert result["status"] == "VALIDATED"
    assert result["ccl_record"]["action_taken"] == "ChatGPT external session coordination complete"
    assert result["ccl_record"]["evidence_payload"]["human_approval_record"]["supervisor_id"] == "supervisor_external_agent"

    # Validate Google account link and workspace synchronization
    assert "google_account_link" in result
    assert result["google_account_link"]["agent_identity_linked"] == "agent_coord_chatgpt"
    assert result["google_account_link"]["linked_account_status"] in ["synced", "dry_run_authorized", "offline_fallback"]


def test_sage_intelligence_augmentation_and_continuity_layer(tmp_path):
    """Verify SAGE Intelligence Augmentation, Agent Binding, Search, Reasoning, and Rehydration.

    Validates:
    - Reusable Agent Runtime Binding (ChatGPT, Jules, Claude, Gemini).
    - Super Search Capability (source ref, confidence, relevance mapping).
    - SAGE Context Enhancement before agent execution.
    - Evidence-Aware Reasoning with unsupported conclusions filtration.
    - Persistent state restoration (Context rehydration and session recovery).
    """
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_intel_feedback.json"

    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_intel_test",
        objective="obj_test_intel_layer",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # 1. Test Agent Runtime Binding
    binding_chatgpt = orchestrator.register_agent_runtime_binding(
        agent_id="agent_coord_chatgpt",
        role="Coordinator",
        governance_tier="TIER_1_COORDINATOR"
    )
    assert binding_chatgpt["role"] == "Coordinator"
    assert binding_chatgpt["governance_tier"] == "TIER_1_COORDINATOR"

    binding_jules = orchestrator.register_agent_runtime_binding(
        agent_id="agent_exec_jules",
        role="Executor",
        governance_tier="TIER_1_COORDINATOR"
    )
    assert binding_jules["role"] == "Executor"

    # 2. Execute an initial run to establish persistent history record
    result = orchestrator.execute_active_development_coordination(
        action_taken="Initial setup action for intelligence test",
        decision_reasoning="Setup baseline records",
        workflow_friction=[{"type": "cognitive_load", "detail": "manual rehydration of files", "severity": "medium"}],
        improvement_opportunities=["Auto-scan workspace"]
    )
    record_id = result["ccl_record"]["record_id"]

    # 3. Test SAGE Super Search
    search_results = orchestrator.execute_super_search("cognitive_load")
    assert len(search_results) >= 1
    match = search_results[0]
    assert match["source_reference"] == record_id
    assert match["confidence"] > 0.0
    assert "Matches friction" in match["relevance"]

    # 4. Test Context Enhancement
    enhanced_context = orchestrator.enhance_agent_execution_context()
    assert enhanced_context["current_mission"]["session_id"] == "session_intel_test"
    assert "Frozen Core Production Protection active." in enhanced_context["required_constraints"]
    assert record_id in enhanced_context["relevant_history"]

    # 5. Test Evidence-Aware Reasoning
    reasoning = orchestrator.request_evidence_aware_reasoning("How to address manual rehydration friction?")
    assert reasoning["question"] == "How to address manual rehydration friction?"
    assert len(reasoning["evidence_retrieved"]) >= 1
    assert "modular workspace caching" in reasoning["advisory_recommendation"]["description"]
    assert reasoning["advisory_recommendation"]["confidence_level"] == 0.85

    # Filter unsupported conclusion (empty results query)
    empty_reasoning = orchestrator.request_evidence_aware_reasoning("unrelated random keyword")
    assert "No preceding operational evidence found" in empty_reasoning["advisory_recommendation"]["description"]
    assert empty_reasoning["advisory_recommendation"]["confidence_level"] == 0.1

    # 6. Test Persistent state rehydration (Session reset simulation)
    new_orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_intel_test_recovered",
        objective="obj_fresh_unloaded",
        ccl=ContinuityControlLoop(session_manager=SessionStateManager(storage_path=str(session_storage)), storage_path=str(record_storage)),
        evidence_output_path=str(evidence_output)
    )

    rehydrated = new_orchestrator.rehydrate_persistent_session_state()
    assert rehydrated["restored"] is True
    assert rehydrated["restored_record_id"] == record_id
    assert "obj_test_intel_layer" in rehydrated["active_mission"]
    assert rehydrated["workflow_position"]["completed_actions"] == []


def test_sage_managed_agent_operating_loop(tmp_path):
    """Verify SAGE-managed agent operating loop (context package retrieval and result submission).

    Validates:
    - Context package retrieval with identity, role, objectives, and Super Search injected intelligence.
    - Security / Permission Boundaries: Unauthorized agent requests are strictly blocked.
    - Intelligence-assisted result submission with evidence check and context state update.
    - Upgraded Control Tower Dashboards rendering intelligence Q&As.
    """
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_loop_feedback.json"

    # Set up loop and managers
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_loop_test",
        objective="obj_test_agent_execution",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # Pre-register agent runtime binding
    orchestrator.register_agent_runtime_binding(
        agent_id="agent_coord_chatgpt",
        role="Coordinator",
        governance_tier="TIER_1_COORDINATOR"
    )

    # 1. Test Context Package Retrieval
    context_package = orchestrator.request_agent_context_package(agent_id="agent_coord_chatgpt")
    assert context_package["agent_identity"]["agent_id"] == "agent_coord_chatgpt"
    assert context_package["agent_identity"]["role"] == "Coordinator"
    assert "obj_test_agent_execution" in context_package["active_mission"]["active_objectives"]
    assert "injected_intelligence" in context_package
    assert context_package["next_required_action"] == "Complete coordination loop and submit validated result package"

    # Verify that a CCL record was generated for context request
    history_records = list(record_storage.glob("*.json"))
    assert len(history_records) >= 1

    # 2. Test Permission Boundary Enforcement
    import pytest
    with pytest.raises(PermissionError, match="Unauthorized agent"):
        orchestrator.request_agent_context_package(agent_id="agent_malicious_attacker")

    # 3. Test Intelligence-Assisted Result Submission
    result = orchestrator.submit_intelligence_assisted_agent_response(
        agent_id="agent_coord_chatgpt",
        action_taken="Completed joint research subtask",
        decision_reasoning="Fulfill coordinator requirements under SAGE-managed session state",
        workflow_friction=[{"type": "api_drift", "detail": "redundant proposal loops", "severity": "low"}],
        completed_action="task_research_complete"
    )

    # Validate state update
    assert "task_research_complete" in orchestrator.session.completed_actions
    assert result["status"] == "VALIDATED"
    assert result["ccl_record"]["action_taken"] == "Completed joint research subtask"

    # 4. Verify Control Tower Dashboard displays intelligence Q&As
    dashboard = orchestrator.render_control_tower_summary(result)
    assert "SAGE INTELLIGENCE LAYER Q&A:" in dashboard
    assert "Q1: What information helped this decision?" in dashboard
    assert "Q2: What previous evidence supports this?" in dashboard
    assert "Q3: What similar problems were solved before?" in dashboard
    assert "Q4: What improvement was created?" in dashboard


def test_sage_continuous_mission_execution_loop(tmp_path):
    """Verify SAGE Autonomous Continuous Mission Execution Loop.

    Validates:
    - Mission Queue & Backlog: Append and serialize structured backlog objectives.
    - Discovery-to-Task Handoff: Automate transition from discovery candidates to backlog tasks.
    - Autonomous Execution Cycle: Complete sequential loops with SAGE-CCL checkpoints.
    - Human Intervention Gates: Code boundaries freezing the loop on active blockers or consecutive failures.
    """
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager
    from pathlib import Path

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_loop_feedback.json"

    # Set up loop and managers
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_autonomous_loop_test",
        objective="obj_continuous_mission_execution",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # 1. Test Mission Queue appending
    t1 = orchestrator.append_mission_to_queue(objective="Automate pre-commit validations")
    assert t1.objective == "Automate pre-commit validations"
    assert t1.status == "queued"

    t2 = orchestrator.append_mission_to_queue(objective="Refactor local cache buffers")
    assert t2.status == "queued"

    # 2. Test Discovery-to-Task Handoff
    # Create mock discovery candidate
    import json
    register_path = Path("evidence_capture/discovery_candidates_register.json")
    register_path.parent.mkdir(parents=True, exist_ok=True)
    mock_candidates = [{
        "candidate_id": "CANDIDATE-OPT-MOCK1",
        "description": "Optimize state rehydration",
        "operational_justification": "Mitigate session loss during coordinate loops",
        "priority": "HIGH"
    }]
    with open(register_path, "w", encoding="utf-8") as f:
        json.dump(mock_candidates, f, indent=2)

    t3 = orchestrator.handoff_discovery_candidate_to_mission(candidate_id="CANDIDATE-OPT-MOCK1")
    assert "Mitigate session loss" in t3.objective
    assert t3.status == "queued"

    # 3. Test Autonomous Execution Cycle & State Checkpoints
    results = orchestrator.execute_autonomous_mission_loop()
    assert len(results) == 3
    # Verify tasks are marked completed
    queue = orchestrator.session.metadata["mission_queue"]
    assert all(t["status"] == "completed" for t in queue)

    # Verify that SAGE-CCL records were generated for completed tasks
    history_records = list(record_storage.glob("*.json"))
    assert len(history_records) >= 3

    # 4. Test Human Intervention Freeze Gates (Code Contamination / Blocker)
    # Reset queue and append a blocked task
    orchestrator.session.metadata["mission_queue"] = []
    t_blocked = orchestrator.append_mission_to_queue(objective="Process failed or broken module validation")

    results_blocked = orchestrator.execute_autonomous_mission_loop()
    assert len(results_blocked) == 0  # Aborted immediately
    queue_blocked = orchestrator.session.metadata["mission_queue"]
    assert queue_blocked[0]["status"] == "blocked"
    assert "HUMAN INTERVENTION GATED" in queue_blocked[0]["failure_reason"]


def test_sage_operator_override_and_manual_mode(tmp_path):
    """Verify SAGE Operator Override and Manual Control boundaries.

    Validates:
    - Manual operator pause/freeze controls (`pause_mission_execution_loop`).
    - Preservation of state, active objectives, and session position during pause.
    - Blocking/Freezing new execution cycles while in manual mode.
    - Manually redirecting backlog objectives and priority lists.
    - Resuming execution safely from the validated checkpoint record.
    """
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_pause_feedback.json"

    # Set up managers and orchestrator
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_manual_control_test",
        objective="obj_operator_control_validation",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # Ingest a task
    orchestrator.append_mission_to_queue(objective="Task 1: Generate setup documents")

    # 1. Test Manual Operator Pause
    pause_res = orchestrator.pause_mission_execution_loop()
    assert pause_res["status"] == "PAUSED"
    assert pause_res["loop_mode"] == "MANUAL_INTERVENTION_PAUSED"
    assert orchestrator.session.metadata["execution_loop_mode"] == "MANUAL_INTERVENTION_PAUSED"

    # Check SAGE-CCL logged the intervention event
    history_records = list(record_storage.glob("*.json"))
    assert len(history_records) == 1

    # 2. Test Execution Freeze (continuous loop must not run when paused)
    results = orchestrator.execute_autonomous_mission_loop()
    assert len(results) == 0  # Execution was frozen/blocked

    # 3. Test Mission Priority Redirection
    new_tasks = orchestrator.redirect_mission_priorities(new_backlog_objectives=[
        "Task 2: Refactor test suite bounds",
        "Task 3: Output structural metrics"
    ])
    assert len(new_tasks) == 2
    assert orchestrator.session.metadata["mission_queue"][0]["objective"] == "Task 2: Refactor test suite bounds"

    # Verify execution is still frozen because mode is still paused
    results_after_redirect = orchestrator.execute_autonomous_mission_loop()
    assert len(results_after_redirect) == 0

    # 4. Test Resume and Continuation
    resume_res = orchestrator.resume_mission_execution_loop()
    assert resume_res["status"] == "RESUMED"
    assert resume_res["loop_mode"] == "CONTINUOUS_EXECUTION"
    assert orchestrator.session.metadata["execution_loop_mode"] == "CONTINUOUS_EXECUTION"

    # Loop should now process redirected tasks autonomously
    results_after_resume = orchestrator.execute_autonomous_mission_loop()
    assert len(results_after_resume) == 2

    # Verify both completed
    queue = orchestrator.session.metadata["mission_queue"]
    assert all(t["status"] == "completed" for t in queue)

    # Lineage remains fully intact
    history_records_final = list(record_storage.glob("*.json"))
    # 1 pause + 1 resume + 2 task execution records = 4 records
    assert len(history_records_final) == 4


def test_sage_safety_alignment_and_drift_detection(tmp_path):
    """Verify SAGE safety alignment, drift-gates, and failure protection boundaries.

    Validates:
    - SAGE external drift detection on protected core production namespaces.
    - Autonomously freezing loop and locking to MANUAL_INTERVENTION_PAUSED on drift detection.
    - Failure Escalation Protection stopping consecutive runtime loops.
    """
    from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, ContinuityControlLoop
    from sage.acr.session.session_state import SessionStateManager
    from pathlib import Path

    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_safety_feedback.json"

    # Set up loop and managers
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_safety_test",
        objective="obj_safety_validation",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # 1. Test External Drift Detection
    # Mock workspace files scan returning a change in sage/core protected namespace
    def mock_scan():
        return {
            "modified_files": ["sage/core/engine.py", "sage/experimental/act/continuity_control.py"],
            "diffs": {"sage/core/engine.py": "unauthorized edit"}
        }
    orchestrator.scan_git_workspace = mock_scan

    drift_report = orchestrator.detect_external_workspace_drift()
    assert drift_report["drift_detected"] is True
    assert "External Drift Detected" in drift_report["reason"]
    assert "sage/core/engine.py" in drift_report["affected_files"]

    # 2. Test Drift-Gate Loop Abort
    # Ingest task and try to run autonomous loop while drift exists
    orchestrator.append_mission_to_queue(objective="Normal continuous coordination task")

    results = orchestrator.execute_autonomous_mission_loop()
    assert len(results) == 0  # Zero tasks completed

    # Check that loop was blocked and loop mode locked to paused
    queue = orchestrator.session.metadata["mission_queue"]
    assert queue[0]["status"] == "blocked"
    assert "CRITICAL INTEGRITY GATED" in queue[0]["failure_reason"]
    assert orchestrator.session.metadata["execution_loop_mode"] == "MANUAL_INTERVENTION_PAUSED"

    # 3. Test Failure Escalation Protection Stop-Gate
    # Reset queue, clear drift, simulate consecutive failures
    orchestrator.session.metadata["mission_queue"] = []
    orchestrator.session.metadata["execution_loop_mode"] = "CONTINUOUS_EXECUTION"
    orchestrator.scan_git_workspace = lambda: {"modified_files": [], "diffs": {}} # clean

    # Mock submit_external_agent_output to raise an exception simulating task failure
    def mock_fail(*args, **kwargs):
        raise ValueError("Simulated runtime connection failure")
    orchestrator.submit_external_agent_output = mock_fail

    # Append 3 tasks
    orchestrator.append_mission_to_queue(objective="Task 1")
    orchestrator.append_mission_to_queue(objective="Task 2")
    orchestrator.append_mission_to_queue(objective="Task 3")

    results_fail = orchestrator.execute_autonomous_mission_loop()
    assert len(results_fail) == 2 # 2 failed, 3rd blocked by escalation gate before execution

    # Check task statuses
    queue_fail = orchestrator.session.metadata["mission_queue"]
    assert queue_fail[0]["status"] == "failed"
    assert queue_fail[1]["status"] == "failed"
    assert queue_fail[2]["status"] == "blocked"  # Gated by consecutive failures count
    assert "HUMAN INTERVENTION GATED" in queue_fail[2]["failure_reason"]
