"""Unit test suite for SAGE Cognitive Kernel and Prefrontal Cortex (PFC) Simulator."""

import time
import pytest
from pathlib import Path
from sage.acr.session.session_state import SessionStateManager, SessionState
from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, SAGEMissionTask
from sage.experimental.cognitive import (
    CognitiveAgentIdentity,
    CognitiveActiveMission,
    CognitiveValidatedFact,
    CognitiveCompletedMilestone,
    CognitiveForbiddenRegression,
    CognitiveOperatorConstraints,
    CognitiveConfidenceState,
    CognitiveNextAction,
    CognitiveState,
    PrefrontalCortexSimulator,
    DecisionGateOutcome,
    CognitiveStateLoader,
    ContinuityRetrievalInterface,
    PFCGovernedExecutor,
    OpenAICognitiveRuntimeActivator,
)


@pytest.fixture
def base_cognitive_state() -> CognitiveState:
    """Fixture to provide a standard approved base CognitiveState."""
    agent = CognitiveAgentIdentity(
        agent_id="agent_jules_sage",
        name="Jules",
        role="Senior Software Engineer",
        authority_level="TIER_1_COORDINATOR",
        governance_tier="TIER_1_COORDINATOR",
    )
    mission = CognitiveActiveMission(
        mission_id="mission_kernel_v1",
        objective="Develop the SAGE Cognitive Kernel foundation and prefrontal cortex simulator",
        milestones=["task_pfc_gate", "task_state_schema"],
        status="RUNNING",
    )
    fact = CognitiveValidatedFact(
        fact_id="fact_pfc_design",
        statement="Prefrontal Cortex architecture uses four safety gates",
        evidence_references=["doc_pfc_spec", "audit_pfc_gate_01"],
        confidence_score=1.0,
    )
    milestone = CognitiveCompletedMilestone(
        milestone_id="task_state_schema",
        completed_at=time.time() - 3600.0,
        evidence_hash="hash_state_schema_v1_validated",
        reopened_count=0,
    )
    forbidden = CognitiveForbiddenRegression(
        regression_id="regr_loop_prevention",
        description="Do not repeat the state planning loops indefinitely",
        restricted_actions=["unauthorized_replan"],
    )
    constraints = CognitiveOperatorConstraints(
        permitted_paths=["sage/experimental/cognitive/"],
        forbidden_paths=["sage/runtime/"],
        requires_approval=True,
        max_consecutive_failures=3,
        authorized_agents=["agent_jules_sage"],
    )
    confidence = CognitiveConfidenceState(
        overall_confidence=1.0,
        last_updated=time.time(),
        notes="Pruned baseline and validated schema",
    )
    next_action = CognitiveNextAction(
        action_id="task_pfc_gate",
        description="Develop and test the PFC simulator and gates",
        assigned_agent="agent_jules_sage",
        required_evidence=["audit_pfc_gate_01"],
    )

    return CognitiveState(
        agent_identity=agent,
        active_mission=mission,
        validated_facts=[fact],
        completed_milestones=[milestone],
        forbidden_regressions=[forbidden],
        operator_constraints=constraints,
        confidence_state=confidence,
        next_action=next_action,
    )


def test_valid_mission_proceeds(base_cognitive_state):
    """Verify that a standard, fully aligned, authorized, and evidenced mission is allowed to PROCEED."""
    simulator = PrefrontalCortexSimulator()
    report = simulator.evaluate_decision(base_cognitive_state)

    assert report.outcome == DecisionGateOutcome.PROCEED
    assert "aligns with active mission" in report.reason
    assert report.checks_performed["mission_alignment"] is True
    assert report.checks_performed["completed_work_protection"] is True
    assert report.checks_performed["constraint_validation"] is True
    assert report.checks_performed["evidence_requirement_detection"] is True


def test_completed_milestone_reopening_blocked(base_cognitive_state):
    """Verify that attempting to re-execute or reopening a completed milestone is BLOCKED."""
    simulator = PrefrontalCortexSimulator()

    # Propose next action that targets an already completed milestone
    base_cognitive_state.next_action = CognitiveNextAction(
        action_id="task_state_schema",  # Already in completed_milestones
        description="Re-execute task_state_schema schema creation",
        assigned_agent="agent_jules_sage",
    )

    report = simulator.evaluate_decision(base_cognitive_state)
    assert report.outcome == DecisionGateOutcome.BLOCK
    assert "Completed milestone reopening/modification blocked" in report.reason


def test_missing_context_requests_clarification(base_cognitive_state):
    """Verify that proposed actions with missing description or missing required evidence request clarification."""
    simulator = PrefrontalCortexSimulator()

    # 1. Test missing proposed action
    base_cognitive_state.next_action = None
    report_no_action = simulator.evaluate_decision(base_cognitive_state)
    assert report_no_action.outcome == DecisionGateOutcome.REQUEST_CLARIFICATION
    assert "No next action proposed" in report_no_action.reason

    # 2. Test blank description in proposed action (missing context)
    base_cognitive_state.next_action = CognitiveNextAction(
        action_id="task_pfc_gate",
        description="",
        assigned_agent="agent_jules_sage",
    )
    report_blank_desc = simulator.evaluate_decision(base_cognitive_state)
    assert report_blank_desc.outcome == DecisionGateOutcome.REQUEST_CLARIFICATION
    assert "missing crucial context" in report_blank_desc.reason

    # 3. Test missing required evidence
    base_cognitive_state.next_action = CognitiveNextAction(
        action_id="task_pfc_gate",
        description="Develop and test the PFC simulator and gates",
        assigned_agent="agent_jules_sage",
        required_evidence=["missing_evidence_audit_token"],
    )
    report_missing_evidence = simulator.evaluate_decision(base_cognitive_state)
    assert report_missing_evidence.outcome == DecisionGateOutcome.REQUEST_CLARIFICATION
    assert "requires evidence references" in report_missing_evidence.reason


def test_invalid_authority_blocked(base_cognitive_state):
    """Verify that actions proposed by an agent with invalid authority or unauthorized identifier are BLOCKED."""
    simulator = PrefrontalCortexSimulator()

    # 1. Agent not in authorized_agents list
    base_cognitive_state.operator_constraints.authorized_agents = ["authorized_supervisor_node"]
    report_unauthorized_id = simulator.evaluate_decision(base_cognitive_state)
    assert report_unauthorized_id.outcome == DecisionGateOutcome.BLOCK
    assert "is not in the operator's authorized agents list" in report_unauthorized_id.reason

    # Restore authorized agent for next check
    base_cognitive_state.operator_constraints.authorized_agents = ["agent_jules_sage"]

    # 2. Agent with UNAUTHORIZED authority level
    base_cognitive_state.agent_identity.authority_level = "UNAUTHORIZED"
    report_unauthorized_level = simulator.evaluate_decision(base_cognitive_state)
    assert report_unauthorized_level.outcome == DecisionGateOutcome.BLOCK
    assert "has invalid or unauthorized authority level" in report_unauthorized_level.reason


def test_confidence_state_recorded(base_cognitive_state):
    """Verify that the simulator records the confidence state accurately in the decision report."""
    simulator = PrefrontalCortexSimulator()

    # Test baseline confidence recording
    base_cognitive_state.confidence_state.overall_confidence = 0.95
    report = simulator.evaluate_decision(base_cognitive_state)
    assert report.confidence_recorded == 0.95

    # Test that confidence below 0.5 triggers REQUEST_CLARIFICATION
    base_cognitive_state.confidence_state.overall_confidence = 0.4
    low_confidence_report = simulator.evaluate_decision(base_cognitive_state)
    assert low_confidence_report.outcome == DecisionGateOutcome.REQUEST_CLARIFICATION
    assert "Confidence level is too low" in low_confidence_report.reason
    assert low_confidence_report.confidence_recorded == 0.4


# ==========================================
# Phase 1: Continuation & Integration Tests
# ==========================================

def test_cognitive_state_restoration(tmp_path):
    """Verify SAGE session can be successfully restored and loaded into a CognitiveState object."""
    session_storage = tmp_path / "sessions"
    session_mgr = SessionStateManager(storage_path=str(session_storage))

    # Create a persistent session state on disk
    session = session_mgr.create_session(
        session_id="session_restoration_01",
        active_objectives=["obj_cognitive_continuity"]
    )
    session.add_completed_action("task_foundation_validated")
    session.add_pending_action("task_restoration_verification")
    session.add_decision("decision_use_pydantic_v2")
    session_mgr.save_session(session)

    # Load CognitiveState from persistent session
    cognitive_state = CognitiveStateLoader.load_cognitive_state(
        session_state=session,
        mission_queue=None
    )

    # Assert accurate state mapping
    assert cognitive_state.active_mission.mission_id == "session_restoration_01"
    assert "obj_cognitive_continuity" in cognitive_state.active_mission.objective
    assert len(cognitive_state.completed_milestones) == 1
    assert cognitive_state.completed_milestones[0].milestone_id == "task_foundation_validated"
    assert len(cognitive_state.validated_facts) == 1
    assert "decision_use_pydantic_v2" in cognitive_state.validated_facts[0].fact_id
    assert cognitive_state.confidence_state.overall_confidence > 0.0


def test_completed_milestone_protection_with_loader(tmp_path):
    """Verify completed milestone protection blocks reopening of completed work loaded from SAGE state."""
    session_storage = tmp_path / "sessions"
    session_mgr = SessionStateManager(storage_path=str(session_storage))

    session = session_mgr.create_session(
        session_id="session_protection_02",
        active_objectives=["obj_completed_work_protection"]
    )
    session.add_completed_action("task_milestone_secured")
    session_mgr.save_session(session)

    # Construct next action targeting the completed milestone
    state = CognitiveStateLoader.load_cognitive_state(
        session_state=session,
        mission_queue=None
    )
    state.next_action = CognitiveNextAction(
        action_id="task_milestone_secured",
        description="Attempt to reopen or modify task_milestone_secured",
        assigned_agent="agent_jules_sage"
    )

    # Evaluate using PFC Simulator
    simulator = PrefrontalCortexSimulator()
    report = simulator.evaluate_decision(state)

    assert report.outcome == DecisionGateOutcome.BLOCK
    assert "Completed milestone reopening/modification blocked" in report.reason


def test_mission_continuity_fresh_session(tmp_path):
    """Verify a fresh runtime session can fully reconstruct and verify essential cognitive states using the interface."""
    session_storage = tmp_path / "sessions"
    session_mgr = SessionStateManager(storage_path=str(session_storage))

    session = session_mgr.create_session(
        session_id="session_fresh_session_03",
        active_objectives=["obj_continuity_verification"]
    )
    session.add_completed_action("task_setup_environment")
    session.add_pending_action("task_run_full_continuity_verification")
    session_mgr.save_session(session)

    # Fresh session: reinitialize continuity manager
    retrieval_interface = ContinuityRetrievalInterface()
    reconstructed_state = retrieval_interface.reconstruct_and_verify(
        session_id="session_fresh_session_03",
        session_manager=session_mgr,
        mission_queue=None
    )

    # Verify key continuity invariants are successfully preserved
    assert reconstructed_state.active_mission.mission_id == "session_fresh_session_03"
    assert reconstructed_state.completed_milestones[0].milestone_id == "task_setup_environment"
    assert len(reconstructed_state.forbidden_regressions) > 0
    assert reconstructed_state.next_action.action_id == "task_run_full_continuity_verification"
    assert reconstructed_state.confidence_state.overall_confidence > 0.0


def test_pfc_execution_gate_integration(tmp_path):
    """Verify PFCGovernedExecutor intercepts SAGE developer workflows and coordinates execution on PROCEED."""
    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_feedback.json"

    session_mgr = SessionStateManager(storage_path=str(session_storage))
    from sage.experimental.act.continuity_control import ContinuityControlLoop
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_pfc_integration_04",
        objective="Verify PFC integration gate",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    task = SAGEMissionTask(
        task_id="task_pfc_integration_gate",
        objective_id="Verify PFC integration gate",
        priority_score=95.0,
        authorized=True,
        description="Verify PFC integration gate",
        assigned_agent="agent_jules_sage",
        evidence_requirements=[]
    )
    orchestrator.mission_queue.add_task(task)

    executor = PFCGovernedExecutor(orchestrator=orchestrator)

    # 1. Evaluate with a clean aligned state (PROCEED outcome)
    res_proceed = executor.execute_governed_cycle(task_id="task_pfc_integration_gate")
    assert res_proceed["execution_status"] == "EXECUTED"
    assert res_proceed["decision_outcome"] == DecisionGateOutcome.PROCEED
    assert orchestrator.mission_queue.get_task("task_pfc_integration_gate").status == "COMPLETED"

    # 2. Evaluate with a blocked state (e.g., trying to execute a completed task)
    res_blocked = executor.execute_governed_cycle(task_id="task_pfc_integration_gate")
    assert res_blocked["execution_status"] == "BLOCKED"
    assert res_blocked["decision_outcome"] == DecisionGateOutcome.BLOCK
    assert orchestrator.loop_state["mode"] == "MANUAL_INTERVENTION_PAUSED"


def test_generate_cognitive_continuity_validation_evidence(tmp_path):
    """Run an end-to-end governed cycle and generate the cognitive continuity validation evidence report."""
    import json
    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_feedback.json"

    session_mgr = SessionStateManager(storage_path=str(session_storage))
    from sage.experimental.act.continuity_control import ContinuityControlLoop
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_evidence_generation",
        objective="Verify PFC integration gate",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    task = SAGEMissionTask(
        task_id="task_continuity_validation",
        objective_id="Verify PFC integration gate",
        priority_score=95.0,
        authorized=True,
        description="Verify PFC integration gate",
        assigned_agent="agent_jules_sage",
        evidence_requirements=[]
    )
    orchestrator.mission_queue.add_task(task)

    executor = PFCGovernedExecutor(orchestrator=orchestrator)
    cycle_res = executor.execute_governed_cycle(task_id="task_continuity_validation")

    # Construct standard-compliant evidence package
    evidence_package = {
        "report_id": "cognitive_continuity_validation",
        "timestamp": time.time(),
        "state_loaded": {
            "session_id": orchestrator.session_id,
            "cognitive_state_dump": cycle_res["cognitive_state_dump"]
        },
        "mission_recovered": {
            "mission_id": orchestrator.session_id,
            "recovered_objectives": orchestrator.session.active_objectives,
            "recovered_completed_actions": orchestrator.session.completed_actions
        },
        "pfc_decision": {
            "outcome": cycle_res["decision_outcome"],
            "reason": cycle_res["decision_reason"],
            "confidence_recorded": cycle_res["confidence_recorded"],
            "checks_performed": cycle_res["checks_performed"]
        },
        "validation_result": {
            "execution_status": cycle_res["execution_status"],
            "success": cycle_res["execution_status"] == "EXECUTED"
        },
        "artifact_references": {
            "state_loader_source": "sage/experimental/cognitive/state_loader.py",
            "pfc_integration_source": "sage/experimental/cognitive/pfc_integration.py",
            "test_suite": "tests/experimental/test_cognitive_kernel.py"
        }
    }

    evidence_path = Path("evidence_capture/cognitive_continuity_validation.json")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence_package, f, indent=2, default=str)

    assert evidence_path.exists()


def test_openai_cognitive_runtime_activation(tmp_path):
    """Verify end-to-end OpenAI Runtime + Cognitive Continuity activation and generate canonical report."""
    import json
    session_storage = tmp_path / "sessions"
    record_storage = tmp_path / "records"
    evidence_output = tmp_path / "evidence" / "ccl_feedback.json"

    session_mgr = SessionStateManager(storage_path=str(session_storage))
    from sage.experimental.act.continuity_control import ContinuityControlLoop
    ccl = ContinuityControlLoop(session_manager=session_mgr, storage_path=str(record_storage))

    orchestrator = DeveloperWorkflowOrchestrator(
        session_id="session_openai_activation",
        objective="Verify PFC integration gate",
        ccl=ccl,
        evidence_output_path=str(evidence_output)
    )

    activator = OpenAICognitiveRuntimeActivator(orchestrator=orchestrator)

    # 1. Run actual activation flow with correct agent ID and auth token
    report = activator.activate_runtime_session(
        agent_id="openai-runtime-agent",
        auth_token="sage_secure_token_abc123",
        task_id="task_openai_runtime_activation",
        task_description="Verify PFC integration gate",
        session_id="session_openai_activation"
    )

    # 2. Verify all elements of the flow are proved and recorded
    assert report["agent_id"] == "openai-runtime-agent"
    assert report["authentication_result"]["success"] is True
    assert report["authentication_result"]["auth_token_hash"] != ""
    assert report["cognitive_state_result"]["state_loaded"] is True
    assert report["pfc_decision"]["outcome"] == DecisionGateOutcome.PROCEED
    assert report["execution_result"]["status"] == "EXECUTED"
    assert report["execution_result"]["success"] is True
    assert report["ledger_update_result"]["status_synchronized"] is True
    assert "task_openai_runtime_activation" in report["ledger_update_result"]["completed_actions"]

    # 3. Generate canonical evidence file at evidence_capture/openai_cognitive_runtime_activation.json
    evidence_path = Path("evidence_capture/openai_cognitive_runtime_activation.json")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    assert evidence_path.exists()
