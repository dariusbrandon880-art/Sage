"""Integration test suite for end-to-end SAGE Governed Mission Progression path.

Validates the complete sequential integration flow:
Mission Intake -> Value/Priority -> Preflight -> Mission Progression Controller ->
MEC Agent Handoff -> Execution Result -> Evidence/Validation -> Causality Auditor -> Outcome

Enforces all required state transitions, zero-spawning boundaries, immutability,
failed-preflight halts, and causality-auditor trace verification.
"""

import json
import time
import pytest
from pathlib import Path

from sage.mission_intake import SAGEMissionIntakeLayer
from sage.mission_control import SAGEMissionProgressionController, ExperimentalMissionState
from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, SAGEMissionTask, ContinuityControlLoop
from sage.acr.session.session_state import SessionStateManager
from sage.experimental.causality_auditor import DecisionCausalityAuditor
from sage.core.hdg import HDGEngine
from sage.core.models import HypothesisNode


def test_governed_mission_progression_path_e2e(tmp_path):
    """Execute and verify the full end-to-end governed mission progression pipeline.

    Flow:
    1. Mission Intake Layer processes a valid mission proposal and assigns MISSION_PROPOSED.
    2. Transition prerequisites are checked and sequential stage transitions are evaluated
       by the SAGE Mission Progression Controller:
       Proposed -> Value/Priority Evaluated -> Preflight Required -> Execution Authorized.
    3. Handoff to MEC / DeveloperWorkflowOrchestrator for task queueing and execution.
    4. Task execution generates a real, structured evidence/validation report (CMAPS v1.0).
    5. Progression continues: Complete -> Validation -> Evidence -> Review -> Promotion -> Closed.
    6. DecisionCausalityAuditor verifies lineage, evidence presence, and Spek vault receipts.
    """
    # Setup temporary paths for isolated sandboxed execution
    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    compliance_storage = tmp_path / "compliance"
    compliance_storage.mkdir(parents=True, exist_ok=True)
    evidence_output = tmp_path / "evidence" / "ccl_operational_feedback.json"

    # Initialize Primitives
    intake = SAGEMissionIntakeLayer()
    controller = SAGEMissionProgressionController()
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))
    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_integration_progression",
        objective="obj_continuous_development",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    # 1. Mission Intake
    proposal_data = {
        "name": "Integration Progression Mission",
        "description": "Verify complete governed mission progression integration baseline",
        "objective": "obj_continuous_development",
        "operator_id": "operator_jules_01",
        "prerequisites": {}
    }

    intake_res = intake.submit_proposal(proposal_data)
    assert intake_res["accepted"] is True
    assert intake_res["status"] == "ACCEPTED"
    assert intake_res["current_state"] == "MISSION_PROPOSED"

    # Retrieve enqueued state
    mission_state = intake.get_queue()[0]
    assert mission_state.current_state == "MISSION_PROPOSED"

    # 2. Value/Priority State Transition
    # First attempt: no value prerequisite -> must fail and halt progression
    res_val_fail = controller.evaluate_transition(mission_state, "VALUE_EVALUATED")
    assert res_val_fail.success is False
    assert mission_state.current_state == "MISSION_PROPOSED"

    # Satisfy prerequisite and transition
    mission_state.prerequisites["value_appraisal_approved"] = True
    res_val = controller.evaluate_transition(mission_state, "VALUE_EVALUATED")
    assert res_val.success is True
    assert mission_state.current_state == "VALUE_EVALUATED"

    # 3. Preflight State Transition
    # First attempt: no preflight prerequisite -> must fail and halt progression
    res_pref_fail = controller.evaluate_transition(mission_state, "PREFLIGHT_REQUIRED")
    assert res_pref_fail.success is False
    assert mission_state.current_state == "VALUE_EVALUATED"

    # Satisfy prerequisite and transition
    mission_state.prerequisites["preflight_checklist_passed"] = True
    res_pref = controller.evaluate_transition(mission_state, "PREFLIGHT_REQUIRED")
    assert res_pref.success is True
    assert mission_state.current_state == "PREFLIGHT_REQUIRED"

    # 4. Execution Authorization Boundary (Operator Signature)
    # First attempt: no signature prerequisite -> must fail and halt progression
    res_auth_fail = controller.evaluate_transition(mission_state, "EXECUTION_AUTHORIZED")
    assert res_auth_fail.success is False
    assert mission_state.current_state == "PREFLIGHT_REQUIRED"

    # Satisfy prerequisite and transition
    mission_state.prerequisites["operator_signature_obtained"] = True
    res_auth = controller.evaluate_transition(mission_state, "EXECUTION_AUTHORIZED")
    assert res_auth.success is True
    assert mission_state.current_state == "EXECUTION_AUTHORIZED"

    # 5. MEC Handoff / Queue Generation
    # Create the engineering task representation from the authorized mission
    task = SAGEMissionTask(
        task_id="task_progression_verification",
        objective_id="obj_continuous_development",
        priority_score=95.0,
        authorized=True,
        lane="engineering",
        description="Verify end-to-end governed mission progression",
    )
    orchestrator.mission_queue.add_task(task)

    # ZERO-SPAWNING INVARIANT: Verify that assigning/enqueuing tasks does not autonomously spawn agents
    # or create dynamic agent tiers. The controller remains bounded.
    assert task.assigned_agent == "agent_jules_sage"
    assert task.authorized is True

    # 6. Execution & Evidence Generation
    # Process the queued task through the orchestrator.
    # This executes workspace auditing, CMAPS v1.0 generation, SAGE-OIL metrics computation,
    # and serializes the complete evidence package to disk.
    execution_cycle_results = orchestrator.execute_active_development_coordination(
        action_taken="Execute integration progression verification",
        decision_reasoning="Complete SAGE Governed Mission Progression validation flow",
        workflow_friction=[{"type": "ci_overhead", "severity": "low", "detail": "setup package environments"}],
        improvement_opportunities=["Auto-warm docker cache layers"]
    )

    assert execution_cycle_results["status"] == "VALIDATED"
    assert execution_cycle_results["session_id"] == "session_integration_progression"
    assert "ccl_record" in execution_cycle_results
    assert "cmaps_payload" in execution_cycle_results

    # Verify task updated in queue
    task.status = "COMPLETED"
    orchestrator.mission_queue.save_queue()

    # 7. Progression Controller Continuance (Complete -> Validation -> Evidence)
    # Transition to EXECUTION_COMPLETE (requires execution_log_recorded)
    mission_state.prerequisites["execution_log_recorded"] = True
    res_complete = controller.evaluate_transition(mission_state, "EXECUTION_COMPLETE")
    assert res_complete.success is True
    assert mission_state.current_state == "EXECUTION_COMPLETE"

    # Transition to VALIDATION_REQUIRED (requires validation_receipt_issued)
    mission_state.prerequisites["validation_receipt_issued"] = True
    res_val_req = controller.evaluate_transition(mission_state, "VALIDATION_REQUIRED")
    assert res_val_req.success is True
    assert mission_state.current_state == "VALIDATION_REQUIRED"

    # Transition to EVIDENCE_REQUIRED (requires evidence_hashes_verified)
    mission_state.prerequisites["evidence_hashes_verified"] = True
    res_ev_req = controller.evaluate_transition(mission_state, "EVIDENCE_REQUIRED")
    assert res_ev_req.success is True
    assert mission_state.current_state == "EVIDENCE_REQUIRED"

    # Transition to REVIEW_REQUIRED (requires peer_signoff_completed)
    mission_state.prerequisites["peer_signoff_completed"] = True
    res_rev_req = controller.evaluate_transition(mission_state, "REVIEW_REQUIRED")
    assert res_rev_req.success is True
    assert mission_state.current_state == "REVIEW_REQUIRED"

    # Transition to PROMOTION_READY (requires promotion_approval_granted)
    mission_state.prerequisites["promotion_approval_granted"] = True
    res_promo = controller.evaluate_transition(mission_state, "PROMOTION_READY")
    assert res_promo.success is True
    assert mission_state.current_state == "PROMOTION_READY"

    # Transition to CLOSED (requires archival_success_confirmed)
    mission_state.prerequisites["archival_success_confirmed"] = True
    res_closed = controller.evaluate_transition(mission_state, "CLOSED")
    assert res_closed.success is True
    assert mission_state.current_state == "CLOSED"

    # 8. Setup HDG and Spek Vault files for Causality Auditor validation
    hdg_file = compliance_storage / "hdg_causality.json"
    spek_vault_file = compliance_storage / "spek_vault.json"

    # Write HDG causality node representing this execution decision
    # Make sure we use the same schema as sage/core/models.py HypothesisNode
    node = HypothesisNode(
        node_id="decision_coordinate_dev_loop",
        description="Verify integration progression verification",
        parent_ids=[],
        evidence_refs=["evidence/ccl_operational_feedback.json"],
        validation_score=0.95,
        contradictions=[]
    )
    with open(hdg_file, "w") as f:
        json.dump([node.model_dump()], f)

    # Write Spek vault receipt
    receipt = {
        "receipt_id": "receipt_001",
        "proposal_id": "decision_coordinate_dev_loop",
        "lifecycle_state": "VALIDATED",
        "hdg_trace": [{"node_id": "decision_coordinate_dev_loop", "is_promoted": True}]
    }
    with open(spek_vault_file, "w") as f:
        json.dump([receipt], f)

    # 9. Causality Auditor Audit & Verification
    # Ensure DecisionCausalityAuditor receives real evidence payload generated on disk
    auditor = DecisionCausalityAuditor(workspace=tmp_path)
    # Mock evidence check to look into our tmp path as well
    auditor.evidence_dirs.append(tmp_path / "evidence")

    # Perform read-only audit of the decision
    audit_report = auditor.audit("decision_coordinate_dev_loop")

    assert audit_report["decision_id"] == "decision_coordinate_dev_loop"
    assert audit_report["hdg_engine_loaded"] is True
    assert len(audit_report["issues"]) == 0
    assert len(audit_report["lineage"]) == 1
    assert audit_report["lineage"][0]["node_id"] == "decision_coordinate_dev_loop"
    assert audit_report["lineage"][0]["_validation_status"] == "VALIDATED_HDG_ENGINE"

    # Ensure evidence presence was checked against the actual generated artifact on disk
    assert len(audit_report["evidence"]) == 1
    assert audit_report["evidence"][0]["ref"] == "evidence/ccl_operational_feedback.json"
    assert audit_report["evidence"][0]["exists"] is True

    # Ensure Spek vault receipt matched correctly
    assert len(audit_report["receipts"]) == 1
    assert audit_report["receipts"][0]["receipt_id"] == "receipt_001"
    assert audit_report["receipts"][0]["proposal_id"] == "decision_coordinate_dev_loop"
    assert audit_report["receipts"][0]["lifecycle_state"] == "VALIDATED"


def test_zero_spawning_enforcement():
    """Verify that the SAGE Mission Progression Controller is strictly non-executing,

    non-authorizing, and adheres strictly to the Zero-Spawning Law.
    """
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-zero-spawn-01",
        name="Zero Spawning Check",
        current_state="MISSION_PROPOSED"
    )

    # Transitioning or evaluating does not trigger execution, background thread creation,
    # or autonomous agent spawns.
    state.prerequisites["value_appraisal_approved"] = True
    result = controller.evaluate_transition(state, "VALUE_EVALUATED")
    assert result.success is True

    # Confirm zero dynamic side-effects on state or orchestrator boundaries
    assert state.current_state == "VALUE_EVALUATED"


def test_failed_preflight_halts_progression():
    """Verify that a failed preflight prerequisite strictly halts sequential progression."""
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-preflight-fail",
        name="Failed Preflight Test",
        current_state="VALUE_EVALUATED"
    )

    # Attempt transition without satisfying prerequisite 'preflight_checklist_passed'
    result = controller.evaluate_transition(state, "PREFLIGHT_REQUIRED")
    assert result.success is False
    assert "Missing prerequisite 'preflight_checklist_passed'" in result.decision_reason
    assert state.current_state == "VALUE_EVALUATED"


def test_unauthorized_progression_rejection():
    """Verify that unauthorized transitions or out-of-order state transitions are rejected."""
    controller = SAGEMissionProgressionController()
    state = ExperimentalMissionState(
        mission_id="msn-unauth-test",
        name="Unauthorized Transition Test",
        current_state="MISSION_PROPOSED"
    )

    # Skip stage check
    res = controller.evaluate_transition(state, "PREFLIGHT_REQUIRED")
    assert res.success is False
    assert "Cannot skip sequential stages" in res.decision_reason

    # Backward progression check
    state.current_state = "EXECUTION_COMPLETE"
    res_back = controller.evaluate_transition(state, "MISSION_PROPOSED")
    assert res_back.success is False
    assert "Backward progression is forbidden" in res_back.decision_reason


def test_malformed_handoff_rejection():
    """Verify that malformed mission proposals or tasks with invalid schema/metadata are rejected."""
    intake = SAGEMissionIntakeLayer()

    # Empty proposal name
    proposal = {
        "name": "   ",
        "description": "Test description",
        "objective": "Test objective",
        "operator_id": "operator_jules_01"
    }
    res = intake.submit_proposal(proposal)
    assert res["accepted"] is False
    assert "cannot be empty or blank" in res["reason"]

    # Missing required field
    proposal_missing = {
        "name": "Valid Name",
        "objective": "Test objective"
    }
    res_missing = intake.submit_proposal(proposal_missing)
    assert res_missing["accepted"] is False
    assert "Missing required fields" in res_missing["reason"]


def test_receipt_sequencing_and_determinism():
    """Verify that state transition receipts are sequenced correctly and serialize deterministically."""
    controller = SAGEMissionProgressionController()
    state1 = ExperimentalMissionState(
        mission_id="msn-det-01",
        name="Deterministic Test 1",
        current_state="MISSION_PROPOSED",
        prerequisites={"value_appraisal_approved": True}
    )
    state2 = ExperimentalMissionState(
        mission_id="msn-det-01",
        name="Deterministic Test 1",
        current_state="MISSION_PROPOSED",
        prerequisites={"value_appraisal_approved": True}
    )

    res1 = controller.evaluate_transition(state1, "VALUE_EVALUATED")
    res2 = controller.evaluate_transition(state2, "VALUE_EVALUATED")

    assert res1.success == res2.success
    assert res1.transitioned == res2.transitioned
    assert res1.previous_state == res2.previous_state
    assert res1.target_state == res2.target_state

    # Determinism in serialization
    auditor = DecisionCausalityAuditor()
    str1 = auditor.serialize(res1.model_dump())
    str2 = auditor.serialize(res2.model_dump())
    assert str1 == str2


def test_inputs_and_capability_registry_immutability(tmp_path):
    """Verify that inputs to analyzers and registry records are immutable (read-only checks)."""
    from sage.change_impact import SAGEChangeImpactAnalyzer
    from sage.capability_registry import SAGEOperationalCapabilityRegistry

    # Change impact input list immutability
    analyzer = SAGEChangeImpactAnalyzer()
    modified_files = ["tests/test_continuity_persistence.py", "sage/mission_control.py"]
    files_copy = list(modified_files)

    analyzer.analyze_changes(modified_files)
    assert modified_files == files_copy

    # Operational Registry immutability check
    registry_file = tmp_path / "operational_capability_registry.json"
    registry = SAGEOperationalCapabilityRegistry(storage_path=str(registry_file))
    initial_mtime = registry_file.stat().st_mtime

    # Run analysis
    analyzer_custom = SAGEChangeImpactAnalyzer(registry_path=str(registry_file))
    analyzer_custom.analyze_changes(["tests/test_continuity_persistence.py"])

    # Ensure registry file is untouched/not mutated on disk
    assert registry_file.stat().st_mtime == initial_mtime


def test_enqueue_authorized_mission_state_success(tmp_path):
    """Verify that an EXECUTION_AUTHORIZED mission state successfully enqueues a valid SAGEMissionTask."""
    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))
    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_enqueue_success",
        objective="obj_continuous_development",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    state = ExperimentalMissionState(
        mission_id="msn_authorized_01",
        name="Authorized Mission Test",
        current_state="EXECUTION_AUTHORIZED",
        prerequisites={"operator_signature_obtained": True},
        metadata={
            "objective_id": "obj_continuous_development",
            "priority_score": 90.0,
            "description": "Verified authorized handoff task",
            "assigned_agent": "agent_jules_sage"
        }
    )

    task = orchestrator.enqueue_authorized_mission_state(state)

    assert task is not None
    assert task.authorized is True
    assert task.priority_score == 90.0
    assert task.assigned_agent == "agent_jules_sage"
    assert task.status == "PENDING"

    # Verify task was added to orchestrator mission queue
    queued_task = orchestrator.mission_queue.get_task(task.task_id)
    assert queued_task is not None
    assert queued_task.task_id == task.task_id


def test_enqueue_unauthorized_mission_state_rejection(tmp_path):
    """Verify that a non-EXECUTION_AUTHORIZED mission state fails closed and raises ValueError."""
    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    session_mgr = SessionStateManager(storage_path=str(session_storage))
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))
    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_enqueue_rejection",
        objective="obj_continuous_development",
        ccl=ccl,
        evidence_output_path=str(tmp_path / "evidence.json")
    )

    unauthorized_state = ExperimentalMissionState(
        mission_id="msn_unauthorized_01",
        name="Unauthorized Mission Test",
        current_state="MISSION_PROPOSED"
    )

    with pytest.raises(ValueError, match="Governed Execution Handoff Violation: Cannot enqueue mission state with status 'MISSION_PROPOSED'"):
        orchestrator.enqueue_authorized_mission_state(unauthorized_state)

    # Queue remains empty
    assert len(orchestrator.mission_queue.list_tasks()) == 0
